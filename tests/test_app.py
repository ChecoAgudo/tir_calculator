import unittest

from app import app


class ResolverApiTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_pagina_incluye_controles_y_graficos_sin_cdn(self):
        respuesta = self.client.get("/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(b'id="btn-quitar-periodo"', respuesta.data)
        self.assertIn(b'id="unidad-periodo"', respuesta.data)
        self.assertNotIn(b"chart.umd.js", respuesta.data)

    def test_resuelve_tir_y_muestra_calculo_van_a_tmar(self):
        respuesta = self.client.post("/api/resolver", json={
            "tipo_analisis": "simple",
            "tmar": 0.1,
            "proyectos": [{
                "nombre": "Proyecto A",
                "flujos": [-1000, 1000, 250],
            }],
        })

        self.assertEqual(respuesta.status_code, 200)
        resultado = respuesta.get_json()
        self.assertAlmostEqual(resultado["tir"][0], 0.20710678, places=6)
        self.assertAlmostEqual(resultado["van_a_tmar"], 115.70, places=2)
        self.assertTrue(any("VAN(10.00 %)" in paso["contenido"] for paso in resultado["pasos"]))

    def test_compara_alternativas_incrementales(self):
        respuesta = self.client.post("/api/resolver", json={
            "tipo_analisis": "incremental",
            "tmar": 0.1,
            "proyectos": [
                {"nombre": "A", "flujos": [-1000, 600, 600]},
                {"nombre": "B", "flujos": [-1500, 1000, 1000]},
            ],
        })

        self.assertEqual(respuesta.status_code, 200)
        resultado = respuesta.get_json()
        self.assertEqual(resultado["tipo_analisis"], "incremental")
        self.assertIn("B", resultado["respuesta_final"])
        self.assertTrue(resultado["pasos_incremental"])

    def test_detecta_tir_multiple_y_muestra_comprobaciones(self):
        respuesta = self.client.post("/api/resolver", json={
            "proyectos": [{"nombre": "Mixto", "flujos": [-100, 230, -132]}],
        })

        self.assertEqual(respuesta.status_code, 200)
        resultado = respuesta.get_json()
        self.assertEqual(resultado["tir"], [0.1, 0.2])
        self.assertEqual(resultado["pasos"][-1]["titulo"], "6. Verificar las tasas encontradas")
        self.assertIn("VAN(10.00 %)", resultado["pasos"][-1]["contenido"])

    def test_rechaza_periodos_vacios_y_tmar_invalida(self):
        respuesta_flujo = self.client.post("/api/resolver", json={
            "proyectos": [{"nombre": "A", "flujos": [-1000, None]}],
        })
        respuesta_tmar = self.client.post("/api/resolver", json={
            "tmar": -1,
            "proyectos": [{"nombre": "A", "flujos": [-1000, 1200]}],
        })

        self.assertEqual(respuesta_flujo.status_code, 400)
        self.assertIn("debe ser numérico", respuesta_flujo.get_json()["error"])
        self.assertEqual(respuesta_tmar.status_code, 400)
        self.assertIn("mayor que -100%", respuesta_tmar.get_json()["error"])

    def test_no_expone_la_ruta_de_analisis_por_ia(self):
        respuesta = self.client.post("/api/analizar", json={"texto": "ejercicio"})
        self.assertEqual(respuesta.status_code, 404)


if __name__ == "__main__":
    unittest.main()
