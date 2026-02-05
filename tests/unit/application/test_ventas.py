"""
Tests unitarios para los casos de uso de ventas.

Utiliza mocks para simular repositorios.
"""

import pytest
from unittest.mock import Mock
from decimal import Decimal
from uuid import uuid4

from domain.entities import Producto, Venta, DetalleVenta, ModalidadVenta, EstadoVenta
from application.ports.repositories import IVentaRepository, IProductoRepository
from application.use_cases.ventas import (
    CrearVenta,
    CrearVentaInput,
    ItemVentaInput,
    CompletarVenta,
    CancelarVenta,
    ObtenerVenta
)


class TestCrearVenta:
    """Tests para el caso de uso CrearVenta."""

    def test_crear_venta_exitosa(self):
        """Verifica que se puede crear una venta correctamente."""
        # Arrange
        producto_uuid = uuid4()
        producto_mock = Producto(
            uuid=producto_uuid,
            nombre="Ibuprofeno",
            barcode="123",
            valor_unitario=Decimal("5000.00"),
            stock=100
        )

        mock_venta_repo = Mock(spec=IVentaRepository)
        mock_producto_repo = Mock(spec=IProductoRepository)
        mock_producto_repo.obtener_por_uuid.return_value = producto_mock

        crear = CrearVenta(mock_venta_repo, mock_producto_repo)
        input_data = CrearVentaInput(
            items=[ItemVentaInput(producto_id=producto_uuid, cantidad=2)],
            modalidad=ModalidadVenta.VIRTUAL,
            comprador_id=uuid4()
        )

        # Act
        resultado = crear.ejecutar(input_data)

        # Assert
        mock_venta_repo.guardar.assert_called_once()
        assert resultado.estado == EstadoVenta.PENDIENTE.value
        assert resultado.modalidad == ModalidadVenta.VIRTUAL.value
        assert resultado.valor_total_cop == Decimal("10000.00")

    def test_crear_venta_sin_items_falla(self):
        """Verifica que falla si no hay items."""
        # Arrange
        mock_venta_repo = Mock(spec=IVentaRepository)
        mock_producto_repo = Mock(spec=IProductoRepository)

        crear = CrearVenta(mock_venta_repo, mock_producto_repo)
        input_data = CrearVentaInput(
            items=[],
            modalidad=ModalidadVenta.FISICA,
            comprador_id=uuid4()
        )

        # Act & Assert
        with pytest.raises(ValueError, match="debe tener al menos un item"):
            crear.ejecutar(input_data)

    def test_crear_venta_producto_no_existe_falla(self):
        """Verifica que falla si el producto no existe."""
        # Arrange
        mock_venta_repo = Mock(spec=IVentaRepository)
        mock_producto_repo = Mock(spec=IProductoRepository)
        mock_producto_repo.obtener_por_uuid.return_value = None

        crear = CrearVenta(mock_venta_repo, mock_producto_repo)
        input_data = CrearVentaInput(
            items=[ItemVentaInput(producto_id=uuid4(), cantidad=1)],
            modalidad=ModalidadVenta.VIRTUAL,
            comprador_id=uuid4()
        )

        # Act & Assert
        with pytest.raises(ValueError, match="no existe"):
            crear.ejecutar(input_data)

    def test_crear_venta_stock_insuficiente_falla(self):
        """Verifica que falla si no hay stock suficiente."""
        # Arrange
        producto_uuid = uuid4()
        producto_mock = Producto(
            uuid=producto_uuid,
            nombre="Producto",
            barcode="123",
            valor_unitario=Decimal("1000.00"),
            stock=5
        )

        mock_venta_repo = Mock(spec=IVentaRepository)
        mock_producto_repo = Mock(spec=IProductoRepository)
        mock_producto_repo.obtener_por_uuid.return_value = producto_mock

        crear = CrearVenta(mock_venta_repo, mock_producto_repo)
        input_data = CrearVentaInput(
            items=[ItemVentaInput(producto_id=producto_uuid, cantidad=10)],
            modalidad=ModalidadVenta.FISICA,
            comprador_id=uuid4()
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Stock insuficiente"):
            crear.ejecutar(input_data)


class TestCompletarVenta:
    """Tests para el caso de uso CompletarVenta."""

    def test_completar_venta_exitosa(self):
        """Verifica que se puede completar una venta pendiente."""
        # Arrange
        venta_uuid = uuid4()
        producto_uuid = uuid4()

        producto_mock = Producto(
            uuid=producto_uuid,
            nombre="Producto",
            barcode="123",
            valor_unitario=Decimal("5000.00"),
            stock=100
        )

        venta_mock = Venta(
            uuid=venta_uuid,
            modalidad=ModalidadVenta.VIRTUAL,
            estado=EstadoVenta.PENDIENTE
        )
        # Agregar item a la venta
        detalle = DetalleVenta(
            producto_id=producto_uuid,
            cantidad=2,
            precio_unitario_historico=Decimal("5000.00")
        )
        venta_mock.agregar_item(detalle)

        mock_venta_repo = Mock(spec=IVentaRepository)
        mock_venta_repo.obtener_por_uuid.return_value = venta_mock

        mock_producto_repo = Mock(spec=IProductoRepository)
        mock_producto_repo.obtener_por_uuid.return_value = producto_mock

        completar = CompletarVenta(mock_venta_repo, mock_producto_repo)

        # Act
        resultado = completar.ejecutar(venta_uuid)

        # Assert
        assert resultado.estado == EstadoVenta.COMPLETADA.value
        mock_venta_repo.guardar.assert_called_once()

    def test_completar_venta_no_pendiente_falla(self):
        """Verifica que falla si la venta no está pendiente."""
        # Arrange
        venta_uuid = uuid4()
        venta_mock = Venta(
            uuid=venta_uuid,
            modalidad=ModalidadVenta.VIRTUAL,
            estado=EstadoVenta.COMPLETADA
        )

        mock_venta_repo = Mock(spec=IVentaRepository)
        mock_venta_repo.obtener_por_uuid.return_value = venta_mock

        mock_producto_repo = Mock(spec=IProductoRepository)

        completar = CompletarVenta(mock_venta_repo, mock_producto_repo)

        # Act & Assert
        with pytest.raises(ValueError, match="no se puede completar"):
            completar.ejecutar(venta_uuid)


class TestCancelarVenta:
    """Tests para el caso de uso CancelarVenta."""

    def test_cancelar_venta_exitosa(self):
        """Verifica que se puede cancelar una venta pendiente."""
        # Arrange
        venta_uuid = uuid4()
        venta_mock = Venta(
            uuid=venta_uuid,
            modalidad=ModalidadVenta.VIRTUAL,
            estado=EstadoVenta.PENDIENTE
        )

        mock_repo = Mock(spec=IVentaRepository)
        mock_repo.obtener_por_uuid.return_value = venta_mock

        cancelar = CancelarVenta(mock_repo)

        # Act
        cancelar.ejecutar(venta_uuid)

        # Assert
        assert venta_mock.estado == EstadoVenta.CANCELADA
        mock_repo.guardar.assert_called_once()

    def test_cancelar_venta_no_existente_falla(self):
        """Verifica que falla si la venta no existe."""
        # Arrange
        mock_repo = Mock(spec=IVentaRepository)
        mock_repo.obtener_por_uuid.return_value = None

        cancelar = CancelarVenta(mock_repo)

        # Act & Assert
        with pytest.raises(ValueError, match="venta no existe"):
            cancelar.ejecutar(uuid4())


class TestObtenerVenta:
    """Tests para el caso de uso ObtenerVenta."""

    def test_obtener_venta_existente(self):
        """Verifica que se puede obtener una venta existente."""
        # Arrange
        venta_uuid = uuid4()
        venta_mock = Venta(
            uuid=venta_uuid,
            modalidad=ModalidadVenta.FISICA,
            estado=EstadoVenta.COMPLETADA
        )

        mock_repo = Mock(spec=IVentaRepository)
        mock_repo.obtener_por_uuid.return_value = venta_mock

        obtener = ObtenerVenta(mock_repo)

        # Act
        resultado = obtener.ejecutar(venta_uuid)

        # Assert
        assert resultado.uuid == str(venta_uuid)
        assert resultado.modalidad == ModalidadVenta.FISICA.value

    def test_obtener_venta_no_existente_falla(self):
        """Verifica que falla si la venta no existe."""
        # Arrange
        mock_repo = Mock(spec=IVentaRepository)
        mock_repo.obtener_por_uuid.return_value = None

        obtener = ObtenerVenta(mock_repo)

        # Act & Assert
        with pytest.raises(ValueError, match="venta no existe"):
            obtener.ejecutar(uuid4())
