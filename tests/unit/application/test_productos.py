"""
Tests unitarios para los casos de uso de productos.

Utiliza mocks para simular repositorios y almacenamiento de imágenes.
"""

import pytest
from unittest.mock import Mock
from decimal import Decimal
from uuid import uuid4, UUID

from domain.entities import Producto
from application.ports.repositories import IProductoRepository
from application.ports.image_storage import IImageStorage
from application.use_cases.productos import (
    CrearProducto,
    CrearProductoInput,
    ActualizarProducto,
    ActualizarProductoInput,
    EliminarProducto,
    ObtenerProducto,
    ListarProductos,
    ListarProductosInput
)


class TestCrearProducto:
    """Tests para el caso de uso CrearProducto."""

    def test_crear_producto_exitoso(self):
        """Verifica que se puede crear un producto correctamente."""
        # Arrange
        mock_repo = Mock(spec=IProductoRepository)
        mock_repo.obtener_por_barcode.return_value = None

        mock_storage = Mock(spec=IImageStorage)

        crear = CrearProducto(mock_repo, mock_storage)
        input_data = CrearProductoInput(
            nombre="Ibuprofeno 400mg",
            barcode="7701234567890",
            valor_unitario=Decimal("8500.00"),
            stock=50,
            descripcion="Analgésico antiinflamatorio"
        )

        # Act
        resultado = crear.ejecutar(input_data)

        # Assert
        mock_repo.guardar.assert_called_once()
        assert resultado.nombre == "Ibuprofeno 400mg"
        assert resultado.barcode == "7701234567890"
        assert resultado.valor_unitario == Decimal("8500.00")

    def test_crear_producto_falla_si_barcode_existe(self):
        """Verifica que falla si el barcode ya existe."""
        # Arrange
        mock_repo = Mock(spec=IProductoRepository)
        mock_repo.obtener_por_barcode.return_value = Mock(spec=Producto)

        mock_storage = Mock(spec=IImageStorage)

        crear = CrearProducto(mock_repo, mock_storage)
        input_data = CrearProductoInput(
            nombre="Producto Duplicado",
            barcode="7701234567890",
            valor_unitario=Decimal("5000.00"),
            stock=10
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Ya existe un producto con este código de barras"):
            crear.ejecutar(input_data)

        mock_repo.guardar.assert_not_called()

    def test_crear_producto_con_imagen(self):
        """Verifica que se puede crear un producto con imagen."""
        # Arrange
        mock_repo = Mock(spec=IProductoRepository)
        mock_repo.obtener_por_barcode.return_value = None

        mock_storage = Mock(spec=IImageStorage)

        crear = CrearProducto(mock_repo, mock_storage)
        input_data = CrearProductoInput(
            nombre="Producto con Imagen",
            barcode="123456",
            valor_unitario=Decimal("1000.00"),
            stock=10,
            imagen=b"imagen_bytes"
        )

        # Act
        resultado = crear.ejecutar(input_data)

        # Assert
        mock_storage.guardar.assert_called_once()
        assert resultado.imagen_uuid is not None


class TestActualizarProducto:
    """Tests para el caso de uso ActualizarProducto."""

    def test_actualizar_producto_exitoso(self):
        """Verifica que se puede actualizar un producto."""
        # Arrange
        producto_uuid = uuid4()
        producto_mock = Producto(
            uuid=producto_uuid,
            nombre="Producto Original",
            barcode="123",
            valor_unitario=Decimal("5000.00"),
            stock=10
        )

        mock_repo = Mock(spec=IProductoRepository)
        mock_repo.obtener_por_uuid.return_value = producto_mock

        mock_storage = Mock(spec=IImageStorage)

        actualizar = ActualizarProducto(mock_repo, mock_storage)
        input_data = ActualizarProductoInput(
            uuid=producto_uuid,
            nombre="Producto Actualizado",
            stock=20
        )

        # Act
        resultado = actualizar.ejecutar(input_data)

        # Assert
        mock_repo.guardar.assert_called_once()
        assert resultado.nombre == "Producto Actualizado"
        assert resultado.stock == 20

    def test_actualizar_producto_no_existente_lanza_error(self):
        """Verifica que falla si el producto no existe."""
        # Arrange
        mock_repo = Mock(spec=IProductoRepository)
        mock_repo.obtener_por_uuid.return_value = None

        mock_storage = Mock(spec=IImageStorage)

        actualizar = ActualizarProducto(mock_repo, mock_storage)
        input_data = ActualizarProductoInput(
            uuid=uuid4(),
            nombre="Nuevo Nombre"
        )

        # Act & Assert
        with pytest.raises(ValueError, match="producto no existe"):
            actualizar.ejecutar(input_data)

    def test_actualizar_solo_precio(self):
        """Verifica que se puede actualizar solo el precio."""
        # Arrange
        producto_uuid = uuid4()
        producto_mock = Producto(
            uuid=producto_uuid,
            nombre="Producto",
            barcode="123",
            valor_unitario=Decimal("5000.00"),
            stock=10
        )

        mock_repo = Mock(spec=IProductoRepository)
        mock_repo.obtener_por_uuid.return_value = producto_mock

        mock_storage = Mock(spec=IImageStorage)

        actualizar = ActualizarProducto(mock_repo, mock_storage)
        input_data = ActualizarProductoInput(
            uuid=producto_uuid,
            valor_unitario=Decimal("9000.00")
        )

        # Act
        resultado = actualizar.ejecutar(input_data)

        # Assert
        assert resultado.valor_unitario == Decimal("9000.00")
        assert resultado.nombre == "Producto"


class TestEliminarProducto:
    """Tests para el caso de uso EliminarProducto."""

    def test_eliminar_producto_exitoso_soft_delete(self):
        """Verifica que eliminar hace soft delete via repo."""
        # Arrange
        producto_uuid = uuid4()
        producto_mock = Producto(
            uuid=producto_uuid,
            nombre="Producto",
            barcode="123",
            valor_unitario=Decimal("5000.00"),
            stock=10,
            eliminado=False
        )

        mock_repo = Mock(spec=IProductoRepository)
        mock_repo.obtener_por_uuid.return_value = producto_mock

        mock_storage = Mock(spec=IImageStorage)

        eliminar = EliminarProducto(mock_repo, mock_storage)

        # Act
        resultado = eliminar.ejecutar(producto_uuid)

        # Assert
        assert resultado is True
        mock_repo.eliminar.assert_called_once_with(producto_uuid)

    def test_eliminar_producto_no_existente_lanza_error(self):
        """Verifica que falla si el producto no existe."""
        # Arrange
        mock_repo = Mock(spec=IProductoRepository)
        mock_repo.obtener_por_uuid.return_value = None

        mock_storage = Mock(spec=IImageStorage)

        eliminar = EliminarProducto(mock_repo, mock_storage)

        # Act & Assert
        with pytest.raises(ValueError, match="producto no existe"):
            eliminar.ejecutar(uuid4())


class TestObtenerProducto:
    """Tests para el caso de uso ObtenerProducto."""

    def test_obtener_producto_existente(self):
        """Verifica que se puede obtener un producto existente."""
        # Arrange
        producto_uuid = uuid4()
        producto_mock = Producto(
            uuid=producto_uuid,
            nombre="Ibuprofeno",
            barcode="123",
            valor_unitario=Decimal("8500.00"),
            stock=50
        )

        mock_repo = Mock(spec=IProductoRepository)
        mock_repo.obtener_por_uuid.return_value = producto_mock

        obtener = ObtenerProducto(mock_repo)

        # Act
        resultado = obtener.ejecutar(producto_uuid)

        # Assert
        assert resultado.uuid == str(producto_uuid)
        assert resultado.nombre == "Ibuprofeno"

    def test_obtener_producto_no_existente_lanza_error(self):
        """Verifica que falla si el producto no existe."""
        # Arrange
        mock_repo = Mock(spec=IProductoRepository)
        mock_repo.obtener_por_uuid.return_value = None

        obtener = ObtenerProducto(mock_repo)

        # Act & Assert
        with pytest.raises(ValueError, match="producto no existe"):
            obtener.ejecutar(uuid4())


class TestListarProductos:
    """Tests para el caso de uso ListarProductos."""

    def test_listar_productos_con_resultados(self):
        """Verifica que se pueden listar productos."""
        # Arrange
        productos = [
            Producto(
                nombre="Producto 1",
                barcode="001",
                valor_unitario=Decimal("1000"),
                stock=10
            ),
            Producto(
                nombre="Producto 2",
                barcode="002",
                valor_unitario=Decimal("2000"),
                stock=20
            )
        ]

        mock_repo = Mock(spec=IProductoRepository)
        mock_repo.obtener_todos.return_value = productos

        listar = ListarProductos(mock_repo)

        # Act
        resultado = listar.ejecutar(ListarProductosInput(limite=10, offset=0))

        # Assert
        assert len(resultado) == 2

    def test_listar_productos_vacio(self):
        """Verifica el comportamiento cuando no hay productos."""
        # Arrange
        mock_repo = Mock(spec=IProductoRepository)
        mock_repo.obtener_todos.return_value = []

        listar = ListarProductos(mock_repo)

        # Act
        resultado = listar.ejecutar(ListarProductosInput(limite=10, offset=0))

        # Assert
        assert len(resultado) == 0
