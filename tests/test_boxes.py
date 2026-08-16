from app.vision.boxes import find_span
from app.vision.pdf import load_pdf, render_page_highlight


def test_bbox_search_finds_tag(tiny_pdf_bytes: bytes) -> None:
    document = load_pdf(tiny_pdf_bytes, filename="tiny.pdf")
    words = [word for page in document.pages for word in page.words]
    assert words, "expected native PDF text words"
    span = find_span(words, "AHU-01")
    assert span is not None
    assert span.page == 1
    x0, y0, x1, y1 = span.bbox
    assert x1 > x0 and y1 > y0


def test_capacity_search_normalizes_commas(tiny_pdf_bytes: bytes) -> None:
    document = load_pdf(tiny_pdf_bytes, filename="tiny.pdf")
    words = [word for page in document.pages for word in page.words]
    span = find_span(words, "25000 CFM")
    assert span is not None


def test_render_highlight_returns_png(tiny_pdf_bytes: bytes) -> None:
    document = load_pdf(tiny_pdf_bytes, filename="tiny.pdf")
    words = [word for page in document.pages for word in page.words]
    span = find_span(words, "Trane")
    png = render_page_highlight(tiny_pdf_bytes, page_number=1, highlight=span)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
