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
    def generar_token(self, usuario: Usuario) -> str:
        """Genera un token para un usuario."""

    @abstractmethod
    def verificar_token(self, token: str) -> Optional[Usuario]:
        """Verifica un token y devuelve el usuario correspondiente."""
