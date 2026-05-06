"""
metadata_service.py — Servicio de extracción de metadatos.

Extrae información de autor y fecha de creación de archivos
según su formato: PDF, DOCX, Imágenes (JPG/PNG) y MP3.
"""

import io
from datetime import datetime


def extraer_metadatos(contenido: bytes, extension: str) -> dict:
    """
    Extrae metadatos de autor y fecha de un archivo.

    Args:
        contenido: Bytes del archivo.
        extension: Extensión del archivo (sin punto), ej: 'pdf', 'docx'.

    Returns:
        Diccionario con claves 'autor' y 'fecha' (pueden ser None).
    """
    extension = extension.lower()

    if extension == "pdf":
        return _extraer_metadatos_pdf(contenido)
    elif extension == "docx":
        return _extraer_metadatos_docx(contenido)
    elif extension in ("jpg", "jpeg", "png"):
        return _extraer_metadatos_imagen(contenido)
    elif extension == "mp3":
        return _extraer_metadatos_mp3(contenido)
    else:
        return {"autor": None, "fecha": None}


def _extraer_metadatos_pdf(contenido: bytes) -> dict:
    """Extrae autor y fecha de un archivo PDF usando pikepdf."""
    import pikepdf

    autor = None
    fecha = None

    try:
        pdf = pikepdf.open(io.BytesIO(contenido))
        # Acceder al diccionario de información del PDF
        docinfo = pdf.docinfo
        if "/Author" in docinfo:
            autor = str(docinfo["/Author"])
        if "/CreationDate" in docinfo:
            fecha = str(docinfo["/CreationDate"])
        pdf.close()
    except Exception:
        pass

    return {"autor": autor, "fecha": fecha}


def _extraer_metadatos_docx(contenido: bytes) -> dict:
    """Extrae autor y fecha de un archivo Word (.docx) usando python-docx."""
    from docx import Document

    autor = None
    fecha = None

    try:
        doc = Document(io.BytesIO(contenido))
        props = doc.core_properties
        if props.author:
            autor = props.author
        if props.created:
            fecha = props.created.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        pass

    return {"autor": autor, "fecha": fecha}


def _extraer_metadatos_imagen(contenido: bytes) -> dict:
    """Extrae autor y fecha de una imagen JPG/PNG usando Pillow (EXIF)."""
    from PIL import Image
    from PIL.ExifTags import TAGS

    autor = None
    fecha = None

    try:
        img = Image.open(io.BytesIO(contenido))
        exif_data = img._getexif()
        if exif_data:
            for tag_id, valor in exif_data.items():
                tag_nombre = TAGS.get(tag_id, tag_id)
                if tag_nombre == "Artist":
                    autor = str(valor)
                elif tag_nombre == "DateTime":
                    fecha = str(valor)
        img.close()
    except Exception:
        pass

    return {"autor": autor, "fecha": fecha}


def _extraer_metadatos_mp3(contenido: bytes) -> dict:
    """Extrae artista y fecha de un archivo MP3 usando mutagen."""
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3

    autor = None
    fecha = None

    try:
        audio = MP3(io.BytesIO(contenido))
        tags = audio.tags
        if tags:
            # TPE1 = Artista principal
            if "TPE1" in tags:
                autor = str(tags["TPE1"])
            # TDRC = Fecha de grabación
            if "TDRC" in tags:
                fecha = str(tags["TDRC"])
    except Exception:
        pass

    return {"autor": autor, "fecha": fecha}
