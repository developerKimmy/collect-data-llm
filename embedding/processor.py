"""수집된 관광 데이터를 RAG용 JSONL로 정제"""

import re

from .config import AREA_CODES, CONTENT_TYPES, INTRO_LABELS


def clean_html(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"&[a-zA-Z]+;", " ", text)
    text = re.sub(r"&#\d+;", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def _extract_url(html: str) -> str:
    urls = re.findall(r'href=["\']([^"\']+)["\']', html)
    return urls[0] if urls else clean_html(html)


def _format_header(item: dict) -> str:
    ct_id = int(item.get("contenttypeid", 0))
    ct_name = CONTENT_TYPES.get(ct_id, "기타")
    return f"[{ct_name}] {item.get('title', '').strip()}"


def _format_address(item: dict) -> str:
    addr = f"{item.get('addr1', '')} {item.get('addr2', '')}".strip()
    return f"주소: {addr}" if addr else ""


def _format_contact(item: dict) -> list[str]:
    parts = []
    tel = item.get("tel", "").strip() or item.get("kakao_phone", "").strip()
    if tel:
        parts.append(f"전화: {clean_html(tel)}")
    homepage = item.get("homepage", "").strip()
    if homepage:
        url = _extract_url(homepage)
        if url:
            parts.append(f"홈페이지: {url}")
    kakao_url = item.get("kakao_place_url", "").strip()
    if kakao_url:
        parts.append(f"카카오맵: {kakao_url}")
    return parts


def _format_category(item: dict) -> str:
    cat = item.get("kakao_category", "").strip()
    return f"카테고리: {cat}" if cat else ""


def _format_overview(item: dict) -> str:
    overview = clean_html(item.get("overview", ""))
    return f"개요: {overview}" if overview else ""


def _format_intro(item: dict) -> list[str]:
    parts = []
    seen = set()
    for key, label in INTRO_LABELS.items():
        value = item.get(key, "")
        if not value or not str(value).strip() or label in seen:
            continue
        cleaned = clean_html(str(value).strip())
        if cleaned:
            seen.add(label)
            parts.append(f"{label}: {cleaned}")
    return parts


def _build_text(item: dict) -> str:
    parts = [_format_header(item)]
    for line in [_format_address(item), _format_category(item), _format_overview(item)]:
        if line:
            parts.append(line)
    parts.extend(_format_contact(item))
    parts.extend(_format_intro(item))
    return "\n".join(parts)


def _safe_float(value) -> float | None:
    try:
        return float(value) if value else None
    except (ValueError, TypeError):
        return None


def _build_metadata(item: dict) -> dict:
    ct_id = int(item.get("contenttypeid", 0))
    area_code = str(item.get("areacode", ""))

    meta = {
        "content_type": CONTENT_TYPES.get(ct_id, "기타"),
        "content_type_id": ct_id,
        "title": item.get("title", "").strip(),
        "address": f"{item.get('addr1', '')} {item.get('addr2', '')}".strip(),
        "area": AREA_CODES.get(area_code, ""),
        "area_code": area_code,
        "sigungu_code": str(item.get("sigungucode", "")),
        "tel": clean_html(item.get("tel", "")),
        "image_url": item.get("firstimage", ""),
        "categories": {
            "cat1": item.get("cat1", ""),
            "cat2": item.get("cat2", ""),
            "cat3": item.get("cat3", ""),
        },
    }

    lat = _safe_float(item.get("mapy"))
    lng = _safe_float(item.get("mapx"))
    if lat:
        meta["lat"] = lat
    if lng:
        meta["lng"] = lng

    for key in ["kakao_place_url", "kakao_category"]:
        value = item.get(key, "")
        if value:
            meta[key] = value

    return meta


def process_item(item: dict) -> dict | None:
    content_id = str(item.get("contentid", ""))
    if not content_id:
        return None
    return {
        "id": content_id,
        "text": _build_text(item),
        "metadata": _build_metadata(item),
    }


def process_all(items: list[dict]) -> list[dict]:
    return [c for i in items if (c := process_item(i)) is not None]
