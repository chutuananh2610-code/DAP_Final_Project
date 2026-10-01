"""Parsing utilities for CafeLand listing data."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

import numpy as np
from bs4 import BeautifulSoup


NEGOTIABLE_TOKENS = ("thỏa thuận", "thoả thuận", "thuong luong", "thương lượng")


def normalize_space(value: Any) -> str:
    """Collapse whitespace and return an empty string for None."""
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def strip_accents(value: str) -> str:
    """Accent-insensitive helper used only for matching."""
    value = normalize_space(value).lower().replace("đ", "d")
    return "".join(
        ch for ch in unicodedata.normalize("NFD", value)
        if unicodedata.category(ch) != "Mn"
    )


def parse_decimal_vi(token: str) -> float | None:
    """Parse a Vietnamese-formatted decimal token."""
    token = normalize_space(token)
    if not token:
        return None
    token = token.replace(" ", "")
    # In price/area strings, comma is normally decimal separator.
    if "," in token and "." not in token:
        token = token.replace(",", ".")
    elif "," in token and "." in token:
        # Keep the right-most symbol as decimal separator.
        if token.rfind(",") > token.rfind("."):
            token = token.replace(".", "").replace(",", ".")
        else:
            token = token.replace(",", "")
    try:
        return float(token)
    except ValueError:
        return None


def parse_price_vnd(value: Any) -> float:
    """Normalize common CafeLand asking-price strings to VND.

    Examples
    --------
    '3 tỷ 800 triệu' -> 3_800_000_000
    '2,25 tỷ' -> 2_250_000_000
    '850 triệu' -> 850_000_000
    'Thương lượng' -> NaN
    """
    text = normalize_space(value).lower()
    if not text or any(tok in text for tok in NEGOTIABLE_TOKENS):
        return np.nan

    plain = strip_accents(text)
    plain = plain.replace("vnd", "").replace("vnđ", "")

    total = 0.0
    matched = False

    m = re.search(r"(\d+(?:[.,]\d+)?)\s*ty\b", plain)
    if m:
        val = parse_decimal_vi(m.group(1))
        if val is not None:
            total += val * 1_000_000_000
            matched = True

    m = re.search(r"(\d+(?:[.,]\d+)?)\s*trieu\b", plain)
    if m:
        val = parse_decimal_vi(m.group(1))
        if val is not None:
            total += val * 1_000_000
            matched = True

    if matched:
        return float(total)

    # Explicit long-form number, e.g. 9.300.000.000
    digits = re.sub(r"[^\d]", "", text)
    if len(digits) >= 7:
        return float(digits)

    return np.nan


def parse_area_m2(value: Any) -> float:
    """Parse square-meter values such as '128.4m2' or '71,04 m²'."""
    text = normalize_space(value).lower()
    if not text:
        return np.nan
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:m2|m²)", text)
    if not match:
        match = re.search(r"(\d+(?:[.,]\d+)?)", text)
    if not match:
        return np.nan
    val = parse_decimal_vi(match.group(1))
    return float(val) if val is not None else np.nan


def parse_int(value: Any) -> float:
    """Return first integer or NaN."""
    text = normalize_space(value)
    match = re.search(r"\d+", text)
    return float(match.group(0)) if match else np.nan


def infer_property_type(text: str) -> str:
    """Infer a coarse property type from title/slug/detail text.

    Rules are ordered from specific to broad so mixed-use titles are less
    likely to be classified as ``house`` too early.
    """
    t = strip_accents(text)
    rules = [
        ("apartment", ["can ho", "chung cu", "chcc", "officetel", "condotel"]),
        ("land", ["ban dat", " dat ", "dat tho cu", "dat nen", "lo dat", "ban lo"]),
        ("villa", ["biet thu", "villa"]),
        ("commercial", ["kho", "nha xuong", "xuong", "khach san", "shophouse", "mat bang kinh doanh"]),
        ("house", ["nha rieng", "nha pho", "ban nha", "toa nha", " can nha ", " nha ", "hxh", "hem xe", " tret", " lau", " tang", "mat tien"]),
    ]
    for label, terms in rules:
        if any(term in f" {t} " for term in terms):
            return label

    if re.search(r"\bcan\b.*\b[1-6]pn\b|\b[1-6]pn\b.*\b[1-6]wc\b", t):
        return "apartment"
    return "unknown"


def _next_text(strings: list[str], label: str) -> str:
    """Find the next non-label text item after an exact label."""
    for i, item in enumerate(strings):
        if normalize_space(item).lower() == label.lower():
            for nxt in strings[i + 1:i + 5]:
                n = normalize_space(nxt)
                if n and n.lower() not in {
                    "giá bán", "diện tích", "phòng ngủ", "thông tin mô tả"
                }:
                    return n
    return ""


def parse_detail_html(html: str, url: str = "") -> dict[str, Any]:
    """Parse a CafeLand detail page with label/regex fallbacks.

    The parser intentionally avoids depending on one CSS class so that small
    site-layout changes do not immediately break the pipeline.
    """
    soup = BeautifulSoup(html, "lxml")
    strings = [normalize_space(s) for s in soup.stripped_strings]
    full = "\n".join(strings)

    h1 = soup.find("h1")
    title = normalize_space(h1.get_text(" ", strip=True)) if h1 else ""

    id_date = re.search(
        r"Mã tài sản:\s*(\d+)\s*/\s*Ngày đăng:\s*(\d{2}-\d{2}-\d{4})",
        full,
        re.I,
    )
    listing_id = id_date.group(1) if id_date else ""
    listing_date = id_date.group(2) if id_date else ""

    location_match = re.search(r"Vị trí:\s*(.+?)(?:\n|Lưu tin)", full, re.I)
    location_text = normalize_space(location_match.group(1)) if location_match else ""

    price_text = _next_text(strings, "Giá bán")
    area_text = _next_text(strings, "Diện tích")
    bedrooms_text = _next_text(strings, "Phòng ngủ")

    # Description bounded by stable labels when available.
    desc_match = re.search(
        r"Thông tin mô tả\s*(.+?)\s*Kiến trúc\s*-\s*Tiện ích",
        full,
        re.I | re.S,
    )
    description = normalize_space(desc_match.group(1)) if desc_match else ""

    detail_type = ""
    type_match = re.search(
        r"Loại địa ốc\s*(.+?)(?=Hướng nhà|Số tầng|Số toilet|Đường trước nhà|Số phòng khách|Số phòng ngủ|Pháp lý|Vị trí tài sản)",
        full,
        re.I | re.S,
    )
    if type_match:
        detail_type = normalize_space(type_match.group(1))

    expired = bool(re.search(r"Tin Hết Hạn", full, re.I))

    return {
        "source": "cafeland",
        "url": url,
        "listing_id": listing_id,
        "title": title,
        "listing_date": listing_date,
        "location_text": location_text,
        "price_text": price_text,
        "area_text": area_text,
        "bedrooms_text": bedrooms_text,
        "description": description,
        "property_type_raw": detail_type,
        "property_type": infer_property_type(f"{detail_type} {title} {url}"),
        "price_vnd": parse_price_vnd(price_text),
        "area_m2": parse_area_m2(area_text),
        "bedrooms": parse_int(bedrooms_text),
        "is_expired": expired,
    }


def parse_card_text(card_text: str, title: str = "", url: str = "") -> dict[str, Any]:
    """Parse a search-result card after its URL/title have been identified."""
    text = normalize_space(card_text)

    price_match = re.search(
        r"((?:\d+(?:[.,]\d+)?\s*tỷ(?:\s*\d+(?:[.,]\d+)?\s*triệu)?)|"
        r"(?:\d+(?:[.,]\d+)?\s*triệu)|Thương lượng)",
        text,
        re.I,
    )
    area_match = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:m2|m²)", text, re.I)
    update_match = re.search(r"Cập nhật:\s*([^|]+?)(?=\s{2,}|$)", text, re.I)

    # Location: nearby segment containing TP.HCM.
    loc_match = re.search(
        r"([^|]{0,100}?TP\.\s*Hồ Chí Minh)",
        text,
        re.I,
    )

    return {
        "source": "cafeland",
        "url": url,
        "title": normalize_space(title),
        "price_text": normalize_space(price_match.group(1)) if price_match else "",
        "area_text": normalize_space(area_match.group(0)) if area_match else "",
        "location_text": normalize_space(loc_match.group(1)) if loc_match else "",
        "update_text": normalize_space(update_match.group(1)) if update_match else "",
        "property_type": infer_property_type(f"{title} {url}"),
    }
