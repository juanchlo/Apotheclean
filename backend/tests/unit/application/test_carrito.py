"""
Tests unitarios para los casos de uso del carrito.
"""

from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from src.application.use_cases.carrito import (
    AgregarAlCarrito,
    ItemCarritoInput,
    EliminarDelCarrito,
    ObtenerCarrito,
    VaciarCarrito,
    CheckoutCarrito,
    CheckoutInput
)
from src.domain.entities import Producto, ModalidadVenta


class TestAgregarAlCarrito:
    """Tests para el caso de uso AgregarAlCarrito."""

    def test_agregar_producto_exitoso(self):
        """Agrega un producto correctamente al carrito."""
        # Arrange
        carrito_cache = MagicMock()
        producto_repo = MagicMock()

        producto = Producto(
            nombre="Paracetamol",
            barcode="123456",
            valor_unitario=Decimal("1500"),
            stock=10
        )
        producto_repo.obtener_por_uuid.return_value = producto

        agregar = AgregarAlCarrito(carrito_cache, producto_repo)
        usuario_id = uuid4()
        producto_id = uuid4()

        # Act
        agregar.ejecutar(usuario_id, ItemCarritoInput(
            producto_id=producto_id,
            cantidad=2
        ))

        # Assert
        carrito_cache.agregar_producto.assert_called_once_with(
            usuario_id=usuario_id,
            producto_id=producto_id,
            cantidad=2
        )

    def test_agregar_producto_no_existente_falla(self):
        """Falla al agregar un producto que no existe."""
        # Arrange
        carrito_cache = MagicMock()
        producto_repo = MagicMock()
        producto_repo.obtener_por_uuid.return_value = None

        agregar = AgregarAlCarrito(carrito_cache, producto_repo)
        usuario_id = uuid4()
        producto_id = uuid4()

        # Act & Assert
        with pytest.raises(ValueError, match="no existe"):
            agregar.ejecutar(usuario_id, ItemCarritoInput(
                producto_id=producto_id,
                cantidad=1
            ))

    def test_agregar_cantidad_cero_falla(self):
        """Falla al agregar cantidad cero o negativa."""
        # Arrange
        carrito_cache = MagicMock()
        producto_repo = MagicMock()

        agregar = AgregarAlCarrito(carrito_cache, producto_repo)
        usuario_id = uuid4()
        producto_id = uuid4()

        # Act & Assert
        with pytest.raises(ValueError, match="mayor a 0"):
            agregar.ejecutar(usuario_id, ItemCarritoInput(
                producto_id=producto_id,
                cantidad=0
            ))


class TestObtenerCarrito:
    """Tests para el caso de uso ObtenerCarrito."""

    def test_obtener_carrito_con_items(self):
        """Obtiene un carrito con items y calcula totales."""
        # Arrange
        carrito_cache = MagicMock()
        producto_repo = MagicMock()

        producto_id = uuid4()
        carrito_cache.obtener_carrito.return_value = [
            {"producto_id": producto_id, "cantidad": 3}
        ]

        producto = Producto(
            nombre="Ibuprofeno",
            barcode="789012",
            valor_unitario=Decimal("2500"),
            stock=50
        )
        producto_repo.obtener_por_uuid.return_value = producto

        obtener = ObtenerCarrito(carrito_cache, producto_repo)
        usuario_id = uuid4()

        # Act
        carrito = obtener.ejecutar(usuario_id)

        # Assert
        assert len(carrito.items) == 1
        assert carrito.total_items == 3
        assert carrito.valor_total == Decimal("7500")
        assert carrito.items[0].nombre == "Ibuprofeno"

    def test_obtener_carrito_vacio(self):
        """Obtiene un carrito vacío."""
        # Arrange
        carrito_cache = MagicMock()
        producto_repo = MagicMock()
        carrito_cache.obtener_carrito.return_value = []

        obtener = ObtenerCarrito(carrito_cache, producto_repo)
        usuario_id = uuid4()

        # Act
        carrito = obtener.ejecutar(usuario_id)

        # Assert
        assert len(carrito.items) == 0
        assert carrito.total_items == 0
        assert carrito.valor_total == Decimal("0")


class TestVaciarCarrito:
    """Tests para el caso de uso VaciarCarrito."""

    def test_vaciar_carrito_exitoso(self):
        """Vacía el carrito correctamente."""
        # Arrange
        carrito_cache = MagicMock()
        vaciar = VaciarCarrito(carrito_cache)
        usuario_id = uuid4()

        # Act
        vaciar.ejecutar(usuario_id)

        # Assert
        carrito_cache.eliminar_carrito.assert_called_once_with(usuario_id)


class TestCheckoutCarrito:
    """Tests para el caso de uso CheckoutCarrito."""

    def test_checkout_carrito_vacio_falla(self):
        """Falla al hacer checkout con carrito vacío."""
        # Arrange
        carrito_cache = MagicMock()
        producto_repo = MagicMock()
        venta_repo = MagicMock()

        carrito_cache.obtener_carrito.return_value = []

        checkout = CheckoutCarrito(carrito_cache, producto_repo, venta_repo)
        usuario_id = uuid4()

        # Act & Assert
        with pytest.raises(ValueError, match="vacío"):
            checkout.ejecutar(usuario_id, CheckoutInput(
                modalidad=ModalidadVenta.VIRTUAL
            ))
