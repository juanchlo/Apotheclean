"""
Casos de uso para el carrito de compras.

Gestiona operaciones del carrito temporal en Redis y su conversión a venta.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from src.domain.entities import ModalidadVenta
from src.application.ports.cache import ICarritoCache
from src.application.ports.repositories import IProductoRepository, IVentaRepository
from src.application.use_cases.ventas import (
    CrearVenta,
    CrearVentaInput,
    ItemVentaInput,
    VentaOutput
)


@dataclass
class ItemCarritoInput:
    """Entrada para agregar/eliminar item del carrito."""
    producto_id: UUID
    cantidad: int


@dataclass
class ItemCarritoOutput:
    """Salida de un item del carrito con info del producto."""
    producto_id: str
    nombre: str
    cantidad: int
    valor_unitario: Decimal
    subtotal: Decimal
    stock_disponible: int


@dataclass
class CarritoOutput:
    """Salida del carrito completo."""
    items: List[ItemCarritoOutput]
    total_items: int
    valor_total: Decimal


@dataclass
class CheckoutInput:
    """Entrada para convertir carrito a venta."""
    modalidad: ModalidadVenta


class AgregarAlCarrito:
    """Caso de uso para agregar un producto al carrito."""

    def __init__(
        self,
        carrito_cache: ICarritoCache,
        producto_repo: IProductoRepository
    ):
        """
        Inicializa el caso de uso.

        Args:
            carrito_cache: Adaptador de cache para carritos.
            producto_repo: Repositorio de productos.
        """
        self.carrito_cache = carrito_cache
        self.producto_repo = producto_repo

    def ejecutar(self, usuario_id: UUID, datos: ItemCarritoInput) -> None:
        """
        Agrega un producto al carrito del usuario.

        Args:
            usuario_id: UUID del usuario.
            datos: Producto y cantidad a agregar.

        Raises:
            ValueError: Si el producto no existe o cantidad inválida.
        """
        if datos.cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor a 0")

        producto = self.producto_repo.obtener_por_uuid(datos.producto_id)
        if producto is None:
            raise ValueError(f"El producto {datos.producto_id} no existe")
        if producto.eliminado:
            raise ValueError(f"El producto {producto.nombre} no está disponible")

        self.carrito_cache.agregar_producto(
            usuario_id=usuario_id,
            producto_id=datos.producto_id,
            cantidad=datos.cantidad
        )


class EliminarDelCarrito:
    """Caso de uso para eliminar o reducir cantidad de un producto."""

    def __init__(self, carrito_cache: ICarritoCache):
        """
        Inicializa el caso de uso.

        Args:
            carrito_cache: Adaptador de cache para carritos.
        """
        self.carrito_cache = carrito_cache

    def ejecutar(
        self,
        usuario_id: UUID,
        producto_id: UUID,
        cantidad: Optional[int] = None
    ) -> None:
        """
        Elimina o reduce cantidad de un producto del carrito.

        Args:
            usuario_id: UUID del usuario.
            producto_id: UUID del producto a eliminar.
            cantidad: Cantidad a reducir. Si es None, elimina todo el producto.

        Raises:
            ValueError: Si la cantidad es inválida.
        """
        if cantidad is not None and cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor a 0")

        # Si no se especifica cantidad, eliminamos 999999 para asegurar remoción
        cantidad_a_eliminar = cantidad if cantidad else 999999

        self.carrito_cache.eliminar_producto(
            usuario_id=usuario_id,
            producto_id=producto_id,
            cantidad=cantidad_a_eliminar
        )


class ObtenerCarrito:
    """Caso de uso para obtener el carrito con info de productos."""

    def __init__(
        self,
        carrito_cache: ICarritoCache,
        producto_repo: IProductoRepository
    ):
        """
        Inicializa el caso de uso.

        Args:
            carrito_cache: Adaptador de cache para carritos.
            producto_repo: Repositorio de productos.
        """
        self.carrito_cache = carrito_cache
        self.producto_repo = producto_repo

    def ejecutar(self, usuario_id: UUID) -> CarritoOutput:
        """
        Obtiene el carrito del usuario con info de productos.

        Args:
            usuario_id: UUID del usuario.

        Returns:
            CarritoOutput con items, totales y valor.
        """
        items_cache = self.carrito_cache.obtener_carrito(usuario_id)
        items_output = []
        valor_total = Decimal("0")

        for item in items_cache:
            producto = self.producto_repo.obtener_por_uuid(item["producto_id"])

            if producto is None or producto.eliminado:
                # Producto ya no existe, lo eliminamos del carrito
                self.carrito_cache.eliminar_producto(
                    usuario_id, item["producto_id"], 999999
                )
                continue

            subtotal = producto.valor_unitario * item["cantidad"]
            valor_total += subtotal

            items_output.append(ItemCarritoOutput(
                producto_id=str(item["producto_id"]),
                nombre=producto.nombre,
                cantidad=item["cantidad"],
                valor_unitario=producto.valor_unitario,
                subtotal=subtotal,
                stock_disponible=producto.stock
            ))

        return CarritoOutput(
            items=items_output,
            total_items=sum(item.cantidad for item in items_output),
            valor_total=valor_total
        )


class VaciarCarrito:
    """Caso de uso para vaciar completamente el carrito."""

    def __init__(self, carrito_cache: ICarritoCache):
        """
        Inicializa el caso de uso.

        Args:
            carrito_cache: Adaptador de cache para carritos.
        """
        self.carrito_cache = carrito_cache

    def ejecutar(self, usuario_id: UUID) -> None:
        """
        Elimina todos los items del carrito.

        Args:
            usuario_id: UUID del usuario.
        """
        self.carrito_cache.eliminar_carrito(usuario_id)


class CheckoutCarrito:
    """Caso de uso para convertir el carrito en una venta."""

    def __init__(
        self,
        carrito_cache: ICarritoCache,
        producto_repo: IProductoRepository,
        venta_repo: IVentaRepository
    ):
        """
        Inicializa el caso de uso.

        Args:
            carrito_cache: Adaptador de cache para carritos.
            producto_repo: Repositorio de productos.
            venta_repo: Repositorio de ventas.
        """
        self.carrito_cache = carrito_cache
        self.producto_repo = producto_repo
        self.venta_repo = venta_repo

    def ejecutar(self, usuario_id: UUID, datos: CheckoutInput) -> VentaOutput:
        """
        Convierte el carrito en una venta pendiente.

        Args:
            usuario_id: UUID del usuario.
            datos: Modalidad de la venta.

        Returns:
            VentaOutput con los datos de la venta creada.

        Raises:
            ValueError: Si el carrito está vacío o hay problemas de stock.
        """
        items_cache = self.carrito_cache.obtener_carrito(usuario_id)

        if not items_cache:
            raise ValueError("El carrito está vacío")

        # Convertir items del carrito a formato de venta
        items_venta = []
        for item in items_cache:
            items_venta.append(ItemVentaInput(
                producto_id=item["producto_id"],
                cantidad=item["cantidad"]
            ))

        # Crear la venta usando el caso de uso existente
        crear_venta = CrearVenta(self.venta_repo, self.producto_repo)
        venta = crear_venta.ejecutar(CrearVentaInput(
            items=items_venta,
            modalidad=datos.modalidad,
            comprador_id=usuario_id
        ))

        # Limpiar el carrito después de crear la venta
        self.carrito_cache.eliminar_carrito(usuario_id)

        return venta
