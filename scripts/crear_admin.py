"""
Script para crear usuarios administradores.

Los administradores no se pueden crear desde la API por regla de negocio,
por lo que este script permite crearlos directamente en la base de datos.

Ejecutar desde la raíz del proyecto:
    JWT_SECRET_KEY="tu_clave" uv run python -m scripts.crear_admin
"""

import sys
from pathlib import Path
from getpass import getpass

# Agregar src al path para poder importar los módulos
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from infraestructure.adapters.orm.config import engine, SessionLocal, inicializar_base_datos
from infraestructure.adapters.sqlalchemy_usuario_repository import SQLAlchemyUsuarioRepository
from infraestructure.auth.jwt_auth_adapter import JwtAuthAdapter
from application.use_cases.usuarios import RegistrarAdministrador, RegistrarUsuarioInput


def crear_administrador():
    """
    Crea un usuario administrador de forma interactiva.

    Solicita los datos por consola y registra el administrador en la base de datos.
    """
    print("=" * 50)
    print("CREAR USUARIO ADMINISTRADOR")
    print("=" * 50)

    # Solicitar datos
    print("\nIngrese los datos del administrador:\n")
    username = input("Username: ").strip()
    if not username:
        print("Error: El username es requerido")
        return

    email = input("Email: ").strip()
    if not email:
        print("Error: El email es requerido")
        return

    nombre = input("Nombre completo: ").strip()
    if not nombre:
        print("Error: El nombre es requerido")
        return

    password = getpass("Contraseña: ")
    if not password:
        print("Error: La contraseña es requerida")
        return

    password_confirm = getpass("Confirmar contraseña: ")
    if password != password_confirm:
        print("Error: Las contraseñas no coinciden")
        return

    # Inicializar base de datos
    print("\nConectando a la base de datos...")
    inicializar_base_datos(engine)
    session = SessionLocal()

    try:
        # Crear dependencias
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        auth_service = JwtAuthAdapter()

        # Crear caso de uso
        registrar_admin = RegistrarAdministrador(usuario_repo, auth_service)

        # Ejecutar registro
        datos = RegistrarUsuarioInput(
            username=username,
            password=password,
            email=email,
            nombre=nombre
        )

        registrar_admin.ejecutar(datos)
        session.commit()

        print("\n" + "=" * 50)
        print("✓ ADMINISTRADOR CREADO EXITOSAMENTE")
        print("=" * 50)
        print(f"\nUsername: {username}")
        print(f"Email: {email}")
        print(f"Nombre: {nombre}")
        print(f"Rol: admin")

    except ValueError as e:
        print(f"\n✗ Error de validación: {e}")
        session.rollback()
    except Exception as e:
        print(f"\n✗ Error inesperado: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def crear_admin_rapido(username: str, password: str, email: str, nombre: str):
    """
    Crea un administrador sin interacción (para scripts automatizados).

    Args:
        username: Nombre de usuario
        password: Contraseña
        email: Correo electrónico
        nombre: Nombre completo

    Returns:
        bool: True si se creó exitosamente

    Raises:
        ValueError: Si los datos son inválidos o el usuario ya existe
    """
    inicializar_base_datos(engine)
    session = SessionLocal()

    try:
        usuario_repo = SQLAlchemyUsuarioRepository(session)
        auth_service = JwtAuthAdapter()
        registrar_admin = RegistrarAdministrador(usuario_repo, auth_service)

        datos = RegistrarUsuarioInput(
            username=username,
            password=password,
            email=email,
            nombre=nombre
        )

        registrar_admin.ejecutar(datos)
        session.commit()
        return True

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    crear_administrador()
