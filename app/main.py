from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
import os

from app.database import engine, Base
from app.routers import upload, verify, auth, history

# Crear tablas en la base de datos al inicio
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Esto asegura que las tablas existan (SQLite)
    Base.metadata.create_all(bind=engine)
    # Crear directorio para subidas si no existe
    os.makedirs("app/uploads", exist_ok=True)
    yield
    # Limpieza al apagar (si es necesaria)

app = FastAPI(
    title="SFI II",
    description="Plataforma de seguridad documental para verificar integridad y autenticidad.",
    version="1.0.0",
    lifespan=lifespan
)

# Añadir SessionMiddleware para manejar la sesión del usuario
app.add_middleware(SessionMiddleware, secret_key="super-secreto-cambiar-en-produccion")

# Configuración de archivos estáticos
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/uploads", StaticFiles(directory="app/uploads"), name="uploads")

# Configuración de plantillas Jinja2
templates = Jinja2Templates(directory="app/templates")

# Incluir routers
app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(verify.router)
app.include_router(history.router)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    username = request.session.get("username")
    return templates.TemplateResponse(
        request=request,
        name="index.html", 
        context={"title": "SFI II", "username": username}
    )

@app.get("/status")
async def get_status():
    return {"status": "ok", "message": "SFI II is running securely"}
