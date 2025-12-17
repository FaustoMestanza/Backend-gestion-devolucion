from django.test import TestCase
from datetime import datetime, timedelta, timezone
from devolucion.models import Devolucion

class DevolucionModelTest(TestCase):

    def test_verificar_tardanza_false(self):
        prestamo = {
            "fecha_compromiso": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        }
        ahora = datetime.now(timezone.utc)

        d = Devolucion()
        self.assertFalse(d.verificarTardanza(prestamo, ahora))

    def test_verificar_tardanza_true(self):
        prestamo = {
            "fecha_compromiso": (datetime.now(timezone.utc) - timedelta(days1:=1)).isoformat()
        }
        ahora = datetime.now(timezone.utc)

        d = Devolucion()
        self.assertTrue(d.verificarTardanza(prestamo, ahora))

    def test_str_devolucion(self):
        d = Devolucion.objects.create(
            prestamo_id=10,
            recibidoPor_id=1
        )
        self.assertIn("Devolución del préstamo", str(d))
