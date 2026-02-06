"""
Rutas de productos de la API.

Provee endpoints CRUD para productos con control de acceso por roles.
"""

import logging
from decimal import Decimal, InvalidOperation
from uuid import UUID

from flask import Blueprint, request, jsonify, current_app, send_file
import io

from src.infraestructure.api.decorators import requiere_auth, requiere_admin
from src.application.use_cases.productos import (
    CrearProducto,
    CrearProductoInput,
    ActualizarProducto,
    ActualizarProductoInput,
    EliminarProducto,
    ObtenerProducto,
    ListarProductos,
    ListarProductosInput,
    RestaurarProducto,
    ListarProductosEliminados
)


logger = logging.getLogger(__name__)

productos_bp = Blueprint("productos", __name__, url_prefix="/api/productos")


def producto_a_dict(producto) -> dict:
    """
    Convierte un ProductoOutput a diccionario serializable.

    Args:
        producto: Objeto ProductoOutput

    Returns:
        dict: Diccionario con los datos del producto
    """
    return {
        "uuid": producto.uuid,
        "nombre": producto.nombre,
        "barcode": producto.barcode,
        "valor_unitario": str(producto.valor_unitario),
        "stock": producto.stock,
        "descripcion": producto.descripcion,
        "imagen_uuid": producto.imagen_uuid
    }


@productos_bp.route("", methods=["GET"])
def listar_productos():
    """
    Lista todos los productos con paginación.

    Query params:
        limite: Número máximo de resultados (default: 10)
        offset: Número de resultados a saltar (default: 0)

    Returns:
        200: Lista de productos
    """
    limite = request.args.get("limite", 10, type=int)
    offset = request.args.get("offset", 0, type=int)
    incluir_eliminados = request.args.get("incluir_eliminados", "false") == "true"

    logger.info(
        "GET /api/productos - limite: %d, offset: %d, eliminados: %s",
        limite, offset, incluir_eliminados
    )

    try:
        producto_repo = current_app.config["PRODUCTO_REPO"]

        if incluir_eliminados:
            listar = ListarProductosEliminados(producto_repo)
            # Nota: ListarProductosEliminados espera los mismos inputs
            # que ListarProductos aunque internamente llame a otro método del repo
        else:
            listar = ListarProductos(producto_repo)

        productos = listar.ejecutar(ListarProductosInput(
            limite=limite,
            offset=offset
        ))

        logger.info("Listados %d productos", len(productos))

        return jsonify({
            "productos": [producto_a_dict(p) for p in productos],
            "total": len(productos),
            "limite": limite,
            "offset": offset
        }), 200

    except Exception as e:
        logger.error("Error al listar productos: %s", str(e))
        return jsonify({
            "error": "Error interno del servidor",
            "codigo": "SERVER_ERROR"
        }), 500


@productos_bp.route("/<producto_uuid>", methods=["GET"])
def obtener_producto(producto_uuid: str):
    """
    Obtiene un producto por su UUID.

    Args:
        producto_uuid: UUID del producto

    Returns:
        200: Datos del producto
        404: Producto no encontrado
    """
    logger.info("GET /api/productos/%s", producto_uuid)

    try:
        uuid = UUID(producto_uuid)
    except ValueError:
        logger.warning("UUID inválido: %s", producto_uuid)
        return jsonify({
            "error": "UUID inválido",
            "codigo": "UUID_INVALIDO"
        }), 400

    try:
        producto_repo = current_app.config["PRODUCTO_REPO"]

        obtener = ObtenerProducto(producto_repo)
        producto = obtener.ejecutar(uuid)

        logger.info("Producto obtenido: %s", producto.nombre)

        return jsonify(producto_a_dict(producto)), 200

    except ValueError as e:
        logger.warning("Producto no encontrado: %s", str(e))
        return jsonify({
            "error": str(e),
            "codigo": "NO_ENCONTRADO"
        }), 404

    except Exception as e:
        logger.error("Error al obtener producto: %s", str(e))
        return jsonify({
            "error": "Error interno del servidor",
            "codigo": "SERVER_ERROR"
        }), 500


@productos_bp.route("/<producto_uuid>/imagen", methods=["POST"])
@requiere_auth
@requiere_admin
def subir_imagen_producto(producto_uuid: str):
    """
    Sube o actualiza la imagen de un producto.

    Requiere autenticación y rol de administrador.

    Args:
        producto_uuid: UUID del producto

    Form Data:
        imagen: Archivo de imagen

    Returns:
        200: Producto actualizado
        400: Archivo inválido
        404: Producto no encontrado
    """
    logger.info("POST /api/productos/%s/imagen", producto_uuid)

    try:
        uuid = UUID(producto_uuid)
    except ValueError:
        return jsonify({"error": "UUID inválido"}), 400

    if "imagen" not in request.files:
        return jsonify({"error": "No se encontró el archivo 'imagen'"}), 400

    archivo = request.files["imagen"]
    if archivo.filename == "":
        return jsonify({"error": "No se seleccionó ningún archivo"}), 400

    try:
        contenido = archivo.read()

        producto_repo = current_app.config["PRODUCTO_REPO"]
        image_storage = current_app.config["IMAGE_STORAGE"]

        actualizar = ActualizarProducto(producto_repo, image_storage)
        producto = actualizar.ejecutar(ActualizarProductoInput(
            uuid=uuid,
            imagen=contenido
        ))

        current_app.config["SESSION"].commit()

        logger.info("Imagen actualizada para producto: %s", producto_uuid)

        return jsonify(producto_a_dict(producto)), 200

    except ValueError as e:
        logger.warning("Error al subir imagen: %s", str(e))
        current_app.config["SESSION"].rollback()
        return jsonify({"error": str(e)}), 404

    except Exception as e:
        logger.error("Error inesperado al subir imagen: %s", str(e))
        current_app.config["SESSION"].rollback()
        return jsonify({"error": "Error interno del servidor"}), 500


@productos_bp.route("/<producto_uuid>/imagen", methods=["GET"])
def obtener_imagen_producto(producto_uuid: str):
    """
    Obtiene la imagen de un producto.

    Args:
        producto_uuid: UUID del producto

    Returns:
        200: Imagen del producto (bytes)
        404: Producto o imagen no encontrada
    """
    logger.info("GET /api/productos/%s/imagen", producto_uuid)

    try:
        uuid = UUID(producto_uuid)
    except ValueError:
        return jsonify({"error": "UUID inválido"}), 400

    try:
        producto_repo = current_app.config["PRODUCTO_REPO"]
        image_storage = current_app.config["IMAGE_STORAGE"]

        # Obtener producto para verificar que existe y tiene imagen
        obtener = ObtenerProducto(producto_repo)
        producto = obtener.ejecutar(uuid)

        if not producto.imagen_uuid:
            return jsonify({
                "error": "El producto no tiene imagen",
                "codigo": "SIN_IMAGEN"
            }), 404

        # Obtener imagen del storage
        imagen = image_storage.obtener(UUID(producto.imagen_uuid))
        if not imagen:
            return jsonify({
                "error": "Imagen no encontrada",
                "codigo": "IMAGEN_NO_ENCONTRADA"
            }), 404

        return send_file(
            io.BytesIO(imagen),
            mimetype="image/jpeg"
        )

    except ValueError as e:
        return jsonify({"error": str(e)}), 404

    except Exception as e:
        logger.error("Error al obtener imagen: %s", str(e))
        return jsonify({"error": "Error interno del servidor"}), 500


@productos_bp.route("", methods=["POST"])
@requiere_auth
@requiere_admin
def crear_producto():
    """
    Crea un nuevo producto.

    Requiere autenticación y rol de administrador.

    Body JSON:
        nombre: Nombre del producto
        barcode: Código de barras único
        valor_unitario: Precio unitario
        stock: Cantidad en inventario
        descripcion: Descripción (opcional)

    Returns:
        201: Producto creado
        400: Datos inválidos
        401: No autenticado
        403: No es administrador
    """
    datos = request.get_json()

    logger.info(
        "POST /api/productos - nombre: %s, barcode: %s",
        datos.get("nombre"),
        datos.get("barcode")
    )

    # Validar campos requeridos
    campos_requeridos = ["nombre", "barcode", "valor_unitario", "stock"]
    for campo in campos_requeridos:
        if campo not in datos:
            return jsonify({
                "error": f"El campo '{campo}' es requerido",
                "codigo": "CAMPO_REQUERIDO"
            }), 400

    try:
        valor_unitario = Decimal(str(datos["valor_unitario"]))
    except (InvalidOperation, ValueError):
        return jsonify({
            "error": "valor_unitario debe ser un número válido",
            "codigo": "VALOR_INVALIDO"
        }), 400

    try:
        stock = int(datos["stock"])
        if stock < 0:
            raise ValueError("Stock negativo")
    except (ValueError, TypeError):
        return jsonify({
            "error": "stock debe ser un número entero positivo",
            "codigo": "STOCK_INVALIDO"
        }), 400

    try:
        producto_repo = current_app.config["PRODUCTO_REPO"]
        image_storage = current_app.config["IMAGE_STORAGE"]

        crear = CrearProducto(producto_repo, image_storage)
        producto = crear.ejecutar(CrearProductoInput(
            nombre=datos["nombre"],
            barcode=datos["barcode"],
            valor_unitario=valor_unitario,
            stock=stock,
            descripcion=datos.get("descripcion")
        ))

        current_app.config["SESSION"].commit()

        logger.info("Producto creado: %s", producto.uuid)

        return jsonify(producto_a_dict(producto)), 201

    except ValueError as e:
        logger.warning("Error al crear producto: %s", str(e))
        current_app.config["SESSION"].rollback()
        return jsonify({
            "error": str(e),
            "codigo": "VALIDACION_ERROR"
        }), 400

    except Exception as e:
        logger.error("Error inesperado al crear producto: %s", str(e))
        current_app.config["SESSION"].rollback()
        return jsonify({
            "error": "Error interno del servidor",
            "codigo": "SERVER_ERROR"
        }), 500


@productos_bp.route("/<producto_uuid>", methods=["PUT"])
@requiere_auth
@requiere_admin
def actualizar_producto(producto_uuid: str):
    """
    Actualiza un producto existente.

    Requiere autenticación y rol de administrador.

    Args:
        producto_uuid: UUID del producto

    Body JSON (todos opcionales):
        nombre: Nuevo nombre
        valor_unitario: Nuevo precio
        stock: Nueva cantidad
        descripcion: Nueva descripción

    Returns:
        200: Producto actualizado
        400: Datos inválidos
        404: Producto no encontrado
    """
    datos = request.get_json()

    logger.info("PUT /api/productos/%s", producto_uuid)

    try:
        uuid = UUID(producto_uuid)
    except ValueError:
        return jsonify({"error": "UUID inválido"}), 400

    # Preparar datos de actualización
    valor_unitario = None
    if "valor_unitario" in datos:
        try:
            valor_unitario = Decimal(str(datos["valor_unitario"]))
        except (InvalidOperation, ValueError):
            return jsonify({
                "error": "valor_unitario debe ser un número válido"
            }), 400

    stock = None
    if "stock" in datos:
        try:
            stock = int(datos["stock"])
            if stock < 0:
                raise ValueError()
        except (ValueError, TypeError):
            return jsonify({
                "error": "stock debe ser un número entero positivo"
            }), 400

    try:
        producto_repo = current_app.config["PRODUCTO_REPO"]
        image_storage = current_app.config["IMAGE_STORAGE"]

        actualizar = ActualizarProducto(producto_repo, image_storage)
        producto = actualizar.ejecutar(ActualizarProductoInput(
            uuid=uuid,
            nombre=datos.get("nombre"),
            valor_unitario=valor_unitario,
            stock=stock,
            descripcion=datos.get("descripcion")
        ))

        current_app.config["SESSION"].commit()

        logger.info("Producto actualizado: %s", producto_uuid)

        return jsonify(producto_a_dict(producto)), 200

    except ValueError as e:
        logger.warning("Error al actualizar producto: %s", str(e))
        current_app.config["SESSION"].rollback()
        return jsonify({"error": str(e)}), 404

    except Exception as e:
        logger.error("Error inesperado al actualizar: %s", str(e))
        current_app.config["SESSION"].rollback()
        return jsonify({"error": "Error interno del servidor"}), 500


@productos_bp.route("/<producto_uuid>", methods=["DELETE"])
@requiere_auth
@requiere_admin
def eliminar_producto(producto_uuid: str):
    """
    Elimina un producto (soft delete).

    Requiere autenticación y rol de administrador.

    Args:
        producto_uuid: UUID del producto

    Returns:
        200: Producto eliminado
        404: Producto no encontrado
    """
    logger.info("DELETE /api/productos/%s", producto_uuid)

    try:
        uuid = UUID(producto_uuid)
    except ValueError:
        return jsonify({"error": "UUID inválido"}), 400

    try:
        producto_repo = current_app.config["PRODUCTO_REPO"]
        image_storage = current_app.config["IMAGE_STORAGE"]

        eliminar = EliminarProducto(producto_repo, image_storage)
        eliminar.ejecutar(uuid)

        current_app.config["SESSION"].commit()

        logger.info("Producto eliminado: %s", producto_uuid)

        return jsonify({
            "mensaje": "Producto eliminado exitosamente",
            "uuid": producto_uuid
        }), 200

    except ValueError as e:
        logger.warning("Error al eliminar producto: %s", str(e))
        current_app.config["SESSION"].rollback()
        return jsonify({"error": str(e)}), 404

    except Exception as e:
        logger.error("Error inesperado al eliminar: %s", str(e))
        current_app.config["SESSION"].rollback()
        return jsonify({"error": "Error interno del servidor"}), 500


@productos_bp.route("/<producto_uuid>/restaurar", methods=["POST"])
@requiere_auth
@requiere_admin
def restaurar_producto(producto_uuid: str):
    """
    Restaura un producto eliminado (revierte soft delete).

    Requiere autenticación y rol de administrador.

    Args:
        producto_uuid: UUID del producto

    Returns:
        200: Producto restaurado
        404: Producto no encontrado
    """
    logger.info("POST /api/productos/%s/restaurar", producto_uuid)

    try:
        uuid = UUID(producto_uuid)
    except ValueError:
        return jsonify({"error": "UUID inválido"}), 400

    try:
        producto_repo = current_app.config["PRODUCTO_REPO"]

        # Restaurar producto
        restaurar = RestaurarProducto(producto_repo)
        producto = restaurar.ejecutar(uuid)

        current_app.config["SESSION"].commit()

        logger.info("Producto restaurado: %s", producto_uuid)

        return jsonify(producto_a_dict(producto)), 200

    except ValueError as e:
        logger.warning("Error al restaurar producto: %s", str(e))
        current_app.config["SESSION"].rollback()
        return jsonify({"error": str(e)}), 404

    except Exception as e:
        logger.error("Error inesperado al restaurar: %s", str(e))
        current_app.config["SESSION"].rollback()
        return jsonify({"error": "Error interno del servidor"}), 500
