"""네이버 API로 주소 검증 + 블로그 태깅"""

import logging
import re
import time

from tqdm import tqdm

from .config import BLOG_DISPLAY, REQUEST_DELAY
from .client import search_place, extract_info, search_blog
from .tagger import tag_by_rules, extract_blog_keywords, merge_tags
from .profiler import build_profile
from .storage import load_jsonl, save_jsonl

logger = logging.getLogger(__name__)


# ── 주소 검증 유틸 ────────────────────────────────


def _short_addr(addr: str) -> str:
    """주소에서 시/도 + 구/군 까지만 추출"""
    parts = addr.split()
    return " ".join(parts[:2]) if len(parts) >= 2 else addr


def _extract_dong(addr: str) -> str:
    """주소에서 동/리/읍/면 추출"""
    match = re.search(r"(\S+[동리읍면가])\b", addr)
    return match.group(1) if match else ""


def _search_naver(item: dict) -> dict:
    """네이버 지역검색으로 장소 검색"""
    title = item.get("title", "")
    addr1 = item.get("addr1", "")
    short = _short_addr(addr1)
    query = f"{title} {short}".strip() if short else title

    place = search_place(query)
    if not place and addr1:
        place = search_place(addr1)

    return extract_info(place) if place else {}


def _verify_match(item: dict, naver: dict) -> str:
    """카카오 vs 네이버 주소 비교로 매칭 검증"""
    kakao_addr = item.get("kakao_address", "")
    naver_addr = naver.get("naver_address", "")

    if not kakao_addr and not naver_addr:
        return "both_empty"
    if not kakao_addr:
        return "kakao_missing"
    if not naver_addr:
        return "naver_missing"

    kakao_dong = _extract_dong(kakao_addr)
    naver_dong = _extract_dong(naver_addr)

    if kakao_dong and naver_dong and kakao_dong == naver_dong:
        return "match"

    kakao_gu = _short_addr(kakao_addr)
    naver_gu = _short_addr(naver_addr)
    if kakao_gu and naver_gu and kakao_gu == naver_gu:
        return "partial"

    return "mismatch"


# ── 주소 검증 + 보강 ──────────────────────────────


def enrich_with_naver(detail_path) -> None:
    """네이버 지역검색으로 더블체크 + 보강"""
    items = load_jsonl(detail_path)
    if not items:
        logger.warning("더블체크할 데이터가 없습니다.")
        return

    logger.info(f"네이버 더블체크: {len(items)}건")
    stats = {"match": 0, "partial": 0, "mismatch": 0,
             "kakao_missing": 0, "naver_missing": 0, "both_empty": 0}
    mismatches = []
    filled_phone = 0

    for item in tqdm(items, desc="네이버 더블체크"):
        naver = _search_naver(item)

        if naver:
            for k, v in naver.items():
                item[k] = v

            if not item.get("tel", "").strip() and not item.get("kakao_phone", "").strip():
                phone = naver.get("naver_phone", "")
                if phone:
                    filled_phone += 1

            result = _verify_match(item, naver)
        else:
            result = "naver_missing"

        stats[result] += 1
        if result == "mismatch":
            mismatches.append({
                "title": item.get("title", ""),
                "addr1": item.get("addr1", ""),
                "kakao": item.get("kakao_address", ""),
                "naver": naver.get("naver_address", ""),
            })

    save_jsonl(detail_path, items)

    logger.info(f"검증 결과: 일치={stats['match']} 부분일치={stats['partial']} "
                f"불일치={stats['mismatch']} 카카오만={stats['kakao_missing']} "
                f"네이버만={stats['naver_missing']} 둘다없음={stats['both_empty']} "
                f"전화번호추가={filled_phone}")

    if mismatches:
        logger.warning(f"불일치 {len(mismatches)}건:")
        for m in mismatches[:20]:
            logger.warning(f"  {m['title']} | addr1={m['addr1']} | kakao={m['kakao']} | naver={m['naver']}")


# ── 태깅 (규칙 + 블로그) ──────────────────────────


def _build_blog_query(item: dict) -> str:
    """블로그 검색 쿼리 생성"""
    title = item.get("title", "")
    addr1 = item.get("addr1", "")
    short = _short_addr(addr1)
    return f"{title} {short}".strip() if short else title


def enrich_with_tags(detail_path) -> None:
    """규칙 태깅 + 네이버 블로그 키워드로 태그 부여"""
    items = load_jsonl(detail_path)
    if not items:
        logger.warning("태깅할 데이터가 없습니다.")
        return

    need_blog = [i for i in items if "blog_snippets" not in i]

    if need_blog:
        logger.info(f"블로그 수집: {len(need_blog)}건")
        for item in tqdm(need_blog, desc="블로그 수집"):
            query = _build_blog_query(item)
            blog = search_blog(query, display=BLOG_DISPLAY)
            item["blog_snippets"] = blog["items"]
            item["blog_count"] = blog["total"]
            time.sleep(REQUEST_DELAY)

    for item in items:
        rule_tags = tag_by_rules(item)
        blog_tags = extract_blog_keywords(item.get("blog_snippets", []))
        item["tags"] = merge_tags(rule_tags, blog_tags)

        profile = build_profile(item)
        item["situation_scores"] = profile["situation_scores"]
        item["situation_tags"] = profile["situation_tags"]

    save_jsonl(detail_path, items)

    # 통계 로그
    tag_counts = {}
    for item in items:
        for t in item.get("tags", []):
            tag_counts[t] = tag_counts.get(t, 0) + 1
    no_tags = sum(1 for i in items if not i.get("tags"))
    logger.info(f"태깅 완료: {len(items) - no_tags}건 태그됨, {no_tags}건 태그 없음")

    sit_counts = {}
    for item in items:
        for t in item.get("situation_tags", []):
            sit_counts[t] = sit_counts.get(t, 0) + 1
    logger.info(f"상황 태그: {dict(sorted(sit_counts.items(), key=lambda x: -x[1]))}")
