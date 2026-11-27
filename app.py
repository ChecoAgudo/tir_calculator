# -*- coding: utf-8 -*-
"""
app.py
Aplicación Flask: sirve el frontend y expone la API REST que conecta
Groq (lectura del problema) con solver.py (cálculo exacto de VAN/TIR).

Rutas:
  GET  /                  -> interfaz web (SPA de una sola página)
  POST /api/analizar      -> recibe texto y/o imagen, devuelve JSON extraído
  POST /api/resolver      -> recibe flujos (extraídos o editados a mano),
                             devuelve la solución paso a paso + datos de gráficos
  GET  /api/salud         -> healthcheck simple para plataformas de deploy
"""
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

from config import Config
import groq_service
import solver

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/salud")
def salud():
    return jsonify({"estado": "ok"})


@app.post("/api/analizar")
def analizar():
    """
    Acepta:
      - multipart/form-data con un archivo 'imagen' (foto o canvas exportado)
        y/o un campo 'texto'
      - o JSON { "texto": "..." }
    Devuelve el JSON estructurado que Groq extrajo del enunciado.
    """
    try:
        texto = None
        imagen_bytes = None
        mime_type = "image/png"

        if request.content_type and "multipart/form-data" in request.content_type:
            texto = request.form.get("texto") or None
            archivo = request.files.get("imagen")
            if archivo and archivo.filename:
                imagen_bytes = archivo.read()
                mime_type = archivo.mimetype or "image/png"
        else:
            cuerpo = request.get_json(silent=True) or {}
            texto = cuerpo.get("texto")

        if not texto and not imagen_bytes:
            return jsonify({"error": "Envía un texto o una imagen para analizar."}), 400

        datos = groq_service.analizar_problema(
            texto=texto, imagen_bytes=imagen_bytes, mime_type=mime_type
        )
        return jsonify(datos)

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 422
    except Exception as exc:  # salvaguarda final
        return jsonify({"error": f"Error inesperado: {exc}"}), 500


@app.post("/api/resolver")
def resolver():
    """
    Espera JSON:
    {
      "tipo_analisis": "simple" | "incremental",
      "tmar": 0.13,                 (opcional si tipo_analisis es "simple")
      "proyectos": [{"nombre": "A", "flujos": [-1000, 1000, 250]}, ...]
    }
    Devuelve fundamento teórico, pasos, respuesta final y datos de gráficos.
    """
    try:
        cuerpo = request.get_json(force=True)
        tipo = cuerpo.get("tipo_analisis", "simple")
        proyectos = cuerpo.get("proyectos", [])
        tmar = cuerpo.get("tmar")

        if not proyectos:
            return jsonify({"error": "No se recibió ningún flujo de caja."}), 400
        for p in proyectos:
            if not isinstance(p.get("flujos"), list) or len(p["flujos"]) < 2:
                return jsonify({
                    "error": f"El proyecto '{p.get('nombre', '?')}' necesita "
                             f"al menos 2 periodos de flujo de caja."
                }), 400

        fundamento = (
            "La Tasa Interna de Retorno (TIR) es la tasa de interés i que "
            "hace que el Valor Actual Neto (VAN) del flujo de caja sea "
            "igual a cero: VAN(i) = Σ CF_t / (1+i)^t = 0. Para inversiones "
            "simples (un solo cambio de signo) existe una única TIR real "
            "positiva; para inversiones mixtas puede haber varias, y la "
            "regla de los signos de Descartes acota cuántas."
        )

        if tipo == "incremental" and len(proyectos) > 1:
            if tmar is None:
                return jsonify({"error": "El análisis incremental requiere una TMAR."}), 400

            detalle_individual = []
            for p in proyectos:
                r = solver.encontrar_tir(p["flujos"])
                detalle_individual.append({
                    "nombre": p["nombre"],
                    "flujos": p["flujos"],
                    "tir": r["tir"],
                    "clasificacion": r["clasificacion"],
                    "van_a_tmar": round(solver.van(p["flujos"], tmar), 2),
                    "grafico_van": solver.curva_van(p["flujos"]),
                    "grafico_flujo": solver.datos_flujo_caja(p["flujos"]),
                })

            incremental = solver.analisis_incremental(proyectos, tmar)

            return jsonify({
                "fundamento_teorico": fundamento,
                "tipo_analisis": "incremental",
                "tmar": tmar,
                "proyectos": detalle_individual,
                "pasos_incremental": incremental["pasos"],
                "respuesta_final": (
                    f"La mejor alternativa según el análisis incremental "
                    f"(TMAR = {solver.fmt_pct(tmar)}) es: "
                    f"{incremental['mejor_proyecto']}."
                ),
            })

        # --- Caso simple: un solo proyecto ---
        proy = proyectos[0]
        resultado = solver.encontrar_tir(proy["flujos"])
        tasas = resultado["tir"]

        if tasas:
            if len(tasas) == 1:
                respuesta_final = f"TIR = {solver.fmt_pct(tasas[0])}."
            else:
                respuesta_final = (
                    "El proyecto tiene TIR múltiple (inversión mixta). "
                    "Valores candidatos: "
                    + ", ".join(solver.fmt_pct(t) for t in tasas) + "."
                )
            if tmar is not None:
                mejor = max(tasas, key=lambda t: t) if len(tasas) else None
                aceptar = mejor is not None and mejor >= tmar
                respuesta_final += (
                    f" Comparada con la TMAR ({solver.fmt_pct(tmar)}), la "
                    f"inversión {'SÍ' if aceptar else 'NO'} es conveniente."
                )
        else:
            respuesta_final = "El proyecto no tiene una TIR real válida."

        return jsonify({
            "fundamento_teorico": fundamento,
            "tipo_analisis": "simple",
            "tmar": tmar,
            "proyecto": {
                "nombre": proy.get("nombre", "Proyecto"),
                "flujos": proy["flujos"],
            },
            "clasificacion": resultado["clasificacion"],
            "pasos": resultado["pasos"],
            "tir": tasas,
            "respuesta_final": respuesta_final,
            "graficos": {
                "curva_van": solver.curva_van(proy["flujos"]),
                "flujo_caja": solver.datos_flujo_caja(proy["flujos"]),
            },
        })

    except Exception as exc:
        return jsonify({"error": f"No se pudo resolver el problema: {exc}"}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
