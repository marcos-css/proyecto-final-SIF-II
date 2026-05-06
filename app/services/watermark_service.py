"""
watermark_service.py — Servicio de marcas de agua.

Aplica marcas de agua visibles o invisibles a archivos según su formato.
- Imágenes (JPG/PNG): Visible (texto superpuesto) / Invisible (metadato EXIF).
- PDF: Visible (texto superpuesto en páginas) / Invisible (metadato en docinfo).
- DOCX: Visible (encabezado) / Invisible (propiedad personalizada).
- MP3: Invisible (comentario en tag ID3).
"""

import io


def aplicar_marca_agua(contenido: bytes, extension: str, texto: str, tipo: str = "visible") -> bytes:
    """
    Aplica una marca de agua a un archivo.

    Args:
        contenido: Bytes del archivo original.
        extension: Extensión del archivo (sin punto).
        texto: Texto de la marca de agua.
        tipo: 'visible' o 'invisible'.

    Returns:
        Bytes del archivo con la marca de agua aplicada.
    """
    extension = extension.lower()

    if extension in ("jpg", "jpeg", "png"):
        if tipo == "visible":
            return _marca_agua_imagen_visible(contenido, texto, extension)
        else:
            return _marca_agua_imagen_invisible(contenido, texto, extension)

    elif extension == "pdf":
        if tipo == "visible":
            return _marca_agua_pdf_visible(contenido, texto)
        else:
            return _marca_agua_pdf_invisible(contenido, texto)

    elif extension == "docx":
        if tipo == "visible":
            return _marca_agua_docx_visible(contenido, texto)
        else:
            return _marca_agua_docx_invisible(contenido, texto)

    elif extension == "mp3":
        return _marca_agua_mp3_invisible(contenido, texto)

    # Si el formato no es soportado, devolver sin cambios
    return contenido


# ─── IMÁGENES ──────────────────────────────────────────────────────────

def _marca_agua_imagen_visible(contenido: bytes, texto: str, extension: str) -> bytes:
    """Superpone un texto semitransparente diagonal sobre la imagen."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.open(io.BytesIO(contenido)).convert("RGBA")
    ancho, alto = img.size

    # Crear capa transparente para la marca de agua
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Calcular tamaño de fuente proporcional al tamaño de la imagen
    font_size = max(20, min(ancho, alto) // 15)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except (OSError, IOError):
        # En entornos Docker slim, las fuentes no están instaladas por defecto.
        # Pillow >= 10.1.0 permite pasar el tamaño al default.
        font = ImageFont.load_default(size=font_size)

    # Obtener dimensiones del texto
    bbox = draw.textbbox((0, 0), texto, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Posicionar texto en el centro
    x = (ancho - text_width) // 2
    y = (alto - text_height) // 2

    # Dibujar texto con contorno para que sea visible en fondos claros y oscuros
    # fill = blanco semitransparente, stroke_fill = negro semitransparente
    draw.text((x, y), texto, font=font, fill=(255, 255, 255, 160), stroke_width=3, stroke_fill=(0, 0, 0, 160))

    # Combinar imagen original con overlay
    resultado = Image.alpha_composite(img, overlay)

    # Convertir de vuelta al formato original
    buffer = io.BytesIO()
    formato_guardado = "PNG" if extension == "png" else "JPEG"
    if formato_guardado == "JPEG":
        resultado = resultado.convert("RGB")
    resultado.save(buffer, format=formato_guardado)
    return buffer.getvalue()


def _marca_agua_imagen_invisible(contenido: bytes, texto: str, extension: str) -> bytes:
    """Inserta la marca de agua como comentario en los metadatos de la imagen."""
    from PIL import Image
    from PIL.PngImagePlugin import PngInfo

    img = Image.open(io.BytesIO(contenido))
    buffer = io.BytesIO()

    if extension == "png":
        # Para PNG: usar metadatos PngInfo
        metadata = PngInfo()
        metadata.add_text("Watermark", texto)
        img.save(buffer, format="PNG", pnginfo=metadata)
    else:
        # Para JPG: insertar en el campo EXIF comment
        img.save(buffer, format="JPEG")
        buffer.seek(0)
        data = buffer.getvalue()
        # Insertar comentario JPEG (marcador COM = 0xFFFE)
        comment_bytes = texto.encode("utf-8")
        comment_marker = b"\xff\xfe" + len(comment_bytes).to_bytes(2, "big") + comment_bytes
        # Insertar después del marcador SOI (primeros 2 bytes)
        data = data[:2] + comment_marker + data[2:]
        return data

    return buffer.getvalue()


# ─── PDF ───────────────────────────────────────────────────────────────

def _marca_agua_pdf_visible(contenido: bytes, texto: str) -> bytes:
    """Superpone un texto diagonal semitransparente en cada página del PDF."""
    import pikepdf

    pdf = pikepdf.open(io.BytesIO(contenido))

    for pagina in pdf.pages:
        # Obtener dimensiones de la página
        mediabox = pagina.get("/MediaBox", [0, 0, 612, 792])
        ancho = float(mediabox[2])
        alto = float(mediabox[3])

        # Gs = estado gráfico, Tm = matriz de texto (rotación 45 grados)
        watermark_content = f"""
        q
        /Gs1 gs
        BT
        /F1 60 Tf
        1 0 0 rg
        0.707 0.707 -0.707 0.707 {ancho/4} {alto/4} Tm
        ({texto}) Tj
        ET
        Q
        """

        # Agregar recurso de fuente si no existe
        if "/Resources" not in pagina:
            pagina["/Resources"] = pikepdf.Dictionary()
        resources = pagina["/Resources"]

        if "/Font" not in resources:
            resources["/Font"] = pikepdf.Dictionary()
        resources["/Font"]["/F1"] = pdf.make_indirect(
            pikepdf.Dictionary({
                "/Type": pikepdf.Name("/Font"),
                "/Subtype": pikepdf.Name("/Type1"),
                "/BaseFont": pikepdf.Name("/Helvetica"),
            })
        )

        # Agregar estado gráfico para transparencia
        if "/ExtGState" not in resources:
            resources["/ExtGState"] = pikepdf.Dictionary()
        resources["/ExtGState"]["/Gs1"] = pdf.make_indirect(
            pikepdf.Dictionary({
                "/CA": 0.5,   # Opacidad del trazo
                "/ca": 0.5,   # Opacidad del relleno
            })
        )

        # Añadir el contenido de marca de agua
        pagina.contents_add(
            pikepdf.Stream(pdf, watermark_content.encode())
        )

    buffer = io.BytesIO()
    pdf.save(buffer)
    pdf.close()
    return buffer.getvalue()


def _marca_agua_pdf_invisible(contenido: bytes, texto: str) -> bytes:
    """Inserta la marca de agua como metadato en el diccionario de info del PDF."""
    import pikepdf

    pdf = pikepdf.open(io.BytesIO(contenido))

    # Escribir marca de agua en el diccionario de información
    with pdf.open_metadata() as meta:
        meta["dc:description"] = f"Watermark: {texto}"

    buffer = io.BytesIO()
    pdf.save(buffer)
    pdf.close()
    return buffer.getvalue()


# ─── WORD (DOCX) ──────────────────────────────────────────────────────

def _marca_agua_docx_visible(contenido: bytes, texto: str) -> bytes:
    """Inserta un encabezado con el texto de marca de agua en cada sección."""
    from docx import Document
    from docx.shared import Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = Document(io.BytesIO(contenido))

    # Agregar encabezado en cada sección
    for seccion in doc.sections:
        header = seccion.header
        header.is_linked_to_previous = False
        parrafo = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
        parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = parrafo.add_run(f"CONFIDENCIAL - {texto} - DOCSECURE")
        run.font.size = Pt(14)
        run.font.bold = True
        run.font.color.rgb = RGBColor(120, 120, 120)

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def _marca_agua_docx_invisible(contenido: bytes, texto: str) -> bytes:
    """Inserta la marca de agua como propiedad personalizada del documento."""
    from docx import Document

    doc = Document(io.BytesIO(contenido))

    # Usar las propiedades del core del documento
    doc.core_properties.comments = f"Watermark: {texto}"

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


# ─── MP3 ───────────────────────────────────────────────────────────────

def _marca_agua_mp3_invisible(contenido: bytes, texto: str) -> bytes:
    """Inserta la marca de agua como comentario en los tags ID3 del MP3."""
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3, COMM, ID3NoHeaderError

    buffer = io.BytesIO(contenido)

    try:
        audio = MP3(buffer)
    except Exception:
        return contenido

    # Agregar tags ID3 si no existen
    if audio.tags is None:
        audio.add_tags()

    # COMM = Comentario en ID3
    audio.tags.add(
        COMM(
            encoding=3,          # UTF-8
            lang="spa",          # Idioma español
            desc="Watermark",
            text=[texto]
        )
    )

    output = io.BytesIO()
    audio.save(output)
    output.seek(0)
    return output.getvalue()
