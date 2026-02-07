---
trigger: always_on
---

# Necesitamos darle solución al siguiente miniproyecto usando arquitectura Hexagonal

## Sobre el proyecto:
### El proyecto se centrará en un sistema de farmacia para la venta, registro de productos y reportes, tendrá dos componentes principales, un backend usando arquitectura hexagonal y un frontend en React para permitir el ingreso de administradores o clientes.

### Reglas de negocio importantes:
- Las cuentas de adminstrador serán las unicas que podrán tener CRUD de los productos, estas cuentas no se pueden crear directamente desde el frontend
- Las cuentas de usuario se permiten crear desde el frontend y solo tendrán permisos read de los productos 
- Las contraseñas deben se hasheadas (bycrypt) 
- No existe delete permante de un producto, solo soft delete
- Estoy usando Decimal para llevar los precios de los productos y no tener problemas por la precsicion de float

## Nuestro stack será
- Python 
- Flask
- sqlalchemy
- React
- SQLite
- Redis

## Objetivo:
Construir un microproyecto completo que permita evaluar habilidades prácticas en python, arquitectura, SQL, y front-end.

## Alcance:
- Backend  con arquitectura Hexagonal.
- ORM.
- SQL local
- Autenticación JWT.
- Front React con CRUD y reporte.
- Git (ramas y mensajes claros).
- README con pasos de ejecución.
- Implementar patrón de resiliencia
- Implementar Paginación en reportes
- Pruebas unitarias
- Docker / Docker Compose.
- Logs estructurados.

## Escenario:
###Sistema de Productos y Ventas.
- CRUD (Create, Read, Update, Delete) de productos (nombre, precio, stock, imagen).
- Registro de ventas con ítems.
- Reporte de ventas por rango de fechas.
- Autenticación JWT y endpoints protegidos.

## Plus:
- IaC Terraform.
- Mocks de Blob Storage