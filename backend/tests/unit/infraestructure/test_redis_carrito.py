
import pytest
from unittest.mock import Mock, patch
from uuid import uuid4
import redis

from src.infraestructure.cache.redis_carrito_adapter import RedisCarritoAdapter

class TestRedisCarritoAdapter:
    """Tests para RedisCarritoAdapter."""

    @pytest.fixture
    def mock_redis(self):
        """Fixture que mockea el cliente de Redis."""
        with patch('redis.Redis') as mock:
            yield mock.return_value

    @pytest.fixture
    def adapter(self, mock_redis):
        """Fixture que inicializa el adaptador con el mock."""
        return RedisCarritoAdapter()

    def test_crear_carrito(self, adapter, mock_redis):
        """Verifica creación de carrito."""
        uuid = uuid4()
        adapter.crear_carrito(uuid)
        
        clave = f"carrito:{uuid}"
        mock_redis.hset.assert_called_with(clave, "_creado", "true")
        mock_redis.expire.assert_called_with(clave, 86400)

    def test_agregar_producto_exitoso(self, adapter, mock_redis):
        """Verifica agregar producto."""
        user_uuid = uuid4()
        prod_uuid = uuid4()
        
        adapter.agregar_producto(user_uuid, prod_uuid, 2)
        
        clave = f"carrito:{user_uuid}"
        mock_redis.hincrby.assert_called_with(clave, str(prod_uuid), 2)
        mock_redis.expire.assert_called_with(clave, 86400)

    def test_agregar_producto_cantidad_invalida(self, adapter):
        """Verifica error con cantidad <= 0."""
        with pytest.raises(ValueError):
            adapter.agregar_producto(uuid4(), uuid4(), 0)

    def test_eliminar_producto_reducir_cantidad(self, adapter, mock_redis):
        """Verifica reducir cantidad sin eliminar."""
        user_uuid = uuid4()
        prod_uuid = uuid4()
        mock_redis.hincrby.return_value = 1  # Queda 1 item
        
        adapter.eliminar_producto(user_uuid, prod_uuid, 1)
        
        clave = f"carrito:{user_uuid}"
        mock_redis.hincrby.assert_called_with(clave, str(prod_uuid), -1)
        mock_redis.hdel.assert_not_called()

    def test_eliminar_producto_completo(self, adapter, mock_redis):
        """Verifica eliminar producto cuando cantidad llega a 0."""
        user_uuid = uuid4()
        prod_uuid = uuid4()
        mock_redis.hincrby.return_value = 0
        
        adapter.eliminar_producto(user_uuid, prod_uuid, 1)
        
        clave = f"carrito:{user_uuid}"
        mock_redis.hdel.assert_called_with(clave, str(prod_uuid))

    def test_eliminar_producto_cantidad_invalida(self, adapter):
        """Verifica error al eliminar cantidad <= 0."""
        with pytest.raises(ValueError):
            adapter.eliminar_producto(uuid4(), uuid4(), 0)

    def test_obtener_carrito_exitoso(self, adapter, mock_redis):
        """Verifica obtener carrito."""
        user_uuid = uuid4()
        prod_uuid = uuid4()
        mock_redis.hgetall.return_value = {
            "_creado": "true",
            str(prod_uuid): "5"
        }
        
        items = adapter.obtener_carrito(user_uuid)
        
        assert len(items) == 1
        assert items[0]["producto_id"] == prod_uuid
        assert items[0]["cantidad"] == 5

    def test_obtener_carrito_fallback(self, adapter, mock_redis):
        """Verifica fallback al obtener carrito."""
        mock_redis.hgetall.side_effect = redis.RedisError("Error")
        items = adapter.obtener_carrito(uuid4())
        assert items == []

    def test_eliminar_carrito(self, adapter, mock_redis):
        """Verifica eliminar carrito completo."""
        user_uuid = uuid4()
        adapter.eliminar_carrito(user_uuid)
        mock_redis.delete.assert_called_with(f"carrito:{user_uuid}")

    def test_obtener_cantidad_items(self, adapter, mock_redis):
        """Verifica conteo total de items."""
        mock_redis.hgetall.return_value = {
            "_creado": "true",
            "prod1": "2",
            "prod2": "3"
        }
        
        total = adapter.obtener_cantidad_items(uuid4())
        assert total == 5

    def test_obtener_cantidad_items_fallback(self, adapter, mock_redis):
        """Verifica fallback en conteo."""
        mock_redis.hgetall.side_effect = redis.RedisError("Error")
        assert adapter.obtener_cantidad_items(uuid4()) == 0

    def test_carrito_existe(self, adapter, mock_redis):
        """Verifica existencia de carrito."""
        mock_redis.exists.return_value = 1
        assert adapter.carrito_existe(uuid4()) is True

    def test_carrito_existe_fallback(self, adapter, mock_redis):
        """Verifica fallback existencia."""
        mock_redis.exists.side_effect = redis.RedisError("Error")
        assert adapter.carrito_existe(uuid4()) is False
