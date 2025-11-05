from django.db import models
from django.utils import timezone
from dateutil.parser import isoparse
from datetime import timezone as dt_timezone  # ✅ Import correcto para UTC

class Devolucion(models.Model):
    prestamo_id = models.IntegerField()
    fecha = models.DateTimeField(auto_now_add=True)
    observacion = models.TextField(blank=True, null=True)
    recibidoPor_id = models.IntegerField()
    condicion = models.CharField(max_length=100, default="Bueno")
    prestamo_vencido = models.BooleanField(default=False)
    sancion_puntos = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def verificarTardanza(self, prestamo_data: dict, fecha_actual):
        """Verifica si el préstamo está vencido comparando fechas con zonas horarias seguras."""
        fecha_limite = isoparse(prestamo_data["fecha_compromiso"])

        # ✅ Convertir ambas fechas a UTC correctamente
        fecha_limite = fecha_limite.astimezone(dt_timezone.utc)
        fecha_actual = fecha_actual.astimezone(dt_timezone.utc)

        return fecha_actual > fecha_limite

    def __str__(self):
        return f"Devolución del préstamo {self.prestamo_id}"
