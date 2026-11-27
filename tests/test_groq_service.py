import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import httpx
import groq_service
from groq import APIConnectionError, APIStatusError


class FakeCompletions:
    def __init__(self, content=None, error=None):
        self.content = content
        self.error = error
        self.request_payload = None

    def create(self, **kwargs):
        self.request_payload = kwargs
        if self.error:
            raise self.error
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=self.content)
                )
            ]
        )


class GroqServiceTests(unittest.TestCase):
    def setUp(self):
        self.api_key_patch = patch.object(
            groq_service.Config, "GROQ_API_KEY", "test-api-key"
        )
        self.api_key_patch.start()
        self.addCleanup(self.api_key_patch.stop)
        self.client_patch = patch.object(groq_service, "_cliente", None)
        self.client_patch.start()
        self.addCleanup(self.client_patch.stop)

    def test_sends_text_and_base64_image_and_validates_result(self):
        result = {
            "tipo_analisis": "simple",
            "tmar": None,
            "unidad_tiempo": "anual",
            "proyectos": [{"nombre": "A", "flujos": [-100, 120]}],
            "enunciado_resumen": "Calcular la TIR",
        }
        completions = FakeCompletions(json.dumps(result))
        fake_client = SimpleNamespace(
            chat=SimpleNamespace(completions=completions)
        )
        with patch.object(groq_service, "Groq", return_value=fake_client) as sdk:
            actual = groq_service.analizar_problema(
                texto="Calcula la TIR",
                imagen_bytes=b"image-bytes",
                mime_type="image/png",
            )

        self.assertEqual(actual, result)
        sdk.assert_called_once_with(
            api_key="test-api-key", timeout=120, max_retries=0
        )
        user_message = completions.request_payload["messages"][1]
        self.assertEqual(user_message["content"][0]["text"], "Calcula la TIR")
        self.assertEqual(
            user_message["content"][1]["image_url"]["url"],
            "data:image/png;base64,aW1hZ2UtYnl0ZXM=",
        )
        self.assertEqual(
            completions.request_payload["response_format"],
            {"type": "json_object"},
        )

    def test_explains_cloudflare_1010_as_client_block(self):
        request = httpx.Request(
            "POST", "https://api.groq.com/openai/v1/chat/completions"
        )
        response = httpx.Response(403, request=request)
        error = APIStatusError(
            "Forbidden", response=response, body="error code: 1010"
        )
        fake_completions = FakeCompletions(error=error)
        fake_client = SimpleNamespace(
            chat=SimpleNamespace(completions=fake_completions)
        )
        with patch.object(groq_service, "Groq", return_value=fake_client):
            with self.assertRaisesRegex(ValueError, "Cloudflare") as raised:
                groq_service.analizar_problema(texto="Calcula la TIR")

        self.assertIn("error code: 1010", str(raised.exception))

    def test_reports_connection_failure(self):
        request = httpx.Request(
            "POST", "https://api.groq.com/openai/v1/chat/completions"
        )
        error = APIConnectionError(request=request)
        fake_completions = FakeCompletions(error=error)
        fake_client = SimpleNamespace(
            chat=SimpleNamespace(completions=fake_completions)
        )
        with patch.object(
            groq_service, "Groq", return_value=fake_client
        ):
            with self.assertRaisesRegex(ValueError, "No se pudo conectar con Groq"):
                groq_service.analizar_problema(texto="Calcula la TIR")

    def test_reports_missing_key_before_requesting_groq(self):
        with patch.object(groq_service.Config, "GROQ_API_KEY", ""):
            with patch.object(groq_service, "Groq") as sdk:
                with self.assertRaisesRegex(ValueError, "GROQ_API_KEY"):
                    groq_service.analizar_problema(texto="Calcula la TIR")

        sdk.assert_not_called()


if __name__ == "__main__":
    unittest.main()
