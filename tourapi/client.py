"""한국관광공사 TourAPI 클라이언트"""

import json
import logging
import math
import time

import requests

from .config import (
    MAX_RETRIES,
    MOBILE_APP,
    MOBILE_OS,
    NUM_OF_ROWS,
    REQUEST_DELAY,
    RESPONSE_TYPE,
    TOUR_API_KEY,
    TOUR_BASE_URL,
)

logger = logging.getLogger(__name__)


class TourAPIError(Exception):
    pass


class RateLimitError(TourAPIError):
    pass


def create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"Accept": "application/json"})
    return session


def request(session: requests.Session, endpoint: str, params: dict) -> dict:
    """TourAPI 단일 요청 (재시도 포함), body 반환"""
    url = f"{TOUR_BASE_URL}/{endpoint}?serviceKey={TOUR_API_KEY}"
    params = {
        "MobileOS": MOBILE_OS,
        "MobileApp": MOBILE_APP,
        "_type": RESPONSE_TYPE,
        **params,
    }

    for attempt in range(MAX_RETRIES):
        try:
            resp = session.get(url, params=params, timeout=30)

            if resp.status_code == 429:
                raise RateLimitError("일일 요청 한도 초과 (429)")

            resp.raise_for_status()
            data = resp.json()

            # 응답 구조 검증
            if "response" not in data:
                raise TourAPIError(f"비정상 응답 구조: 'response' 키 없음")

            header = data["response"].get("header", {})

            if header.get("resultCode") != "0000":
                raise TourAPIError(
                    f"API 오류 [{header.get('resultCode')}]: "
                    f"{header.get('resultMsg', 'Unknown')}"
                )

            body = data["response"].get("body")
            if body is None:
                raise TourAPIError("비정상 응답: body가 없음")

            return body

        except RateLimitError:
            raise

        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            logger.warning(f"요청 실패 (시도 {attempt + 1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** (attempt + 1))
                continue
            raise TourAPIError(f"요청 실패 (재시도 초과): {e}")


def parse_items(body: dict) -> list:
    """API 응답 body에서 items 리스트 추출"""
    items = body.get("items", "")
    if not items:
        return []
    item_list = items.get("item", [])
    if isinstance(item_list, dict):
        item_list = [item_list]
    return item_list


def fetch_list(
    session: requests.Session,
    content_type_id: int,
    area_code: str = "",
    sigungu_code: str = "",
    limit: int = 0,
) -> list:
    """특정 콘텐츠 타입 목록 조회 (페이징 포함)"""
    rows = limit if limit > 0 else NUM_OF_ROWS
    params = {
        "numOfRows": rows,
        "pageNo": 1,
        "contentTypeId": content_type_id,
        "arrange": "A",
    }
    if area_code:
        params["areaCode"] = area_code
    if sigungu_code:
        params["sigunguCode"] = sigungu_code

    body = request(session, "areaBasedList2", params)
    total_count = body.get("totalCount", 0)

    if not total_count:
        return []

    all_items = parse_items(body)

    if limit > 0:
        return all_items[:limit]

    total_pages = math.ceil(total_count / NUM_OF_ROWS)
    for page in range(2, total_pages + 1):
        time.sleep(REQUEST_DELAY)
        params["pageNo"] = page
        body = request(session, "areaBasedList2", params)
        all_items.extend(parse_items(body))

    return all_items


def fetch_common(session: requests.Session, content_id: str) -> dict:
    """공통정보 조회 (overview 포함)"""
    body = request(
        session,
        "detailCommon2",
        {"contentId": content_id, "numOfRows": 1, "pageNo": 1},
    )
    items = parse_items(body)
    return items[0] if items else {}
