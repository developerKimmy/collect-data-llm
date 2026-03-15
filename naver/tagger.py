"""키워드 기반 태깅 로직 (규칙 + 블로그)"""

import re
from collections import Counter

from .config import BLOG_THRESHOLD

# ── 콘텐츠 타입 → 기본 태그 ──────────────────────

TYPE_TAGS = {
    12: ["관광지"],
    14: ["문화시설"],
    15: ["축제"],
    25: ["여행코스"],
    28: ["레포츠"],
    32: ["숙박"],
    38: ["쇼핑"],
    39: ["맛집"],
}

# ── overview에서 추출할 세부 태그 ────────────────

DETAIL_TAGS = {
    "자연": ["자연휴양림", "수목원", "습지", "생태공원", "생태", "계곡", "폭포",
             "둘레길", "산책로", "호수", "저수지"],
    "역사": ["유적", "문화재", "사적", "고인돌", "향교", "서원", "왕릉",
             "백제", "고려", "삼국", "의병", "독립", "현충", "순국"],
    "사찰": ["사찰", "법당", "대웅전", "불교", "석탑", "부도", "암자"],
    "카페": ["카페", "커피", "디저트", "베이커리", "브런치"],
    "공원": ["공원", "근린공원", "도시공원", "체육공원"],
    "박물관": ["박물관", "미술관", "갤러리", "전시관", "기념관"],
    "온천": ["온천", "스파", "족욕", "찜질"],
    "캠핑": ["캠핑", "글램핑", "오토캠핑", "캠핑장"],
    "시장": ["시장", "재래시장", "전통시장", "장터"],
}

# ── 블로그에서만 추출할 분위기/특징 태그 ─────────

BLOG_TAGS = {
    "가족": ["가족", "아이와", "아이들", "어린이", "키즈", "가족나들이",
             "아이랑", "아기", "유아"],
    "데이트": ["데이트", "연인", "커플", "로맨틱"],
    "혼밥": ["혼밥", "혼자", "혼술", "1인"],
    "산책": ["산책", "걷기", "트레킹", "트레일"],
    "힐링": ["힐링", "휴식", "명상", "웰니스", "치유"],
    "야경": ["야경", "야간", "일루미네이션", "빛축제", "야간개장"],
    "벚꽃": ["벚꽃", "봄꽃", "벚꽃길", "벚꽃명소"],
    "단풍": ["단풍", "단풍길", "단풍명소", "가을여행"],
    "전망": ["전망", "뷰맛집", "풍경", "일출", "일몰", "노을"],
    "무료": ["무료", "무료입장", "입장료무료"],
    "포토": ["인생샷", "포토", "인스타", "사진명소", "사진맛집", "포토존"],
    "주차": ["주차", "주차장", "주차가능", "무료주차"],
    "맛집": ["맛집", "맛있", "존맛", "메뉴추천", "먹방"],
}


def _normalize(text: str) -> str:
    """HTML 제거 + 소문자"""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"&[a-zA-Z]+;|&#\d+;", " ", text)
    return text.lower()


def tag_by_rules(item: dict) -> list[str]:
    """콘텐츠 타입 + overview 키워드 기반 태그"""
    tags = []

    ct_id = int(item.get("contenttypeid", 0))
    tags.extend(TYPE_TAGS.get(ct_id, []))

    kakao_cat = item.get("kakao_category", "")
    if "카페" in kakao_cat or "커피" in kakao_cat:
        if "카페" not in tags:
            tags.append("카페")

    text = _normalize(" ".join([
        item.get("overview", ""),
        item.get("title", ""),
    ]))

    for tag, keywords in DETAIL_TAGS.items():
        if tag not in tags and any(kw in text for kw in keywords):
            tags.append(tag)

    return tags


def extract_blog_keywords(blog_items: list[dict]) -> list[str]:
    """블로그 제목+설명에서 분위기/특징 태그 추출"""
    if not blog_items:
        return []

    texts = " ".join(
        f"{b.get('title', '')} {b.get('description', '')}"
        for b in blog_items
    )
    text = _normalize(texts)

    found = Counter()
    for tag, keywords in BLOG_TAGS.items():
        count = sum(text.count(kw) for kw in keywords)
        if count >= BLOG_THRESHOLD:
            found[tag] = count

    return [tag for tag, _ in found.most_common()]


def merge_tags(rule_tags: list[str], blog_tags: list[str]) -> list[str]:
    """규칙 태그 + 블로그 태그 합치기 (중복 제거, 순서 유지)"""
    seen = set()
    merged = []
    for tag in rule_tags + blog_tags:
        if tag not in seen:
            seen.add(tag)
            merged.append(tag)
    return merged
