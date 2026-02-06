"""Implementación SQLAlchemy del repositorio de productos."""

from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.domain.entities import Producto
from src.application.ports.repositories import IProductoRepository
from src.infraestructure.adapters.orm.models import ProductoModel


class SQLAlchemyProductoRepository(IProductoRepository):
    """Implementación del repositorio de productos usando SQLAlchemy."""

    def __init__(self, session: Session):
        """
        Inicializa el repositorio con una sesión de SQLAlchemy.

        Args:
            session: Sesión de SQLAlchemy
        """
        self.session = session

    def guardar(self, producto: Producto) -> None:
        """
        Guarda un nuevo producto o actualiza uno existente.

        Args:
            producto: Entidad Producto a guardar
        """
        modelo_existente = self.session.query(ProductoModel).filter_by(
            uuid=producto.uuid.bytes
        ).first()

        if modelo_existente:
            modelo_existente.nombre = producto.nombre
            modelo_existente.barcode = producto.barcode
            modelo_existente.valor_unitario = producto.valor_unitario
            modelo_existente.stock = producto.stock
            modelo_existente.descripcion = producto.descripcion
            modelo_existente.imagen_uuid = producto.imagen_uuid
            modelo_existente.eliminado = producto.eliminado
        else:
            modelo = ProductoModel(
                uuid=producto.uuid.bytes,
                nombre=producto.nombre,
                barcode=producto.barcode,
                valor_unitario=producto.valor_unitario,
                stock=producto.stock,
                descripcion=producto.descripcion,
                imagen_uuid=producto.imagen_uuid,
                eliminado=producto.eliminado
            )
            self.session.add(modelo)

        self.session.commit()

    def obtener_por_uuid(self, uuid: UUID) -> Optional[Producto]:
        """Obtiene un producto por su UUID."""
        modelo = self.session.query(ProductoModel).filter_by(
            uuid=uuid.bytes
        ).first()
        return self._modelo_a_entidad(modelo) if modelo else None

    def obtener_por_barcode(self, barcode: str) -> Optional[Producto]:
        """Obtiene un producto por su código de barras."""
        modelo = self.session.query(ProductoModel).filter_by(
            barcode=barcode
        ).first()
        return self._modelo_a_entidad(modelo) if modelo else None

    def obtener_todos(self, limite: int, offset: int) -> List[Producto]:
        """Obtiene todos los productos activos con paginación."""
        modelos = self.session.query(ProductoModel)\
            .filter_by(eliminado=False)\
            .limit(limite)\
            .offset(offset)\
            .all()
        return [self._modelo_a_entidad(m) for m in modelos]

    def eliminar(self, uuid: UUID) -> None:
        """Soft delete de un producto."""
        modelo = self.session.query(ProductoModel).filter_by(
            uuid=uuid.bytes
        ).first()

        if modelo:
            modelo.eliminado = True
            self.session.commit()

    def restaurar(self, uuid: UUID) -> None:
        """
        Restaura un producto eliminado.

        Args:
            uuid: UUID del producto a restaurar
        """
        modelo = self.session.query(ProductoModel).filter_by(
            uuid=uuid.bytes
        ).first()

        if modelo:
            modelo.eliminado = False
            self.session.commit()

    def obtener_eliminados(self, limite: int, offset: int) -> List[Producto]:
        """
        Obtiene productos eliminados con paginación.

        Args:
            limite: Número máximo de resultados
            offset: Número de resultados a saltar

        Returns:
            Lista de productos eliminados
        """
        modelos = self.session.query(ProductoModel)\
            .filter_by(eliminado=True)\
            .limit(limite)\
            .offset(offset)\
            .all()
        return [self._modelo_a_entidad(m) for m in modelos]

    def _modelo_a_entidad(self, modelo: ProductoModel) -> Producto:
        """Convierte un modelo SQLAlchemy a entidad de dominio."""
        return Producto(
            uuid=UUID(bytes=modelo.uuid),
            nombre=modelo.nombre,
            barcode=modelo.barcode,
            valor_unitario=Decimal(str(modelo.valor_unitario)),
            stock=modelo.stock,
            descripcion=modelo.descripcion,
            imagen_uuid=modelo.imagen_uuid,
            eliminado=modelo.eliminado
        )
