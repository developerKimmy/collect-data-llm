"""TourAPI 데이터 수집 (목록 + 공통정보)"""

import logging
import time

from tqdm import tqdm

from .config import CONTENT_TYPES, REQUEST_DELAY
from .client import RateLimitError, TourAPIError, create_session, fetch_common, fetch_list
from .storage import append_jsonl, load_ids, load_jsonl, save_jsonl

logger = logging.getLogger(__name__)


def fetch_all_lists(areas: list[dict], list_path, limit: int = 0) -> list[dict]:
    """전체 지역 × 콘텐츠 타입 목록 수집 (이어받기 지원)"""
    existing = load_jsonl(list_path)
    done_keys = {
        (str(i.get("areacode", "")), str(i.get("sigungucode", "")), str(i.get("contenttypeid", "")))
        for i in existing
    }

    if existing and limit == 0:
        logger.info(f"기존 목록 {len(existing)}건 로드, 미완료 조합만 수집")

    session = create_session()
    all_items = list(existing)
    new_count = 0

    for area in areas:
        area_code = area.get("area_code", "")
        sigungu_code = area.get("sigungu_code", "")
        area_name = area.get("name", "전국")
        logger.info(f"[{area_name}]")

        for ct_id, ct_name in CONTENT_TYPES.items():
            key = (area_code, sigungu_code, str(ct_id))
            if key in done_keys and limit == 0:
                logger.info(f"  [{ct_name}] 이미 수집됨, 스킵")
                continue

            try:
                items = fetch_list(
                    session, ct_id,
                    area_code=area_code,
                    sigungu_code=sigungu_code,
                    limit=limit,
                )
            except TourAPIError as e:
                logger.error(f"  [{ct_name}] 수집 실패: {e}")
                continue

            if not items:
                logger.info(f"  [{ct_name}] 0건")
                continue

            # 응답 검증: contentid 필수
            valid = [i for i in items if i.get("contentid")]
            if len(valid) < len(items):
                logger.warning(f"  [{ct_name}] contentid 누락 {len(items) - len(valid)}건 제외")

            logger.info(f"  [{ct_name}] {len(valid)}건")
            all_items.extend(valid)
            new_count += len(valid)
            time.sleep(REQUEST_DELAY)

    # 중복 제거 (contentid 기준)
    seen = set()
    deduped = []
    for item in all_items:
        cid = str(item.get("contentid", ""))
        if cid not in seen:
            seen.add(cid)
            deduped.append(item)

    if len(all_items) != len(deduped):
        logger.warning(f"중복 {len(all_items) - len(deduped)}건 제거")

    save_jsonl(list_path, deduped)
    logger.info(f"목록 수집 완료: 총 {len(deduped)}건 (신규 {new_count}건)")
    return deduped


def fetch_all_commons(items: list[dict], common_path) -> None:
    """TourAPI 공통정보(overview) 수집 (이어받기, 429시 중단)"""
    fetched = load_ids(common_path)
    to_fetch = [i for i in items if str(i.get("contentid", "")) not in fetched]

    if not to_fetch:
        logger.info("모든 항목의 공통정보가 이미 수집되었습니다.")
        return

    logger.info(f"공통정보: 전체 {len(items)}건 중 {len(to_fetch)}건 수집 예정")
    session = create_session()
    collected = 0

    for item in tqdm(to_fetch, desc="공통정보 수집"):
        content_id = str(item.get("contentid", ""))
        try:
            common = fetch_common(session, content_id)
        except RateLimitError:
            logger.warning(f"일일 요청 한도 초과! {collected}건 수집 후 중단.")
            logger.info("내일 다시 실행하면 이어서 수집합니다.")
            break
        except TourAPIError as e:
            logger.error(f"실패 [contentid={content_id}]: {e}")
            continue

        # 응답 검증: overview 없으면 경고
        if not common.get("overview"):
            logger.warning(f"overview 누락 [contentid={content_id}] {item.get('title', '')}")

        merged = {**item, **common}
        append_jsonl(common_path, merged)
        collected += 1
        time.sleep(REQUEST_DELAY)

    logger.info(f"이번 세션: {collected}건 수집")
