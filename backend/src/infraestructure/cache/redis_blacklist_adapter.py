"""
Adaptador de Blacklist usando Redis para tokens revocados.

Proporciona almacenamiento temporal con TTL automático para JTI de tokens.
"""

import logging
from typing import Optional
import redis
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class RedisBlacklistAdapter:
    """
    Adaptador de Blacklist para invalidar tokens JWT usando Redis.

    Utiliza el campo JTI (JWT ID) como clave y establece TTL automático
    basado en la expiración del token.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None
    ):
        """
        Inicializa la conexión a Redis.

        Args:
            host: Host del servidor Redis.
            port: Puerto del servidor Redis.
            db: Base de datos de Redis (0-15).
            password: Contraseña de Redis (opcional).
        """
        try:
            self._client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,
                socket_timeout=2.0,
                socket_connect_timeout=2.0
            )
            # Verificar conexión
            self._client.ping()
            logger.info("Conexión a Redis establecida correctamente")
        except redis.RedisError as e:
            logger.error(f"Error al conectar con Redis: {e}")
            raise

    @property
    def redis_client(self):
        """Propiedad para acceder al cliente Redis (útil para tests)."""
        return self._client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.1, min=0.1, max=0.5)
    )
    def agregar(self, jti: str, expiracion_segundos: int) -> None:
        """
        Agrega un JTI a la blacklist con TTL automático.

        Args:
            jti: JWT ID único del token.
            expiracion_segundos: Segundos hasta que expire el token (TTL).
        
        Raises:
            redis.RedisError: Si falla después de 3 intentos.
        """
        try:
            clave = f"blacklist:{jti}"
            # Usar int directamente en lugar de timedelta
            self._client.setex(clave, expiracion_segundos, "revoked")
            logger.info(f"Token JTI {jti} agregado a blacklist (TTL: {expiracion_segundos}s)")
        except redis.RedisError as e:
            logger.error(f"Error al agregar JTI a blacklist: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.1, min=0.1, max=0.5)
    )
    def esta_en_blacklist(self, jti: str) -> bool:
        """
        Verifica si un JTI está en la blacklist.

        Args:
            jti: JWT ID a verificar.

        Returns:
            True si está en blacklist (revocado), False en caso contrario.
            
        Nota:
            Implementa "Fail Close": si Redis falla después de reintentos,
            retorna True (considera el token revocado) por seguridad.
            Esto previene que tokens potencialmente revocados sean aceptados
            en caso de problemas de infraestructura.
        """
        try:
            clave = f"blacklist:{jti}"
            existe = self._client.exists(clave)
            return bool(existe)
        except redis.RedisError as e:
            logger.error(f"Error al consultar blacklist (Fail Close): {e}")
            # Fail Close: por seguridad, considerar token revocado si Redis falla
            return True