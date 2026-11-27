# -*- coding: utf-8 -*-
"""
gemini_service.py
Capa de integración con Google Gemini (modelo multimodal con visión),
usando el SDK vigente `google-genai` (el paquete anterior
`google-generativeai` fue descontinuado por Google).

Importante (diseño): a Gemini SOLO se le pide que "lea" el enunciado
(texto, foto del libro o boceto del canvas) y lo convierta en una
tabla de flujos de caja estructurada (JSON). El cálculo matemático
real de VAN/TIR lo hace siempre `solver.py` con NumPy/SciPy, nunca el
modelo de lenguaje. Esto evita que un error de la IA se traduzca en
una tasa de rendimiento incorrecta.
"""
from __future__ import annotations
import json
import re
from google import genai
from google.genai import types
from config import Config

_cliente = None


def _get_client() -> genai.Client:
    global _cliente
    if _cliente is None:
        if not Config.GOOGLE_API_KEY:
            raise ValueError(
                "No se configuró GOOGLE_API_KEY. Revisa tu archivo .env."
            )
        _cliente = genai.Client(api_key=Config.GOOGLE_API_KEY)
    return _cliente


ESQUEMA_JSON = """
Debes responder SOLO con un objeto JSON (sin texto adicional, sin markdown),
con esta forma exacta:

{
  "tipo_analisis": "simple" | "incremental",
  "tmar": <número decimal, ej. 0.13 para 13%, o null si no aplica>,
  "unidad_tiempo": "anual" | "mensual" | "quincenal" | "otro",
  "proyectos": [
    {
      "nombre": "A",
      "flujos": [<monto periodo 0>, <monto periodo 1>, ...]
    }
  ],
  "enunciado_resumen": "<resumen breve en español de qué pide el ejercicio>"
}

Reglas para construir "flujos":
- El periodo 0 es el momento de la inversión inicial (normalmente NEGATIVO).
- Si el problema menciona un valor de salvamento o venta final, súmalo en el
  ÚLTIMO periodo junto con el flujo normal de ese periodo.
- Si los ingresos crecen con un gradiente aritmético o geométrico, o si hay
  periodos con mensualidades agrupadas, calcula tú mismo cada monto neto por
  periodo y entrégalo ya como número (no dejes fórmulas sin resolver).
- Si el ejercicio compara varias alternativas (varios proyectos/países/
  máquinas) usa "tipo_analisis": "incremental" y llena un objeto por cada
  proyecto dentro de "proyectos", todos con la MISMA cantidad de periodos
  (rellena con 0 los periodos que no apliquen).
- Si es un solo flujo de caja (una sola inversión), usa
  "tipo_analisis": "simple" y entrega un único proyecto.
- Si no puedes leer algún dato con certeza, usa null en ese campo específico
  en vez de inventar un número.
"""


def _extraer_json(texto_crudo: str) -> dict:
    """Limpia posibles cercos de markdown y parsea JSON de forma tolerante."""
    limpio = (texto_crudo or "").strip()
    limpio = re.sub(r"^```(json)?", "", limpio).strip()
    limpio = re.sub(r"```$", "", limpio).strip()
    return json.loads(limpio)


def analizar_problema(texto: str | None = None,
                       imagen_bytes: bytes | None = None,
                       mime_type: str = "image/png") -> dict:
    """
    Envía el enunciado (texto y/o imagen) a Gemini y devuelve el JSON
    estructurado de flujos de caja ya listo para el solver.

    Lanza ValueError con un mensaje claro en español si algo falla, para
    que la UI pueda mostrarlo directamente.
    """
    cliente = _get_client()

    contenidos = [
        "Eres un asistente experto en Ingeniería Económica (Análisis de la "
        "Tasa de Rendimiento / TIR). Analiza el siguiente problema y "
        "extrae sus datos." + ESQUEMA_JSON
    ]
    if texto:
        contenidos.append(f"\nEnunciado (texto): {texto}")
    if imagen_bytes:
        contenidos.append(types.Part.from_bytes(data=imagen_bytes, mime_type=mime_type))

    try:
        respuesta = cliente.models.generate_content(
            model=Config.GEMINI_MODEL,
            contents=contenidos,
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json",
            ),
        )
    except Exception as exc:  # errores de red, cuota, API key inválida, etc.
        raise ValueError(f"Error al contactar la API de Gemini: {exc}") from exc

    if not getattr(respuesta, "text", None):
        raise ValueError(
            "Gemini no devolvió una respuesta (puede que la imagen haya "
            "sido bloqueada por filtros de seguridad). Intenta con otra foto."
        )

    try:
        datos = _extraer_json(respuesta.text)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError(
            "No se pudo interpretar la respuesta de la IA como datos "
            "estructurados. Intenta con una imagen más clara o ingresa "
            "los datos manualmente."
        ) from exc

    _validar_esquema(datos)
    return datos


def _validar_esquema(datos: dict) -> None:
    if "proyectos" not in datos or not isinstance(datos["proyectos"], list):
        raise ValueError("La IA no devolvió ningún flujo de caja reconocible.")
    if len(datos["proyectos"]) == 0:
        raise ValueError("La IA no pudo extraer ningún proyecto del enunciado.")
    for p in datos["proyectos"]:
        if "flujos" not in p or not isinstance(p["flujos"], list) or len(p["flujos"]) < 2:
            raise ValueError(
                f"El proyecto '{p.get('nombre', '?')}' no tiene un flujo de "
                f"caja válido (se necesitan al menos 2 periodos)."
            )
        if any(v is None for v in p["flujos"]):
            raise ValueError(
                f"Hay montos que la IA no pudo leer con certeza en el "
                f"proyecto '{p.get('nombre', '?')}'. Revisa/edita los datos "
                f"extraídos antes de resolver."
            )
