"""Interfaz que rige los procesos de autenticación"""

from abc import ABC, abstractmethod
from typing import Optional
from src.domain.entities import Usuario


class IAuth(ABC):
    """Interfaz para el autenticador de usuarios."""

    @abstractmethod
    def hash_password(self, password: str) -> bytes:
        """Hashea una contraseña."""

    @abstractmethod
    def verificar_password(self, password: str, stored_password_hash: bytes) -> bool:
        """Verifica si una contraseña es correcta."""

    @abstractmethod
    def generar_tokens(self, usuario: Usuario) -> dict:
        """Genera par de tokens (Access + Refresh) para un usuario."""

    @abstractmethod
    def verificar_token(self, token: str, tipo_esperado: str = "access") -> Optional[dict]:
        """
        Verifica un token y devuelve su payload.
        
        Args:
            token: El JWT a verificar.
            tipo_esperado: 'access' o 'refresh'.
            
        Returns:
            Payload del token si es válido, None si no.
        """

    @abstractmethod
    def renovar_access_token(self, refresh_token: str) -> Optional[dict]:
        """Genera un nuevo access token a partir de un refresh token válido."""
    
    @abstractmethod
    def renovar_tokens_con_rotacion(self, refresh_token: str) -> Optional[dict]:
        """
        Renueva ambos tokens (access y refresh) implementando Token Rotation.
        
        Returns:
            dict: {
                "access_token": "...",
                "refresh_token": "...",
                "old_jti": "..."
            } o None si falla.
        """
        
    @abstractmethod
    def revocar_token(self, token: str) -> bool:
        """Invalida un token (usualmente refresh token)."""