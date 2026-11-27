# -*- coding: utf-8 -*-
"""Integración local con Ollama para extraer flujos de caja desde texto e imágenes."""
from __future__ import annotations

import base64
import json
import re
import urllib.error
import urllib.request

from config import Config


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

_INSTRUCCIONES = (
    "Eres un asistente experto en Ingeniería Económica y análisis de TIR. "
    "Extrae los datos del problema y devuelve el objeto JSON indicado. "
    "No calcules la TIR final; eso lo hará el programa.\n" + ESQUEMA_JSON
)


def _extraer_json(texto_crudo: str) -> dict:
    """Limpia posibles cercos de markdown y parsea JSON de forma tolerante."""
    limpio = (texto_crudo or "").strip()
    limpio = re.sub(r"^```(?:json)?", "", limpio, flags=re.IGNORECASE).strip()
    limpio = re.sub(r"```$", "", limpio).strip()
    return json.loads(limpio)


def analizar_problema(
    texto: str | None = None,
    imagen_bytes: bytes | None = None,
) -> dict:
    """Solicita a Ollama el JSON estructurado de flujos de caja."""
    contenido = texto.strip() if texto else ""
    if not contenido:
        contenido = "Analiza el problema de Ingeniería Económica de la imagen adjunta."

    mensaje_usuario: dict[str, object] = {"role": "user", "content": contenido}
    if imagen_bytes:
        mensaje_usuario["images"] = [base64.b64encode(imagen_bytes).decode("ascii")]

    payload = {
        "model": Config.OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": _INSTRUCCIONES},
            mensaje_usuario,
        ],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.1},
    }
    request = urllib.request.Request(
        f"{Config.OLLAMA_BASE_URL}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            respuesta_api = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detalle = exc.read().decode("utf-8", errors="replace")
        try:
            detalle_json = json.loads(detalle)
            if isinstance(detalle_json, dict):
                detalle = detalle_json.get("error", detalle)
        except json.JSONDecodeError:
            pass
        raise ValueError(f"Ollama respondió HTTP {exc.code}: {detalle}") from exc
    except urllib.error.URLError as exc:
        raise ValueError(
            "No se pudo conectar con Ollama en "
            f"{Config.OLLAMA_BASE_URL}. Abre Ollama y verifica que esté "
            "ejecutándose en esta computadora."
        ) from exc
    except TimeoutError as exc:
        raise ValueError(
            "Ollama tardó demasiado en responder. Prueba con una imagen "
            "más pequeña o un equipo con más memoria."
        ) from exc
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError("Ollama devolvió una respuesta HTTP que no es JSON.") from exc

    try:
        texto_respuesta = respuesta_api["message"]["content"]
    except (KeyError, TypeError) as exc:
        raise ValueError("Ollama no devolvió el contenido esperado.") from exc

    if not texto_respuesta:
        raise ValueError("Ollama devolvió una respuesta vacía.")

    try:
        datos = _extraer_json(texto_respuesta)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError(
            "No se pudo interpretar la respuesta de Ollama como JSON. "
            "Intenta con un enunciado o una imagen más claros."
        ) from exc

    _validar_esquema(datos)
    return datos


def _validar_esquema(datos: dict) -> None:
    if "proyectos" not in datos or not isinstance(datos["proyectos"], list):
        raise ValueError("La IA no devolvió ningún flujo de caja reconocible.")
    if len(datos["proyectos"]) == 0:
        raise ValueError("La IA no pudo extraer ningún proyecto del enunciado.")
    for proyecto in datos["proyectos"]:
        flujos = proyecto.get("flujos")
        if not isinstance(flujos, list) or len(flujos) < 2:
            raise ValueError(
                f"El proyecto '{proyecto.get('nombre', '?')}' no tiene un "
                "flujo de caja válido (se necesitan al menos 2 periodos)."
            )
        if any(monto is None for monto in flujos):
            raise ValueError(
                f"Hay montos que Ollama no pudo leer con certeza en el "
                f"proyecto '{proyecto.get('nombre', '?')}'. Revisa los datos "
                "extraídos antes de resolver."
            )
