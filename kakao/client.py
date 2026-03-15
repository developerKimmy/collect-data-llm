"""카카오 로컬 API 클라이언트"""

import logging

import requests

from .config import KAKAO_API_KEY, SEARCH_URL, TIMEOUT

logger = logging.getLogger(__name__)


def search_place(query: str, x: str = "", y: str = "") -> dict | None:
    """키워드로 장소 검색, 첫 번째 결과 반환"""
    if not KAKAO_API_KEY:
        logger.warning("KAKAO_MAP_API_KEY가 설정되지 않음")
        return None

    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {"query": query, "size": 1}

    if x and y:
        params["x"] = x
        params["y"] = y
        params["sort"] = "distance"

    try:
        resp = requests.get(SEARCH_URL, headers=headers, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        if "documents" not in data:
            logger.warning(f"비정상 응답 구조: 'documents' 키 없음 (query={query})")
            return None

        docs = data["documents"]
        return docs[0] if docs else None

    except requests.exceptions.RequestException as e:
        logger.error(f"카카오 API 요청 실패 (query={query}): {e}")
        return None


def extract_info(place: dict) -> dict:
    """카카오 장소 결과에서 필요한 필드 추출"""
    return {
        "kakao_phone": place.get("phone", ""),
        "kakao_category": place.get("category_name", ""),
        "kakao_place_url": place.get("place_url", ""),
        "kakao_place_name": place.get("place_name", ""),
        "kakao_address": place.get("address_name", ""),
        "kakao_road_address": place.get("road_address_name", ""),
        "kakao_lng": place.get("x", ""),
        "kakao_lat": place.get("y", ""),
    }
