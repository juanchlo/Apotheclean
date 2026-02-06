"""
Configuración de Redis desde variables de entorno.

Provee funciones para crear instancias de los adaptadores de Redis
con la configuración centralizada.
"""

import os

from src.infraestructure.cache.redis_cache_adapter import RedisCacheAdapter
from src.infraestructure.cache.redis_carrito_adapter import RedisCarritoAdapter


def obtener_config_redis() -> dict:
    """
    Obtiene la configuración de Redis desde variables de entorno.

    Returns:
        dict: Configuración con host, port, db y password.
    """
    return {
        "host": os.getenv("REDIS_HOST", "localhost"),
        "port": int(os.getenv("REDIS_PORT", "6379")),
        "db": int(os.getenv("REDIS_DB", "0")),
        "password": os.getenv("REDIS_PASSWORD") or None,
    }


def crear_cache_adapter(
    prefix: str = "cache",
    ttl_seconds: int = 3600
) -> RedisCacheAdapter:
    """
    Crea una instancia de RedisCacheAdapter con la configuración del entorno.

    Args:
        prefix: Prefijo para las claves de cache.
        ttl_seconds: Tiempo de vida en segundos.

    Returns:
        RedisCacheAdapter: Instancia configurada.
    """
    config = obtener_config_redis()
    return RedisCacheAdapter(
        host=config["host"],
        port=config["port"],
        db=config["db"],
        password=config["password"],
        prefix=prefix,
        ttl_seconds=ttl_seconds
    )


def crear_carrito_adapter(
    ttl_seconds: int = 86400
) -> RedisCarritoAdapter:
    """
    Crea una instancia de RedisCarritoAdapter con la configuración del entorno.

    Args:
        ttl_seconds: Tiempo de vida del carrito en segundos (default: 24h).

    Returns:
        RedisCarritoAdapter: Instancia configurada.
    """
    config = obtener_config_redis()
    # Carrito usa db=1 para separar de cache general
    return RedisCarritoAdapter(
        host=config["host"],
        port=config["port"],
        db=1,
        password=config["password"],
        ttl_seconds=ttl_seconds
    )
