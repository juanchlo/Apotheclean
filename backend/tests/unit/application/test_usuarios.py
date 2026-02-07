"""
Tests unitarios para los casos de uso de usuarios.

Utiliza mocks para simular repositorios y servicios de autenticación.
"""

import pytest
from unittest.mock import Mock
from uuid import uuid4

from src.domain.entities import Usuario, RolUsuario
from src.application.ports.repositories import IUsuarioRepository
from src.application.ports.auth import IAuth
from src.application.use_cases.usuarios import (
    RegistrarUsuario,
    RegistrarAdministrador,
    RegistrarUsuarioInput,
    LoginUsuario,
    LoginUsuarioInput,
    DeshabilitarUsuario
)


class TestRegistrarUsuario:
    """Tests para el caso de uso RegistrarUsuario."""

    def test_registrar_usuario_exitoso(self):
        """Verifica que se puede registrar un usuario nuevo correctamente."""
        # Arrange
        mock_repo = Mock(spec=IUsuarioRepository)
        mock_repo.obtener_por_username.return_value = None
        mock_repo.obtener_por_email.return_value = None
        mock_repo.guardar.return_value = True

        mock_auth = Mock(spec=IAuth)
        mock_auth.hash_password.return_value = b"hash_seguro"

        registrar = RegistrarUsuario(mock_repo, mock_auth)
        input_data = RegistrarUsuarioInput(
            username="cliente1",
            password="pass123",
            email="cliente@test.com",
            nombre="Cliente Test"
        )

        # Act
        resultado = registrar.ejecutar(input_data)

        # Assert
        assert resultado is True
        mock_repo.guardar.assert_called_once()
        usuario_guardado = mock_repo.guardar.call_args[0][0]
        assert usuario_guardado.username == "cliente1"
        assert usuario_guardado.rol == RolUsuario.CLIENTE

    def test_registrar_usuario_falla_si_username_existe(self):
        """Verifica que falla si el username ya existe."""
        # Arrange
        mock_repo = Mock(spec=IUsuarioRepository)
        mock_repo.obtener_por_username.return_value = Mock(spec=Usuario)

        mock_auth = Mock(spec=IAuth)

        registrar = RegistrarUsuario(mock_repo, mock_auth)
        input_data = RegistrarUsuarioInput(
            username="existente",
            password="pass123",
            email="nuevo@test.com",
            nombre="Test"
        )

        # Act & Assert
        with pytest.raises(ValueError, match="nombre de usuario ya está registrado"):
            registrar.ejecutar(input_data)

        mock_repo.guardar.assert_not_called()

    def test_registrar_usuario_falla_si_email_existe(self):
        """Verifica que falla si el email ya existe."""
        # Arrange
        mock_repo = Mock(spec=IUsuarioRepository)
        mock_repo.obtener_por_username.return_value = None
        mock_repo.obtener_por_email.return_value = Mock(spec=Usuario)

        mock_auth = Mock(spec=IAuth)

        registrar = RegistrarUsuario(mock_repo, mock_auth)
        input_data = RegistrarUsuarioInput(
            username="nuevo",
            password="pass123",
            email="existente@test.com",
            nombre="Test"
        )

        # Act & Assert
        with pytest.raises(ValueError, match="correo electrónico ya está registrado"):
            registrar.ejecutar(input_data)


class TestRegistrarAdministrador:
    """Tests para el caso de uso RegistrarAdministrador."""

    def test_registrar_admin_con_rol_correcto(self):
        """Verifica que el administrador se registra con rol ADMIN."""
        # Arrange
        mock_repo = Mock(spec=IUsuarioRepository)
        mock_repo.obtener_por_username.return_value = None
        mock_repo.obtener_por_email.return_value = None
        mock_repo.guardar.return_value = True

        mock_auth = Mock(spec=IAuth)
        mock_auth.hash_password.return_value = b"hash_seguro"

        registrar = RegistrarAdministrador(mock_repo, mock_auth)
        input_data = RegistrarUsuarioInput(
            username="admin1",
            password="admin123",
            email="admin@test.com",
            nombre="Admin Test"
        )

        # Act
        resultado = registrar.ejecutar(input_data)

        # Assert
        assert resultado is True
        mock_repo.guardar.assert_called_once()
        usuario_guardado = mock_repo.guardar.call_args[0][0]
        assert usuario_guardado.rol == RolUsuario.ADMIN


class TestLoginUsuario:
    """Tests para el caso de uso LoginUsuario."""

    def test_login_exitoso_con_username(self):
        """Verifica que el login funciona con username."""
        # Arrange
        usuario_mock = Mock(spec=Usuario)
        usuario_mock.password_hash = b"hash_guardado"
        usuario_mock.activo = True

        mock_repo = Mock(spec=IUsuarioRepository)
        mock_repo.obtener_por_username_o_email.return_value = usuario_mock

        mock_auth = Mock(spec=IAuth)
        mock_auth.verificar_password.return_value = True
        mock_auth.generar_tokens.return_value = "token_jwt_valido"

        login = LoginUsuario(mock_repo, mock_auth)
        input_data = LoginUsuarioInput(
            username="cliente1",
            password="pass123"
        )

        # Act
        token = login.ejecutar(input_data)

        # Assert
        assert token == "token_jwt_valido"
        mock_auth.generar_tokens.assert_called_once_with(usuario_mock)

    def test_login_exitoso_con_email(self):
        """Verifica que el login funciona con email."""
        # Arrange
        usuario_mock = Mock(spec=Usuario)
        usuario_mock.password_hash = b"hash_guardado"
        usuario_mock.activo = True

        mock_repo = Mock(spec=IUsuarioRepository)
        mock_repo.obtener_por_username_o_email.return_value = usuario_mock

        mock_auth = Mock(spec=IAuth)
        mock_auth.verificar_password.return_value = True
        mock_auth.generar_tokens.return_value = "token_jwt"

        login = LoginUsuario(mock_repo, mock_auth)
        input_data = LoginUsuarioInput(
            email="cliente@test.com",
            password="pass123"
        )

        # Act
        token = login.ejecutar(input_data)

        # Assert
        assert token == "token_jwt"

    def test_login_falla_con_password_incorrecta(self):
        """Verifica que el login falla con password incorrecta."""
        # Arrange
        usuario_mock = Mock(spec=Usuario)
        usuario_mock.password_hash = b"hash_guardado"
        usuario_mock.activo = True

        mock_repo = Mock(spec=IUsuarioRepository)
        mock_repo.obtener_por_username_o_email.return_value = usuario_mock

        mock_auth = Mock(spec=IAuth)
        mock_auth.verificar_password.return_value = False

        login = LoginUsuario(mock_repo, mock_auth)
        input_data = LoginUsuarioInput(
            username="cliente1",
            password="password_incorrecta"
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Credenciales incorrectas"):
            login.ejecutar(input_data)

    def test_login_falla_si_usuario_no_existe(self):
        """Verifica que el login falla si el usuario no existe."""
        # Arrange
        mock_repo = Mock(spec=IUsuarioRepository)
        mock_repo.obtener_por_username_o_email.return_value = None

        mock_auth = Mock(spec=IAuth)

        login = LoginUsuario(mock_repo, mock_auth)
        input_data = LoginUsuarioInput(
            username="inexistente",
            password="pass123"
        )

        # Act & Assert
        with pytest.raises(ValueError, match="no está registrado"):
            login.ejecutar(input_data)

    def test_login_falla_si_usuario_inactivo(self):
        """Verifica que el login falla si el usuario está inactivo."""
        # Arrange
        usuario_mock = Mock(spec=Usuario)
        usuario_mock.password_hash = b"hash_guardado"
        usuario_mock.activo = False

        mock_repo = Mock(spec=IUsuarioRepository)
        mock_repo.obtener_por_username_o_email.return_value = usuario_mock

        mock_auth = Mock(spec=IAuth)

        login = LoginUsuario(mock_repo, mock_auth)
        input_data = LoginUsuarioInput(
            username="cliente1",
            password="pass123"
        )

        # Act & Assert
        with pytest.raises(ValueError, match="deshabilitado"):
            login.ejecutar(input_data)


class TestDeshabilitarUsuario:
    """Tests para el caso de uso DeshabilitarUsuario."""

    def test_deshabilitar_usuario_exitoso(self):
        """Verifica que se puede deshabilitar un usuario."""
        # Arrange
        usuario_uuid = uuid4()
        usuario_mock = Mock(spec=Usuario)
        usuario_mock.uuid = usuario_uuid
        usuario_mock.activo = True

        mock_repo = Mock(spec=IUsuarioRepository)
        mock_repo.obtener_por_uuid.return_value = usuario_mock
        mock_repo.deshabilitar.return_value = True

        deshabilitar = DeshabilitarUsuario(mock_repo)

        # Act
        resultado = deshabilitar.ejecutar(usuario_uuid)

        # Assert
        assert resultado is True
        mock_repo.deshabilitar.assert_called_once_with(usuario_uuid)

    def test_deshabilitar_usuario_no_existente_lanza_error(self):
        """Verifica que falla si el usuario no existe."""
        # Arrange
        mock_repo = Mock(spec=IUsuarioRepository)
        mock_repo.obtener_por_uuid.return_value = None

        deshabilitar = DeshabilitarUsuario(mock_repo)

        # Act & Assert
        with pytest.raises(ValueError, match="usuario no existe"):
            deshabilitar.ejecutar(uuid4())
