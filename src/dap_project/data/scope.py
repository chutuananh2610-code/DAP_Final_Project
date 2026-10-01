"""Geographic scope logic for pre-2025 HCMC boundary."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any


def _norm(text: Any) -> str:
    text = "" if text is None else str(text)
    text = text.lower().replace("đ", "d")
    text = "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"\s+", " ", text).strip()


def load_scope_map(path: str | Path) -> dict[str, str]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


LEGACY_TEXT_RULES = [
    (r"\b(?:quan|q)\s*1\b", "Quận 1"),
    (r"\b(?:quan|q)\s*3\b", "Quận 3"),
    (r"\b(?:quan|q)\s*4\b", "Quận 4"),
    (r"\b(?:quan|q)\s*5\b", "Quận 5"),
    (r"\b(?:quan|q)\s*6\b", "Quận 6"),
    (r"\b(?:quan|q)\s*7\b", "Quận 7"),
    (r"\b(?:quan|q)\s*8\b", "Quận 8"),
    (r"\b(?:quan|q)\s*10\b", "Quận 10"),
    (r"\b(?:quan|q)\s*11\b", "Quận 11"),
    (r"\b(?:quan|q)\s*12\b", "Quận 12"),
    (r"\bbinh thanh\b", "Quận Bình Thạnh"),
    (r"\bbinh tan\b", "Quận Bình Tân"),
    (r"\bgo vap\b", "Quận Gò Vấp"),
    (r"\bphu nhuan\b", "Quận Phú Nhuận"),
    (r"\btan binh\b", "Quận Tân Bình"),
    (r"\btan phu\b", "Quận Tân Phú"),
    (r"\b(?:quan|q)\s*2\b|\b(?:quan|q)\s*9\b|\btp\.?\s*thu duc\b|\bthanh pho thu duc\b",
     "TP Thủ Đức"),
    (r"\bbinh chanh\b", "Huyện Bình Chánh"),
    (r"\bcan gio\b", "Huyện Cần Giờ"),
    (r"\bcu chi\b", "Huyện Củ Chi"),
    (r"\bhoc mon\b", "Huyện Hóc Môn"),
    (r"\bnha be\b", "Huyện Nhà Bè"),
]


def infer_legacy_area_from_text(text: str) -> str:
    normalized = _norm(text)
    for pattern, label in LEGACY_TEXT_RULES:
        if re.search(pattern, normalized, re.I):
            return label
    return ""


def infer_scope(
    location_text: str,
    title: str,
    description: str,
    scope_map: dict[str, str],
) -> tuple[str, str, str]:
    """Return (status, current_ward, legacy_area).

    Priority:
    1) current ward whitelist,
    2) explicit historical district/huyện text,
    3) unresolved.

    If ward/text disagree, mark conflict.
    """
    location_n = _norm(location_text)
    matched_ward = ""
    ward_legacy = ""

    # Longest names first reduces substring collisions.
    for ward in sorted(scope_map, key=len, reverse=True):
        if _norm(ward) in location_n:
            matched_ward = ward
            ward_legacy = scope_map[ward]
            break

    text_legacy = infer_legacy_area_from_text(f"{title} {description}")

    if ward_legacy and text_legacy and ward_legacy != text_legacy:
        return "conflict", matched_ward, ward_legacy
    if ward_legacy:
        return "confirmed_by_current_ward", matched_ward, ward_legacy
    if text_legacy:
        return "confirmed_by_legacy_text", "", text_legacy
    return "unresolved", "", ""
