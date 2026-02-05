"""
Rutas de autenticación de la API.

Provee endpoints para registro de usuarios y login.
"""

import logging

from flask import Blueprint, request, jsonify

from application.use_cases.usuarios import (
    RegistrarUsuario,
    RegistrarUsuarioInput,
    LoginUsuario,
    LoginUsuarioInput
)


logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/registro", methods=["POST"])
def registro():
    """
    Registra un nuevo usuario cliente.

    Body JSON:
        username: Nombre de usuario único
        password: Contraseña
        email: Correo electrónico único
        nombre: Nombre completo

    Returns:
        201: Usuario registrado exitosamente
        400: Datos inválidos o usuario/email duplicado
    """
    datos = request.get_json()

    logger.info(
        "POST /api/auth/registro - username: %s, email: %s",
        datos.get("username"),
        datos.get("email")
    )

    # Validar campos requeridos
    campos_requeridos = ["username", "password", "email", "nombre"]
    for campo in campos_requeridos:
        if not datos.get(campo):
            logger.warning("Campo requerido faltante: %s", campo)
            return jsonify({
                "error": f"El campo '{campo}' es requerido",
                "codigo": "CAMPO_REQUERIDO"
            }), 400

    try:
        # Obtener dependencias del contexto de la app
        from flask import current_app
        usuario_repo = current_app.config["USUARIO_REPO"]
        auth_service = current_app.config["AUTH_SERVICE"]

        # Ejecutar caso de uso
        registrar = RegistrarUsuario(usuario_repo, auth_service)
        input_data = RegistrarUsuarioInput(
            username=datos["username"],
            password=datos["password"],
            email=datos["email"],
            nombre=datos["nombre"]
        )

        registrar.ejecutar(input_data)

        # Commit de la transacción
        current_app.config["SESSION"].commit()

        logger.info("Usuario registrado exitosamente: %s", datos["username"])

        return jsonify({
            "mensaje": "Usuario registrado exitosamente",
            "username": datos["username"]
        }), 201

    except ValueError as e:
        logger.warning("Error de validación en registro: %s", str(e))
        return jsonify({
            "error": str(e),
            "codigo": "VALIDACION_ERROR"
        }), 400

    except Exception as e:
        logger.error("Error inesperado en registro: %s", str(e))
        current_app.config["SESSION"].rollback()
        return jsonify({
            "error": "Error interno del servidor",
            "codigo": "SERVER_ERROR"
        }), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Inicia sesión de un usuario.

    Body JSON:
        username: Nombre de usuario (opcional si se provee email)
        email: Correo electrónico (opcional si se provee username)
        password: Contraseña

    Returns:
        200: Login exitoso con token JWT
        400: Credenciales inválidas o datos faltantes
    """
    datos = request.get_json()

    logger.info(
        "POST /api/auth/login - username: %s, email: %s",
        datos.get("username"),
        datos.get("email")
    )

    # Validar que al menos username o email estén presentes
    if not datos.get("username") and not datos.get("email"):
        logger.warning("Login sin username ni email")
        return jsonify({
            "error": "Debe proporcionar username o email",
            "codigo": "CREDENCIALES_REQUERIDAS"
        }), 400

    if not datos.get("password"):
        logger.warning("Login sin password")
        return jsonify({
            "error": "La contraseña es requerida",
            "codigo": "PASSWORD_REQUERIDO"
        }), 400

    try:
        from flask import current_app
        usuario_repo = current_app.config["USUARIO_REPO"]
        auth_service = current_app.config["AUTH_SERVICE"]

        # Ejecutar caso de uso
        login_uc = LoginUsuario(usuario_repo, auth_service)
        input_data = LoginUsuarioInput(
            username=datos.get("username"),
            email=datos.get("email"),
            password=datos["password"]
        )

        token = login_uc.ejecutar(input_data)

        logger.info(
            "Login exitoso para usuario: %s",
            datos.get("username") or datos.get("email")
        )

        return jsonify({
            "mensaje": "Login exitoso",
            "token": token
        }), 200

    except ValueError as e:
        logger.warning("Error en login: %s", str(e))
        return jsonify({
            "error": str(e),
            "codigo": "CREDENCIALES_INVALIDAS"
        }), 400

    except Exception as e:
        logger.error("Error inesperado en login: %s", str(e))
        return jsonify({
            "error": "Error interno del servidor",
            "codigo": "SERVER_ERROR"
        }), 500
