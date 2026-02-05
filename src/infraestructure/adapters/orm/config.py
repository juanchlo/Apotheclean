"""Configuración de SQLAlchemy para la base de datos."""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Base para todos los modelos
Base = declarative_base()

# Ruta de la base de datos SQLite
DATABASE_PATH = os.environ.get("DATABASE_PATH", "farmacia.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"


def crear_engine(echo: bool = False):
    """
    Crea el engine de SQLAlchemy.

    Args:
        echo: Si True, imprime las consultas SQL generadas (útil para debug)

    Returns:
        Engine de SQLAlchemy configurado
    """
    return create_engine(
        DATABASE_URL,
        echo=echo,
        connect_args={"check_same_thread": False}  # Necesario para SQLite con Flask
    )


def crear_session_factory(engine):
    """
    Crea la fábrica de sesiones.

    Args:
        engine: Engine de SQLAlchemy

    Returns:
        Clase Session configurada
    """
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def inicializar_base_datos(engine):
    """
    Crea todas las tablas definidas en los modelos.

    Args:
        engine: Engine de SQLAlchemy
    """
    Base.metadata.create_all(bind=engine)


# Instancias globales para uso en la aplicación
engine = crear_engine(echo=False)
SessionLocal = crear_session_factory(engine)


def obtener_session():
    """
    Generador de sesiones para uso con Flask o dependencias.

    Yields:
        Sesión de SQLAlchemy
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
