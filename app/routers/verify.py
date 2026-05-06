from fastapi import APIRouter, Request, UploadFile, File, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Documento, Usuario
from app.services.verification_service import verificar_integridad
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/verify", tags=["Verify"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def get_verify_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Muestra el formulario para subir un documento sospechoso y seleccionar el original."""
    documentos_usuario = db.query(Documento).filter(Documento.usuario_id == current_user.id).order_by(Documento.fecha_registro.desc()).all()
    
    return templates.TemplateResponse(
        request=request, name="verify.html", 
        context={
            "title": "Verificar Documento", 
            "username": current_user.username,
            "documentos": documentos_usuario
        }
    )

@router.post("/", response_class=HTMLResponse)
async def verificar_documento(
    request: Request,
    file: UploadFile = File(...),
    hash_original: str = Form(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Calcula el hash del archivo y verifica su integridad contra el documento seleccionado."""
    documentos_usuario = db.query(Documento).filter(Documento.usuario_id == current_user.id).order_by(Documento.fecha_registro.desc()).all()
    context_base = {
        "title": "Resultado de Verificación", 
        "username": current_user.username,
        "documentos": documentos_usuario
    }

    if not file.filename:
        context_base.update({"error": "No se proporcionó ningún archivo."})
        return templates.TemplateResponse(request=request, name="verify.html", context=context_base)
        
    if not hash_original:
        context_base.update({"error": "Debe seleccionar un documento original de su historial."})
        return templates.TemplateResponse(request=request, name="verify.html", context=context_base)

    contenido = await file.read()
    
    # Buscar el documento original seleccionado (asegurando que pertenezca al usuario)
    documento = db.query(Documento).filter(
        Documento.hash_sha256 == hash_original,
        Documento.usuario_id == current_user.id
    ).first()
    
    if not documento:
        context_base.update({"error": "El documento original seleccionado no existe o no tienes permiso para acceder a él."})
        return templates.TemplateResponse(request=request, name="verify.html", context=context_base)
    
    # Realizar comparación 1 a 1
    resultado = verificar_integridad(contenido, documento.hash_sha256)
    
    if resultado["integro"]:
        estado = "integro"
    else:
        estado = "corrupto"
        
    context_base.update({
        "estado": estado,
        "documento": documento,
        "resultado": resultado
    })
    
    return templates.TemplateResponse(request=request, name="verify_result.html", context=context_base)
