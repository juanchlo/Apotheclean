"""
Script de prueba para verificar la conexión con la base de datos.

Ejecutar desde la raíz del proyecto:
    python -m scripts.test_db
"""

import sys
from pathlib import Path
from decimal import Decimal
# Agregar src al path para poder importar los módulos
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from infraestructure.adapters.orm.config import engine, SessionLocal, inicializar_base_datos
from infraestructure.adapters.orm.models import UsuarioModel, ProductoModel
from infraestructure.adapters.sqlalchemy_usuario_repository import SQLAlchemyUsuarioRepository
from infraestructure.adapters.sqlalchemy_producto_repository import SQLAlchemyProductoRepository
from domain.entities import Usuario, Producto, RolUsuario


def test_conexion():
    """Prueba básica de conexión a la base de datos."""
    print("=" * 50)
    print("PRUEBA DE CONEXIÓN A BASE DE DATOS")
    print("=" * 50)

    # 1. Inicializar base de datos (crear tablas)
    print("\n1. Inicializando base de datos...")
    inicializar_base_datos(engine)
    print("   ✓ Tablas creadas exitosamente")

    # 2. Crear sesión
    session = SessionLocal()
    print("   ✓ Sesión creada")

    try:
        # 3. Probar repositorio de usuarios
        print("\n2. Probando repositorio de usuarios...")
        usuario_repo = SQLAlchemyUsuarioRepository(session)

        usuario_test = Usuario(
            username="test_user",
            password_hash=b"hash_temporal",
            email="test@farmacia.com",
            nombre="Usuario de Prueba",
            rol=RolUsuario.CLIENTE
        )

        # Verificar si ya existe
        existente = usuario_repo.obtener_por_username("test_user")
        if existente:
            print(f"   → Usuario ya existe: {existente.username}")
        else:
            usuario_repo.guardar(usuario_test)
            print(f"   ✓ Usuario creado: {usuario_test.username}")

        # Verificar que se guardó
        usuario_guardado = usuario_repo.obtener_por_username("test_user")
        if usuario_guardado:
            print(f"   ✓ Usuario recuperado: {usuario_guardado.email}")

        # 4. Probar repositorio de productos
        print("\n3. Probando repositorio de productos...")
        producto_repo = SQLAlchemyProductoRepository(session)

        producto_test = Producto(
            nombre="Acetaminofén 500mg",
            barcode="7701234567890",
            valor_unitario=Decimal("5500.00"),
            stock=100,
            descripcion="Analgésico y antipirético"
        )

        # Verificar si ya existe
        existente = producto_repo.obtener_por_barcode("7701234567890")
        if existente:
            print(f"   → Producto ya existe: {existente.nombre}")
        else:
            producto_repo.guardar(producto_test)
            print(f"   ✓ Producto creado: {producto_test.nombre}")

        # Verificar que se guardó
        producto_guardado = producto_repo.obtener_por_barcode("7701234567890")
        if producto_guardado:
            print(f"   ✓ Producto recuperado: ${producto_guardado.valor_unitario}")

        # 5. Listar todos los productos
        print("\n4. Listando productos...")
        productos = producto_repo.obtener_todos(limite=10, offset=0)
        for p in productos:
            print(f"   - {p.nombre}: ${p.valor_unitario} (Stock: {p.stock})")

        print("\n" + "=" * 50)
        print("✓ TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
        print("=" * 50)
        print(f"\nBase de datos: farmacia.db")

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    test_conexion()
