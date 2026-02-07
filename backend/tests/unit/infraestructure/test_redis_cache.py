
import json
import pytest
from unittest.mock import Mock, patch
from uuid import uuid4
import redis

from src.infraestructure.cache.redis_cache_adapter import RedisCacheAdapter

class TestRedisCacheAdapter:
    """Tests para RedisCacheAdapter."""

    @pytest.fixture
    def mock_redis(self):
        """Fixture que mockea el cliente de Redis."""
        with patch('redis.Redis') as mock:
            yield mock.return_value

    @pytest.fixture
    def adapter(self, mock_redis):
        """Fixture que inicializa el adaptador con el mock."""
        return RedisCacheAdapter()

    def test_guardar_exitoso(self, adapter, mock_redis):
        """Verifica que guarda datos correctamente."""
        uuid = uuid4()
        datos = {"key": "value"}
        
        adapter.guardar(uuid, datos)
        
        mock_redis.setex.assert_called_once()
        args = mock_redis.setex.call_args[0]
        assert args[0] == f"cache:{uuid}"
        assert args[1] == 3600
        assert json.loads(args[2]) == datos

    def test_obtener_exitoso(self, adapter, mock_redis):
        """Verifica que obtiene datos correctamente."""
        uuid = uuid4()
        datos = {"key": "value"}
        mock_redis.get.return_value = json.dumps(datos)
        
        resultado = adapter.obtener(uuid)
        
        assert resultado == datos
        mock_redis.get.assert_called_once_with(f"cache:{uuid}")

    def test_obtener_no_existente_retorna_none(self, adapter, mock_redis):
        """Verifica que retorna None si la clave no existe."""
        uuid = uuid4()
        mock_redis.get.return_value = None
        
        resultado = adapter.obtener(uuid)
        
        assert resultado is None

    def test_obtener_fallback_error_redis(self, adapter, mock_redis):
        """Verifica el fallback silencioso si Redis falla."""
        uuid = uuid4()
        mock_redis.get.side_effect = redis.RedisError("Connection error")
        
        resultado = adapter.obtener(uuid)
        
        assert resultado is None

    def test_eliminar_exitoso(self, adapter, mock_redis):
        """Verifica que elimina correctamente."""
        uuid = uuid4()
        mock_redis.delete.return_value = 1
        
        adapter.eliminar(uuid)
        
        mock_redis.delete.assert_called_once_with(f"cache:{uuid}")

    def test_obtener_batch_exitoso(self, adapter, mock_redis):
        """Verifica obtener multiples claves en batch."""
        uuid1 = uuid4()
        uuid2 = uuid4()
        datos1 = {"id": 1}
        mock_redis.mget.return_value = [json.dumps(datos1), None]
        
        resultados = adapter.obtener_batch([uuid1, uuid2])
        
        assert len(resultados) == 2
        assert resultados[0] == datos1
        assert resultados[1] is None
        mock_redis.mget.assert_called_once()

    def test_obtener_batch_lista_vacia(self, adapter, mock_redis):
        """Verifica comportamiento con lista vacía."""
        resultados = adapter.obtener_batch([])
        assert resultados == []
        mock_redis.mget.assert_not_called()

    def test_obtener_batch_fallback(self, adapter, mock_redis):
        """Verifica fallback en batch."""
        uuid = uuid4()
        mock_redis.mget.side_effect = redis.RedisError("Error")
        
        resultados = adapter.obtener_batch([uuid])
        
        assert resultados == [None]

    def test_existe_true(self, adapter, mock_redis):
        """Verifica existe devuelve True."""
        uuid = uuid4()
        mock_redis.exists.return_value = 1
        assert adapter.existe(uuid) is True

    def test_existe_false(self, adapter, mock_redis):
        """Verifica existe devuelve False."""
        uuid = uuid4()
        mock_redis.exists.return_value = 0
        assert adapter.existe(uuid) is False

    def test_existe_fallback(self, adapter, mock_redis):
        """Verifica existe fallback devuelve False."""
        uuid = uuid4()
        mock_redis.exists.side_effect = redis.RedisError("Error")
        assert adapter.existe(uuid) is False

    def test_refrescar_ttl_exitoso(self, adapter, mock_redis):
        """Verifica refrescar TTL."""
        uuid = uuid4()
        mock_redis.expire.return_value = True
        assert adapter.refrescar_ttl(uuid) is True

    def test_refrescar_ttl_fallback(self, adapter, mock_redis):
        """Verifica refrescar TTL fallback."""
        uuid = uuid4()
        mock_redis.expire.side_effect = redis.RedisError("Error")
        assert adapter.refrescar_ttl(uuid) is False

    def test_ping_exitoso(self, adapter, mock_redis):
        """Verifica ping."""
        mock_redis.ping.return_value = True
        assert adapter.ping() is True

    def test_ping_fallo(self, adapter, mock_redis):
        """Verifica ping fallo."""
        mock_redis.ping.side_effect = redis.RedisError("Error")
        assert adapter.ping() is False
