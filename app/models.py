"""
models.py — Modelos ORM para la base de datos.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class Usuario(Base):
    """
    Modelo que representa a un usuario del sistema.
    """
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    fecha_registro = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relación con documentos
    documentos = relationship("Documento", back_populates="propietario")


class Documento(Base):
    """
    Modelo que representa un documento registrado en la plataforma.
    """
    __tablename__ = "documentos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre_archivo = Column(String, nullable=False)
    tipo_archivo = Column(String, nullable=False)
    hash_sha256 = Column(String, unique=True, nullable=False)
    autor = Column(String, nullable=True)
    fecha_creacion = Column(String, nullable=True)
    tipo_marca_agua = Column(String, default="ninguna")
    texto_marca_agua = Column(String, nullable=True)
    fecha_registro = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Llave foránea hacia el usuario
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    # Relación con usuario
    propietario = relationship("Usuario", back_populates="documentos")
