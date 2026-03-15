"""네이버 검색 API 클라이언트 (지역 + 블로그)"""

import logging
import re

import requests

from .config import (
    BLOG_URL,
    LOCAL_URL,
    NAVER_CLIENT_ID,
    NAVER_CLIENT_SECRET,
    TIMEOUT,
)

logger = logging.getLogger(__name__)


def _headers() -> dict:
    return {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }


def _clean_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def search_place(query: str) -> dict | None:
    """키워드로 장소 검색, 첫 번째 결과 반환"""
    if not NAVER_CLIENT_ID:
        logger.warning("NAVER_CLIENT_ID가 설정되지 않음")
        return None

    params = {"query": query, "display": 1}

    try:
        resp = requests.get(LOCAL_URL, headers=_headers(), params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        if "items" not in data:
            logger.warning(f"비정상 응답 구조: 'items' 키 없음 (query={query})")
            return None

        items = data["items"]
        return items[0] if items else None

    except requests.exceptions.RequestException as e:
        logger.error(f"네이버 지역검색 실패 (query={query}): {e}")
        return None


def extract_info(place: dict) -> dict:
    """네이버 장소 결과에서 필요한 필드 추출"""
    return {
        "naver_phone": place.get("telephone", ""),
        "naver_category": place.get("category", ""),
        "naver_address": place.get("address", ""),
        "naver_road_address": place.get("roadAddress", ""),
        "naver_place_name": _clean_html(place.get("title", "")),
        "naver_link": place.get("link", ""),
    }


def search_blog(query: str, display: int = 10) -> dict:
    """키워드로 블로그 검색, 결과 목록 + 총 건수 반환"""
    if not NAVER_CLIENT_ID:
        return {"total": 0, "items": []}

    params = {"query": query, "display": display, "sort": "sim"}

    try:
        resp = requests.get(BLOG_URL, headers=_headers(), params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        return {
            "total": data.get("total", 0),
            "items": [
                {
                    "title": _clean_html(item.get("title", "")),
                    "description": _clean_html(item.get("description", "")),
                }
                for item in data.get("items", [])
            ],
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"네이버 블로그검색 실패 (query={query}): {e}")
        return {"total": 0, "items": []}
