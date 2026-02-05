"""
Tests unitarios para el adaptador de autenticación JWT.

Verifica el correcto funcionamiento del hashing de contraseñas
y la generación/verificación de tokens JWT.
"""

import pytest
import os
from uuid import uuid4

from domain.entities import Usuario, RolUsuario
from infraestructure.auth.jwt_auth_adapter import JwtAuthAdapter


class TestJwtAuthAdapter:
    """Tests para JwtAuthAdapter."""

    @pytest.fixture
    def auth_service(self):
        """Crea una instancia del servicio de autenticación para tests."""
        return JwtAuthAdapter(
            secret_key="test_secret_key_muy_segura",
            token_expiration_hours=1
        )

    def test_hash_password_genera_hash_diferente_al_original(self, auth_service):
        """Verifica que el hash es diferente a la contraseña original."""
        password = "mi_password_segura"

        hash_resultado = auth_service.hash_password(password)

        assert hash_resultado != password.encode("utf-8")
        assert isinstance(hash_resultado, bytes)

    def test_hash_password_genera_hash_unico_cada_vez(self, auth_service):
        """Verifica que cada hash es único debido a la sal."""
        password = "misma_password"

        hash1 = auth_service.hash_password(password)
        hash2 = auth_service.hash_password(password)

        # Los hashes deben ser diferentes por la sal aleatoria
        assert hash1 != hash2

    def test_verificar_password_correcta_retorna_true(self, auth_service):
        """Verifica que una contraseña correcta es validada."""
        password = "password_correcta"
        hash_guardado = auth_service.hash_password(password)

        resultado = auth_service.verificar_password(password, hash_guardado)

        assert resultado is True

    def test_verificar_password_incorrecta_retorna_false(self, auth_service):
        """Verifica que una contraseña incorrecta es rechazada."""
        password_original = "password_original"
        password_incorrecta = "password_incorrecta"
        hash_guardado = auth_service.hash_password(password_original)

        resultado = auth_service.verificar_password(password_incorrecta, hash_guardado)

        assert resultado is False

    def test_generar_token_retorna_string(self, auth_service):
        """Verifica que generar_token retorna un string JWT."""
        usuario = Usuario(
            uuid=uuid4(),
            username="testuser",
            password_hash=b"hash",
            email="test@test.com",
            nombre="Test User",
            rol=RolUsuario.CLIENTE
        )

        token = auth_service.generar_token(usuario)

        assert isinstance(token, str)
        assert len(token) > 0
        # Un JWT tiene 3 partes separadas por puntos
        assert token.count(".") == 2

    def test_verificar_token_valido_retorna_datos_usuario(self, auth_service):
        """Verifica que un token válido retorna los datos del usuario."""
        usuario = Usuario(
            uuid=uuid4(),
            username="testuser",
            password_hash=b"hash",
            email="test@test.com",
            nombre="Test User",
            rol=RolUsuario.ADMIN
        )

        token = auth_service.generar_token(usuario)
        datos = auth_service.verificar_token(token)

        assert datos is not None
        assert datos["uuid"] == usuario.uuid
        assert datos["username"] == "testuser"
        assert datos["email"] == "test@test.com"
        assert datos["rol"] == RolUsuario.ADMIN

    def test_verificar_token_invalido_retorna_none(self, auth_service):
        """Verifica que un token inválido retorna None."""
        token_invalido = "token.invalido.aqui"

        resultado = auth_service.verificar_token(token_invalido)

        assert resultado is None

    def test_verificar_token_con_secret_diferente_retorna_none(self):
        """Verifica que un token firmado con otra clave es rechazado."""
        auth1 = JwtAuthAdapter(secret_key="clave_uno")
        auth2 = JwtAuthAdapter(secret_key="clave_dos")

        usuario = Usuario(
            uuid=uuid4(),
            username="testuser",
            password_hash=b"hash",
            email="test@test.com",
            nombre="Test",
            rol=RolUsuario.CLIENTE
        )

        token = auth1.generar_token(usuario)
        resultado = auth2.verificar_token(token)

        assert resultado is None

    def test_inicializar_sin_secret_key_lanza_error(self):
        """Verifica que se requiere JWT_SECRET_KEY."""
        # Asegurar que no hay variable de entorno
        original = os.environ.get("JWT_SECRET_KEY")
        if original:
            del os.environ["JWT_SECRET_KEY"]

        try:
            with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
                JwtAuthAdapter()
        finally:
            # Restaurar variable si existía
            if original:
                os.environ["JWT_SECRET_KEY"] = original
