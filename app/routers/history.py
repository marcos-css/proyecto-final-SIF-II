from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os

from app.database import get_db
from app.models import Documento, Usuario
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/history", tags=["History"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def get_history_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Muestra la cuadrícula de historial de documentos del usuario."""
    documentos_usuario = db.query(Documento).filter(Documento.usuario_id == current_user.id).order_by(Documento.fecha_registro.desc()).all()
    
    return templates.TemplateResponse(
        request=request, name="history.html", 
        context={
            "title": "Mi Historial", 
            "username": current_user.username,
            "documentos": documentos_usuario
        }
    )

@router.post("/delete/{hash_sha256}")
async def delete_document(
    request: Request,
    hash_sha256: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Elimina un documento de la base de datos y su archivo físico."""
    documento = db.query(Documento).filter(
        Documento.hash_sha256 == hash_sha256,
        Documento.usuario_id == current_user.id
    ).first()
    
    if not documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado o sin permisos")
        
    # Eliminar archivo físico
    file_path = f"app/uploads/{documento.hash_sha256[:10]}_{documento.nombre_archivo}"
    if os.path.exists(file_path):
        os.remove(file_path)
        
    # Eliminar de la base de datos
    db.delete(documento)
    db.commit()
    
    return RedirectResponse(url="/history", status_code=status.HTTP_303_SEE_OTHER)
