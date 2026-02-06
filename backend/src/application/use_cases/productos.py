"""Casos de uso de productos."""

from uuid import UUID, uuid4
from decimal import Decimal
from typing import Optional, List
from dataclasses import dataclass

from src.domain.entities import Producto
from src.application.ports.repositories import IProductoRepository
from src.application.ports.image_storage import IImageStorage


@dataclass
class CrearProductoInput:
    """Entrada para el caso de uso de creación de producto."""
    nombre: str
    barcode: str
    valor_unitario: Decimal
    stock: int
    descripcion: Optional[str] = None
    imagen: Optional[bytes] = None


@dataclass
class ListarProductosInput:
    """Entrada para el caso de uso de listado de productos."""
    limite: int = 10
    offset: int = 0


@dataclass
class ActualizarProductoInput:
    """Entrada para el caso de uso de actualización de producto."""
    uuid: UUID
    nombre: Optional[str] = None
    valor_unitario: Optional[Decimal] = None
    stock: Optional[int] = None
    descripcion: Optional[str] = None
    imagen: Optional[bytes] = None


@dataclass
class ProductoOutput:
    """Salida estándar para operaciones de producto."""
    uuid: str
    nombre: str
    barcode: str
    valor_unitario: Decimal
    stock: int
    descripcion: Optional[str]
    imagen_uuid: Optional[str]


class CrearProducto:
    """Caso de uso para crear un nuevo producto."""

    def __init__(self, producto_repo: IProductoRepository,
                 image_storage: IImageStorage):
        self.producto_repo = producto_repo
        self.image_storage = image_storage

    def ejecutar(self, datos: CrearProductoInput) -> ProductoOutput:
        """
        Crea un nuevo producto validando que el barcode sea único.

        Args:
            datos: Datos del producto a crear

        Returns:
            ProductoOutput con los datos del producto creado

        Raises:
            ValueError: Si el barcode ya existe
        """
        if self.producto_repo.obtener_por_barcode(datos.barcode) is not None:
            raise ValueError("Ya existe un producto con este código de barras")

        imagen_uuid = None
        if datos.imagen:
            imagen_uuid = str(uuid4())
            self.image_storage.guardar(datos.imagen, UUID(imagen_uuid))

        producto = Producto(
            nombre=datos.nombre,
            barcode=datos.barcode,
            valor_unitario=datos.valor_unitario,
            stock=datos.stock,
            descripcion=datos.descripcion,
            imagen_uuid=imagen_uuid
        )

        self.producto_repo.guardar(producto)

        return ProductoOutput(
            uuid=str(producto.uuid),
            nombre=producto.nombre,
            barcode=producto.barcode,
            valor_unitario=producto.valor_unitario,
            stock=producto.stock,
            descripcion=producto.descripcion,
            imagen_uuid=producto.imagen_uuid
        )


class ActualizarProducto:
    """Caso de uso para actualizar un producto existente."""

    def __init__(self, producto_repo: IProductoRepository,
                 image_storage: IImageStorage):
        self.producto_repo = producto_repo
        self.image_storage = image_storage

    def ejecutar(self, datos: ActualizarProductoInput) -> ProductoOutput:
        """
        Actualiza un producto existente.

        Args:
            datos: Datos a actualizar del producto

        Returns:
            ProductoOutput con los datos actualizados

        Raises:
            ValueError: Si el producto no existe o está eliminado
        """
        producto = self.producto_repo.obtener_por_uuid(datos.uuid)
        if producto is None:
            raise ValueError("El producto no existe")
        if producto.eliminado:
            raise ValueError("No se puede actualizar un producto eliminado")

        if datos.nombre is not None:
            producto.nombre = datos.nombre
        if datos.valor_unitario is not None:
            producto.valor_unitario = datos.valor_unitario
        if datos.stock is not None:
            producto.stock = datos.stock
        if datos.descripcion is not None:
            producto.descripcion = datos.descripcion
        if datos.imagen is not None:
            if producto.imagen_uuid:
                self.image_storage.eliminar(UUID(producto.imagen_uuid))
            nuevo_imagen_uuid = str(uuid4())
            self.image_storage.guardar(datos.imagen, UUID(nuevo_imagen_uuid))
            producto.imagen_uuid = nuevo_imagen_uuid

        self.producto_repo.guardar(producto)

        return ProductoOutput(
            uuid=str(producto.uuid),
            nombre=producto.nombre,
            barcode=producto.barcode,
            valor_unitario=producto.valor_unitario,
            stock=producto.stock,
            descripcion=producto.descripcion,
            imagen_uuid=producto.imagen_uuid
        )


class EliminarProducto:
    """Caso de uso para eliminar (soft delete) un producto."""

    def __init__(self, producto_repo: IProductoRepository,
                 image_storage: IImageStorage):
        self.producto_repo = producto_repo
        self.image_storage = image_storage

    def ejecutar(self, producto_id: UUID) -> bool:
        """
        Elimina un producto (soft delete).

        Args:
            producto_id: UUID del producto a eliminar

        Returns:
            True si se eliminó correctamente

        Raises:
            ValueError: Si el producto no existe o ya está eliminado
        """
        producto = self.producto_repo.obtener_por_uuid(producto_id)
        if producto is None:
            raise ValueError("El producto no existe")
        if producto.eliminado:
            raise ValueError("El producto ya está eliminado")

        self.producto_repo.eliminar(producto_id)
        return True


class ObtenerProducto:
    """Caso de uso para obtener un producto por su UUID."""

    def __init__(self, producto_repo: IProductoRepository):
        self.producto_repo = producto_repo

    def ejecutar(self, producto_id: UUID) -> ProductoOutput:
        """
        Obtiene un producto por su UUID.

        Args:
            producto_id: UUID del producto

        Returns:
            ProductoOutput con los datos del producto

        Raises:
            ValueError: Si el producto no existe o está eliminado
        """
        producto = self.producto_repo.obtener_por_uuid(producto_id)
        if producto is None:
            raise ValueError("El producto no existe")
        if producto.eliminado:
            raise ValueError("El producto no está disponible")

        return ProductoOutput(
            uuid=str(producto.uuid),
            nombre=producto.nombre,
            barcode=producto.barcode,
            valor_unitario=producto.valor_unitario,
            stock=producto.stock,
            descripcion=producto.descripcion,
            imagen_uuid=producto.imagen_uuid
        )


class ListarProductos:
    """Caso de uso para listar productos con paginación."""

    def __init__(self, producto_repo: IProductoRepository):
        self.producto_repo = producto_repo

    def ejecutar(self, datos: ListarProductosInput) -> List[ProductoOutput]:
        """
        Lista productos con paginación.

        Args:
            datos: Parámetros de paginación

        Returns:
            Lista de ProductoOutput
        """
        productos = self.producto_repo.obtener_todos(datos.limite, datos.offset)

        return [
            ProductoOutput(
                uuid=str(p.uuid),
                nombre=p.nombre,
                barcode=p.barcode,
                valor_unitario=p.valor_unitario,
                stock=p.stock,
                descripcion=p.descripcion,
                imagen_uuid=p.imagen_uuid
            )
            for p in productos
            if not p.eliminado
        ]


class RestaurarProducto:
    """Caso de uso para restaurar un producto eliminado."""

    def __init__(self, producto_repo: IProductoRepository):
        """
        Inicializa el caso de uso.

        Args:
            producto_repo: Repositorio de productos
        """
        self.producto_repo = producto_repo

    def ejecutar(self, producto_id: UUID) -> ProductoOutput:
        """
        Restaura un producto previamente eliminado (revierte soft delete).

        Args:
            producto_id: UUID del producto a restaurar

        Returns:
            ProductoOutput con los datos del producto restaurado

        Raises:
            ValueError: Si el producto no existe o no está eliminado
        """
        producto = self.producto_repo.obtener_por_uuid(producto_id)
        if producto is None:
            raise ValueError("El producto no existe")
        if not producto.eliminado:
            raise ValueError("El producto no está eliminado")

        self.producto_repo.restaurar(producto_id)

        # Recargar el producto para obtener el estado actualizado
        producto = self.producto_repo.obtener_por_uuid(producto_id)

        return ProductoOutput(
            uuid=str(producto.uuid),
            nombre=producto.nombre,
            barcode=producto.barcode,
            valor_unitario=producto.valor_unitario,
            stock=producto.stock,
            descripcion=producto.descripcion,
            imagen_uuid=producto.imagen_uuid
        )


class ListarProductosEliminados:
    """Caso de uso para listar productos eliminados (archivados)."""

    def __init__(self, producto_repo: IProductoRepository):
        """
        Inicializa el caso de uso.

        Args:
            producto_repo: Repositorio de productos
        """
        self.producto_repo = producto_repo

    def ejecutar(self, datos: ListarProductosInput) -> List[ProductoOutput]:
        """
        Lista productos eliminados con paginación.

        Args:
            datos: Parámetros de paginación (limite, offset)

        Returns:
            Lista de ProductoOutput de productos eliminados
        """
        productos = self.producto_repo.obtener_eliminados(
            datos.limite,
            datos.offset
        )

        return [
            ProductoOutput(
                uuid=str(p.uuid),
                nombre=p.nombre,
                barcode=p.barcode,
                valor_unitario=p.valor_unitario,
                stock=p.stock,
                descripcion=p.descripcion,
                imagen_uuid=p.imagen_uuid
            )
            for p in productos
        ]
