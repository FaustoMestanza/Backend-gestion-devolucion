from datetime import datetime, timezone as dt_timezone
import requests
from dateutil.parser import isoparse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Devolucion
from .serializers import DevolucionSerializer

# 🌐 URLs de los microservicios externos
API_PRESTAMOS = "https://microservicio-gestionprestamo-fmcxb0gvcshag6av.brazilsouth-01.azurewebsites.net/api/prestamos/"
API_INVENTARIO = "https://microservicio-gestioninventario-e7byadgfgdhpfyen.brazilsouth-01.azurewebsites.net/api/equipos/"


class DevolucionViewSet(viewsets.ModelViewSet):
    queryset = Devolucion.objects.all()
    serializer_class = DevolucionSerializer

    # 🟢 CREAR DEVOLUCIÓN
    def create(self, request, *args, **kwargs):
        """
        Crea una devolución, verificando el estado del préstamo e inventario.
        """
        try:
            data = request.data
            prestamo_id = data.get('prestamo_id')

            # 1️⃣ Obtener datos del préstamo
            prestamo_resp = requests.get(f"{API_PRESTAMOS}{prestamo_id}/")
            if prestamo_resp.status_code != 200:
                return Response({"error": "No se encontró el préstamo."}, status=status.HTTP_400_BAD_REQUEST)
            prestamo = prestamo_resp.json()

            equipo_id = prestamo.get("equipo_id")
            usuario_id = prestamo.get("usuario_id")

            # 2️⃣ Consultar equipo en inventario
            equipo_resp = requests.get(f"{API_INVENTARIO}{equipo_id}/")
            if equipo_resp.status_code != 200:
                return Response({"error": "No se pudo verificar el equipo."}, status=status.HTTP_400_BAD_REQUEST)
            equipo = equipo_resp.json()

            # 3️⃣ Verificar si el equipo ya está disponible
            if equipo["estado"].lower() == "disponible":
                return Response({
                    "mensaje": "El equipo ya fue devuelto y está disponible."
                }, status=status.HTTP_200_OK)

            # 4️⃣ Verificar vencimiento del préstamo
            fecha_actual = timezone.now().astimezone(dt_timezone.utc)
            devolucion = Devolucion()
            vencido = devolucion.verificarTardanza(prestamo, fecha_actual)
            sancion = 0

            if vencido:
                sancion = float(data.get("sancion_puntos", 0))
                if sancion == 0:
                    return Response({
                        "mensaje": "El préstamo está vencido. Ingrese sanción en puntos para continuar."
                    }, status=status.HTTP_400_BAD_REQUEST)

            # 5️⃣ Crear la devolución
            nueva_devolucion = {
                "prestamo_id": prestamo_id,
                "recibidoPor_id": data.get("recibidoPor_id"),
                "observacion": data.get("observacion", ""),
                "condicion": data.get("condicion", "Bueno"),
                "prestamo_vencido": vencido,
                "sancion_puntos": sancion
            }

            serializer = self.get_serializer(data=nueva_devolucion)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)

            # 6️⃣ Actualizar estados en otros microservicios
            requests.patch(f"{API_PRESTAMOS}{prestamo_id}/", json={"estado": "Cerrado"})
            requests.patch(f"{API_INVENTARIO}{equipo_id}/", json={"estado": "Disponible"})

            return Response({
                "mensaje": "Devolución registrada correctamente.",
                "datos": serializer.data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "error": "Error interno al crear la devolución.",
                "detalle": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # 🔍 VERIFICAR ESTADO DEL PRÉSTAMO
    @action(detail=False, methods=['get'], url_path='verificar/(?P<prestamo_id>[^/.]+)')
    def verificar(self, request, prestamo_id=None):
        """
        Verifica si un préstamo está activo, vencido o ya devuelto.
        """
        try:
            # 1️⃣ Obtener préstamo
            prestamo_resp = requests.get(f"{API_PRESTAMOS}{prestamo_id}/")
            if prestamo_resp.status_code != 200:
                return Response({"error": "No se encontró el préstamo."}, status=status.HTTP_404_NOT_FOUND)
            prestamo = prestamo_resp.json()

            # 2️⃣ Obtener equipo
            equipo_id = prestamo.get("equipo_id")
            equipo_resp = requests.get(f"{API_INVENTARIO}{equipo_id}/")
            if equipo_resp.status_code != 200:
                return Response({"error": "No se pudo verificar el equipo."}, status=status.HTTP_400_BAD_REQUEST)
            equipo = equipo_resp.json()

            # 3️⃣ Si el equipo ya está disponible
            if equipo["estado"].lower() == "disponible":
                return Response({
                    "estado": "disponible",
                    "mensaje": "El equipo ya fue devuelto y está disponible."
                }, status=status.HTTP_200_OK)

            # 4️⃣ Verificar si el préstamo está vencido
            fecha_actual = timezone.now().astimezone(dt_timezone.utc)
            fecha_compromiso = prestamo.get("fecha_compromiso")

            if not fecha_compromiso:
                return Response({
                    "error": "El préstamo no tiene fecha_compromiso definida."
                }, status=status.HTTP_400_BAD_REQUEST)

            fecha_limite = isoparse(fecha_compromiso)
            # Asegurar que ambas fechas sean aware en UTC
            if fecha_limite.tzinfo is None:
                fecha_limite = fecha_limite.replace(tzinfo=dt_timezone.utc)

            if fecha_actual > fecha_limite:
                return Response({
                    "estado": "vencido",
                    "mensaje": "El préstamo está vencido. Se requiere ingresar sanción en puntos."
                }, status=status.HTTP_200_OK)

            # 5️⃣ Si todo está correcto
            return Response({
                "estado": "activo",
                "mensaje": "El préstamo está activo. Puede registrar la devolución sin sanción."
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "error": "Error interno en la verificación del préstamo.",
                "detalle": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
