"""
Rutas del carrito de compras.

Provee endpoints para gestionar el carrito temporal en Redis.
"""

import logging
from uuid import UUID

from flask import Blueprint, request, jsonify, current_app, g

from src.infraestructure.api.decorators import requiere_auth
from src.domain.entities import ModalidadVenta
from src.application.use_cases.carrito import (
    AgregarAlCarrito,
    ItemCarritoInput,
    EliminarDelCarrito,
    ObtenerCarrito,
    VaciarCarrito,
    CheckoutCarrito,
    CheckoutInput
)


logger = logging.getLogger(__name__)

carrito_bp = Blueprint("carrito", __name__, url_prefix="/api/carrito")


def _obtener_usuario_id() -> UUID:
    """
    Obtiene el UUID del usuario autenticado.

    Maneja el caso donde uuid puede ser string o UUID.

    Returns:
        UUID del usuario
    """
    usuario = g.usuario
    if isinstance(usuario.uuid, str):
        return UUID(usuario.uuid)
    return usuario.uuid


def carrito_a_dict(carrito) -> dict:
    """
    Convierte un CarritoOutput a diccionario serializable.

    Args:
        carrito: Objeto CarritoOutput

    Returns:
        dict: Diccionario con los datos del carrito
    """
    return {
        "items": [
            {
                "producto_id": item.producto_id,
                "nombre": item.nombre,
                "cantidad": item.cantidad,
                "valor_unitario": str(item.valor_unitario),
                "subtotal": str(item.subtotal),
                "stock_disponible": item.stock_disponible
            }
            for item in carrito.items
        ],
        "total_items": carrito.total_items,
        "valor_total": str(carrito.valor_total)
    }


@carrito_bp.route("", methods=["GET"])
@requiere_auth
def obtener_carrito():
    """
    Obtiene el carrito del usuario autenticado.

    Returns:
        200: Carrito con items e info de productos
    """
    usuario = g.usuario
    usuario_id = _obtener_usuario_id()

    logger.info("GET /api/carrito - usuario: %s", usuario.username)

    try:
        carrito_cache = current_app.config["CARRITO_CACHE"]
        producto_repo = current_app.config["PRODUCTO_REPO"]

        obtener = ObtenerCarrito(carrito_cache, producto_repo)
        carrito = obtener.ejecutar(usuario_id)

        logger.info(
            "Carrito obtenido: %d items, total: %s",
            carrito.total_items, carrito.valor_total
        )

        return jsonify(carrito_a_dict(carrito)), 200

    except Exception as e:
        logger.error("Error al obtener carrito: %s", str(e))
        return jsonify({
            "error": "Error interno del servidor",
            "codigo": "SERVER_ERROR"
        }), 500


@carrito_bp.route("/items", methods=["POST"])
@requiere_auth
def agregar_item():
    """
    Agrega un producto al carrito.

    Body JSON:
        producto_id: UUID del producto
        cantidad: Cantidad a agregar

    Returns:
        200: Item agregado exitosamente
        400: Datos inválidos o producto no disponible
    """
    datos = request.get_json()
    usuario = g.usuario
    usuario_id = _obtener_usuario_id()

    logger.info(
        "POST /api/carrito/items - usuario: %s, producto: %s, cantidad: %s",
        usuario.username, datos.get("producto_id"), datos.get("cantidad")
    )

    # Validar campos requeridos
    if not datos.get("producto_id"):
        return jsonify({
            "error": "El producto_id es requerido",
            "codigo": "CAMPO_REQUERIDO"
        }), 400

    if not datos.get("cantidad"):
        return jsonify({
            "error": "La cantidad es requerida",
            "codigo": "CAMPO_REQUERIDO"
        }), 400

    try:
        producto_id = UUID(datos["producto_id"])
    except ValueError:
        return jsonify({
            "error": "producto_id inválido",
            "codigo": "UUID_INVALIDO"
        }), 400

    try:
        cantidad = int(datos["cantidad"])
        if cantidad <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({
            "error": "La cantidad debe ser un número entero positivo",
            "codigo": "CANTIDAD_INVALIDA"
        }), 400

    try:
        carrito_cache = current_app.config["CARRITO_CACHE"]
        producto_repo = current_app.config["PRODUCTO_REPO"]

        agregar = AgregarAlCarrito(carrito_cache, producto_repo)
        agregar.ejecutar(usuario_id, ItemCarritoInput(
            producto_id=producto_id,
            cantidad=cantidad
        ))

        logger.info("Item agregado al carrito de %s", usuario.username)

        return jsonify({
            "mensaje": "Producto agregado al carrito",
            "producto_id": str(producto_id),
            "cantidad": cantidad
        }), 200

    except ValueError as e:
        logger.warning("Error al agregar item: %s", str(e))
        return jsonify({
            "error": str(e),
            "codigo": "VALIDACION_ERROR"
        }), 400

    except Exception as e:
        logger.error("Error inesperado al agregar item: %s", str(e))
        return jsonify({
            "error": "Error interno del servidor",
            "codigo": "SERVER_ERROR"
        }), 500


@carrito_bp.route("/items/<producto_uuid>", methods=["DELETE"])
@requiere_auth
def eliminar_item(producto_uuid: str):
    """
    Elimina o reduce cantidad de un producto del carrito.

    Args:
        producto_uuid: UUID del producto a eliminar

    Query params:
        cantidad: Cantidad a eliminar (opcional, si no se indica elimina todo)

    Returns:
        200: Item eliminado/reducido
        400: UUID inválido
    """
    usuario = g.usuario
    usuario_id = _obtener_usuario_id()
    cantidad = request.args.get("cantidad", type=int)

    logger.info(
        "DELETE /api/carrito/items/%s - usuario: %s, cantidad: %s",
        producto_uuid, usuario.username, cantidad
    )

    try:
        producto_id = UUID(producto_uuid)
    except ValueError:
        return jsonify({
            "error": "UUID inválido",
            "codigo": "UUID_INVALIDO"
        }), 400

    try:
        carrito_cache = current_app.config["CARRITO_CACHE"]

        eliminar = EliminarDelCarrito(carrito_cache)
        eliminar.ejecutar(usuario_id, producto_id, cantidad)

        logger.info("Item eliminado del carrito de %s", usuario.username)

        return jsonify({
            "mensaje": "Producto eliminado del carrito",
            "producto_id": producto_uuid
        }), 200

    except ValueError as e:
        logger.warning("Error al eliminar item: %s", str(e))
        return jsonify({
            "error": str(e),
            "codigo": "VALIDACION_ERROR"
        }), 400

    except Exception as e:
        logger.error("Error inesperado al eliminar item: %s", str(e))
        return jsonify({
            "error": "Error interno del servidor",
            "codigo": "SERVER_ERROR"
        }), 500


@carrito_bp.route("", methods=["DELETE"])
@requiere_auth
def vaciar_carrito():
    """
    Vacía completamente el carrito del usuario.

    Returns:
        200: Carrito vaciado
    """
    usuario = g.usuario
    usuario_id = _obtener_usuario_id()

    logger.info("DELETE /api/carrito - usuario: %s", usuario.username)

    try:
        carrito_cache = current_app.config["CARRITO_CACHE"]

        vaciar = VaciarCarrito(carrito_cache)
        vaciar.ejecutar(usuario_id)

        logger.info("Carrito vaciado para %s", usuario.username)

        return jsonify({
            "mensaje": "Carrito vaciado exitosamente"
        }), 200

    except Exception as e:
        logger.error("Error al vaciar carrito: %s", str(e))
        return jsonify({
            "error": "Error interno del servidor",
            "codigo": "SERVER_ERROR"
        }), 500


@carrito_bp.route("/checkout", methods=["POST"])
@requiere_auth
def checkout():
    """
    Convierte el carrito en una venta pendiente.

    Body JSON:
        modalidad: "virtual" o "fisica"

    Returns:
        201: Venta creada
        400: Carrito vacío o modalidad inválida
    """
    datos = request.get_json()
    usuario = g.usuario
    usuario_id = _obtener_usuario_id()

    logger.info(
        "POST /api/carrito/checkout - usuario: %s, modalidad: %s",
        usuario.username, datos.get("modalidad")
    )

    # Validar modalidad
    if not datos.get("modalidad"):
        return jsonify({
            "error": "La modalidad es requerida (virtual/fisica)",
            "codigo": "MODALIDAD_REQUERIDA"
        }), 400

    try:
        modalidad = ModalidadVenta(datos["modalidad"])
    except ValueError:
        return jsonify({
            "error": "Modalidad inválida. Use 'virtual' o 'fisica'",
            "codigo": "MODALIDAD_INVALIDA"
        }), 400

    try:
        carrito_cache = current_app.config["CARRITO_CACHE"]
        producto_repo = current_app.config["PRODUCTO_REPO"]
        venta_repo = current_app.config["VENTA_REPO"]

        checkout_uc = CheckoutCarrito(carrito_cache, producto_repo, venta_repo)
        venta = checkout_uc.ejecutar(usuario_id, CheckoutInput(modalidad=modalidad))

        # Commit de la transacción
        current_app.config["SESSION"].commit()

        logger.info("Checkout completado, venta creada: %s", venta.uuid)

        return jsonify({
            "mensaje": "Venta creada exitosamente",
            "venta": {
                "uuid": venta.uuid,
                "estado": venta.estado,
                "valor_total": str(venta.valor_total_cop),
                "items": len(venta.items)
            }
        }), 201

    except ValueError as e:
        logger.warning("Error en checkout: %s", str(e))
        current_app.config["SESSION"].rollback()
        return jsonify({
            "error": str(e),
            "codigo": "VALIDACION_ERROR"
        }), 400

    except Exception as e:
        logger.error("Error inesperado en checkout: %s", str(e))
        current_app.config["SESSION"].rollback()
        return jsonify({
            "error": "Error interno del servidor",
            "codigo": "SERVER_ERROR"
        }), 500
