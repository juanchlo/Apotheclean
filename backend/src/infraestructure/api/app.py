"""
Fábrica de la aplicación Flask.

Configura la aplicación con logging estructurado, manejo de errores,
inyección de dependencias y registro de blueprints.
"""

import logging
import os
import sys
from typing import Optional

from flask import Flask, jsonify

from src.infraestructure.adapters.orm.config import (
    engine,
    SessionLocal,
    inicializar_base_datos
)
from src.infraestructure.adapters.sqlalchemy_usuario_repository import SQLAlchemyUsuarioRepository
from src.infraestructure.adapters.sqlalchemy_producto_repository import SQLAlchemyProductoRepository
from src.infraestructure.adapters.sqlalchemy_venta_repository import SQLAlchemyVentaRepository
from src.infraestructure.auth.jwt_auth_adapter import JwtAuthAdapter
from src.infraestructure.storage.filesystem_image_adapter import FilesystemImageAdapter
from src.infraestructure.cache.config import crear_carrito_adapter

from src.infraestructure.api.routes.auth import auth_bp
from src.infraestructure.api.routes.productos import productos_bp
from src.infraestructure.api.routes.ventas import ventas_bp
from src.infraestructure.api.routes.carrito import carrito_bp


def configurar_logging(nivel: str = "INFO") -> None:
    """
    Configura el logging estructurado de la aplicación.

    Args:
        nivel: Nivel de logging (DEBUG, INFO, WARNING, ERROR)
    """
    formato = (
        "%(asctime)s | %(levelname)-8s | %(name)s | "
        "%(funcName)s:%(lineno)d | %(message)s"
    )

    logging.basicConfig(
        level=getattr(logging, nivel.upper()),
        format=formato,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Reducir verbosidad de librerías externas
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def crear_app(config: Optional[dict] = None) -> Flask:
    """
    Crea y configura la aplicación Flask.

    Args:
        config: Configuración adicional (opcional)

    Returns:
        Flask: Aplicación Flask configurada
    """
    # Configurar logging
    configurar_logging(os.getenv("LOG_LEVEL", "INFO"))
    logger = logging.getLogger(__name__)

    # Crear aplicación
    app = Flask(__name__)
    app.config["JSON_AS_ASCII"] = False

    if config:
        app.config.update(config)

    # Inicializar base de datos
    logger.info("Inicializando base de datos...")
    inicializar_base_datos(engine)

    # Crear sesión (proxy scoped_session)
    session = SessionLocal
    app.config["SESSION"] = session

    # Inyectar dependencias
    logger.info("Configurando dependencias...")

    app.config["AUTH_SERVICE"] = JwtAuthAdapter()
    app.config["IMAGE_STORAGE"] = FilesystemImageAdapter()

    app.config["USUARIO_REPO"] = SQLAlchemyUsuarioRepository(session)
    app.config["PRODUCTO_REPO"] = SQLAlchemyProductoRepository(session)
    app.config["VENTA_REPO"] = SQLAlchemyVentaRepository(session)
    app.config["CARRITO_CACHE"] = crear_carrito_adapter()

    # Registrar blueprints
    logger.info("Registrando rutas...")
    app.register_blueprint(auth_bp)
    app.register_blueprint(productos_bp)
    app.register_blueprint(ventas_bp)
    app.register_blueprint(carrito_bp)

    # Manejador de errores global
    @app.errorhandler(404)
    def not_found(error):
        """Maneja errores 404."""
        return jsonify({
            "error": "Recurso no encontrado",
            "codigo": "NOT_FOUND"
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Maneja errores 500."""
        logger.error("Error interno: %s", str(error))
        return jsonify({
            "error": "Error interno del servidor",
            "codigo": "SERVER_ERROR"
        }), 500

    @app.errorhandler(405)
    def method_not_allowed(error):
        """Maneja errores 405."""
        return jsonify({
            "error": "Método no permitido",
            "codigo": "METHOD_NOT_ALLOWED"
        }), 405

    # Cerrar sesión al terminar request
    @app.teardown_appcontext
    def cerrar_sesion(exception=None):
        """Cierra la sesión de base de datos al finalizar el request."""
        # SessionLocal es un scoped_session, remove() limpia la sesión del thread
        SessionLocal.remove()

    # Endpoint de salud
    @app.route("/health", methods=["GET"])
    def health_check():
        """Endpoint de verificación de salud."""
        return jsonify({
            "status": "ok",
            "servicio": "Apotheclean API"
        }), 200

    logger.info("Aplicación Flask iniciada correctamente")

    return app
