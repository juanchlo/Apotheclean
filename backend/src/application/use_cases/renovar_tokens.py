"""Caso de uso para renovar tokens con rotación"""

from dataclasses import dataclass
from uuid import UUID
from src.application.ports.repositories import IUsuarioRepository
from src.application.ports.auth import IAuth


@dataclass
class RenovarTokensInput:
    """Entrada para el caso de uso de renovación de tokens."""
    refresh_token: str


class RenovarTokensConRotacion:
    """
    Caso de uso para renovar tokens implementando Refresh Token Rotation.
    
    Implementa las mejores prácticas de seguridad:
    1. Verifica el refresh token
    2. Genera nuevo par de tokens (access + refresh)
    3. Revoca el refresh token antiguo
    4. Consulta DB para obtener info actualizada del usuario
    """

    def __init__(self, usuario_repo: IUsuarioRepository, auth_service: IAuth):
        self.usuario_repo = usuario_repo
        self.auth_service = auth_service

    def ejecutar(self, datos: RenovarTokensInput) -> dict:
        """
        Renueva tokens con rotación completa.

        Args:
            datos: Contiene el refresh token actual

        Returns:
            dict: {
                "access_token": "...",
                "refresh_token": "..."
            }

        Raises:
            ValueError: Si el token es inválido, revocado, o el usuario no existe/está deshabilitado
        """
        # 1. Renovar tokens (esto verifica el refresh token)
        nuevos_tokens = self.auth_service.renovar_tokens_con_rotacion(datos.refresh_token)
        
        if nuevos_tokens is None:
            raise ValueError("Token de actualización inválido o revocado")

        # 2. Verificar que el usuario aún existe y está activo
        # (consultamos DB para seguridad adicional)
        access_payload = self.auth_service.verificar_token(
            nuevos_tokens["access_token"], 
            tipo_esperado="access"
        )
        
        if not access_payload:
            raise ValueError("Error al generar tokens")
        
        # Convertir string UUID a objeto UUID
        usuario_uuid = UUID(access_payload["sub"])
        usuario = self.usuario_repo.obtener_por_uuid(usuario_uuid)
        
        if usuario is None:
            raise ValueError("Usuario no encontrado")
        
        if not usuario.activo:
            # Revocar el nuevo refresh token si el usuario fue deshabilitado
            self.auth_service.revocar_token(nuevos_tokens["refresh_token"])
            raise ValueError("Usuario deshabilitado")

        # 3. Revocar el refresh token antiguo
        old_jti = nuevos_tokens.get("old_jti")
        if old_jti:
            # Calcular TTL del token viejo para la blacklist
            refresh_payload = self.auth_service.verificar_token(
                datos.refresh_token,
                tipo_esperado="refresh"
            )
            if refresh_payload:
                exp_timestamp = refresh_payload.get("exp", 0)
                from datetime import datetime, timezone
                ahora_ts = datetime.now(timezone.utc).timestamp()
                ttl = int(exp_timestamp - ahora_ts)
                
                if ttl > 0:
                    # Construir el token viejo para revocarlo
                    # (necesitamos el token completo, no solo el JTI)
                    self.auth_service.revocar_token(datos.refresh_token)

        # 4. Retornar solo los tokens nuevos (sin old_jti)
        return {
            "access_token": nuevos_tokens["access_token"],
            "refresh_token": nuevos_tokens["refresh_token"]
        }


class RenovarAccessToken:
    """
    Caso de uso para renovar SOLO el access token (sin rotación de refresh).
    
    Menos seguro que RenovarTokensConRotacion, pero útil para compatibilidad.
    """

    def __init__(self, usuario_repo: IUsuarioRepository, auth_service: IAuth):
        self.usuario_repo = usuario_repo
        self.auth_service = auth_service

    def ejecutar(self, datos: RenovarTokensInput) -> dict:
        """
        Renueva solo el access token.

        Args:
            datos: Contiene el refresh token actual

        Returns:
            dict: { "access_token": "..." }

        Raises:
            ValueError: Si el token es inválido, revocado, o el usuario no existe/está deshabilitado
        """
        nuevo_access = self.auth_service.renovar_access_token(datos.refresh_token)
        
        if nuevo_access is None:
            raise ValueError("Token de actualización inválido o revocado")

        # Verificar que el usuario aún existe y está activo
        payload = self.auth_service.verificar_token(
            nuevo_access["access_token"], 
            tipo_esperado="access"
        )
        
        if not payload:
            raise ValueError("Error al generar token")
        
        usuario_uuid = UUID(payload["sub"])
        usuario = self.usuario_repo.obtener_por_uuid(usuario_uuid)
        
        if usuario is None:
            raise ValueError("Usuario no encontrado")
        
        if not usuario.activo:
            raise ValueError("Usuario deshabilitado")

        return nuevo_access