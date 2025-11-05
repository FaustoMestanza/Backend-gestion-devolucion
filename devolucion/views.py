import requests
from datetime import datetime, timezone as dt_timezone   # ✅ UTC nativo
from dateutil.parser import isoparse

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Devolucion
from .serializers import DevolucionSerializer

API_PRESTAMOS = "https://microservicio-gestionprestamo-fmcxb0gvcshag6av.brazilsouth-01.azurewebsites.net/api/prestamos/"
API_INVENTARIO = "https://microservicio-gestioninventario-e7byadgfgdhpfyen.brazilsouth-01.azurewebsites.net/api/equipos/"


class DevolucionViewSet(viewsets.ModelViewSet):
    queryset = Devolucion.objects.all()
    serializer_class = DevolucionSerializer

    # 🟢 crear devolución
    def create(self, request, *args, **kwargs):
        try:
            data = request.data
            prestamo_id = data.get("prestamo_id")

            # 1) préstamo
            p_resp = requests.get(f"{API_PRESTAMOS}{prestamo_id}/")
            if p_resp.status_code != 200:
                return Response({"error": "No se encontró el préstamo."}, status=400)
            prestamo = p_resp.json()
            equipo_id = prestamo.get("equipo_id")

            # 2) equipo
            e_resp = requests.get(f"{API_INVENTARIO}{equipo_id}/")
            if e_resp.status_code != 200:
                return Response({"error": "No se pudo verificar el equipo."}, status=400)
            equipo = e_resp.json()

            if equipo["estado"].lower() == "disponible":
                return Response({"mensaje": "El equipo ya fue devuelto y está disponible."}, status=200)

            # 3) vencimiento
            ahora_utc = datetime.now(dt_timezone.utc)
            vencido = Devolucion().verificarTardanza(prestamo, ahora_utc)

            sancion = 0
            if vencido:
                sancion = float(data.get("sancion_puntos", 0))
                if sancion == 0:
                    return Response(
                        {"mensaje": "El préstamo está vencido. Ingrese sanción en puntos para continuar."},
                        status=400,
                    )

            # 4) crear devolución
            payload = {
                "prestamo_id": prestamo_id,
                "recibidoPor_id": data.get("recibidoPor_id"),
                "observacion": data.get("observacion", ""),
                "condicion": data.get("condicion", "Bueno"),
                "prestamo_vencido": vencido,
                "sancion_puntos": sancion,
            }
            ser = self.get_serializer(data=payload)
            ser.is_valid(raise_exception=True)
            self.perform_create(ser)

            # 5) actualizar otros ms
            requests.patch(f"{API_PRESTAMOS}{prestamo_id}/", json={"estado": "Cerrado"})
            requests.patch(f"{API_INVENTARIO}{equipo_id}/", json={"estado": "Disponible"})

            return Response({"mensaje": "Devolución registrada correctamente.", "datos": ser.data}, status=201)

        except Exception as e:
            return Response({"error": "Error interno al crear la devolución.", "detalle": str(e)}, status=500)

    # 🔍 verificar préstamo
    @action(detail=False, methods=["get"], url_path=r"verificar/(?P<prestamo_id>[^/.]+)")
    def verificar(self, request, prestamo_id=None):
        try:
            # 1) préstamo
            p_resp = requests.get(f"{API_PRESTAMOS}{prestamo_id}/")
            if p_resp.status_code != 200:
                return Response({"error": "No se encontró el préstamo."}, status=404)
            prestamo = p_resp.json()

            # 2) equipo
            equipo_id = prestamo.get("equipo_id")
            e_resp = requests.get(f"{API_INVENTARIO}{equipo_id}/")
            if e_resp.status_code != 200:
                return Response({"error": "No se pudo verificar el equipo."}, status=400)
            equipo = e_resp.json()

            if equipo["estado"].lower() == "disponible":
                return Response(
                    {"estado": "disponible", "mensaje": "El equipo ya fue devuelto y está disponible."},
                    status=200,
                )

            # 3) comparar fechas en UTC
            ahora_utc = datetime.now(dt_timezone.utc)
            fecha_comp = prestamo.get("fecha_compromiso")
            if not fecha_comp:
                return Response({"error": "El préstamo no tiene fecha_compromiso definida."}, status=400)

            fecha_limite = isoparse(fecha_comp)
            if fecha_limite.tzinfo is None:
                fecha_limite = fecha_limite.replace(tzinfo=dt_timezone.utc)
            else:
                fecha_limite = fecha_limite.astimezone(dt_timezone.utc)

            if ahora_utc > fecha_limite:
                return Response(
                    {"estado": "vencido", "mensaje": "El préstamo está vencido. Se requiere ingresar sanción en puntos."},
                    status=200,
                )

            return Response(
                {"estado": "activo", "mensaje": "El préstamo está activo. Puede registrar la devolución sin sanción."},
                status=200,
            )

        except Exception as e:
            return Response({"error": "Error interno en la verificación del préstamo.", "detalle": str(e)}, status=500)
