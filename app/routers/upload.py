from fastapi import APIRouter, Request, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os

from app.database import get_db
from app.models import Documento, Usuario
from app.services.hash_service import calcular_hash
from app.services.metadata_service import extraer_metadatos
from app.services.watermark_service import aplicar_marca_agua
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/upload", tags=["Upload"])
templates = Jinja2Templates(directory="app/templates")

ALLOWED_EXTENSIONS = {"pdf", "docx", "jpg", "jpeg", "png", "mp3"}

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@router.get("/", response_class=HTMLResponse)
async def get_upload_page(
    request: Request,
    current_user: Usuario = Depends(get_current_user)
):
    """Muestra el formulario de carga."""
    return templates.TemplateResponse(
        request=request, name="upload.html", context={"title": "Registrar Documento", "username": current_user.username}
    )

@router.post("/", response_class=HTMLResponse)
async def procesar_documento(
    request: Request,
    file: UploadFile = File(...),
    aplicar_marca: bool = Form(False),
    tipo_marca: str = Form("ninguna"), # visible, invisible
    texto_marca: str = Form(""),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Procesa el archivo, extrae datos, aplica marca (opcional) y guarda en BD."""
    if not file.filename or not allowed_file(file.filename):
        return templates.TemplateResponse(
            request=request, name="upload.html", 
            context={"title": "Registrar Documento", "error": "Formato de archivo no soportado."}
        )

    extension = file.filename.rsplit(".", 1)[1].lower()
    contenido = await file.read()

    # 1. Extraer metadatos del archivo original
    metadatos = extraer_metadatos(contenido, extension)

    # 2. Aplicar marca de agua si es necesario
    if aplicar_marca and tipo_marca != "ninguna" and texto_marca:
        # Reasignamos el contenido con la marca de agua aplicada
        contenido = aplicar_marca_agua(contenido, extension, texto_marca, tipo_marca)
    else:
        # Si no aplica, forzamos a 'ninguna' por si el form mandó datos inconsistentes
        tipo_marca = "ninguna"
        texto_marca = None

    # 3. Calcular hash sobre el contenido FINAL (con o sin marca)
    hash_final = calcular_hash(contenido)

    # Verificar si el documento ya existe
    doc_existente = db.query(Documento).filter(Documento.hash_sha256 == hash_final).first()
    if doc_existente:
         return templates.TemplateResponse(
            request=request, name="upload.html", 
            context={"title": "Registrar Documento", "error": "Este documento (o uno idéntico) ya ha sido registrado."}
        )

    # Guardar archivo físicamente
    # Asegurar que el directorio uploads exista
    os.makedirs("app/uploads", exist_ok=True)
    file_path = f"app/uploads/{hash_final[:10]}_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(contenido)

    # 4. Registrar en la base de datos
    nuevo_doc = Documento(
        nombre_archivo=file.filename,
        tipo_archivo=extension,
        hash_sha256=hash_final,
        autor=metadatos.get("autor"),
        fecha_creacion=metadatos.get("fecha"),
        tipo_marca_agua=tipo_marca,
        texto_marca_agua=texto_marca,
        usuario_id=current_user.id
    )
    
    try:
        db.add(nuevo_doc)
        db.commit()
        db.refresh(nuevo_doc)
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(
            request=request, name="upload.html", 
            context={"title": "Registrar Documento", "error": f"Error al guardar en base de datos: {str(e)}", "username": current_user.username}
        )

    # 5. Mostrar resultado
    return templates.TemplateResponse(
        request=request, name="result.html", 
        context={"title": "Documento Registrado", "documento": nuevo_doc, "username": current_user.username}
    )
