"""
Rutas de ventas de la API.

Provee endpoints para crear, consultar y gestionar ventas.
"""

import logging
from datetime import datetime
from uuid import UUID

from flask import Blueprint, request, jsonify, current_app, g

from infraestructure.api.decorators import requiere_auth, requiere_admin
from domain.entities import ModalidadVenta, EstadoVenta
from application.use_cases.ventas import (
    CrearVenta,
    CrearVentaInput,
    ItemVentaInput,
    CompletarVenta,
    CancelarVenta,
    ObtenerVenta,
    BuscarVentas,
    BuscarVentasInput
)


logger = logging.getLogger(__name__)

ventas_bp = Blueprint("ventas", __name__, url_prefix="/api/ventas")


def venta_a_dict(venta) -> dict:
    """
    Convierte un VentaOutput a diccionario serializable.

    Args:
        venta: Objeto VentaOutput

    Returns:
        dict: Diccionario con los datos de la venta
    """
    return {
        "uuid": venta.uuid,
        "items": [
            {
                "producto_id": item.producto_id,
                "cantidad": item.cantidad,
                "precio_unitario": str(item.precio_unitario),
                "subtotal": str(item.subtotal)
            }
            for item in venta.items
        ],
        "modalidad": venta.modalidad,
        "estado": venta.estado,
        "comprador_id": venta.comprador_id,
        "vendedor_id": venta.vendedor_id,
        "fecha": venta.fecha.isoformat(),
        "valor_total_cop": str(venta.valor_total_cop)
    }


@ventas_bp.route("", methods=["POST"])
@requiere_auth
def crear_venta():
    """
    Crea una nueva venta.

    Requiere autenticación.

    Body JSON:
        items: Lista de items [{producto_id, cantidad}]
        modalidad: "virtual" o "fisica"

    Returns:
        201: Venta creada
        400: Datos inválidos
    """
    datos = request.get_json()
    usuario = g.usuario

    logger.info(
        "POST /api/ventas - usuario: %s, items: %d",
        usuario["username"],
        len(datos.get("items", []))
    )

    # Validar campos requeridos
    if not datos.get("items"):
        return jsonify({
            "error": "Debe incluir al menos un item",
            "codigo": "ITEMS_REQUERIDOS"
        }), 400

    if not datos.get("modalidad"):
        return jsonify({
            "error": "La modalidad es requerida (virtual/fisica)",
            "codigo": "MODALIDAD_REQUERIDA"
        }), 400

    # Validar modalidad
    try:
        modalidad = ModalidadVenta(datos["modalidad"])
    except ValueError:
        return jsonify({
            "error": "Modalidad inválida. Use 'virtual' o 'fisica'",
            "codigo": "MODALIDAD_INVALIDA"
        }), 400

    # Validar items
    items = []
    for i, item in enumerate(datos["items"]):
        if not item.get("producto_id"):
            return jsonify({
                "error": f"Item {i+1}: producto_id es requerido"
            }), 400
        if not item.get("cantidad") or item["cantidad"] <= 0:
            return jsonify({
                "error": f"Item {i+1}: cantidad debe ser mayor a 0"
            }), 400

        try:
            producto_id = UUID(item["producto_id"])
        except ValueError:
            return jsonify({
                "error": f"Item {i+1}: producto_id inválido"
            }), 400

        items.append(ItemVentaInput(
            producto_id=producto_id,
            cantidad=int(item["cantidad"])
        ))

    try:
        venta_repo = current_app.config["VENTA_REPO"]
        producto_repo = current_app.config["PRODUCTO_REPO"]

        crear = CrearVenta(venta_repo, producto_repo)
        venta = crear.ejecutar(CrearVentaInput(
            items=items,
            modalidad=modalidad,
            comprador_id=usuario["uuid"]
        ))

        current_app.config["SESSION"].commit()

        logger.info("Venta creada: %s", venta.uuid)

        return jsonify(venta_a_dict(venta)), 201

    except ValueError as e:
        logger.warning("Error al crear venta: %s", str(e))
        current_app.config["SESSION"].rollback()
        return jsonify({
            "error": str(e),
            "codigo": "VALIDACION_ERROR"
        }), 400

    except Exception as e:
        logger.error("Error inesperado al crear venta: %s", str(e))
        current_app.config["SESSION"].rollback()
        return jsonify({
            "error": "Error interno del servidor",
            "codigo": "SERVER_ERROR"
        }), 500


@ventas_bp.route("/<venta_uuid>", methods=["GET"])
@requiere_auth
def obtener_venta(venta_uuid: str):
    """
    Obtiene una venta por su UUID.

    Requiere autenticación.

    Args:
        venta_uuid: UUID de la venta

    Returns:
        200: Datos de la venta
        404: Venta no encontrada
    """
    logger.info("GET /api/ventas/%s", venta_uuid)

    try:
        uuid = UUID(venta_uuid)
    except ValueError:
        return jsonify({"error": "UUID inválido"}), 400

    try:
        venta_repo = current_app.config["VENTA_REPO"]

        obtener = ObtenerVenta(venta_repo)
        venta = obtener.ejecutar(uuid)

        logger.info("Venta obtenida: %s", venta_uuid)

        return jsonify(venta_a_dict(venta)), 200

    except ValueError as e:
        logger.warning("Venta no encontrada: %s", str(e))
        return jsonify({"error": str(e)}), 404

    except Exception as e:
        logger.error("Error al obtener venta: %s", str(e))
        return jsonify({"error": "Error interno del servidor"}), 500


@ventas_bp.route("/<venta_uuid>/completar", methods=["POST"])
@requiere_auth
def completar_venta(venta_uuid: str):
    """
    Completa una venta pendiente.

    Requiere autenticación. Reduce el stock de los productos.

    Args:
        venta_uuid: UUID de la venta

    Returns:
        200: Venta completada
        400: Venta no pendiente o stock insuficiente
        404: Venta no encontrada
    """
    logger.info("POST /api/ventas/%s/completar", venta_uuid)

    try:
        uuid = UUID(venta_uuid)
    except ValueError:
        return jsonify({"error": "UUID inválido"}), 400

    try:
        venta_repo = current_app.config["VENTA_REPO"]
        producto_repo = current_app.config["PRODUCTO_REPO"]

        completar = CompletarVenta(venta_repo, producto_repo)
        venta = completar.ejecutar(uuid)

        current_app.config["SESSION"].commit()

        logger.info("Venta completada: %s", venta_uuid)

        return jsonify(venta_a_dict(venta)), 200

    except ValueError as e:
        logger.warning("Error al completar venta: %s", str(e))
        current_app.config["SESSION"].rollback()
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        logger.error("Error inesperado al completar venta: %s", str(e))
        current_app.config["SESSION"].rollback()
        return jsonify({"error": "Error interno del servidor"}), 500


@ventas_bp.route("/<venta_uuid>/cancelar", methods=["POST"])
@requiere_auth
def cancelar_venta(venta_uuid: str):
    """
    Cancela una venta pendiente.

    Requiere autenticación.

    Args:
        venta_uuid: UUID de la venta

    Returns:
        200: Venta cancelada
        400: Venta no pendiente
        404: Venta no encontrada
    """
    logger.info("POST /api/ventas/%s/cancelar", venta_uuid)

    try:
        uuid = UUID(venta_uuid)
    except ValueError:
        return jsonify({"error": "UUID inválido"}), 400

    try:
        venta_repo = current_app.config["VENTA_REPO"]

        cancelar = CancelarVenta(venta_repo)
        cancelar.ejecutar(uuid)

        current_app.config["SESSION"].commit()

        logger.info("Venta cancelada: %s", venta_uuid)

        return jsonify({
            "mensaje": "Venta cancelada exitosamente",
            "uuid": venta_uuid
        }), 200

    except ValueError as e:
        logger.warning("Error al cancelar venta: %s", str(e))
        current_app.config["SESSION"].rollback()
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        logger.error("Error inesperado al cancelar venta: %s", str(e))
        current_app.config["SESSION"].rollback()
        return jsonify({"error": "Error interno del servidor"}), 500


@ventas_bp.route("/reporte", methods=["GET"])
@requiere_auth
@requiere_admin
def reporte_ventas():
    """
    Genera un reporte de ventas con filtros.

    Requiere autenticación y rol de administrador.

    Query params:
        modalidad: Filtrar por modalidad (virtual/fisica)
        estado: Filtrar por estado (pendiente/completada/cancelada)
        fecha_inicio: Fecha inicio (ISO format)
        fecha_fin: Fecha fin (ISO format)
        limite: Número máximo de resultados (default: 10)
        offset: Número de resultados a saltar (default: 0)

    Returns:
        200: Lista de ventas con filtros aplicados
    """
    logger.info("GET /api/ventas/reporte - params: %s", dict(request.args))

    # Parsear parámetros
    modalidad = None
    if request.args.get("modalidad"):
        try:
            modalidad = ModalidadVenta(request.args.get("modalidad"))
        except ValueError:
            return jsonify({
                "error": "Modalidad inválida"
            }), 400

    estado = None
    if request.args.get("estado"):
        try:
            estado = EstadoVenta(request.args.get("estado"))
        except ValueError:
            return jsonify({
                "error": "Estado inválido"
            }), 400

    fecha_inicio = None
    if request.args.get("fecha_inicio"):
        try:
            fecha_inicio = datetime.fromisoformat(request.args.get("fecha_inicio"))
        except ValueError:
            return jsonify({
                "error": "fecha_inicio debe estar en formato ISO"
            }), 400

    fecha_fin = None
    if request.args.get("fecha_fin"):
        try:
            fecha_fin = datetime.fromisoformat(request.args.get("fecha_fin"))
        except ValueError:
            return jsonify({
                "error": "fecha_fin debe estar en formato ISO"
            }), 400

    limite = request.args.get("limite", 10, type=int)
    offset = request.args.get("offset", 0, type=int)

    try:
        venta_repo = current_app.config["VENTA_REPO"]

        buscar = BuscarVentas(venta_repo)
        ventas = buscar.ejecutar(BuscarVentasInput(
            modalidad=modalidad,
            estado=estado,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            limite=limite,
            offset=offset
        ))

        logger.info("Reporte generado: %d ventas", len(ventas))

        return jsonify({
            "ventas": [venta_a_dict(v) for v in ventas],
            "total": len(ventas),
            "limite": limite,
            "offset": offset
        }), 200

    except Exception as e:
        logger.error("Error al generar reporte: %s", str(e))
        return jsonify({
            "error": "Error interno del servidor"
        }), 500
