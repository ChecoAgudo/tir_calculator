# -*- coding: utf-8 -*-
"""Integración con Groq para extraer flujos de caja desde texto e imágenes."""
from __future__ import annotations

import base64
import json
import re

from config import Config
from groq import APIConnectionError, APIStatusError, APITimeoutError, Groq


_cliente = None

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


def _get_client() -> Groq:
    global _cliente
    if _cliente is None:
        if not Config.GROQ_API_KEY:
            raise ValueError(
                "No se configuró GROQ_API_KEY. Añade tu clave al archivo .env "
                "y reinicia Flask."
            )
        _cliente = Groq(
            api_key=Config.GROQ_API_KEY,
            timeout=120,
            max_retries=0,
        )
    return _cliente


def _detalle_error_api(error: APIStatusError) -> str:
    detalle = getattr(error, "body", None)
    if isinstance(detalle, dict):
        error_cuerpo = detalle.get("error")
        if isinstance(error_cuerpo, dict):
            return str(error_cuerpo.get("message", error_cuerpo))
        if error_cuerpo:
            return str(error_cuerpo)
    if detalle:
        return str(detalle)
    return str(error)


def analizar_problema(
    texto: str | None = None,
    imagen_bytes: bytes | None = None,
    mime_type: str = "image/png",
) -> dict:
    """Envía el texto y/o la imagen a Groq y valida el JSON devuelto."""
    cliente = _get_client()

    texto_usuario = texto.strip() if texto else ""
    if not texto_usuario:
        texto_usuario = "Analiza el problema de Ingeniería Económica de la imagen adjunta."

    if imagen_bytes:
        imagen_base64 = base64.b64encode(imagen_bytes).decode("ascii")
        contenido_usuario = [
            {"type": "text", "text": texto_usuario},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{imagen_base64}",
                },
            },
        ]
    else:
        contenido_usuario = texto_usuario

    try:
        respuesta = cliente.chat.completions.create(
            model=Config.GROQ_MODEL,
            messages=[
                {"role": "system", "content": _INSTRUCCIONES},
                {"role": "user", "content": contenido_usuario},
            ],
            temperature=0.1,
            max_completion_tokens=4096,
            response_format={"type": "json_object"},
        )
    except APIStatusError as exc:
        detalle = _detalle_error_api(exc)
        if exc.status_code == 401:
            mensaje = "Groq rechazó la clave. Revisa GROQ_API_KEY en .env."
        elif exc.status_code == 403 and "1010" in detalle:
            mensaje = (
                "El filtro de tráfico de Groq/Cloudflare bloqueó la conexión "
                "(error 1010). El cliente ya usa el SDK oficial de Groq; si "
                "persiste, prueba sin VPN/proxy o consulta a soporte de Groq."
            )
        elif exc.status_code == 403:
            mensaje = "Groq denegó el acceso. Revisa el acceso al modelo y tu cuenta."
        elif exc.status_code == 429:
            mensaje = (
                "Groq indicó que se alcanzó un límite o la cuota disponible. "
                "Revisa Usage, Limits y Billing en tu consola de Groq."
            )
        else:
            mensaje = f"Groq respondió HTTP {exc.status_code}."
        raise ValueError(f"{mensaje} Detalle: {detalle}") from exc
    except APITimeoutError as exc:
        raise ValueError(
            "La solicitud a Groq tardó demasiado. Intenta nuevamente."
        ) from exc
    except APIConnectionError as exc:
        raise ValueError(
            "No se pudo conectar con Groq. Verifica tu conexión a internet."
        ) from exc

    try:
        texto_respuesta = respuesta.choices[0].message.content
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("Groq no devolvió el contenido esperado.") from exc

    if not texto_respuesta:
        raise ValueError("Groq devolvió una respuesta vacía.")

    try:
        datos = _extraer_json(texto_respuesta)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError(
            "No se pudo interpretar la respuesta de Groq como JSON. "
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
                f"Hay montos que Groq no pudo leer con certeza en el "
                f"proyecto '{proyecto.get('nombre', '?')}'. Revisa los datos "
                "extraídos antes de resolver."
            )
