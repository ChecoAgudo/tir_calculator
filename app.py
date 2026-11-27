# -*- coding: utf-8 -*-
"""Aplicación Flask para resolver ejercicios de VAN y TIR con datos manuales."""
from math import isfinite

from flask import Flask, jsonify, render_template, request

import solver

app = Flask(__name__)


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/salud")
def salud():
    return jsonify({"estado": "ok"})


def _validar_datos(cuerpo):
    if not isinstance(cuerpo, dict):
        raise ValueError("Envía los datos del ejercicio en formato JSON.")

    tipo = cuerpo.get("tipo_analisis", "simple")
    if tipo not in ("simple", "incremental"):
        raise ValueError("El tipo de análisis debe ser simple o incremental.")

    proyectos = cuerpo.get("proyectos")
    if not isinstance(proyectos, list):
        raise ValueError("Agrega al menos un proyecto con sus flujos de caja.")

    minimo = 2 if tipo == "incremental" else 1
    if len(proyectos) < minimo:
        raise ValueError(
            "El análisis incremental requiere al menos dos alternativas."
            if tipo == "incremental"
            else "Agrega un proyecto para resolver."
        )
    if tipo == "simple" and len(proyectos) != 1:
        raise ValueError("El análisis simple debe contener un solo proyecto.")

    proyectos_validos = []
    for indice, proyecto in enumerate(proyectos, start=1):
        if not isinstance(proyecto, dict):
            raise ValueError(f"El proyecto {indice} no tiene un formato válido.")

        nombre = str(proyecto.get("nombre") or f"Proyecto {indice}").strip()
        flujos = proyecto.get("flujos")
        if not isinstance(flujos, list) or len(flujos) < 2:
            raise ValueError(
                f"{nombre} necesita al menos dos periodos de flujo de caja."
            )

        flujos_validos = []
        for periodo, monto in enumerate(flujos):
            if isinstance(monto, bool) or not isinstance(monto, (int, float)):
                raise ValueError(
                    f"El monto del periodo {periodo} de {nombre} debe ser numérico."
                )
            try:
                valor = float(monto)
            except OverflowError as exc:
                raise ValueError(
                    f"El monto del periodo {periodo} de {nombre} está fuera de rango."
                ) from exc
            if not isfinite(valor):
                raise ValueError(
                    f"El monto del periodo {periodo} de {nombre} debe ser finito."
                )
            flujos_validos.append(valor)

        if not any(flujos_validos):
            raise ValueError(f"{nombre} no puede tener todos sus flujos en cero.")

        proyectos_validos.append({"nombre": nombre, "flujos": flujos_validos})

    tmar = cuerpo.get("tmar")
    if tmar is not None:
        if isinstance(tmar, bool) or not isinstance(tmar, (int, float)):
            raise ValueError("La TMAR debe ser un porcentaje numérico.")
        try:
            tmar = float(tmar)
        except OverflowError as exc:
            raise ValueError("La TMAR está fuera de rango.") from exc
        if not isfinite(tmar) or tmar <= -1:
            raise ValueError("La TMAR debe ser mayor que -100%.")
    if tipo == "incremental" and tmar is None:
        raise ValueError("El análisis incremental requiere una TMAR.")

    return tipo, proyectos_validos, tmar


@app.post("/api/resolver")
def resolver():
    if not request.is_json:
        return jsonify({"error": "Envía los datos del ejercicio en formato JSON."}), 400

    try:
        tipo, proyectos, tmar = _validar_datos(request.get_json(silent=True))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    fundamento = (
        "La Tasa Interna de Retorno (TIR) es la tasa i que hace que el "
        "Valor Actual Neto (VAN) sea cero: VAN(i) = Σ CFₜ / (1+i)ᵗ = 0. "
        "Cada flujo ingresado representa el monto neto de su periodo; suma "
        "en la tabla cualquier ingreso, costo, gradiente o valor de "
        "salvamento correspondiente a ese periodo."
    )

    if tipo == "incremental":
        detalle_individual = []
        for proyecto in proyectos:
            resultado = solver.encontrar_tir(proyecto["flujos"])
            detalle_individual.append({
                "nombre": proyecto["nombre"],
                "flujos": proyecto["flujos"],
                "tir": resultado["tir"],
                "clasificacion": resultado["clasificacion"],
                "van_a_tmar": round(solver.van(proyecto["flujos"], tmar), 2),
                "pasos": resultado["pasos"] + solver.pasos_van(proyecto["flujos"], tmar),
                "grafico_van": solver.curva_van(proyecto["flujos"]),
                "grafico_flujo": solver.datos_flujo_caja(proyecto["flujos"]),
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

    proyecto = proyectos[0]
    resultado = solver.encontrar_tir(proyecto["flujos"])
    tasas = resultado["tir"]

    if tasas:
        respuesta_final = (
            f"TIR = {solver.fmt_pct(tasas[0])}."
            if len(tasas) == 1
            else "El proyecto tiene TIR múltiple. Valores candidatos: "
            + ", ".join(solver.fmt_pct(tasa) for tasa in tasas) + "."
        )
    else:
        respuesta_final = "El proyecto no tiene una TIR real válida."

    van_a_tmar = None
    if tmar is not None:
        van_a_tmar = solver.van(proyecto["flujos"], tmar)
        resultado["pasos"].extend(solver.pasos_van(proyecto["flujos"], tmar))
        respuesta_final += (
            f" A la TMAR ({solver.fmt_pct(tmar)}), el VAN es "
            f"{solver.fmt_money(van_a_tmar)}; la inversión "
            f"{'es' if van_a_tmar >= 0 else 'no es'} conveniente."
        )

    return jsonify({
        "fundamento_teorico": fundamento,
        "tipo_analisis": "simple",
        "tmar": tmar,
        "proyecto": proyecto,
        "clasificacion": resultado["clasificacion"],
        "pasos": resultado["pasos"],
        "tir": tasas,
        "van_a_tmar": van_a_tmar,
        "respuesta_final": respuesta_final,
        "graficos": {
            "curva_van": solver.curva_van(proyecto["flujos"]),
            "flujo_caja": solver.datos_flujo_caja(proyecto["flujos"]),
        },
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
