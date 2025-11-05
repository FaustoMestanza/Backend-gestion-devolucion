from datetime import datetime
import requests
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Devolucion
from .serializers import DevolucionSerializer

# 🌐 URLs de tus microservicios en la nube (Azure)
API_PRESTAMOS = "https://microservicio-gestionprestamo-fmcxb0gvcshag6av.brazilsouth-01.azurewebsites.net/api/prestamos/"
API_INVEMTARIO = "https://microservicio-gestioninventario-e7byadgfgdhpfyen.brazilsouth-01.azurewebsites.net/api/equipos/"

class DevolucionViewSet(viewsets.ModelViewSet):
    queryset = Devolucion.objects.all()
    serializer_class = DevolucionSerializer

    def create(self, request, *args, **kwargs):
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

        if equipo["estado"].lower() == "disponible":
            return Response({"mensaje": "El equipo ya fue devuelto y está disponible."}, status=status.HTTP_200_OK)

        # 3️⃣ Verificar vencimiento
        fecha_actual = datetime.now()
        devolucion = Devolucion()
        vencido = devolucion.verificarTardanza(prestamo, fecha_actual)
        sancion = 0

        if vencido:
            sancion = float(data.get("sancion_puntos", 0))
            if sancion == 0:
                return Response({
                    "mensaje": "El préstamo está vencido. Ingrese sanción en puntos para continuar."
                }, status=status.HTTP_400_BAD_REQUEST)

        # 4️⃣ Crear devolución
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

        # 5️⃣ Actualizar otros microservicios
        requests.patch(f"{API_PRESTAMOS}{prestamo_id}/", json={"estado": "devuelto"})
        requests.patch(f"{API_INVENTARIO}{equipo_id}/", json={"estado": "disponible"})

        return Response({
            "mensaje": "Devolución registrada correctamente.",
            "datos": serializer.data
        }, status=status.HTTP_201_CREATED)

    # Endpoint adicional: verificar estado antes de devolver
    @action(detail=False, methods=['get'], url_path='verificar/(?P<prestamo_id>[^/.]+)')
    def verificar(self, request, prestamo_id=None):
        prestamo_resp = requests.get(f"{API_PRESTAMOS}{prestamo_id}/")
        if prestamo_resp.status_code != 200:
            return Response({"error": "No se encontró el préstamo."}, status=status.HTTP_404_NOT_FOUND)
        prestamo = prestamo_resp.json()

        equipo_id = prestamo.get("equipo_id")
        equipo_resp = requests.get(f"{API_INVENTARIO}{equipo_id}/")
        if equipo_resp.status_code != 200:
            return Response({"error": "No se pudo verificar el equipo."}, status=status.HTTP_400_BAD_REQUEST)
        equipo = equipo_resp.json()

        if equipo["estado"].lower() == "disponible":
            return Response({
                "estado": "disponible",
                "mensaje": "El equipo ya fue devuelto y está disponible."
            }, status=status.HTTP_200_OK)

        fecha_actual = datetime.now()
        fecha_limite = datetime.fromisoformat(prestamo["fecha_devolucion_programada"])

        if fecha_actual > fecha_limite:
            return Response({
                "estado": "vencido",
                "mensaje": "El préstamo está vencido. Se requiere ingresar sanción en puntos."
            }, status=status.HTTP_200_OK)

        return Response({
            "estado": "activo",
            "mensaje": "El préstamo está activo. Puede registrar la devolución sin sanción."
        }, status=status.HTTP_200_OK)