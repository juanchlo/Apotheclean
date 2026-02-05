"""
Adaptador de cache genérico que implementa la interfaz ICache usando Redis.

Provee operaciones básicas de cache como guardar, obtener, eliminar y
operaciones en batch para optimizar las consultas.

Incluye patrones de resiliencia:
- Retry con backoff exponencial para operaciones fallidas
- Fallback silencioso cuando Redis no está disponible
"""

import json
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

from application.ports.cache import ICache


logger = logging.getLogger(__name__)


# Configuración de retry para operaciones de cache
RETRY_CONFIG = {
    "stop": stop_after_attempt(3),
    "wait": wait_exponential(multiplier=0.1, min=0.1, max=2),
    "retry": retry_if_exception_type(redis.RedisError),
    "before_sleep": before_sleep_log(logger, logging.WARNING),
    "reraise": True
}


class RedisCacheAdapter(ICache):
    """
    Adaptador de cache genérico que utiliza Redis como backend.

    Implementa patrones de resiliencia para manejar fallos de conexión
    y timeouts de forma automática.

    Atributos:
        host: Host del servidor Redis.
        port: Puerto del servidor Redis.
        db: Número de base de datos Redis.
        prefix: Prefijo para las claves de cache.
        ttl_seconds: Tiempo de vida de los datos en segundos.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        prefix: str = "cache",
        ttl_seconds: int = 3600,
        socket_timeout: float = 2.0
    ):
        """
        Inicializa el adaptador de cache Redis.

        Args:
            host: Host del servidor Redis.
            port: Puerto del servidor Redis.
            db: Número de base de datos Redis a usar.
            password: Contraseña para autenticación (opcional).
            prefix: Prefijo para las claves de cache.
            ttl_seconds: Tiempo de vida por defecto en segundos.
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
        self._prefix = prefix
        self._ttl_seconds = ttl_seconds
        self._disponible = True

        logger.info(
            "RedisCacheAdapter inicializado en %s:%d db=%d con prefijo '%s'",
            host, port, db, prefix
        )

    def _crear_clave(self, uuid: UUID) -> str:
        """
        Crea la clave completa para Redis con el prefijo.

        Args:
            uuid: UUID del recurso.

        Returns:
            str: Clave formateada con prefijo.
        """
        return f"{self._prefix}:{str(uuid)}"

    @retry(**RETRY_CONFIG)
    def guardar(self, uuid: UUID, datos: dict) -> None:
        """
        Guarda datos en el cache con reintentos automáticos.

        Args:
            uuid: UUID identificador del recurso.
            datos: Diccionario con los datos a guardar.

        Raises:
            redis.RedisError: Si falla después de todos los reintentos.
        """
        clave = self._crear_clave(uuid)
        self._client.setex(
            clave,
            self._ttl_seconds,
            json.dumps(datos, default=str)
        )
        logger.debug("Datos guardados en cache con clave %s", clave)

    def obtener(self, uuid: UUID) -> Optional[dict]:
        """
        Obtiene datos del cache con fallback silencioso.

        Si Redis no está disponible, retorna None sin propagar el error.
        Esto permite que la aplicación continúe funcionando usando la BD.

        Args:
            uuid: UUID identificador del recurso.

        Returns:
            dict: Los datos almacenados o None si no existen/error.
        """
        clave = self._crear_clave(uuid)
        try:
            datos = self._obtener_con_retry(clave)
            if datos:
                logger.debug("Cache hit para clave %s", clave)
                return json.loads(datos)
            logger.debug("Cache miss para clave %s", clave)
            return None
        except redis.RedisError as e:
            # Fallback silencioso - la aplicación continúa sin cache
            logger.warning(
                "Cache no disponible, continuando sin cache: %s",
                str(e)
            )
            return None

    @retry(**RETRY_CONFIG)
    def _obtener_con_retry(self, clave: str) -> Optional[str]:
        """
        Operación interna de obtención con retry.

        Args:
            clave: Clave de Redis a consultar.

        Returns:
            str: Valor almacenado o None.
        """
        return self._client.get(clave)

    @retry(**RETRY_CONFIG)
    def eliminar(self, uuid: UUID) -> None:
        """
        Elimina datos del cache con reintentos automáticos.

        Args:
            uuid: UUID identificador del recurso a eliminar.

        Raises:
            redis.RedisError: Si falla después de todos los reintentos.
        """
        clave = self._crear_clave(uuid)
        resultado = self._client.delete(clave)
        if resultado:
            logger.debug("Clave %s eliminada del cache", clave)
        else:
            logger.debug("Clave %s no existía en cache", clave)

    def obtener_batch(self, uuids: List[UUID]) -> List[Optional[dict]]:
        """
        Obtiene un batch de datos del cache con fallback silencioso.

        Si Redis no está disponible, retorna lista de None.

        Args:
            uuids: Lista de UUIDs a consultar.

        Returns:
            List[Optional[dict]]: Lista de datos en el mismo orden,
                                  None para los que no existen.
        """
        if not uuids:
            return []

        claves = [self._crear_clave(uuid) for uuid in uuids]
        try:
            return self._obtener_batch_con_retry(claves)
        except redis.RedisError as e:
            logger.warning(
                "Cache no disponible para batch, continuando sin cache: %s",
                str(e)
            )
            return [None] * len(uuids)

    @retry(**RETRY_CONFIG)
    def _obtener_batch_con_retry(self, claves: List[str]) -> List[Optional[dict]]:
        """
        Operación interna de obtención batch con retry.

        Args:
            claves: Lista de claves de Redis a consultar.

        Returns:
            Lista de diccionarios o None para cada clave.
        """
        resultados = self._client.mget(claves)
        datos = []
        for i, resultado in enumerate(resultados):
            if resultado:
                datos.append(json.loads(resultado))
                logger.debug("Cache hit para clave %s", claves[i])
            else:
                datos.append(None)
                logger.debug("Cache miss para clave %s", claves[i])
        return datos

    def existe(self, uuid: UUID) -> bool:
        """
        Verifica si existe una clave en el cache.

        En caso de error, retorna False (fallback silencioso).

        Args:
            uuid: UUID identificador del recurso.

        Returns:
            bool: True si existe, False en caso contrario o error.
        """
        clave = self._crear_clave(uuid)
        try:
            return self._existe_con_retry(clave)
        except redis.RedisError as e:
            logger.warning("Error al verificar existencia en cache: %s", str(e))
            return False

    @retry(**RETRY_CONFIG)
    def _existe_con_retry(self, clave: str) -> bool:
        """
        Operación interna de verificación con retry.

        Args:
            clave: Clave de Redis a verificar.

        Returns:
            bool: True si existe la clave.
        """
        return bool(self._client.exists(clave))

    def refrescar_ttl(self, uuid: UUID) -> bool:
        """
        Renueva el tiempo de vida de una clave.

        En caso de error, retorna False (fallback silencioso).

        Args:
            uuid: UUID identificador del recurso.

        Returns:
            bool: True si se renovó exitosamente, False si error.
        """
        clave = self._crear_clave(uuid)
        try:
            return self._refrescar_ttl_con_retry(clave)
        except redis.RedisError as e:
            logger.warning("Error al refrescar TTL: %s", str(e))
            return False

    @retry(**RETRY_CONFIG)
    def _refrescar_ttl_con_retry(self, clave: str) -> bool:
        """
        Operación interna de renovación de TTL con retry.

        Args:
            clave: Clave de Redis a renovar.

        Returns:
            bool: True si se renovó exitosamente.
        """
        return bool(self._client.expire(clave, self._ttl_seconds))

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
