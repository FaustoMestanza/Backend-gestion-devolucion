from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch
from datetime import datetime, timedelta, timezone

class DevolucionAPITest(APITestCase):

    @patch("devolucion.views.requests.get")
    @patch("devolucion.views.requests.patch")
    def test_crear_devolucion_exitosa(self, mock_patch, mock_get):
        # Mock préstamo
        mock_get.side_effect = [
            type("Resp", (), {
                "status_code": 200,
                "json": lambda: {
                    "equipo_id": 5,
                    "fecha_compromiso": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
                }
            }),
            # Mock equipo
            type("Resp", (), {
                "status_code": 200,
                "json": lambda: {"estado": "Prestado"}
            }),
        ]

        data = {
            "prestamo_id": 1,
            "recibidoPor_id": 99,
            "sancion_puntos": 2
        }

        response = self.client.post(
            "/devoluciones/",
            data,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @patch("devolucion.views.requests.get")
    def test_verificar_prestamo_vencido(self, mock_get):
        mock_get.side_effect = [
            # préstamo
            type("Resp", (), {
                "status_code": 200,
                "json": lambda: {
                    "equipo_id": 3,
                    "fecha_compromiso": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
                }
            }),
            # equipo
            type("Resp", (), {
                "status_code": 200,
                "json": lambda: {"estado": "Prestado"}
            }),
        ]

        response = self.client.get("/devoluciones/verificar/1/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["estado"], "vencido")
