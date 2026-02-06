"""Interfaz para el almacenamiento de imágenes."""

from abc import ABC, abstractmethod
from typing import List
from uuid import UUID


class IImageStorage(ABC):
    """Interfaz para el almacenamiento de imágenes."""

    @abstractmethod
    def guardar(self, imagen: bytes, uuid: UUID) -> None:
        """Guarda una imagen."""

    @abstractmethod
    def obtener(self, uuid: UUID) -> bytes:
        """Obtiene una imagen."""

    @abstractmethod
    def eliminar(self, uuid: UUID) -> None:
        """Elimina una imagen."""

    @abstractmethod
    def obtener_batch_imagenes(self, uuids: List[UUID]) -> List[bytes]:
        """Obtiene un batch de imágenes."""
