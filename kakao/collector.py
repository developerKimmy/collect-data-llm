"""카카오 로컬 API로 관광지 데이터 보강"""

import logging
import math

from tqdm import tqdm

from .config import MAX_DISTANCE_KM
from .client import search_place, extract_info
from .storage import append_jsonl, load_ids, load_jsonl

logger = logging.getLogger(__name__)


def _short_addr(addr: str) -> str:
    """주소에서 시/도 + 구/군 까지만 추출"""
    parts = addr.split()
    return " ".join(parts[:2]) if len(parts) >= 2 else addr


def _distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """두 좌표 간 거리(km) 계산"""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlng / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _is_valid_match(item: dict, kakao: dict) -> bool:
    """TourAPI 좌표와 카카오 좌표를 비교하여 유효한 매칭인지 확인"""
    try:
        tour_lat = float(item.get("mapy", 0))
        tour_lng = float(item.get("mapx", 0))
        kakao_lat = float(kakao.get("kakao_lat", 0))
        kakao_lng = float(kakao.get("kakao_lng", 0))
    except (ValueError, TypeError):
        return True

    if not tour_lat or not kakao_lat:
        return True

    dist = _distance_km(tour_lat, tour_lng, kakao_lat, kakao_lng)
    if dist > MAX_DISTANCE_KM:
        logger.warning(
            f"좌표 불일치 ({dist:.1f}km): {item.get('title', '')} "
            f"tour=({tour_lat},{tour_lng}) kakao=({kakao_lat},{kakao_lng})"
        )
        return False
    return True


def _search_kakao(item: dict) -> dict:
    """항목의 제목+지역으로 검색, 실패 시 주소로 재검색"""
    title = item.get("title", "")
    addr1 = item.get("addr1", "")
    short = _short_addr(addr1)
    x = str(item.get("mapx", ""))
    y = str(item.get("mapy", ""))

    query = f"{title} {short}".strip() if short else title
    place = search_place(query, x=x, y=y)

    if not place and addr1:
        place = search_place(addr1, x=x, y=y)

    if not place:
        return {}

    info = extract_info(place)
    if not _is_valid_match(item, info):
        return {}

    return info


def _fill_addr2(item: dict, kakao: dict) -> None:
    """addr2가 비어있으면 카카오 지번 주소로 보완"""
    if item.get("addr2", "").strip():
        return
    kakao_addr = kakao.get("kakao_address", "")
    if kakao_addr:
        item["addr2"] = f"({kakao_addr})"


def enrich_with_kakao(common_path, detail_path) -> None:
    """카카오 로컬 API로 보강 (전화, 카테고리, 주소 보완)"""
    commons = load_jsonl(common_path)
    if not commons:
        logger.warning("보강할 공통정보가 없습니다.")
        return

    fetched = load_ids(detail_path)
    to_enrich = [i for i in commons if str(i.get("contentid", "")) not in fetched]

    if not to_enrich:
        logger.info("모든 항목이 이미 보강되었습니다.")
        return

    logger.info(f"카카오 보강: 전체 {len(commons)}건 중 {len(to_enrich)}건 예정")
    collected = 0
    no_match = 0

    for item in tqdm(to_enrich, desc="카카오 보강"):
        kakao = _search_kakao(item)
        if not kakao:
            no_match += 1

        merged = {**item, **kakao}
        _fill_addr2(merged, kakao)
        append_jsonl(detail_path, merged)
        collected += 1

    logger.info(f"보강 완료: {collected}건 (매칭 실패: {no_match}건)")
