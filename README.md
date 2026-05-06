# Proyecto Final SIF II

Una plataforma web criptográfica diseñada para garantizar la integridad, autenticidad y trazabilidad de documentos digitales. Utiliza funciones de hashing (SHA-256), extracción de metadatos profundos y la aplicación de marcas de agua (visibles e invisibles) para proteger archivos multimedia.

## Requisitos Previos

Para ejecutar este proyecto, solo necesitas tener instalado:
- **Docker**
- **Docker Compose**

## Instalación y Ejecución

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/marcos-css/proyecto-final-SIF-II
   cd proyecto-final-SIF-II
   ```

2. **Levantar los contenedores**:
   Ejecuta el siguiente comando en la raíz del proyecto (donde se encuentra el `docker-compose.yml`):
   ```bash
   docker-compose up --build
   ```

3. **Acceder a la aplicación**:
   Abre tu navegador web y visita: **http://localhost:8000**

4. **Para detener el servidor**:
   Presiona `Ctrl + C` en la terminal donde se está ejecutando, o corre:
   ```bash
   docker-compose down
   ```

## Estructura del Proyecto

```text
proyecto-final-SIF-II/
├── app/
│   ├── main.py                 # Punto de entrada de la aplicación FastAPI
│   ├── database.py             # Configuración de SQLite y SQLAlchemy
│   ├── models.py               # Modelos de la base de datos (Usuarios, Documentos)
│   ├── routers/                # Endpoints agrupados por funcionalidad (auth, upload, history, verify)
│   ├── services/               # Lógica de negocio pesada (ej. watermark_service.py)
│   ├── templates/              # Vistas HTML (Jinja2) usando Tailwind CSS
│   ├── static/                 # Archivos estáticos (CSS extra, JS, imágenes)
│   └── uploads/                # Carpeta local (ignorada en git) donde se guardan los archivos
├── docker-compose.yml          # Orquestador del contenedor
├── Dockerfile                  # Receta de construcción de la imagen Python 3.11
└── requirements.txt            # Dependencias del proyecto
```

## Equipo de Desarrollo
- Enrique Alejandro Pereda Meraz
- Erick Rangel Rubio
- Raúl Esteban Aniles Macias
- Sebastián Valencia Terrazas
- Marcos Casas Caldera