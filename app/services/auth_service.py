"""
auth_service.py — Servicio de autenticación.
"""
from passlib.context import CryptContext
from fastapi import Request, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.models import Usuario
from app.database import get_db

# Configuración de encriptación
# Se usa pbkdf2_sha256 en lugar de bcrypt para evitar el bug de compatibilidad
# de passlib con las versiones recientes de la librería bcrypt.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def hash_password(password: str) -> str:
    """Encripta una contraseña en texto plano."""
    # bcrypt tiene un límite de 72 bytes, truncamos por seguridad
    return pwd_context.hash(password[:72])

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña coincide con el hash."""
    return pwd_context.verify(plain_password[:72], hashed_password)

def get_current_user(request: Request, db: Session = Depends(get_db)) -> Usuario:
    """
    Obtiene el usuario actual a partir de la cookie de sesión.
    Lanza HTTPException si no hay sesión activa.
    """
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="No autenticado",
            headers={"Location": "/auth/login"}
        )
    
    usuario = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not usuario:
        # Sesión inválida, limpiar
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="Usuario no encontrado",
            headers={"Location": "/auth/login"}
        )
    
    return usuario
