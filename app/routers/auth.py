from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models import Usuario
from app.services.auth_service import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Auth"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/login", response_class=HTMLResponse)
async def get_login_page(request: Request):
    """Muestra el formulario de inicio de sesión."""
    # Si ya está logueado, redirigir
    if request.session.get("user_id"):
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(
        request=request, name="login.html", context={"title": "Iniciar Sesión"}
    )

@router.post("/login")
async def procesar_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Valida credenciales y crea sesión."""
    usuario = db.query(Usuario).filter(Usuario.username == username).first()
    
    if not usuario or not verify_password(password, usuario.password_hash):
        return templates.TemplateResponse(
            request=request, name="login.html", 
            context={"title": "Iniciar Sesión", "error": "Usuario o contraseña incorrectos."}
        )
    
    # Crear sesión
    request.session["user_id"] = usuario.id
    request.session["username"] = usuario.username
    
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

@router.get("/register", response_class=HTMLResponse)
async def get_register_page(request: Request):
    """Muestra el formulario de registro."""
    if request.session.get("user_id"):
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(
        request=request, name="register.html", context={"title": "Crear Cuenta"}
    )

@router.post("/register")
async def procesar_registro(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Crea un nuevo usuario."""
    if password != confirm_password:
        return templates.TemplateResponse(
            request=request, name="register.html", 
            context={"title": "Crear Cuenta", "error": "Las contraseñas no coinciden."}
        )
    
    if len(password) < 6:
        return templates.TemplateResponse(
            request=request, name="register.html", 
            context={"title": "Crear Cuenta", "error": "La contraseña debe tener al menos 6 caracteres."}
        )

    nuevo_usuario = Usuario(
        username=username,
        password_hash=hash_password(password)
    )
    
    try:
        db.add(nuevo_usuario)
        db.commit()
        db.refresh(nuevo_usuario)
        # Loguear automáticamente
        request.session["user_id"] = nuevo_usuario.id
        request.session["username"] = nuevo_usuario.username
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    except IntegrityError:
        db.rollback()
        return templates.TemplateResponse(
            request=request, name="register.html", 
            context={"title": "Crear Cuenta", "error": "El nombre de usuario ya está en uso."}
        )
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(
            request=request, name="register.html", 
            context={"title": "Crear Cuenta", "error": f"Error: {str(e)}"}
        )

@router.get("/logout")
async def logout(request: Request):
    """Cierra la sesión."""
    request.session.clear()
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
