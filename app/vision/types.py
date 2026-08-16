from pydantic import BaseModel, Field


class WordBox(BaseModel):
    text: str
    page: int
    bbox: tuple[float, float, float, float]


class PageContent(BaseModel):
    page: int
    width: float
    height: float
    text: str
    words: list[WordBox] = Field(default_factory=list)
    tables: list[list[list[str | None]]] = Field(default_factory=list)
    used_ocr: bool = False
    image_png: bytes | None = None


class DocumentContent(BaseModel):
    filename: str
    pages: list[PageContent] = Field(default_factory=list)

    @property
    def used_ocr(self) -> bool:
        return any(page.used_ocr for page in self.pages)

    @property
    def ocr_pages(self) -> list[int]:
        return [page.page for page in self.pages if page.used_ocr]

    @property
    def full_text(self) -> str:
        parts = []
        for page in self.pages:
            parts.append(f"--- page {page.page} ---\n{page.text}")
        return "\n\n".join(parts)
