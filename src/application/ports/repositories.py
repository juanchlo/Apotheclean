"""
Módulo que contiene las interfaces de repositorio para la aplicación.
"""

from datetime import datetime
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from domain.entities import Producto, Usuario, Venta, ModalidadVenta, EstadoVenta


class IProductoRepository(ABC):
    """Interfaz para el repositorio de productos."""

    @abstractmethod
    def guardar(self, producto: Producto) -> None:
        """Guarda un nuevo producto o actualiza uno existente."""

    @abstractmethod
    def obtener_por_uuid(self, uuid: UUID) -> Optional[Producto]:
        """Obtiene un producto por su UUID."""

    @abstractmethod
    def obtener_por_barcode(self, barcode: str) -> Optional[Producto]:
        """Deduplicación de productos."""

    @abstractmethod
    def obtener_todos(self, limite: int, offset: int) -> List[Producto]:
        """Implementa el soporte para paginación."""

    @abstractmethod
    def eliminar(self, uuid: UUID) -> None:
        """Soft Delete, el adaptador cambiará el flag."""


class IUsuarioRepository(ABC):
    """Interfaz para el repositorio de usuarios."""

    @abstractmethod
    def guardar(self, usuario: Usuario) -> bool:
        """Guarda un nuevo usuario."""

    @abstractmethod
    def obtener_por_email(self, email: str) -> Optional[Usuario]:
        """Obtiene un usuario por su correo electrónico."""

    @abstractmethod
    def obtener_por_uuid(self, uuid: UUID) -> Optional[Usuario]:
        """Obtiene un usuario por su UUID."""

    @abstractmethod
    def obtener_por_username_o_email(self, username: Optional[str],
                                     email: Optional[str]) -> Optional[Usuario]:
        """Obtiene un usuario por su username o correo electrónico."""

    @abstractmethod
    def obtener_por_username(self, username: str) -> Optional[Usuario]:
        """Obtiene un usuario por su username."""

    @abstractmethod
    def obtener_todos(self, limite: int, offset: int) -> List[Usuario]:
        """
        Necesario para reporte administrativo de usuarios,
        implementa el soporte para paginación.
        """

    @abstractmethod
    def deshabilitar(self, uuid: UUID) -> bool:
        """Soft Delete, el adaptador cambiará el flag."""


class IVentaRepository(ABC):
    """Interfaz para el repositorio de ventas."""

    @abstractmethod
    def guardar(self, venta: Venta) -> None:
        """Guarda una nueva venta."""

    @abstractmethod
    def obtener_por_uuid(self, uuid: UUID) -> Optional[Venta]:
        """Obtiene una venta por su UUID."""

    @abstractmethod
    def obtener_todos(self, limite: int, offset: int) -> List[Venta]:
        """Implementa el soporte para paginación."""

    @abstractmethod
    def eliminar(self, uuid: UUID) -> None:
        """Soft Delete, el adaptador cambiará el flag."""

    @abstractmethod
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
        """
        Búsqueda flexible con filtros opcionales.
        Permite filtrar por usuario, producto, modalidad, estado y rango de fechas.
        Soporta paginación con limite y offset.
        """
