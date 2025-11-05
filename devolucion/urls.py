from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DevolucionViewSet

router = DefaultRouter()
router.register(r'devoluciones', DevolucionViewSet, basename='devoluciones')

urlpatterns = [
    path('', include(router.urls)),
]
