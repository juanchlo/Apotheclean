"""Casos de uso de ventas."""

from datetime import datetime
from uuid import UUID
from decimal import Decimal
from typing import Optional, List
from dataclasses import dataclass

from domain.entities import (
    Venta, DetalleVenta, ModalidadVenta, EstadoVenta
)
from application.ports.repositories import (
    IVentaRepository, IProductoRepository
)


@dataclass
class ItemVentaInput:
    """Representa un item en la creación de venta."""
    producto_id: UUID
    cantidad: int


@dataclass
class CrearVentaInput:
    """Entrada para el caso de uso de creación de venta."""
    items: List[ItemVentaInput]
    modalidad: ModalidadVenta
    comprador_id: Optional[UUID] = None
    vendedor_id: Optional[UUID] = None


@dataclass
class BuscarVentasInput:
    """Entrada para el caso de uso de búsqueda/reporte de ventas."""
    usuario_id: Optional[UUID] = None
    producto_id: Optional[UUID] = None
    modalidad: Optional[ModalidadVenta] = None
    estado: Optional[EstadoVenta] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    limite: int = 10
    offset: int = 0


@dataclass
class DetalleVentaOutput:
    """Salida para un detalle de venta."""
    producto_id: str
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal


@dataclass
class VentaOutput:
    """Salida estándar para operaciones de venta."""
    uuid: str
    items: List[DetalleVentaOutput]
    modalidad: str
    estado: str
    comprador_id: Optional[str]
    vendedor_id: Optional[str]
    fecha: datetime
    valor_total_cop: Decimal


class CrearVenta:
    """Caso de uso para crear una nueva venta."""

    def __init__(self, venta_repo: IVentaRepository,
                 producto_repo: IProductoRepository):
        self.venta_repo = venta_repo
        self.producto_repo = producto_repo

    def ejecutar(self, datos: CrearVentaInput) -> VentaOutput:
        """
        Crea una nueva venta validando stock de productos.

        Args:
            datos: Datos de la venta a crear

        Returns:
            VentaOutput con los datos de la venta creada

        Raises:
            ValueError: Si algún producto no existe o no tiene stock suficiente
        """
        if not datos.items:
            raise ValueError("La venta debe tener al menos un item")

        venta = Venta(
            modalidad=datos.modalidad,
            comprador_id=datos.comprador_id,
            vendedor_id=datos.vendedor_id
        )

        for item in datos.items:
            producto = self.producto_repo.obtener_por_uuid(item.producto_id)
            if producto is None:
                raise ValueError(f"El producto {item.producto_id} no existe")
            if producto.eliminado:
                raise ValueError(f"El producto {producto.nombre} no está disponible")
            if not producto.tiene_stock(item.cantidad):
                raise ValueError(
                    f"Stock insuficiente para {producto.nombre}. "
                    f"Disponible: {producto.stock}, Solicitado: {item.cantidad}"
                )

            detalle = DetalleVenta(
                producto_id=item.producto_id,
                cantidad=item.cantidad,
                precio_unitario_historico=producto.valor_unitario
            )
            venta.agregar_item(detalle)

        self.venta_repo.guardar(venta)

        return self._crear_output(venta)

    def _crear_output(self, venta: Venta) -> VentaOutput:
        """Convierte una entidad Venta a VentaOutput."""
        return VentaOutput(
            uuid=str(venta.uuid),
            items=[
                DetalleVentaOutput(
                    producto_id=str(item.producto_id),
                    cantidad=item.cantidad,
                    precio_unitario=item.precio_unitario_historico,
                    subtotal=item.subtotal
                )
                for item in venta.items
            ],
            modalidad=venta.modalidad.value,
            estado=venta.estado.value,
            comprador_id=str(venta.comprador_id) if venta.comprador_id else None,
            vendedor_id=str(venta.vendedor_id) if venta.vendedor_id else None,
            fecha=venta.fecha,
            valor_total_cop=venta.valor_total_cop
        )


class CompletarVenta:
    """Caso de uso para completar una venta pendiente."""

    def __init__(self, venta_repo: IVentaRepository,
                 producto_repo: IProductoRepository):
        self.venta_repo = venta_repo
        self.producto_repo = producto_repo

    def ejecutar(self, venta_id: UUID) -> VentaOutput:
        """
        Completa una venta pendiente y reduce el stock de los productos.

        Args:
            venta_id: UUID de la venta a completar

        Returns:
            VentaOutput con los datos de la venta completada

        Raises:
            ValueError: Si la venta no existe o no está pendiente
        """
        venta = self.venta_repo.obtener_por_uuid(venta_id)
        if venta is None:
            raise ValueError("La venta no existe")
        if venta.estado != EstadoVenta.PENDIENTE:
            raise ValueError(f"La venta no se puede completar, estado actual: {venta.estado.value}")

        for item in venta.items:
            producto = self.producto_repo.obtener_por_uuid(item.producto_id)
            if producto is None:
                raise ValueError(f"El producto {item.producto_id} ya no existe")
            if not producto.tiene_stock(item.cantidad):
                raise ValueError(f"Stock insuficiente para {producto.nombre}")

            producto.reducir_stock(item.cantidad)
            self.producto_repo.guardar(producto)

        venta.estado = EstadoVenta.COMPLETADA
        self.venta_repo.guardar(venta)

        return self._crear_output(venta)

    def _crear_output(self, venta: Venta) -> VentaOutput:
        """Convierte una entidad Venta a VentaOutput."""
        return VentaOutput(
            uuid=str(venta.uuid),
            items=[
                DetalleVentaOutput(
                    producto_id=str(item.producto_id),
                    cantidad=item.cantidad,
                    precio_unitario=item.precio_unitario_historico,
                    subtotal=item.subtotal
                )
                for item in venta.items
            ],
            modalidad=venta.modalidad.value,
            estado=venta.estado.value,
            comprador_id=str(venta.comprador_id) if venta.comprador_id else None,
            vendedor_id=str(venta.vendedor_id) if venta.vendedor_id else None,
            fecha=venta.fecha,
            valor_total_cop=venta.valor_total_cop
        )


class CancelarVenta:
    """Caso de uso para cancelar una venta."""

    def __init__(self, venta_repo: IVentaRepository):
        self.venta_repo = venta_repo

    def ejecutar(self, venta_id: UUID) -> bool:
        """
        Cancela una venta pendiente.

        Args:
            venta_id: UUID de la venta a cancelar

        Returns:
            True si la venta se canceló correctamente

        Raises:
            ValueError: Si la venta no existe o no está pendiente
        """
        venta = self.venta_repo.obtener_por_uuid(venta_id)
        if venta is None:
            raise ValueError("La venta no existe")
        if venta.estado != EstadoVenta.PENDIENTE:
            raise ValueError(f"Solo se pueden cancelar ventas pendientes, estado actual: {venta.estado.value}")

        venta.estado = EstadoVenta.CANCELADA
        self.venta_repo.guardar(venta)

        return True


class ObtenerVenta:
    """Caso de uso para obtener una venta por su UUID."""

    def __init__(self, venta_repo: IVentaRepository):
        self.venta_repo = venta_repo

    def ejecutar(self, venta_id: UUID) -> VentaOutput:
        """
        Obtiene una venta por su UUID.

        Args:
            venta_id: UUID de la venta

        Returns:
            VentaOutput con los datos de la venta

        Raises:
            ValueError: Si la venta no existe
        """
        venta = self.venta_repo.obtener_por_uuid(venta_id)
        if venta is None:
            raise ValueError("La venta no existe")

        return VentaOutput(
            uuid=str(venta.uuid),
            items=[
                DetalleVentaOutput(
                    producto_id=str(item.producto_id),
                    cantidad=item.cantidad,
                    precio_unitario=item.precio_unitario_historico,
                    subtotal=item.subtotal
                )
                for item in venta.items
            ],
            modalidad=venta.modalidad.value,
            estado=venta.estado.value,
            comprador_id=str(venta.comprador_id) if venta.comprador_id else None,
            vendedor_id=str(venta.vendedor_id) if venta.vendedor_id else None,
            fecha=venta.fecha,
            valor_total_cop=venta.valor_total_cop
        )


class BuscarVentas:
    """Caso de uso para buscar ventas con filtros (reportes)."""

    def __init__(self, venta_repo: IVentaRepository):
        self.venta_repo = venta_repo

    def ejecutar(self, datos: BuscarVentasInput) -> List[VentaOutput]:
        """
        Busca ventas con filtros opcionales para reportes.

        Args:
            datos: Filtros de búsqueda

        Returns:
            Lista de VentaOutput que cumplen los filtros
        """
        ventas = self.venta_repo.buscar(
            usuario_id=datos.usuario_id,
            producto_id=datos.producto_id,
            modalidad=datos.modalidad,
            estado=datos.estado,
            fecha_inicio=datos.fecha_inicio,
            fecha_fin=datos.fecha_fin,
            limite=datos.limite,
            offset=datos.offset
        )

        return [
            VentaOutput(
                uuid=str(venta.uuid),
                items=[
                    DetalleVentaOutput(
                        producto_id=str(item.producto_id),
                        cantidad=item.cantidad,
                        precio_unitario=item.precio_unitario_historico,
                        subtotal=item.subtotal
                    )
                    for item in venta.items
                ],
                modalidad=venta.modalidad.value,
                estado=venta.estado.value,
                comprador_id=str(venta.comprador_id) if venta.comprador_id else None,
                vendedor_id=str(venta.vendedor_id) if venta.vendedor_id else None,
                fecha=venta.fecha,
                valor_total_cop=venta.valor_total_cop
            )
            for venta in ventas
        ]
