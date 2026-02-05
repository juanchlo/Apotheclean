"""
Decoradores de autenticación y autorización para los endpoints de la API.

Provee decoradores para verificar tokens JWT y roles de usuario.
"""

import logging
from functools import wraps
from typing import Callable, Optional

from flask import request, jsonify, g

from src.infraestructure.auth.jwt_auth_adapter import JwtAuthAdapter
from src.domain.entities import RolUsuario


logger = logging.getLogger(__name__)


def obtener_auth_service() -> JwtAuthAdapter:
    """
    Obtiene el servicio de autenticación.

    Returns:
        JwtAuthAdapter: Servicio de autenticación configurado.
    """
    if not hasattr(g, "auth_service"):
        g.auth_service = JwtAuthAdapter()
    return g.auth_service


def extraer_token() -> Optional[str]:
    """
    Extrae el token JWT del header Authorization.

    Returns:
        Optional[str]: Token JWT o None si no está presente.
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None


def requiere_auth(f: Callable) -> Callable:
    """
    Decorador que requiere autenticación JWT válida.

    Verifica que el request contenga un token JWT válido en el header
    Authorization. Si es válido, almacena los datos del usuario en g.usuario.

    Args:
        f: Función a decorar.

    Returns:
        Función decorada que verifica autenticación.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = extraer_token()

        if not token:
            logger.warning("Intento de acceso sin token de autenticación")
            return jsonify({
                "error": "Token de autenticación requerido",
                "codigo": "AUTH_REQUIRED"
            }), 401

        auth_service = obtener_auth_service()
        datos_usuario = auth_service.verificar_token(token)

        if not datos_usuario:
            logger.warning("Intento de acceso con token inválido o expirado")
            return jsonify({
                "error": "Token inválido o expirado",
                "codigo": "TOKEN_INVALID"
            }), 401

        # Almacenar datos del usuario en el contexto de Flask
        g.usuario = datos_usuario
        g.token = token

        logger.debug(
            "Usuario autenticado: %s (rol: %s)",
            datos_usuario["username"],
            datos_usuario["rol"].value
        )

        return f(*args, **kwargs)

    return decorated


def requiere_admin(f: Callable) -> Callable:
    """
    Decorador que requiere rol de administrador.

    Debe usarse después de @requiere_auth. Verifica que el usuario
    autenticado tenga rol de administrador.

    Args:
        f: Función a decorar.

    Returns:
        Función decorada que verifica rol admin.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Verificar que el usuario está autenticado
        if not hasattr(g, "usuario"):
            logger.error("@requiere_admin usado sin @requiere_auth previo")
            return jsonify({
                "error": "Error de configuración del servidor",
                "codigo": "SERVER_ERROR"
            }), 500

        usuario = g.usuario

        if usuario["rol"] != RolUsuario.ADMIN:
            logger.warning(
                "Usuario %s intentó acceder a recurso de admin",
                usuario["username"]
            )
            return jsonify({
                "error": "Acceso denegado. Se requiere rol de administrador",
                "codigo": "ADMIN_REQUIRED"
            }), 403

        return f(*args, **kwargs)

    return decorated
