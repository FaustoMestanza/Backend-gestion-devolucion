from django.contrib import admin
from .models import Devolucion

@admin.register(Devolucion)
class DevolucionAdmin(admin.ModelAdmin):
    list_display = ('id', 'prestamo_id', 'fecha', 'recibidoPor_id', 'condicion', 'prestamo_vencido', 'sancion_puntos')
    list_filter = ('prestamo_vencido', 'condicion')
    search_fields = ('prestamo_id', 'recibidoPor_id')
