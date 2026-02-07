"""
Adaptador de autenticación JWT que implementa la interfaz IAuth.

Utiliza bcrypt para el hashing seguro de contraseñas y PyJWT para
la generación y verificación de tokens de autenticación.
"""

import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional


import bcrypt
import jwt

from src.infraestructure.cache.redis_blacklist_adapter import RedisBlacklistAdapter
from src.application.ports.auth import IAuth
from src.domain.entities import Usuario


logger = logging.getLogger(__name__)


class JwtAuthAdapter(IAuth):
    """
    Adaptador de autenticación que implementa JWT y bcrypt.

    Soporta Access y Refresh Tokens, y revocación mediante Blacklist en Redis.

    Atributos:
        secret_key: Clave secreta para firmar tokens JWT.
        algorithm: Algoritmo de encriptación para JWT (default: HS256).
        access_token_expire_minutes: Tiempo de vida del Access Token.
        refresh_token_expire_days: Tiempo de vida del Refresh Token.
    """

    def __init__(
        self,
        blacklist_adapter: Optional['RedisBlacklistAdapter'] = None,
        secret_key: Optional[str] = None,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 15,
        refresh_token_expire_days: int = 7
    ):
        """
        Inicializa el adaptador de autenticación.

        Args:
            blacklist_adapter: Adaptador para verificar tokens revocados.
            secret_key: Clave secreta para JWT.
            algorithm: Algoritmo de encriptación.
            access_token_expire_minutes: TTL Access Token (minutos).
            refresh_token_expire_days: TTL Refresh Token (días).
        """
        self._blacklist = blacklist_adapter
        self._secret_key = secret_key or os.getenv("JWT_SECRET_KEY")
        if not self._secret_key:
            raise ValueError(
                "Se requiere JWT_SECRET_KEY en variables de entorno o como parámetro"
            )

        self._algorithm = algorithm
        self._access_token_expire_minutes = access_token_expire_minutes
        self._refresh_token_expire_days = refresh_token_expire_days

        logger.info(
            "JwtAuthAdapter inicializado (Alg: %s, Access: %dm, Refresh: %dd)",
            self._algorithm,
            self._access_token_expire_minutes,
            self._refresh_token_expire_days
        )

    def hash_password(self, password: str) -> bytes:
        """Hashea una contraseña usando bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt)

    def verificar_password(self, password: str, stored_password_hash: bytes) -> bool:
        """Verifica si una contraseña coincide con su hash almacenado."""
        try:
            return bcrypt.checkpw(password.encode("utf-8"), stored_password_hash)
        except Exception as e:
            logger.error("Error al verificar contraseña: %s", str(e))
            return False

    def generar_tokens(self, usuario: Usuario) -> dict:
        """
        Genera par de tokens (Access + Refresh) para un usuario.

        Returns:
            dict: { "access_token": "...", "refresh_token": "..." }
        """
        ahora = datetime.now(timezone.utc)
        jti = str(uuid.uuid4())  # ID único para el refresh token

        # 1. Generar Access Token
        exp_access = ahora + timedelta(minutes=self._access_token_expire_minutes)
        payload_access = {
            "sub": str(usuario.uuid),
            "rol": usuario.rol.value,
            "type": "access",
            "exp": exp_access,
            "iat": ahora
        }
        access_token = jwt.encode(payload_access, self._secret_key, algorithm=self._algorithm)

        # 2. Generar Refresh Token
        exp_refresh = ahora + timedelta(days=self._refresh_token_expire_days)
        payload_refresh = {
            "sub": str(usuario.uuid),
            "rol": usuario.rol.value,  # Incluir rol para renovación
            "type": "refresh",
            "jti": jti,
            "exp": exp_refresh,
            "iat": ahora
        }
        refresh_token = jwt.encode(payload_refresh, self._secret_key, algorithm=self._algorithm)

        logger.info("Tokens generados para usuario %s", usuario.username)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token
        }

    def verificar_token(self, token: str, tipo_esperado: str = "access") -> Optional[dict]:
        """
        Verifica un token JWT y su tipo.

        Args:
            token: JWT a verificar.
            tipo_esperado: 'access' o 'refresh'.

        Returns:
            Payload decodificado o None si es inválido/revocado.
        """
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])

            # Validar tipo de token
            if payload.get("type") != tipo_esperado:
                logger.warning("Tipo de token inválido. Esperado: %s, Recibido: %s",
                               tipo_esperado, payload.get("type"))
                return None

            # Verificar Blacklist (solo si se inyectó el adaptador y aplica)
            # Generalmente verificamos blacklist para Refresh Tokens
            jti = payload.get("jti")
            if jti and self._blacklist:
                if self._blacklist.esta_en_blacklist(jti):
                    logger.warning("Token revocado (JTI: %s) intentó ser usado", jti)
                    return None

            return payload

        except jwt.ExpiredSignatureError:
            logger.debug("Token expirado")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning("Token inválido: %s", str(e))
            return None
        except Exception as e:
            logger.error("Error verificando token: %s", str(e))
            return None

    def renovar_access_token(self, refresh_token: str) -> Optional[dict]:
        """
        Genera un nuevo Access Token usando un Refresh Token válido.
        
        NOTA: Este método NO implementa rotación de refresh token.
        Para rotación completa, usar renovar_tokens_con_rotacion().
        
        Returns:
            dict: { "access_token": "..." } o None si falla.
        """
        payload = self.verificar_token(refresh_token, tipo_esperado="refresh")
        
        if not payload:
            return None

        # Generar nuevo access token
        # NOTA: Idealmente se debería consultar la DB para obtener el rol actualizado
        # del usuario, pero para mantener el adaptador sin dependencias, 
        # generamos el token con la info disponible
        ahora = datetime.now(timezone.utc)
        exp_access = ahora + timedelta(minutes=self._access_token_expire_minutes)
        
        payload_access = {
            "sub": payload["sub"],
            "rol": payload.get("rol", "cliente"),  # Usamos rol del refresh o default
            "type": "access",
            "exp": exp_access,
            "iat": ahora
        }
        
        access_token = jwt.encode(payload_access, self._secret_key, algorithm=self._algorithm)
        
        return {
            "access_token": access_token
        }

    def renovar_tokens_con_rotacion(self, refresh_token: str) -> Optional[dict]:
        """
        Renueva AMBOS tokens (access y refresh) implementando Refresh Token Rotation.
        
        Ventajas de la rotación:
        - Mayor seguridad: cada refresh invalida el anterior
        - Detecta uso de tokens robados (si se usa el viejo, se detecta)
        - Limita ventana de exposición si un token es comprometido
        
        Returns:
            dict: {
                "access_token": "...",
                "refresh_token": "...",
                "old_jti": "..."  # Para revocar el anterior
            } o None si falla.
        """
        payload = self.verificar_token(refresh_token, tipo_esperado="refresh")
        
        if not payload:
            return None

        old_jti = payload.get("jti")
        ahora = datetime.now(timezone.utc)
        
        # 1. Generar NUEVO Access Token
        exp_access = ahora + timedelta(minutes=self._access_token_expire_minutes)
        payload_access = {
            "sub": payload["sub"],
            "rol": payload.get("rol", "cliente"),
            "type": "access",
            "exp": exp_access,
            "iat": ahora
        }
        access_token = jwt.encode(payload_access, self._secret_key, algorithm=self._algorithm)

        # 2. Generar NUEVO Refresh Token (con nuevo JTI)
        new_jti = str(uuid.uuid4())
        exp_refresh = ahora + timedelta(days=self._refresh_token_expire_days)
        payload_refresh = {
            "sub": payload["sub"],
            "rol": payload.get("rol", "cliente"),
            "type": "refresh",
            "jti": new_jti,
            "exp": exp_refresh,
            "iat": ahora
        }
        new_refresh_token = jwt.encode(payload_refresh, self._secret_key, algorithm=self._algorithm)

        logger.info(f"Token rotation: usuario {payload['sub']}, old_jti={old_jti}, new_jti={new_jti}")

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "old_jti": old_jti  # Para que el caller lo revoque
        }

    def revocar_token(self, token: str) -> bool:
        """
        Revoca un token agregando su JTI a la blacklist.
        
        Args:
            token: Refresh token a revocar.
        """
        if not self._blacklist:
            logger.warning("Intento de revocar token sin BlacklistAdapter configurado")
            return False

        try:
            # Decodificar sin verificar expiración (queremos revocar incluso si expiró hace poco)
            # Pero SÍ verificamos firma para no llenar redis de basura
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm], 
                                 options={"verify_exp": False})
            
            jti = payload.get("jti")
            exp = payload.get("exp")
            
            if not jti or not exp:
                logger.warning("Token sin JTI o EXP no se puede revocar")
                return False

            ahora_ts = datetime.now(timezone.utc).timestamp()
            ttl = int(exp - ahora_ts)
            
            if ttl > 0:
                self._blacklist.agregar(jti, ttl)
                return True
            else:
                logger.info("Token ya expirado, no es necesario revocar")
                return True

        except Exception as e:
            logger.error("Error al revocar token: %s", str(e))
            return False

    def generar_token(self, usuario: Usuario) -> str:
        """Mantiene compatibilidad con interfaz antigua (DEPRECATED)."""
        logger.warning("Uso de método depreciado: generar_token")
        return self.generar_tokens(usuario)["access_token"]