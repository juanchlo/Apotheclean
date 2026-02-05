"""
Módulo que contiene las entidades de dominio de la aplicación.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4


# Enums para reglas de negocio
class RolUsuario(Enum):
    """
    Enum para mapear los roles de los usuarios.
    """
    ADMIN = "admin"
    CLIENTE = "cliente"


class ModalidadVenta(Enum):
    """
    Enum para mapear las modalidades de venta.
    """
    VIRTUAL = "virtual"
    FISICA = "fisica"


class EstadoVenta(Enum):
    """
    Enum para mapear los estados de una venta.
    """
    PENDIENTE = "pendiente"
    COMPLETADA = "completada"
    CANCELADA = "cancelada"


# Entidades de dominio
@dataclass
class Producto:
    """
    Entidad que representa un producto.
    """
    nombre: str
    barcode: str
    valor_unitario: Decimal
    stock: int
    uuid: UUID = field(default_factory=uuid4)
    descripcion: Optional[str] = None
    imagen_uuid: Optional[str] = None
    eliminado: bool = False

    def tiene_stock(self, cantidad: int) -> bool:
        """
        Verifica si el producto tiene suficiente stock.
        """
        return self.stock >= cantidad and not self.eliminado

    def agregar_stock(self, cantidad: int):
        """
        Agrega stock al producto.
        """
        self.stock += cantidad

    def reducir_stock(self, cantidad: int):
        """
        Reduce el stock del producto.
        """
        if not self.tiene_stock(cantidad):
            raise ValueError(f"Stock insuficiente para el producto: {self.nombre}")
        self.stock -= cantidad


@dataclass
class Usuario:
    """
    Entidad que representa un usuario.
    """
    username: str
    password_hash: str
    email: str
    nombre: str
    rol: RolUsuario
    uuid: UUID = field(default_factory=uuid4)
    timestamp_creacion: datetime = field(default_factory=datetime.now)
    activo: bool = True


@dataclass
class DetalleVenta:
    """
    Entidad que representa un detalle de venta.
    """
    producto_id: UUID
    cantidad: int
    precio_unitario_historico: Decimal

    @property
    def subtotal(self) -> Decimal:
        """
        Calcula el subtotal del detalle de venta.
        """
        return self.precio_unitario_historico * self.cantidad


@dataclass
class Venta:
    """
    Entidad que representa una venta.
    """
    modalidad: ModalidadVenta
    items: List[DetalleVenta] = field(default_factory=list)
    estado: EstadoVenta = EstadoVenta.PENDIENTE
    comprador_id: Optional[UUID] = None
    vendedor_id: Optional[UUID] = None
    uuid: UUID = field(default_factory=uuid4)
    fecha: datetime = field(default_factory=datetime.now)
    valor_total_cop: Decimal = field(default=Decimal('0.00'))

    def calcular_total(self):
        """Calcula el total sumando los subtotales de los detalles."""
        self.valor_total_cop = sum((item.subtotal for item in self.items), Decimal('0.00'))

    def agregar_item(self, nuevo_item: DetalleVenta):
        """
        Agrega un item a la venta.
        """
        item_existente = self.obtener_item(nuevo_item.producto_id)
        if item_existente:
            item_existente.cantidad += nuevo_item.cantidad
        else:
            self.items.append(nuevo_item)

        self.calcular_total()

    def remover_item(self, item: DetalleVenta):
        """
        Remueve un item de la venta.
        """
        self.items.remove(item)
        self.calcular_total()

    def obtener_item(self, producto_id: UUID) -> Optional[DetalleVenta]:
        """
        Obtiene un item de la venta por el id del producto.
        """
        for item in self.items:
            if item.producto_id == producto_id:
                return item
        return None
