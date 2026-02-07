"""Implementación SQLAlchemy del repositorio de ventas."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.domain.entities import Venta, DetalleVenta, ModalidadVenta, EstadoVenta
from src.application.ports.repositories import IVentaRepository
from src.infraestructure.adapters.orm.models import VentaModel, DetalleVentaModel


from src.infraestructure.resilience import retry_db_operation


class SQLAlchemyVentaRepository(IVentaRepository):
    """Implementación del repositorio de ventas usando SQLAlchemy."""

    def __init__(self, session: Session):
        """
        Inicializa el repositorio con una sesión de SQLAlchemy.

        Args:
            session: Sesión de SQLAlchemy
        """
        self.session = session

    @retry_db_operation
    def guardar(self, venta: Venta) -> None:
        """
        Guarda una nueva venta o actualiza una existente.

        Args:
            venta: Entidad Venta a guardar
        """
        modelo_existente = self.session.query(VentaModel).filter_by(
            uuid=venta.uuid.bytes
        ).first()

        if modelo_existente:
            modelo_existente.modalidad = venta.modalidad.value
            modelo_existente.estado = venta.estado.value
            modelo_existente.valor_total_cop = venta.valor_total_cop
            # Actualizar items
            modelo_existente.items.clear()
            for item in venta.items:
                detalle = DetalleVentaModel(
                    producto_id=item.producto_id.bytes,
                    cantidad=item.cantidad,
                    precio_unitario_historico=item.precio_unitario_historico
                )
                modelo_existente.items.append(detalle)
        else:
            modelo = VentaModel(
                uuid=venta.uuid.bytes,
                modalidad=venta.modalidad.value,
                estado=venta.estado.value,
                comprador_id=self._obtener_usuario_id(venta.comprador_id),
                vendedor_id=self._obtener_usuario_id(venta.vendedor_id),
                fecha=venta.fecha,
                valor_total_cop=venta.valor_total_cop
            )
            for item in venta.items:
                detalle = DetalleVentaModel(
                    producto_id=item.producto_id.bytes,
                    cantidad=item.cantidad,
                    precio_unitario_historico=item.precio_unitario_historico
                )
                modelo.items.append(detalle)
            self.session.add(modelo)

        self.session.commit()

    @retry_db_operation
    def obtener_por_uuid(self, uuid: UUID) -> Optional[Venta]:
        """Obtiene una venta por su UUID."""
        modelo = self.session.query(VentaModel).filter_by(
            uuid=uuid.bytes
        ).first()
        return self._modelo_a_entidad(modelo) if modelo else None

    @retry_db_operation
    def obtener_todos(self, limite: int, offset: int) -> List[Venta]:
        """Obtiene todas las ventas con paginación."""
        modelos = self.session.query(VentaModel)\
            .order_by(VentaModel.fecha.desc())\
            .limit(limite)\
            .offset(offset)\
            .all()
        return [self._modelo_a_entidad(m) for m in modelos]

    @retry_db_operation
    def eliminar(self, uuid: UUID) -> None:
        """Elimina una venta (cancela)."""
        modelo = self.session.query(VentaModel).filter_by(
            uuid=uuid.bytes
        ).first()
        if modelo:
            modelo.estado = EstadoVenta.CANCELADA.value
            self.session.commit()

    @retry_db_operation
    def buscar(
        self,
        usuario_id: Optional[UUID] = None,
        producto_id: Optional[UUID] = None,
        modalidad: Optional[ModalidadVenta] = None,
        estado: Optional[EstadoVenta] = None,
        fecha_inicio: Optional[datetime] = None,
        fecha_fin: Optional[datetime] = None,
        limite: int = 10,
        offset: int = 0
    ) -> List[Venta]:
        """Búsqueda flexible con filtros opcionales."""
        query = self.session.query(VentaModel)

        if usuario_id:
            user_id_int = self._obtener_usuario_id(usuario_id)
            query = query.filter(
                (VentaModel.comprador_id == user_id_int) |
                (VentaModel.vendedor_id == user_id_int)
            )

        if modalidad:
            query = query.filter(VentaModel.modalidad == modalidad.value)

        if estado:
            query = query.filter(VentaModel.estado == estado.value)

        if fecha_inicio:
            query = query.filter(VentaModel.fecha >= fecha_inicio)

        if fecha_fin:
            query = query.filter(VentaModel.fecha <= fecha_fin)

        if producto_id:
            query = query.join(DetalleVentaModel).filter(
                DetalleVentaModel.producto_id == producto_id.bytes
            )

        modelos = query.order_by(VentaModel.fecha.desc())\
            .limit(limite)\
            .offset(offset)\
            .all()

        return [self._modelo_a_entidad(m) for m in modelos]

    def _obtener_usuario_id(self, uuid: Optional[UUID]) -> Optional[int]:
        """Obtiene el ID interno de un usuario por su UUID."""
        if uuid is None:
            return None
        from src.infraestructure.adapters.orm.models import UsuarioModel
        modelo = self.session.query(UsuarioModel).filter_by(
            uuid=uuid.bytes
        ).first()
        return modelo.id if modelo else None

    def _modelo_a_entidad(self, modelo: VentaModel) -> Venta:
        """Convierte un modelo SQLAlchemy a entidad de dominio."""
        items = [
            DetalleVenta(
                producto_id=UUID(bytes=item.producto_id),
                cantidad=item.cantidad,
                precio_unitario_historico=Decimal(str(item.precio_unitario_historico))
            )
            for item in modelo.items
        ]

        comprador_uuid = None
        if modelo.comprador:
            comprador_uuid = UUID(bytes=modelo.comprador.uuid)

        vendedor_uuid = None
        if modelo.vendedor:
            vendedor_uuid = UUID(bytes=modelo.vendedor.uuid)

        return Venta(
            uuid=UUID(bytes=modelo.uuid),
            items=items,
            modalidad=ModalidadVenta(modelo.modalidad),
            estado=EstadoVenta(modelo.estado),
            comprador_id=comprador_uuid,
            vendedor_id=vendedor_uuid,
            fecha=modelo.fecha,
            valor_total_cop=Decimal(str(modelo.valor_total_cop))
        )
