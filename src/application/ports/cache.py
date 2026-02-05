"""Interfaz para el cache"""

from abc import ABC, abstractmethod
from typing import List
from uuid import UUID


class ICache(ABC):
    """Interfaz para el cache genérico"""

    @abstractmethod
    def guardar(self, uuid: UUID, datos: dict) -> None:
        """Guarda datos en el cache."""

    @abstractmethod
    def obtener(self, uuid: UUID) -> dict:
        """Obtiene datos del cache."""

    @abstractmethod
    def eliminar(self, uuid: UUID) -> None:
        """Elimina datos del cache."""

    @abstractmethod
    def obtener_batch(self, uuids: List[UUID]) -> List[dict]:
        """Obtiene un batch de datos del cache."""


class ICarritoCache(ABC):
    """Interfaz para el cache de carritos."""

    @abstractmethod
    def crear_carrito(self, usuario_id: UUID) -> None:
        """Crea un carrito para un usuario."""

    @abstractmethod
    def agregar_producto(self, usuario_id: UUID, producto_id: UUID, cantidad: int) -> None:
        """Agrega un producto al carrito de un usuario."""

    @abstractmethod
    def eliminar_producto(self, usuario_id: UUID, producto_id: UUID, cantidad: int) -> None:
        """Elimina un producto del carrito de un usuario."""

    @abstractmethod
    def obtener_carrito(self, usuario_id: UUID) -> List[dict]:
        """Obtiene el carrito de un usuario."""

    @abstractmethod
    def eliminar_carrito(self, usuario_id: UUID) -> None:
        """Elimina el carrito de un usuario."""
