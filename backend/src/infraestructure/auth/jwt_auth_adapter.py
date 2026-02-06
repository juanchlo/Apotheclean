"""
Adaptador de autenticación JWT que implementa la interfaz IAuth.

Utiliza bcrypt para el hashing seguro de contraseñas y PyJWT para
la generación y verificación de tokens de autenticación.
"""

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import bcrypt
import jwt

from src.application.ports.auth import IAuth
from src.domain.entities import Usuario, RolUsuario


logger = logging.getLogger(__name__)


class JwtAuthAdapter(IAuth):
    """
    Adaptador de autenticación que implementa JWT y bcrypt.

    Atributos:
        secret_key: Clave secreta para firmar tokens JWT.
        algorithm: Algoritmo de encriptación para JWT (default: HS256).
        token_expiration_hours: Horas de validez del token (default: 24).
    """

    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: str = "HS256",
        token_expiration_hours: int = 24
    ):
        """
        Inicializa el adaptador de autenticación.

        Args:
            secret_key: Clave secreta para JWT. Si no se provee, se obtiene
                       de la variable de entorno JWT_SECRET_KEY.
            algorithm: Algoritmo de encriptación para JWT.
            token_expiration_hours: Tiempo de expiración del token en horas.

        Raises:
            ValueError: Si no se provee secret_key ni existe en variables de entorno.
        """
        self._secret_key = secret_key or os.getenv("JWT_SECRET_KEY")
        if not self._secret_key:
            raise ValueError(
                "Se requiere JWT_SECRET_KEY en variables de entorno o como parámetro"
            )

        self._algorithm = algorithm
        self._token_expiration_hours = token_expiration_hours

        logger.info(
            "JwtAuthAdapter inicializado con algoritmo %s y expiración de %d horas",
            self._algorithm,
            self._token_expiration_hours
        )

    def hash_password(self, password: str) -> bytes:
        """
        Hashea una contraseña usando bcrypt.

        Args:
            password: La contraseña en texto plano.

        Returns:
            bytes: El hash de la contraseña.
        """
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode("utf-8"), salt)

        logger.debug("Contraseña hasheada exitosamente")
        return password_hash

    def verificar_password(self, password: str, stored_password_hash: bytes) -> bool:
        """
        Verifica si una contraseña coincide con su hash almacenado.

        Args:
            password: La contraseña en texto plano a verificar.
            stored_password_hash: El hash de la contraseña almacenada.

        Returns:
            bool: True si la contraseña es correcta, False en caso contrario.
        """
        try:
            es_valida = bcrypt.checkpw(password.encode("utf-8"), stored_password_hash)

            if es_valida:
                logger.debug("Verificación de contraseña exitosa")
            else:
                logger.warning("Verificación de contraseña fallida")

            return es_valida
        except Exception as e:
            logger.error("Error al verificar contraseña: %s", str(e))
            return False

    def generar_token(self, usuario: Usuario) -> str:
        """
        Genera un token JWT para un usuario autenticado.

        Args:
            usuario: La entidad Usuario para la cual se genera el token.

        Returns:
            str: El token JWT codificado.
        """
        ahora = datetime.now(timezone.utc)
        expiracion = ahora + timedelta(hours=self._token_expiration_hours)

        payload = {
            "sub": str(usuario.uuid),
            "username": usuario.username,
            "email": usuario.email,
            "nombre": usuario.nombre,
            "rol": usuario.rol.value,
            "iat": ahora,
            "exp": expiracion
        }

        token = jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

        logger.info(
            "Token generado para usuario %s con expiración %s",
            usuario.username,
            expiracion.isoformat()
        )

        return token

    def verificar_token(self, token: str) -> Optional[dict]:
        """
        Verifica un token JWT y extrae la información del usuario.

        Args:
            token: El token JWT a verificar.

        Returns:
            Optional[dict]: Diccionario con los datos del usuario si el token es
                           válido, None si es inválido o ha expirado.
                           Contiene: uuid, username, email, nombre, rol.
        """
        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm]
            )

            datos_usuario = {
                "uuid": UUID(payload["sub"]),
                "username": payload["username"],
                "email": payload["email"],
                "nombre": payload["nombre"],
                "rol": RolUsuario(payload["rol"])
            }

            logger.info("Token verificado exitosamente para usuario %s", payload["username"])

            return datos_usuario

        except jwt.ExpiredSignatureError:
            logger.warning("Intento de uso de token expirado")
            return None

        except jwt.InvalidTokenError as e:
            logger.warning("Token inválido: %s", str(e))
            return None

        except Exception as e:
            logger.error("Error inesperado al verificar token: %s", str(e))
            return None

    def decodificar_token_sin_verificar(self, token: str) -> Optional[dict]:
        """
        Decodifica un token sin verificar su firma (útil para debugging).

        Args:
            token: El token JWT a decodificar.

        Returns:
            Optional[dict]: Los datos del payload si la decodificación es exitosa,
                           None en caso de error.

        Note:
            Este método NO verifica la firma ni la expiración del token.
            Usar solo para propósitos de debugging o logging.
        """
        try:
            payload = jwt.decode(
                token,
                options={"verify_signature": False}
            )
            return payload
        except Exception as e:
            logger.error("Error al decodificar token: %s", str(e))
            return None
