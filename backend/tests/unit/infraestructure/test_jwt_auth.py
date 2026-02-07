"""
Tests unitarios para el adaptador de autenticación JWT.

Verifica el correcto funcionamiento del hashing de contraseñas,
generación de pares de tokens, verificación y renovación.
"""

import pytest
from uuid import uuid4
from unittest.mock import MagicMock

from src.domain.entities import Usuario, RolUsuario
from src.infraestructure.auth.jwt_auth_adapter import JwtAuthAdapter
from src.infraestructure.cache.redis_blacklist_adapter import RedisBlacklistAdapter


class TestJwtAuthAdapter:
    """Tests para JwtAuthAdapter."""

    @pytest.fixture
    def mock_blacklist(self):
        """Mock del adaptador de blacklist."""
        return MagicMock(spec=RedisBlacklistAdapter)

    @pytest.fixture
    def auth_service(self, mock_blacklist):
        """Crea una instancia del servicio de autenticación para tests."""
        return JwtAuthAdapter(
            secret_key="test_secret_key_muy_segura",
            blacklist_adapter=mock_blacklist,
            access_token_expire_minutes=1,
            refresh_token_expire_days=1
        )

    def test_generar_tokens_retorna_par_de_tokens(self, auth_service):
        """Verifica que generar_tokens retorna access y refresh tokens."""
        usuario = Usuario(
            uuid=uuid4(),
            username="testuser",
            password_hash=b"hash",
            email="test@test.com",
            nombre="Test User",
            rol=RolUsuario.CLIENTE
        )

        tokens = auth_service.generar_tokens(usuario)

        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert isinstance(tokens["access_token"], str)
        assert isinstance(tokens["refresh_token"], str)

    def test_verificar_token_access_valido(self, auth_service):
        """Verifica que un access token válido es aceptado."""
        usuario = Usuario(
            uuid=uuid4(),
            username="testuser",
            password_hash=b"hash",
            email="test@test.com",
            nombre="Test User",
            rol=RolUsuario.ADMIN
        )

        tokens = auth_service.generar_tokens(usuario)
        payload = auth_service.verificar_token(tokens["access_token"], tipo_esperado="access")

        assert payload is not None
        assert payload["sub"] == str(usuario.uuid)
        assert payload["rol"] == "admin"
        assert payload["type"] == "access"

    def test_verificar_token_refresh_valido(self, auth_service, mock_blacklist):
        """Verifica que un refresh token válido es aceptado."""
        usuario = Usuario(
            uuid=uuid4(),
            username="testuser",
            password_hash=b"hash",
            email="test@test.com",
            nombre="Test User",
            rol=RolUsuario.CLIENTE
        )

        # Configurar mock para que retorne False (token NO revocado)
        mock_blacklist.esta_en_blacklist.return_value = False

        tokens = auth_service.generar_tokens(usuario)
        payload = auth_service.verificar_token(tokens["refresh_token"], tipo_esperado="refresh")

        assert payload is not None
        assert payload["sub"] == str(usuario.uuid)
        assert payload["type"] == "refresh"
        assert "jti" in payload

    def test_verificar_token_tipo_incorrecto_falla(self, auth_service):
        """Verifica que usar un access token como refresh token falla."""
        usuario = Usuario(
            uuid=uuid4(),
            username="testuser",
            password_hash=b"hash",
            email="test@test.com",
            nombre="Test User",
            rol=RolUsuario.CLIENTE
        )

        tokens = auth_service.generar_tokens(usuario)
        
        # Intentar verificar access token esperando refresh
        payload = auth_service.verificar_token(tokens["access_token"], tipo_esperado="refresh")
        assert payload is None

    def test_verificar_token_revocado_falla(self, auth_service, mock_blacklist):
        """Verifica que un token en la blacklist es rechazado."""
        usuario = Usuario(
            uuid=uuid4(),
            username="testuser",
            password_hash=b"hash",
            email="test@test.com",
            nombre="Test User",
            rol=RolUsuario.CLIENTE
        )

        tokens = auth_service.generar_tokens(usuario)
        refresh_token = tokens["refresh_token"]

        # Simular que el token está en blacklist
        mock_blacklist.esta_en_blacklist.return_value = True

        payload = auth_service.verificar_token(refresh_token, tipo_esperado="refresh")
        
        assert payload is None
        mock_blacklist.esta_en_blacklist.assert_called_once()

    def test_renovar_access_token_exitoso(self, auth_service, mock_blacklist):
        """Verifica que se puede renovar un access token con un refresh token válido."""
        usuario = Usuario(
            uuid=uuid4(),
            username="testuser",
            password_hash=b"hash",
            email="test@test.com",
            nombre="Test User",
            rol=RolUsuario.CLIENTE
        )

        tokens = auth_service.generar_tokens(usuario)
        refresh_token = tokens["refresh_token"]
        
        mock_blacklist.esta_en_blacklist.return_value = False

        nuevo_access = auth_service.renovar_access_token(refresh_token)

        assert nuevo_access is not None
        assert "access_token" in nuevo_access
        
        # Verificar que el nuevo token es válido
        payload = auth_service.verificar_token(nuevo_access["access_token"], tipo_esperado="access")
        assert payload is not None
        assert payload["sub"] == str(usuario.uuid)

    def test_renovar_access_token_con_token_revocado_falla(self, auth_service, mock_blacklist):
        """Verifica que no se puede renovar con un refresh token revocado."""
        usuario = Usuario(
            uuid=uuid4(),
            username="testuser",
            password_hash=b"hash",
            email="test@test.com",
            nombre="Test User",
            rol=RolUsuario.CLIENTE
        )

        tokens = auth_service.generar_tokens(usuario)
        refresh_token = tokens["refresh_token"]
        
        # Simular revocado
        mock_blacklist.esta_en_blacklist.return_value = True

        nuevo_access = auth_service.renovar_access_token(refresh_token)

        assert nuevo_access is None

    def test_revocar_token_llama_blacklist(self, auth_service, mock_blacklist):
        """Verifica que revocar_token llama al adaptador de blacklist."""
        usuario = Usuario(
            uuid=uuid4(),
            username="testuser",
            password_hash=b"hash",
            email="test@test.com",
            nombre="Test User",
            rol=RolUsuario.CLIENTE
        )

        tokens = auth_service.generar_tokens(usuario)
        refresh_token = tokens["refresh_token"]

        auth_service.revocar_token(refresh_token)

        mock_blacklist.agregar.assert_called_once()

    def test_renovar_tokens_con_rotacion_genera_nuevos_tokens(self, auth_service, mock_blacklist):
        """Verifica que la rotación genera un nuevo par de tokens."""
        usuario = Usuario(
            uuid=uuid4(),
            username="testuser",
            password_hash=b"hash",
            email="test@test.com",
            nombre="Test User",
            rol=RolUsuario.ADMIN
        )

        mock_blacklist.esta_en_blacklist.return_value = False

        tokens = auth_service.generar_tokens(usuario)
        old_refresh_token = tokens["refresh_token"]
        
        # Decodificar para obtener el JTI viejo
        old_payload = auth_service.verificar_token(old_refresh_token, tipo_esperado="refresh")
        old_jti = old_payload["jti"]

        # Renovar con rotación
        nuevos_tokens = auth_service.renovar_tokens_con_rotacion(old_refresh_token)

        assert nuevos_tokens is not None
        assert "access_token" in nuevos_tokens
        assert "refresh_token" in nuevos_tokens
        assert "old_jti" in nuevos_tokens
        assert nuevos_tokens["old_jti"] == old_jti

        # Verificar que el nuevo refresh token es diferente
        assert nuevos_tokens["refresh_token"] != old_refresh_token

        # Verificar que el nuevo refresh token tiene un JTI diferente
        new_payload = auth_service.verificar_token(nuevos_tokens["refresh_token"], tipo_esperado="refresh")
        assert new_payload is not None
        assert new_payload["jti"] != old_jti
        assert new_payload["sub"] == str(usuario.uuid)

    def test_renovar_tokens_con_rotacion_con_token_revocado_falla(self, auth_service, mock_blacklist):
        """Verifica que no se puede renovar con un refresh token revocado."""
        usuario = Usuario(
            uuid=uuid4(),
            username="testuser",
            password_hash=b"hash",
            email="test@test.com",
            nombre="Test User",
            rol=RolUsuario.CLIENTE
        )

        tokens = auth_service.generar_tokens(usuario)
        refresh_token = tokens["refresh_token"]
        
        # Simular que el token fue revocado
        mock_blacklist.esta_en_blacklist.return_value = True

        nuevos_tokens = auth_service.renovar_tokens_con_rotacion(refresh_token)

        assert nuevos_tokens is None