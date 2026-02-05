"""
Mock de Blob Storage implementado con el sistema de archivos local.

Este adaptador simula un servicio de almacenamiento de blobs guardando
las imágenes en disco usando el UUID como nombre de archivo.
"""

import logging
import os
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from application.ports.image_storage import IImageStorage


logger = logging.getLogger(__name__)


class FilesystemImageAdapter(IImageStorage):
    """
    Adaptador de almacenamiento de imágenes usando el sistema de archivos.

    Guarda las imágenes en un directorio local usando el UUID como
    nombre de archivo. Simula el comportamiento de un Blob Storage.

    Atributos:
        base_path: Ruta base donde se almacenan las imágenes.
        extension: Extensión por defecto para los archivos de imagen.
    """

    def __init__(
        self,
        base_path: Optional[str] = None,
        extension: str = ".jpg"
    ):
        """
        Inicializa el adaptador de almacenamiento de imágenes.

        Args:
            base_path: Ruta base para almacenar imágenes.
                      Si no se provee, usa './data/imagenes'.
            extension: Extensión por defecto para archivos de imagen.
        """
        self._base_path = Path(base_path or "./data/imagenes")
        self._extension = extension

        # Crear directorio si no existe
        self._base_path.mkdir(parents=True, exist_ok=True)

        logger.info(
            "FilesystemImageAdapter inicializado en %s",
            self._base_path.absolute()
        )

    def _crear_ruta(self, uuid: UUID) -> Path:
        """
        Crea la ruta completa para una imagen.

        Args:
            uuid: UUID de la imagen.

        Returns:
            Path: Ruta completa del archivo.
        """
        return self._base_path / f"{str(uuid)}{self._extension}"

    def guardar(self, imagen: bytes, uuid: UUID) -> None:
        """
        Guarda una imagen en el sistema de archivos.

        Args:
            imagen: Contenido binario de la imagen.
            uuid: UUID único para identificar la imagen.

        Raises:
            IOError: Si ocurre un error al escribir el archivo.
        """
        ruta = self._crear_ruta(uuid)

        try:
            with open(ruta, "wb") as archivo:
                archivo.write(imagen)

            logger.info("Imagen guardada en %s (%d bytes)", ruta, len(imagen))
        except IOError as e:
            logger.error("Error al guardar imagen %s: %s", str(uuid), str(e))
            raise

    def obtener(self, uuid: UUID) -> Optional[bytes]:
        """
        Obtiene una imagen del sistema de archivos.

        Args:
            uuid: UUID de la imagen a obtener.

        Returns:
            bytes: Contenido binario de la imagen, None si no existe.
        """
        ruta = self._crear_ruta(uuid)

        try:
            if not ruta.exists():
                logger.warning("Imagen no encontrada: %s", str(uuid))
                return None

            with open(ruta, "rb") as archivo:
                contenido = archivo.read()

            logger.debug("Imagen obtenida de %s (%d bytes)", ruta, len(contenido))
            return contenido
        except IOError as e:
            logger.error("Error al leer imagen %s: %s", str(uuid), str(e))
            return None

    def eliminar(self, uuid: UUID) -> None:
        """
        Elimina una imagen del sistema de archivos.

        Args:
            uuid: UUID de la imagen a eliminar.

        Raises:
            FileNotFoundError: Si la imagen no existe.
        """
        ruta = self._crear_ruta(uuid)

        try:
            if not ruta.exists():
                logger.warning("Intento de eliminar imagen inexistente: %s", str(uuid))
                raise FileNotFoundError(f"Imagen no encontrada: {uuid}")

            os.remove(ruta)
            logger.info("Imagen eliminada: %s", str(uuid))
        except OSError as e:
            logger.error("Error al eliminar imagen %s: %s", str(uuid), str(e))
            raise

    def obtener_batch_imagenes(self, uuids: List[UUID]) -> List[Optional[bytes]]:
        """
        Obtiene un batch de imágenes del sistema de archivos.

        Args:
            uuids: Lista de UUIDs de imágenes a obtener.

        Returns:
            List[Optional[bytes]]: Lista de contenidos, None para las no encontradas.
        """
        resultados = []

        for uuid in uuids:
            imagen = self.obtener(uuid)
            resultados.append(imagen)

        encontradas = sum(1 for img in resultados if img is not None)
        logger.debug(
            "Batch de imágenes: %d/%d encontradas",
            encontradas, len(uuids)
        )

        return resultados

    def existe(self, uuid: UUID) -> bool:
        """
        Verifica si existe una imagen.

        Args:
            uuid: UUID de la imagen.

        Returns:
            bool: True si existe, False en caso contrario.
        """
        return self._crear_ruta(uuid).exists()

    def obtener_tamanio(self, uuid: UUID) -> Optional[int]:
        """
        Obtiene el tamaño de una imagen en bytes.

        Args:
            uuid: UUID de la imagen.

        Returns:
            int: Tamaño en bytes, None si no existe.
        """
        ruta = self._crear_ruta(uuid)

        if not ruta.exists():
            return None

        return ruta.stat().st_size

    def listar_imagenes(self) -> List[UUID]:
        """
        Lista todos los UUIDs de imágenes almacenadas.

        Returns:
            List[UUID]: Lista de UUIDs de imágenes.
        """
        imagenes = []

        for archivo in self._base_path.glob(f"*{self._extension}"):
            try:
                uuid_str = archivo.stem
                imagenes.append(UUID(uuid_str))
            except ValueError:
                logger.warning("Archivo con nombre no válido como UUID: %s", archivo.name)

        logger.debug("Listadas %d imágenes", len(imagenes))
        return imagenes
