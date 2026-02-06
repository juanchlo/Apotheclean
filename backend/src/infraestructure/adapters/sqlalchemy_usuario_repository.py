"""Implementación SQLAlchemy del repositorio de usuarios."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.domain.entities import Usuario, RolUsuario
from src.application.ports.repositories import IUsuarioRepository
from src.infraestructure.adapters.orm.models import UsuarioModel


class SQLAlchemyUsuarioRepository(IUsuarioRepository):
    """Implementación del repositorio de usuarios usando SQLAlchemy."""

    def __init__(self, session: Session):
        """
        Inicializa el repositorio con una sesión de SQLAlchemy.

        Args:
            session: Sesión de SQLAlchemy
        """
        self.session = session

    def guardar(self, usuario: Usuario) -> bool:
        """
        Guarda un nuevo usuario o actualiza uno existente.

        Args:
            usuario: Entidad Usuario a guardar

        Returns:
            True si se guardó correctamente
        """
        modelo_existente = self.session.query(UsuarioModel).filter_by(
            uuid=usuario.uuid.bytes
        ).first()

        if modelo_existente:
            modelo_existente.username = usuario.username
            modelo_existente.password_hash = usuario.password_hash
            modelo_existente.email = usuario.email
            modelo_existente.nombre = usuario.nombre
            modelo_existente.rol = usuario.rol.value
            modelo_existente.activo = usuario.activo
        else:
            modelo = UsuarioModel(
                uuid=usuario.uuid.bytes,
                username=usuario.username,
                password_hash=usuario.password_hash,
                email=usuario.email,
                nombre=usuario.nombre,
                rol=usuario.rol.value,
                timestamp_creacion=usuario.timestamp_creacion,
                activo=usuario.activo
            )
            self.session.add(modelo)

        self.session.commit()
        return True

    def obtener_por_uuid(self, uuid: UUID) -> Optional[Usuario]:
        """Obtiene un usuario por su UUID."""
        modelo = self.session.query(UsuarioModel).filter_by(
            uuid=uuid.bytes
        ).first()
        return self._modelo_a_entidad(modelo) if modelo else None

    def obtener_por_email(self, email: str) -> Optional[Usuario]:
        """Obtiene un usuario por su email."""
        modelo = self.session.query(UsuarioModel).filter_by(
            email=email
        ).first()
        return self._modelo_a_entidad(modelo) if modelo else None

    def obtener_por_username(self, username: str) -> Optional[Usuario]:
        """Obtiene un usuario por su username."""
        modelo = self.session.query(UsuarioModel).filter_by(
            username=username
        ).first()
        return self._modelo_a_entidad(modelo) if modelo else None

    def obtener_por_username_o_email(self, username: Optional[str],
                                     email: Optional[str]) -> Optional[Usuario]:
        """Obtiene un usuario por su username o email."""
        query = self.session.query(UsuarioModel)

        if username:
            modelo = query.filter_by(username=username).first()
            if modelo:
                return self._modelo_a_entidad(modelo)

        if email:
            modelo = query.filter_by(email=email).first()
            if modelo:
                return self._modelo_a_entidad(modelo)

        return None

    def obtener_todos(self, limite: int, offset: int) -> List[Usuario]:
        """Obtiene todos los usuarios con paginación."""
        modelos = self.session.query(UsuarioModel)\
            .limit(limite)\
            .offset(offset)\
            .all()
        return [self._modelo_a_entidad(m) for m in modelos]

    def deshabilitar(self, uuid: UUID) -> bool:
        """Deshabilita un usuario (soft delete)."""
        modelo = self.session.query(UsuarioModel).filter_by(
            uuid=uuid.bytes
        ).first()

        if modelo:
            modelo.activo = False
            self.session.commit()
            return True
        return False

    def _modelo_a_entidad(self, modelo: UsuarioModel) -> Usuario:
        """Convierte un modelo SQLAlchemy a entidad de dominio."""
        return Usuario(
            uuid=UUID(bytes=modelo.uuid),
            username=modelo.username,
            password_hash=modelo.password_hash,
            email=modelo.email,
            nombre=modelo.nombre,
            rol=RolUsuario(modelo.rol),
            timestamp_creacion=modelo.timestamp_creacion,
            activo=modelo.activo
        )
