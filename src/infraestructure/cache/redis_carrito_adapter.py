"""
Adaptador de cache para carritos de compra usando Redis.

Implementa la interfaz ICarritoCache para manejar carritos temporales
de usuarios en Redis con operaciones atómicas.

Incluye patrones de resiliencia:
- Retry con backoff exponencial para operaciones fallidas
- Fallback silencioso para operaciones de lectura
"""

import logging
from typing import List, Optional
from uuid import UUID

import redis
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

from application.ports.cache import ICarritoCache


logger = logging.getLogger(__name__)


# Configuración de retry para operaciones de carrito
RETRY_CONFIG = {
    "stop": stop_after_attempt(3),
    "wait": wait_exponential(multiplier=0.1, min=0.1, max=2),
    "retry": retry_if_exception_type(redis.RedisError),
    "before_sleep": before_sleep_log(logger, logging.WARNING),
    "reraise": True
}


class RedisCarritoAdapter(ICarritoCache):
    """
    Adaptador de cache para carritos usando Redis Hashes.

    Utiliza Redis Hashes para almacenar productos y cantidades
    de manera eficiente, permitiendo operaciones atómicas.

    Implementa patrones de resiliencia para manejar fallos de conexión.

    Atributos:
        host: Host del servidor Redis.
        port: Puerto del servidor Redis.
        db: Número de base de datos Redis.
        ttl_seconds: Tiempo de vida del carrito en segundos.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 1,
        password: Optional[str] = None,
        ttl_seconds: int = 86400,
        socket_timeout: float = 2.0
    ):
        """
        Inicializa el adaptador de carrito Redis.

        Args:
            host: Host del servidor Redis.
            port: Puerto del servidor Redis.
            db: Número de base de datos Redis (default: 1 para separar de cache).
            password: Contraseña para autenticación (opcional).
            ttl_seconds: Tiempo de vida del carrito en segundos (default: 24h).
            socket_timeout: Timeout de conexión en segundos.
        """
        self._client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_timeout
        )
        self._ttl_seconds = ttl_seconds
        self._prefix = "carrito"

        logger.info(
            "RedisCarritoAdapter inicializado en %s:%d db=%d",
            host, port, db
        )

    def _crear_clave(self, usuario_id: UUID) -> str:
        """
        Crea la clave del carrito para un usuario.

        Args:
            usuario_id: UUID del usuario.

        Returns:
            str: Clave del carrito formateada.
        """
        return f"{self._prefix}:{str(usuario_id)}"

    @retry(**RETRY_CONFIG)
    def crear_carrito(self, usuario_id: UUID) -> None:
        """
        Crea un carrito vacío para un usuario con reintentos.

        Args:
            usuario_id: UUID del usuario.

        Raises:
            redis.RedisError: Si falla después de reintentos.
        """
        clave = self._crear_clave(usuario_id)
        self._client.hset(clave, "_creado", "true")
        self._client.expire(clave, self._ttl_seconds)
        logger.info("Carrito creado para usuario %s", str(usuario_id))

    @retry(**RETRY_CONFIG)
    def agregar_producto(
        self,
        usuario_id: UUID,
        producto_id: UUID,
        cantidad: int
    ) -> None:
        """
        Agrega un producto al carrito con reintentos.

        Si el producto ya existe, incrementa la cantidad.

        Args:
            usuario_id: UUID del usuario.
            producto_id: UUID del producto.
            cantidad: Cantidad a agregar.

        Raises:
            ValueError: Si la cantidad es menor o igual a 0.
            redis.RedisError: Si falla después de reintentos.
        """
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor a 0")

        clave = self._crear_clave(usuario_id)
        producto_key = str(producto_id)

        nueva_cantidad = self._client.hincrby(clave, producto_key, cantidad)
        self._client.expire(clave, self._ttl_seconds)

        logger.info(
            "Producto %s agregado al carrito de %s, cantidad total: %d",
            producto_key, str(usuario_id), nueva_cantidad
        )

    @retry(**RETRY_CONFIG)
    def eliminar_producto(
        self,
        usuario_id: UUID,
        producto_id: UUID,
        cantidad: int
    ) -> None:
        """
        Elimina o reduce cantidad de un producto con reintentos.

        Si la cantidad resultante es 0 o menor, elimina el producto.

        Args:
            usuario_id: UUID del usuario.
            producto_id: UUID del producto.
            cantidad: Cantidad a eliminar.

        Raises:
            ValueError: Si la cantidad es menor o igual a 0.
            redis.RedisError: Si falla después de reintentos.
        """
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor a 0")

        clave = self._crear_clave(usuario_id)
        producto_key = str(producto_id)

        nueva_cantidad = self._client.hincrby(clave, producto_key, -cantidad)

        if nueva_cantidad <= 0:
            self._client.hdel(clave, producto_key)
            logger.info(
                "Producto %s eliminado del carrito de %s",
                producto_key, str(usuario_id)
            )
        else:
            logger.info(
                "Producto %s reducido en carrito de %s, cantidad restante: %d",
                producto_key, str(usuario_id), nueva_cantidad
            )

        self._client.expire(clave, self._ttl_seconds)

    def obtener_carrito(self, usuario_id: UUID) -> List[dict]:
        """
        Obtiene el carrito completo con fallback silencioso.

        Si Redis no está disponible, retorna lista vacía.

        Args:
            usuario_id: UUID del usuario.

        Returns:
            List[dict]: Lista de items con producto_id y cantidad.
        """
        clave = self._crear_clave(usuario_id)

        try:
            return self._obtener_carrito_con_retry(clave, usuario_id)
        except redis.RedisError as e:
            logger.warning(
                "Error al obtener carrito, retornando vacío: %s",
                str(e)
            )
            return []

    @retry(**RETRY_CONFIG)
    def _obtener_carrito_con_retry(
        self,
        clave: str,
        usuario_id: UUID
    ) -> List[dict]:
        """
        Operación interna de obtención de carrito con retry.

        Args:
            clave: Clave de Redis del carrito.
            usuario_id: UUID del usuario para logging.

        Returns:
            Lista de items del carrito.
        """
        datos = self._client.hgetall(clave)
        items = []

        for producto_id, cantidad in datos.items():
            if producto_id == "_creado":
                continue

            items.append({
                "producto_id": UUID(producto_id),
                "cantidad": int(cantidad)
            })

        logger.debug(
            "Carrito de %s obtenido con %d items",
            str(usuario_id), len(items)
        )
        return items

    @retry(**RETRY_CONFIG)
    def eliminar_carrito(self, usuario_id: UUID) -> None:
        """
        Elimina completamente el carrito con reintentos.

        Args:
            usuario_id: UUID del usuario.

        Raises:
            redis.RedisError: Si falla después de reintentos.
        """
        clave = self._crear_clave(usuario_id)
        resultado = self._client.delete(clave)

        if resultado:
            logger.info("Carrito eliminado para usuario %s", str(usuario_id))
        else:
            logger.debug("No existía carrito para usuario %s", str(usuario_id))

    def obtener_cantidad_items(self, usuario_id: UUID) -> int:
        """
        Obtiene el número total de items con fallback silencioso.

        Si Redis no está disponible, retorna 0.

        Args:
            usuario_id: UUID del usuario.

        Returns:
            int: Cantidad total de items (suma de cantidades).
        """
        clave = self._crear_clave(usuario_id)

        try:
            return self._obtener_cantidad_items_con_retry(clave)
        except redis.RedisError as e:
            logger.warning(
                "Error al contar items del carrito, retornando 0: %s",
                str(e)
            )
            return 0

    @retry(**RETRY_CONFIG)
    def _obtener_cantidad_items_con_retry(self, clave: str) -> int:
        """
        Operación interna de conteo de items con retry.

        Args:
            clave: Clave de Redis del carrito.

        Returns:
            Cantidad total de items.
        """
        datos = self._client.hgetall(clave)
        return sum(
            int(cantidad)
            for producto_id, cantidad in datos.items()
            if producto_id != "_creado"
        )

    def carrito_existe(self, usuario_id: UUID) -> bool:
        """
        Verifica si existe un carrito con fallback silencioso.

        Si Redis no está disponible, retorna False.

        Args:
            usuario_id: UUID del usuario.

        Returns:
            bool: True si existe, False en caso contrario o error.
        """
        clave = self._crear_clave(usuario_id)
        try:
            return self._carrito_existe_con_retry(clave)
        except redis.RedisError as e:
            logger.warning(
                "Error al verificar existencia de carrito: %s",
                str(e)
            )
            return False

    @retry(**RETRY_CONFIG)
    def _carrito_existe_con_retry(self, clave: str) -> bool:
        """
        Operación interna de verificación con retry.

        Args:
            clave: Clave de Redis a verificar.

        Returns:
            True si existe el carrito.
        """
        return bool(self._client.exists(clave))

    def ping(self) -> bool:
        """
        Verifica si Redis está disponible.

        Returns:
            bool: True si Redis responde, False en caso contrario.
        """
        try:
            return self._client.ping()
        except redis.RedisError:
            return False
