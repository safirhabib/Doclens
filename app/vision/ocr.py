from __future__ import annotations

import io

from PIL import Image

from app.vision.types import WordBox

try:
    import pytesseract
    from pytesseract import Output
except ImportError:  # pragma: no cover
    pytesseract = None
    Output = None


class OcrUnavailable(RuntimeError):
    pass


def ocr_image(image_png: bytes, page: int, pdf_width: float, pdf_height: float) -> tuple[str, list[WordBox]]:
    if pytesseract is None:
        raise OcrUnavailable("pytesseract is not installed")

    image = Image.open(io.BytesIO(image_png)).convert("RGB")
    try:
        data = pytesseract.image_to_data(image, output_type=Output.DICT)
    except pytesseract.TesseractNotFoundError as exc:
        raise OcrUnavailable("tesseract binary is not installed") from exc

    scale_x = pdf_width / max(image.width, 1)
    scale_y = pdf_height / max(image.height, 1)
    words: list[WordBox] = []
    parts: list[str] = []
    n = len(data["text"])
    for i in range(n):
        text = (data["text"][i] or "").strip()
        if not text:
            continue
        try:
            conf = float(data["conf"][i])
        except (TypeError, ValueError):
            conf = -1
        if conf < 0:
            continue
        x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
        bbox = (
            x * scale_x,
            y * scale_y,
            (x + w) * scale_x,
            (y + h) * scale_y,
        )
        words.append(WordBox(text=text, page=page, bbox=bbox))
        parts.append(text)
    return " ".join(parts), words
