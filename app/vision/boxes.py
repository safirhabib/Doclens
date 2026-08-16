from __future__ import annotations

import io
import re
from collections.abc import Sequence

from app.schemas.extraction import SourceSpan
from app.vision.types import WordBox


def normalize_text(value: str) -> str:
    text = value.lower().replace(",", "")
    text = text.replace("—", "-").replace("–", "-")
    text = re.sub(r"[^\w.\-/ ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def tokenize(value: str) -> list[str]:
    return [token for token in normalize_text(value).split(" ") if token]


def _union(boxes: Sequence[tuple[float, float, float, float]]) -> tuple[float, float, float, float]:
    return (
        min(box[0] for box in boxes),
        min(box[1] for box in boxes),
        max(box[2] for box in boxes),
        max(box[3] for box in boxes),
    )


def _center(bbox: tuple[float, float, float, float]) -> tuple[float, float]:
    return ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)


def _distance(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
) -> float:
    ax, ay = _center(a)
    bx, by = _center(b)
    return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5


def find_span(
    words: Sequence[WordBox],
    query: str,
    *,
    page: int | None = None,
    anchor: SourceSpan | None = None,
) -> SourceSpan | None:
    """Locate query text in word boxes. Prefers the match closest to an anchor (usually the tag)."""
    tokens = tokenize(str(query))
    if not tokens:
        return None

    candidates = [word for word in words if page is None or word.page == page]
    if not candidates:
        candidates = list(words)

    matches: list[SourceSpan] = []
    for index, word in enumerate(candidates):
        window: list[WordBox] = []
        token_index = 0
        for follow in candidates[index:]:
            if window and follow.page != window[0].page:
                break
            piece = tokenize(follow.text)
            if not piece:
                continue
            window.append(follow)
            joined = tokenize(" ".join(item.text for item in window))
            if joined[: len(tokens)] == tokens[: len(joined)]:
                token_index = len(joined)
                if token_index >= len(tokens):
                    matches.append(
                        SourceSpan(
                            page=window[0].page,
                            bbox=_union([item.bbox for item in window]),
                        )
                    )
                    break
            elif tokens[0] in normalize_text(follow.text) and len(tokens) == 1:
                matches.append(SourceSpan(page=follow.page, bbox=follow.bbox))
                break
            else:
                break

    if not matches:
        return _fuzzy_single_token(candidates, tokens)

    if anchor is None:
        return matches[0]

    same_page = [match for match in matches if match.page == anchor.page]
    pool = same_page or matches
    return min(pool, key=lambda match: _distance(match.bbox, anchor.bbox))


def _fuzzy_single_token(words: Sequence[WordBox], tokens: list[str]) -> SourceSpan | None:
    needle = "".join(tokens)
    if not needle:
        return None
    for word in words:
        hay = normalize_text(word.text).replace(" ", "")
        if hay == needle or needle in hay:
            return SourceSpan(page=word.page, bbox=word.bbox)
    return None
