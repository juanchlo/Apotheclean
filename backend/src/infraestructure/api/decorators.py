"""
Decoradores de autenticación y autorización para los endpoints de la API.

Provee decoradores para verificar tokens JWT y roles de usuario.
"""

import logging
from functools import wraps
from typing import Callable, Optional

from flask import request, jsonify, g, current_app

from src.infraestructure.auth.jwt_auth_adapter import JwtAuthAdapter
from src.domain.entities import RolUsuario


logger = logging.getLogger(__name__)


def obtener_auth_service() -> JwtAuthAdapter:
    """
    Obtiene el servicio de autenticación desde la configuración de la app.

    Returns:
        JwtAuthAdapter: Servicio de autenticación configurado.
    """
    return current_app.config["AUTH_SERVICE"]


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

    Verifica token y estado del usuario en base de datos.
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
        
        # 1. Verificar firma y validez del token (solo Access Tokens)
        payload = auth_service.verificar_token(token, tipo_esperado="access")

        if not payload:
            logger.warning("Intento de acceso con token inválido o expirado")
            return jsonify({
                "error": "Token inválido o expirado",
                "codigo": "TOKEN_INVALID"
            }), 401

        # 2. Consultar usuario en DB para asegurar que sigue activo/existente
        # Esto es un patrón "Stateful", más seguro que confiar ciegamente en el token stateless
        try:
            from uuid import UUID
            uuid_usuario = UUID(payload["sub"]) # convertir string a UUID object
            usuario_repo = current_app.config["USUARIO_REPO"]
            usuario = usuario_repo.obtener_por_uuid(uuid_usuario)
            
            if not usuario:
                logger.warning("Token válido pero usuario %s no encontrado en DB", uuid_usuario)
                return jsonify({
                    "error": "Usuario no encontrado",
                    "codigo": "USER_NOT_FOUND"
                }), 401
                
            if not usuario.activo:
                logger.warning("Intento de acceso de usuario inactivo %s", usuario.username)
                return jsonify({
                    "error": "Usuario inactivo",
                    "codigo": "USER_INACTIVE"
                }), 401

            # Almacenar entidad usuario completa
            g.usuario = usuario
            g.token = token
            
            logger.debug("Usuario autenticado: %s", usuario.username)

        except Exception as e:
            logger.error("Error validando usuario en DB: %s", str(e))
            return jsonify({
                "error": "Error interno de autenticación",
                "codigo": "AUTH_ERROR"
            }), 500

        return f(*args, **kwargs)

    return decorated


def requiere_admin(f: Callable) -> Callable:
    """
    Decorador que requiere rol de administrador.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(g, "usuario"):
            logger.error("@requiere_admin usado sin @requiere_auth previo")
            return jsonify({
                "error": "Error de configuración del servidor",
                "codigo": "SERVER_ERROR"
            }), 500

        usuario = g.usuario

        if usuario.rol != RolUsuario.ADMIN:
            logger.warning(
                "Usuario %s intentó acceder a recurso de admin",
                usuario.username
            )
            return jsonify({
                "error": "Acceso denegado. Se requiere rol de administrador",
                "codigo": "ADMIN_REQUIRED"
            }), 403

        return f(*args, **kwargs)

    return decorated
