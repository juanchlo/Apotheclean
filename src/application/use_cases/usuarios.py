"""Caso de uso de usuarios"""

from uuid import UUID
from typing import Optional
from dataclasses import dataclass
from src.domain.entities import Usuario, RolUsuario
from src.application.ports.repositories import IUsuarioRepository
from src.application.ports.auth import IAuth


@dataclass
class RegistrarUsuarioInput:
    """Entrada para el caso de uso de registro de usuario"""
    username: str
    password: str
    email: str
    nombre: str


class RegistrarUsuario:
    """Caso de uso para registrar un usuario"""

    def __init__(self, usuario_repo: IUsuarioRepository, auth_service: IAuth):
        self.usuario_repo = usuario_repo
        self.auth_service = auth_service

    def ejecutar(self, usuario: RegistrarUsuarioInput) -> bool:
        """Registra un usuario, validando unicidad del correo y username"""
        if self.usuario_repo.obtener_por_username(usuario.username) is not None:
            raise ValueError("El nombre de usuario ya está registrado")
        if self.usuario_repo.obtener_por_email(usuario.email) is not None:
            raise ValueError("Este correo electrónico ya está registrado")

        password_hash = self.auth_service.hash_password(usuario.password)

        usuario = Usuario(
            username=usuario.username,
            password_hash=password_hash,
            email=usuario.email,
            nombre=usuario.nombre,
            rol=RolUsuario.CLIENTE
        )

        saved_status = self.usuario_repo.guardar(usuario)
        if not saved_status:
            raise ValueError("Error al guardar el usuario")

        return True


class RegistrarAdministrador:
    """
    Caso de uso para registrar un usuario administrador.
    """

    def __init__(self, usuario_repo: IUsuarioRepository, auth_service: IAuth):
        self.usuario_repo = usuario_repo
        self.auth_service = auth_service

    def ejecutar(self, datos: RegistrarUsuarioInput) -> bool:
        """
        Registra un administrador validando unicidad del correo y username.

        Args:
            datos: Datos del administrador a registrar

        Returns:
            True si el administrador se registró correctamente

        Raises:
            ValueError: Si el username o email ya están registrados
        """
        if self.usuario_repo.obtener_por_username(datos.username) is not None:
            raise ValueError("El nombre de usuario ya está registrado")
        if self.usuario_repo.obtener_por_email(datos.email) is not None:
            raise ValueError("Este correo electrónico ya está registrado")

        password_hash = self.auth_service.hash_password(datos.password)

        administrador = Usuario(
            username=datos.username,
            password_hash=password_hash,
            email=datos.email,
            nombre=datos.nombre,
            rol=RolUsuario.ADMIN
        )

        saved_status = self.usuario_repo.guardar(administrador)
        if not saved_status:
            raise ValueError("Error al guardar el administrador")

        return True


@dataclass
class LoginUsuarioInput:
    """Entrada para el caso de uso de inicio de sesión."""
    password: str
    username: Optional[str] = None
    email: Optional[str] = None


class LoginUsuario:
    """Caso de uso para iniciar sesión de un usuario."""

    def __init__(self, usuario_repo: IUsuarioRepository, auth_service: IAuth):
        self.usuario_repo = usuario_repo
        self.auth_service = auth_service

    def ejecutar(self, datos: LoginUsuarioInput) -> str:
        """
        Autentica un usuario y retorna un token JWT.

        Args:
            datos: Credenciales del usuario (password + username o email)

        Returns:
            Token JWT para autenticación en requests posteriores

        Raises:
            ValueError: Si las credenciales son inválidas o el usuario está deshabilitado
        """
        if datos.username is None and datos.email is None:
            raise ValueError("Debe proporcionar un nombre de usuario o correo electrónico")

        usuario_db = self.usuario_repo.obtener_por_username_o_email(
            datos.username,
            datos.email
        )

        if usuario_db is None:
            raise ValueError("El nombre de usuario o correo electrónico no está registrado")

        if not usuario_db.activo:
            raise ValueError("El usuario se encuentra deshabilitado")

        if not self.auth_service.verificar_password(datos.password, usuario_db.password_hash):
            raise ValueError("Credenciales incorrectas")

        return self.auth_service.generar_token(usuario_db)


class DeshabilitarUsuario:
    """Caso de uso para deshabilitar un usuario."""

    def __init__(self, usuario_repo: IUsuarioRepository):
        self.usuario_repo = usuario_repo

    def ejecutar(self, usuario_id: UUID) -> bool:
        """
        Deshabilita un usuario por su ID.

        Args:
            usuario_id: Identificador único del usuario

        Returns:
            True si el usuario se deshabilitó correctamente, False en caso contrario
        """

        usuario = self.usuario_repo.obtener_por_uuid(usuario_id)
        if usuario is None:
            raise ValueError("El usuario no existe")

        if not usuario.activo:
            raise ValueError("El usuario ya está deshabilitado")

        return self.usuario_repo.deshabilitar(usuario_id)
