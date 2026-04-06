# Backend-gestion-inventario-prestamo-devoluciones
En este repositorio se encuentra microservicos para gestión lógica y CRUD  de devoluciones
# Backend Gestión de Devoluciones

Microservicio desarrollado con **Django REST Framework** para la gestión de devoluciones de equipos dentro de un sistema de inventario institucional basado en arquitectura de microservicios.

## Descripción

Este microservicio forma parte de una solución distribuida orientada a la gestión de activos tecnológicos. Su propósito es controlar el proceso de devolución de equipos previamente prestados, garantizando trazabilidad, integridad de datos y comunicación eficiente con otros microservicios del sistema.

## Objetivo

Implementar un servicio backend desacoplado que permita registrar, validar y gestionar devoluciones de equipos, optimizando el control de recursos institucionales.

## Tecnologías utilizadas

- **Python**
- **Django**
- **Django REST Framework**
- **JWT Authentication**
- **Docker**
- **GitHub Actions (CI/CD)**
- **PostgreSQL / Neon (opcional)**
- **REST API**

## Funcionalidades principales

- Registro de devoluciones de equipos
- Validación de préstamos activos antes de procesar devoluciones
- Actualización del estado de los equipos
- Integración con microservicio de préstamos
- API REST para consumo externo
- Manejo de autenticación mediante JWT
- Comunicación segura entre microservicios

## Arquitectura

Este microservicio forma parte de una arquitectura basada en microservicios, donde cada servicio cumple una responsabilidad específica:

- **Usuarios** → autenticación y gestión de usuarios
- **Inventario** → control de equipos
- **Préstamos** → gestión de asignaciones
- **Devoluciones** → control de retorno de equipos

## Endpoints principales

| Método | Endpoint              | Descripción                          |
|--------|---------------------|--------------------------------------|
| POST   | /api/devoluciones/  | Registrar devolución de equipo       |
| GET    | /api/devoluciones/  | Listar devoluciones                  |
| GET    | /api/devoluciones/{id} | Obtener detalle de devolución     |

## Instalación y ejecución

```bash
git clone https://github.com/FaustoMestanza/Backend-gestion-devolucion.git
cd Backend-gestion-devolucion
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
