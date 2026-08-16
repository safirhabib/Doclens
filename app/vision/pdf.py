from __future__ import annotations

import io
from pathlib import Path

import pymupdf as fitz
from PIL import Image, ImageDraw

from app.config import get_settings
from app.schemas.extraction import SourceSpan
from app.vision.ocr import OcrUnavailable, ocr_image
from app.vision.types import DocumentContent, PageContent, WordBox


def _native_words(page: fitz.Page, page_number: int) -> list[WordBox]:
    words: list[WordBox] = []
    for item in page.get_text("words"):
        x0, y0, x1, y1, text, *_ = item
        if not str(text).strip():
            continue
        words.append(
            WordBox(
                text=str(text),
                page=page_number,
                bbox=(float(x0), float(y0), float(x1), float(y1)),
            )
        )
    return words


def _render_png(page: fitz.Page, dpi: int) -> bytes:
    zoom = dpi / 72
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    return pix.tobytes("png")


def _extract_tables(page: fitz.Page) -> list[list[list[str | None]]]:
    try:
        found = page.find_tables()
    except Exception:
        return []
    tables: list[list[list[str | None]]] = []
    for table in found.tables:
        tables.append(table.extract())
    return tables


def load_pdf(source: bytes | Path, filename: str | None = None) -> DocumentContent:
    settings = get_settings()
    if isinstance(source, Path):
        data = source.read_bytes()
        name = filename or source.name
    else:
        data = source
        name = filename or "document.pdf"

    doc = fitz.open(stream=data, filetype="pdf")
    pages: list[PageContent] = []
    try:
        for index, page in enumerate(doc, start=1):
            native = _native_words(page, index)
            text = page.get_text("text") or ""
            image_png = _render_png(page, settings.render_dpi)
            used_ocr = False
            words = native
            if len(native) < settings.ocr_min_words:
                try:
                    ocr_text, ocr_words = ocr_image(
                        image_png,
                        page=index,
                        pdf_width=float(page.rect.width),
                        pdf_height=float(page.rect.height),
                    )
                    if ocr_words:
                        words = ocr_words
                        text = ocr_text
                        used_ocr = True
                except OcrUnavailable:
                    pass
            pages.append(
                PageContent(
                    page=index,
                    width=float(page.rect.width),
                    height=float(page.rect.height),
                    text=text.strip(),
                    words=words,
                    tables=_extract_tables(page),
                    used_ocr=used_ocr,
                    image_png=image_png,
                )
            )
    finally:
        doc.close()
    return DocumentContent(filename=name, pages=pages)


def render_page_highlight(
    source: bytes | Path,
    page_number: int,
    highlight: SourceSpan | None = None,
    dpi: int | None = None,
) -> bytes:
    settings = get_settings()
    dpi = dpi or settings.render_dpi
    data = source.read_bytes() if isinstance(source, Path) else source
    doc = fitz.open(stream=data, filetype="pdf")
    try:
        page = doc[page_number - 1]
        png = _render_png(page, dpi)
    finally:
        doc.close()

    if highlight is None:
        return png

    image = Image.open(io.BytesIO(png)).convert("RGBA")
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    zoom = dpi / 72
    x0, y0, x1, y1 = highlight.bbox
    pad = 3
    box = [
        x0 * zoom - pad,
        y0 * zoom - pad,
        x1 * zoom + pad,
        y1 * zoom + pad,
    ]
    draw.rectangle(box, outline=(42, 157, 143, 255), width=3)
    draw.rectangle(box, fill=(42, 157, 143, 50))
    merged = Image.alpha_composite(image, overlay).convert("RGB")
    buf = io.BytesIO()
    merged.save(buf, format="PNG")
    return buf.getvalue()
