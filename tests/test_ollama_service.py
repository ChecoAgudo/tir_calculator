import io
import json
import unittest
from unittest.mock import patch
from urllib.error import URLError

import ollama_service


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return self.data


class OllamaServiceTests(unittest.TestCase):
    def test_sends_text_and_base64_image_and_validates_result(self):
        result = {
            "tipo_analisis": "simple",
            "tmar": None,
            "unidad_tiempo": "anual",
            "proyectos": [{"nombre": "A", "flujos": [-100, 120]}],
            "enunciado_resumen": "Calcular la TIR",
        }
        response_body = json.dumps({
            "message": {"content": json.dumps(result)}
        }).encode("utf-8")
        captured = {}

        def fake_urlopen(request, timeout):
            captured["payload"] = json.loads(request.data.decode("utf-8"))
            captured["url"] = request.full_url
            return FakeResponse(response_body)

        with patch.object(ollama_service.urllib.request, "urlopen", fake_urlopen):
            actual = ollama_service.analizar_problema(
                texto="Calcula la TIR", imagen_bytes=b"image-bytes"
            )

        self.assertEqual(actual, result)
        self.assertTrue(captured["url"].endswith("/api/chat"))
        user_message = captured["payload"]["messages"][1]
        self.assertEqual(user_message["content"], "Calcula la TIR")
        self.assertEqual(user_message["images"], ["aW1hZ2UtYnl0ZXM="])
        self.assertFalse(captured["payload"]["stream"])

    def test_reports_ollama_connection_failure(self):
        with patch.object(
            ollama_service.urllib.request,
            "urlopen",
            side_effect=URLError("connection refused"),
        ):
            with self.assertRaisesRegex(ValueError, "No se pudo conectar con Ollama"):
                ollama_service.analizar_problema(texto="Calcula la TIR")


if __name__ == "__main__":
    unittest.main()
