"""
database.py — Configuración de la base de datos SQLite con SQLAlchemy.

Este módulo define el motor de la base de datos, la sesión local
y la clase Base de la que heredarán todos los modelos ORM.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Ruta al archivo SQLite (se crea automáticamente si no existe)
DATABASE_URL = "sqlite:///./app/db.sqlite3"

# Motor de la base de datos
# check_same_thread=False es necesario para SQLite con FastAPI (async)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Sesión local para interactuar con la BD
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase base para los modelos ORM
Base = declarative_base()


def get_db():
    """
    Dependencia de FastAPI que proporciona una sesión de base de datos.
    Se asegura de cerrar la sesión después de cada request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
