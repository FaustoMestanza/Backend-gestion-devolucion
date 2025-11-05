from django.db import models
from datetime import datetime

class Devolucion(models.Model):
    prestamo_id = models.IntegerField()  # ID del préstamo en otro microservicio
    fecha = models.DateTimeField(auto_now_add=True)
    observacion = models.TextField(blank=True, null=True)
    recibidoPor_id = models.IntegerField()  # ID del usuario que recibe el equipo
    condicion = models.CharField(max_length=100, default="Bueno")
    prestamo_vencido = models.BooleanField(default=False)
    sancion_puntos = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def verificarTardanza(self, prestamo_data: dict, fecha_actual: datetime) -> bool:
        """Verifica si el préstamo está vencido comparando fechas."""
        fecha_limite = datetime.fromisoformat(prestamo_data["fecha_devolucion_programada"])
        return fecha_actual > fecha_limite

    def __str__(self):
        return f"Devolución del préstamo {self.prestamo_id}"
