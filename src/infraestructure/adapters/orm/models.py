"""Modelos SQLAlchemy que mapean las entidades de dominio a tablas."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime,
    Numeric, ForeignKey, LargeBinary
)
from sqlalchemy.orm import relationship

from src.infraestructure.adapters.orm.config import Base


class UsuarioModel(Base):
    """Modelo SQLAlchemy para la entidad Usuario."""

    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(LargeBinary(16), unique=True, nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(LargeBinary, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    rol = Column(String(20), nullable=False)  # "admin" o "cliente"
    timestamp_creacion = Column(DateTime, default=datetime.now)
    activo = Column(Boolean, default=True)

    # Relaciones
    ventas_como_comprador = relationship(
        "VentaModel",
        foreign_keys="VentaModel.comprador_id",
        back_populates="comprador"
    )
    ventas_como_vendedor = relationship(
        "VentaModel",
        foreign_keys="VentaModel.vendedor_id",
        back_populates="vendedor"
    )


class ProductoModel(Base):
    """Modelo SQLAlchemy para la entidad Producto."""

    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(LargeBinary(16), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    barcode = Column(String(50), unique=True, nullable=False)
    valor_unitario = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, nullable=False, default=0)
    descripcion = Column(String(500), nullable=True)
    imagen_uuid = Column(String(36), nullable=True)
    eliminado = Column(Boolean, default=False)


class VentaModel(Base):
    """Modelo SQLAlchemy para la entidad Venta."""

    __tablename__ = "ventas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(LargeBinary(16), unique=True, nullable=False)
    modalidad = Column(String(20), nullable=False)  # "virtual" o "fisica"
    estado = Column(String(20), nullable=False, default="pendiente")
    comprador_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    vendedor_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    fecha = Column(DateTime, default=datetime.now)
    valor_total_cop = Column(Numeric(12, 2), default=Decimal("0.00"))

    # Relaciones
    comprador = relationship(
        "UsuarioModel",
        foreign_keys=[comprador_id],
        back_populates="ventas_como_comprador"
    )
    vendedor = relationship(
        "UsuarioModel",
        foreign_keys=[vendedor_id],
        back_populates="ventas_como_vendedor"
    )
    items = relationship(
        "DetalleVentaModel",
        back_populates="venta",
        cascade="all, delete-orphan"
    )


class DetalleVentaModel(Base):
    """Modelo SQLAlchemy para la entidad DetalleVenta."""

    __tablename__ = "detalle_ventas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    venta_id = Column(Integer, ForeignKey("ventas.id"), nullable=False)
    producto_id = Column(LargeBinary(16), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario_historico = Column(Numeric(10, 2), nullable=False)

    # Relación
    venta = relationship("VentaModel", back_populates="items")
