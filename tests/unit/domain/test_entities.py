"""
Tests unitarios para las entidades de dominio.

Verifica el comportamiento de Producto, Usuario, Venta y DetalleVenta.
"""

import pytest
from decimal import Decimal
from uuid import uuid4

from domain.entities import (
    Producto,
    Usuario,
    Venta,
    DetalleVenta,
    RolUsuario,
    ModalidadVenta,
    EstadoVenta
)


class TestProducto:
    """Tests para la entidad Producto."""

    def test_crear_producto_con_valores_validos(self):
        """Verifica que se puede crear un producto con valores válidos."""
        producto = Producto(
            nombre="Ibuprofeno 400mg",
            barcode="7701234567890",
            valor_unitario=Decimal("8500.00"),
            stock=50
        )

        assert producto.nombre == "Ibuprofeno 400mg"
        assert producto.barcode == "7701234567890"
        assert producto.valor_unitario == Decimal("8500.00")
        assert producto.stock == 50
        assert producto.eliminado is False
        assert producto.uuid is not None

    def test_tiene_stock_retorna_true_cuando_hay_suficiente(self):
        """Verifica que tiene_stock retorna True si hay stock suficiente."""
        producto = Producto(
            nombre="Test",
            barcode="123",
            valor_unitario=Decimal("1000"),
            stock=10
        )

        assert producto.tiene_stock(5) is True
        assert producto.tiene_stock(10) is True

    def test_tiene_stock_retorna_false_cuando_no_hay_suficiente(self):
        """Verifica que tiene_stock retorna False si no hay stock suficiente."""
        producto = Producto(
            nombre="Test",
            barcode="123",
            valor_unitario=Decimal("1000"),
            stock=5
        )

        assert producto.tiene_stock(6) is False
        assert producto.tiene_stock(100) is False

    def test_tiene_stock_retorna_false_si_producto_eliminado(self):
        """Verifica que un producto eliminado no tiene stock disponible."""
        producto = Producto(
            nombre="Test",
            barcode="123",
            valor_unitario=Decimal("1000"),
            stock=100,
            eliminado=True
        )

        assert producto.tiene_stock(1) is False

    def test_agregar_stock_incrementa_cantidad(self):
        """Verifica que agregar_stock incrementa el stock correctamente."""
        producto = Producto(
            nombre="Test",
            barcode="123",
            valor_unitario=Decimal("1000"),
            stock=10
        )

        producto.agregar_stock(5)

        assert producto.stock == 15

    def test_reducir_stock_decrementa_cantidad(self):
        """Verifica que reducir_stock decrementa el stock correctamente."""
        producto = Producto(
            nombre="Test",
            barcode="123",
            valor_unitario=Decimal("1000"),
            stock=10
        )

        producto.reducir_stock(3)

        assert producto.stock == 7

    def test_reducir_stock_lanza_error_si_no_hay_suficiente(self):
        """Verifica que reducir_stock lanza error si no hay stock suficiente."""
        producto = Producto(
            nombre="Test",
            barcode="123",
            valor_unitario=Decimal("1000"),
            stock=5
        )

        with pytest.raises(ValueError, match="Stock insuficiente"):
            producto.reducir_stock(10)


class TestUsuario:
    """Tests para la entidad Usuario."""

    def test_crear_usuario_cliente(self):
        """Verifica que se puede crear un usuario cliente."""
        usuario = Usuario(
            username="cliente1",
            password_hash=b"hash_seguro",
            email="cliente@test.com",
            nombre="Cliente Test",
            rol=RolUsuario.CLIENTE
        )

        assert usuario.username == "cliente1"
        assert usuario.rol == RolUsuario.CLIENTE
        assert usuario.activo is True
        assert usuario.uuid is not None

    def test_crear_usuario_admin(self):
        """Verifica que se puede crear un usuario administrador."""
        usuario = Usuario(
            username="admin1",
            password_hash=b"hash_seguro",
            email="admin@test.com",
            nombre="Admin Test",
            rol=RolUsuario.ADMIN
        )

        assert usuario.rol == RolUsuario.ADMIN


class TestDetalleVenta:
    """Tests para la entidad DetalleVenta."""

    def test_calcular_subtotal(self):
        """Verifica que el subtotal se calcula correctamente."""
        detalle = DetalleVenta(
            producto_id=uuid4(),
            cantidad=3,
            precio_unitario_historico=Decimal("5000.00")
        )

        assert detalle.subtotal == Decimal("15000.00")

    def test_subtotal_con_cantidad_uno(self):
        """Verifica el subtotal cuando la cantidad es 1."""
        detalle = DetalleVenta(
            producto_id=uuid4(),
            cantidad=1,
            precio_unitario_historico=Decimal("8500.50")
        )

        assert detalle.subtotal == Decimal("8500.50")


class TestVenta:
    """Tests para la entidad Venta."""

    def test_crear_venta_pendiente_por_defecto(self):
        """Verifica que una venta nueva tiene estado pendiente."""
        venta = Venta(modalidad=ModalidadVenta.VIRTUAL)

        assert venta.estado == EstadoVenta.PENDIENTE
        assert venta.modalidad == ModalidadVenta.VIRTUAL
        assert venta.items == []
        assert venta.valor_total_cop == Decimal("0.00")

    def test_agregar_item_a_venta(self):
        """Verifica que se pueden agregar items a una venta."""
        venta = Venta(modalidad=ModalidadVenta.FISICA)
        detalle = DetalleVenta(
            producto_id=uuid4(),
            cantidad=2,
            precio_unitario_historico=Decimal("5000.00")
        )

        venta.agregar_item(detalle)

        assert len(venta.items) == 1
        assert venta.valor_total_cop == Decimal("10000.00")

    def test_agregar_mismo_producto_incrementa_cantidad(self):
        """Verifica que agregar el mismo producto incrementa la cantidad."""
        producto_id = uuid4()
        venta = Venta(modalidad=ModalidadVenta.VIRTUAL)

        detalle1 = DetalleVenta(
            producto_id=producto_id,
            cantidad=2,
            precio_unitario_historico=Decimal("5000.00")
        )
        detalle2 = DetalleVenta(
            producto_id=producto_id,
            cantidad=3,
            precio_unitario_historico=Decimal("5000.00")
        )

        venta.agregar_item(detalle1)
        venta.agregar_item(detalle2)

        assert len(venta.items) == 1
        assert venta.items[0].cantidad == 5
        assert venta.valor_total_cop == Decimal("25000.00")

    def test_calcular_total_con_multiples_items(self):
        """Verifica el cálculo del total con múltiples items."""
        venta = Venta(modalidad=ModalidadVenta.FISICA)

        venta.agregar_item(DetalleVenta(
            producto_id=uuid4(),
            cantidad=2,
            precio_unitario_historico=Decimal("5000.00")
        ))
        venta.agregar_item(DetalleVenta(
            producto_id=uuid4(),
            cantidad=1,
            precio_unitario_historico=Decimal("8500.00")
        ))

        # 2 * 5000 + 1 * 8500 = 18500
        assert venta.valor_total_cop == Decimal("18500.00")

    def test_remover_item_de_venta(self):
        """Verifica que se pueden remover items de una venta."""
        venta = Venta(modalidad=ModalidadVenta.VIRTUAL)
        detalle = DetalleVenta(
            producto_id=uuid4(),
            cantidad=2,
            precio_unitario_historico=Decimal("5000.00")
        )

        venta.agregar_item(detalle)
        assert venta.valor_total_cop == Decimal("10000.00")

        venta.remover_item(detalle)

        assert len(venta.items) == 0
        assert venta.valor_total_cop == Decimal("0.00")

    def test_obtener_item_existente(self):
        """Verifica que se puede obtener un item por producto_id."""
        producto_id = uuid4()
        venta = Venta(modalidad=ModalidadVenta.FISICA)
        detalle = DetalleVenta(
            producto_id=producto_id,
            cantidad=2,
            precio_unitario_historico=Decimal("5000.00")
        )

        venta.agregar_item(detalle)
        item = venta.obtener_item(producto_id)

        assert item is not None
        assert item.producto_id == producto_id

    def test_obtener_item_no_existente_retorna_none(self):
        """Verifica que obtener_item retorna None si no existe."""
        venta = Venta(modalidad=ModalidadVenta.VIRTUAL)

        item = venta.obtener_item(uuid4())

        assert item is None
