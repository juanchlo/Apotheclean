"""
Tests unitarios para el adaptador de Blacklist en Redis.

Verifica agregar y consultar tokens, y el manejo de excepciones de Redis.
"""

import pytest
from unittest.mock import patch
from redis import RedisError
from tenacity import RetryError

from src.infraestructure.cache.redis_blacklist_adapter import RedisBlacklistAdapter


class TestRedisBlacklistAdapter:
    """Tests para RedisBlacklistAdapter."""

    @patch("redis.Redis")
    def test_inicializacion_correcta(self, mock_redis_cls):
        """Verifica que se inicializa la conexión con los parámetros correctos."""
        adapter = RedisBlacklistAdapter(
            host="localhost",
            port=6379,
            db=2,
            password="pass"
        )
        
        mock_redis_cls.assert_called_with(
            host="localhost",
            port=6379,
            db=2,
            password="pass",
            decode_responses=True,
            socket_timeout=2.0,
            socket_connect_timeout=2.0
        )
        assert adapter.redis_client is not None

    @patch("redis.Redis")
    def test_agregar_token_exitoso(self, mock_redis_cls):
        """Verifica que agregar inserta el token en Redis con TTL."""
        mock_client = mock_redis_cls.return_value
        adapter = RedisBlacklistAdapter()
        
        jti = "test-jti-123"
        expiracion_segundos = 3600

        adapter.agregar(jti, expiracion_segundos)

        # Ahora esperamos int directamente, no timedelta
        mock_client.setex.assert_called_once_with(
            f"blacklist:{jti}",
            expiracion_segundos,
            "revoked"
        )

    @patch("redis.Redis")
    def test_agregar_token_falla_con_reintento(self, mock_redis_cls):
        """Verifica que si Redis falla, se reintenta y luego lanza excepción."""
        mock_client = mock_redis_cls.return_value
        mock_client.setex.side_effect = RedisError("Connection refused")
        
        adapter = RedisBlacklistAdapter()

        # Con @retry configurado, debería reintentar y luego lanzar RetryError
        with pytest.raises(RetryError):
            adapter.agregar("jti", 100)

    @patch("redis.Redis")
    def test_esta_en_blacklist_retorna_true_si_existe(self, mock_redis_cls):
        """Verifica que retorna True si la clave existe."""
        mock_client = mock_redis_cls.return_value
        mock_client.exists.return_value = 1
        
        adapter = RedisBlacklistAdapter()
        resultado = adapter.esta_en_blacklist("jti-existente")

        assert resultado is True

    @patch("redis.Redis")
    def test_esta_en_blacklist_retorna_false_si_no_existe(self, mock_redis_cls):
        """Verifica que retorna False si la clave no existe."""
        mock_client = mock_redis_cls.return_value
        mock_client.exists.return_value = 0
        
        adapter = RedisBlacklistAdapter()
        resultado = adapter.esta_en_blacklist("jti-inexistente")

        assert resultado is False

    @patch("redis.Redis")
    def test_esta_en_blacklist_fail_close(self, mock_redis_cls):
        """
        Verifica política Fail Close: si Redis falla al leer, 
        asumimos que SÍ está en blacklist por seguridad (denegar acceso)
        para prevenir que tokens revocados sean aceptados si Redis falla.
        """
        mock_client = mock_redis_cls.return_value
        mock_client.exists.side_effect = RedisError("Timeout")
        
        adapter = RedisBlacklistAdapter()
        resultado = adapter.esta_en_blacklist("jti-cualquiera")

        # Esperamos True (denegar acceso) en caso de error de infraestructura por seguridad
        assert resultado is True