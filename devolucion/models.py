from django.db import models
from django.utils import timezone       # ✅ para manejar fechas con zona horaria
from dateutil.parser import isoparse    # ✅ para leer la fecha ISO que viene del microservicio

class Devolucion(models.Model):
    prestamo_id = models.IntegerField()  # ID del préstamo en otro microservicio
    fecha = models.DateTimeField(auto_now_add=True)
    observacion = models.TextField(blank=True, null=True)
    recibidoPor_id = models.IntegerField()  # ID del usuario que recibe el equipo
    condicion = models.CharField(max_length=100, default="Bueno")
    prestamo_vencido = models.BooleanField(default=False)
    sancion_puntos = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def verificarTardanza(self, prestamo_data: dict, fecha_actual: timezone.datetime) -> bool:
        """
        Verifica si el préstamo está vencido comparando la fecha de compromiso
        con la fecha actual, manejando correctamente la zona horaria.
        """
        # La fecha viene en formato ISO con zona horaria (ej: 2025-11-05T01:09:06.986354-05:00)
        fecha_limite = isoparse(prestamo_data["fecha_compromiso"])

        # Normalizamos ambas fechas a UTC para evitar el error "naive vs aware"
        fecha_limite = fecha_limite.astimezone(timezone.utc)
        fecha_actual = fecha_actual.astimezone(timezone.utc)

        return fecha_actual > fecha_limite

    def __str__(self):
        return f"Devolución del préstamo {self.prestamo_id}"
