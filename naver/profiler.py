"""상황 기반 프로필 스코어링

단편 키워드가 아닌, 사용자 의도(상황)에 맞는 복합 프로필을 생성한다.
예: "가족 주말 나들이" → 아이동반 + 주차 + 야외 + 체험

각 항목에 상황별 점수(0~1)를 부여하고, 임계값 이상이면 태그 부여.
"""


# ── 시그널 추출 ──────────────────────────────────


def _get_parking(item: dict) -> str:
    """주차 가능 여부: 'yes' / 'no' / 'unknown'"""
    for key in ("parking", "parkingculture", "parkingfood",
                "parkingshopping", "parkingleports", "parkinglodging"):
        val = item.get(key, "").strip()
        if val:
            if "불가" in val or "없음" in val:
                return "no"
            if "가능" in val or "있음" in val:
                return "yes"
    return "unknown"


def _get_fee(item: dict) -> str:
    """입장료: 'free' / 'paid' / 'unknown'"""
    for key in ("usefee", "usefeeleports", "usetimefestival"):
        val = item.get(key, "").strip()
        if val:
            if "무료" in val:
                return "free"
            return "paid"
    return "unknown"


def _get_stroller(item: dict) -> str:
    """유모차 대여: 'yes' / 'no' / 'unknown'"""
    for key in ("chkbabycarriage", "chkbabycarriageculture",
                "chkbabycarriageleports", "chkbabycarriageshopping"):
        val = item.get(key, "").strip()
        if val:
            if "가능" in val or "있" in val:
                return "yes"
            return "no"
    return "unknown"


def _is_indoor(item: dict) -> bool:
    """실내 시설 여부"""
    ct_id = int(item.get("contenttypeid", 0))
    if ct_id in (14, 38, 39):
        return True
    text = f"{item.get('overview', '')} {item.get('kakao_category', '')}".lower()
    return any(kw in text for kw in ("실내", "박물관", "미술관", "전시", "도서관", "영화"))


def _blog_keyword_count(item: dict, keywords: list[str]) -> int:
    """블로그 스니펫에서 키워드 등장 횟수"""
    snippets = item.get("blog_snippets", [])
    if not snippets:
        return 0
    text = " ".join(
        f"{s.get('title', '')} {s.get('description', '')}"
        for s in snippets
    ).lower()
    return sum(text.count(kw) for kw in keywords)


def _overview_has(item: dict, keywords: list[str]) -> bool:
    """overview + title에서 키워드 존재 여부"""
    text = f"{item.get('overview', '')} {item.get('title', '')}".lower()
    return any(kw in text for kw in keywords)


# ── 상황 프로필 스코어링 ─────────────────────────


def score_kid_friendly(item: dict) -> float:
    """아이동반 적합도 (0~1)"""
    score = 0.0
    weights_total = 0.0

    parking = _get_parking(item)
    if parking == "yes":
        score += 0.2
    weights_total += 0.2

    stroller = _get_stroller(item)
    if stroller == "yes":
        score += 0.15
    weights_total += 0.15

    kid_kws = ["아이와", "아이랑", "아기", "유아", "어린이", "키즈",
               "가족나들이", "아이들", "놀이터", "체험학습"]
    blog_count = _blog_keyword_count(item, kid_kws)
    if blog_count >= 5:
        score += 0.3
    elif blog_count >= 2:
        score += 0.15
    weights_total += 0.3

    if _overview_has(item, ["어린이", "키즈", "가족", "체험", "놀이"]):
        score += 0.15
    weights_total += 0.15

    ct_id = int(item.get("contenttypeid", 0))
    if ct_id in (12, 14, 28):
        score += 0.1
    weights_total += 0.1

    if _get_fee(item) == "free":
        score += 0.1
    weights_total += 0.1

    return min(score / weights_total, 1.0) if weights_total else 0.0


def score_date(item: dict) -> float:
    """데이트 적합도 (0~1)"""
    score = 0.0
    weights_total = 0.0

    date_kws = ["데이트", "커플", "연인", "로맨틱", "분위기"]
    blog_count = _blog_keyword_count(item, date_kws)
    if blog_count >= 4:
        score += 0.35
    elif blog_count >= 2:
        score += 0.2
    weights_total += 0.35

    ct_id = int(item.get("contenttypeid", 0))
    kakao_cat = item.get("kakao_category", "")
    if ct_id == 39 or "카페" in kakao_cat:
        score += 0.15
    weights_total += 0.15

    if _overview_has(item, ["야경", "야간", "조명", "분위기", "경치", "전망"]):
        score += 0.2
    weights_total += 0.2

    photo_kws = ["인생샷", "포토", "인스타", "사진명소", "포토존"]
    if _blog_keyword_count(item, photo_kws) >= 2:
        score += 0.15
    weights_total += 0.15

    if _blog_keyword_count(item, ["산책", "드라이브", "코스"]) >= 2:
        score += 0.15
    weights_total += 0.15

    return min(score / weights_total, 1.0) if weights_total else 0.0


def score_solo(item: dict) -> float:
    """혼자 여행 적합도 (0~1)"""
    score = 0.0
    weights_total = 0.0

    solo_kws = ["혼자", "혼밥", "혼술", "1인", "솔로"]
    blog_count = _blog_keyword_count(item, solo_kws)
    if blog_count >= 3:
        score += 0.3
    elif blog_count >= 1:
        score += 0.15
    weights_total += 0.3

    ct_id = int(item.get("contenttypeid", 0))
    kakao_cat = item.get("kakao_category", "")
    if "카페" in kakao_cat or ct_id == 39:
        score += 0.2
    weights_total += 0.2

    if _overview_has(item, ["산책", "둘레길", "공원", "도서관", "박물관"]):
        score += 0.25
    weights_total += 0.25

    if _is_indoor(item):
        score += 0.15
    weights_total += 0.15

    if _overview_has(item, ["지하철", "역", "버스", "도보"]):
        score += 0.1
    weights_total += 0.1

    return min(score / weights_total, 1.0) if weights_total else 0.0


def score_pet_friendly(item: dict) -> float:
    """반려동물 동반 적합도 (0~1)"""
    score = 0.0
    weights_total = 0.0

    pet_kws = ["반려", "애견", "펫", "강아지", "멍멍이", "반려견", "댕댕이",
               "애견동반", "펫프렌들리"]
    blog_count = _blog_keyword_count(item, pet_kws)
    if blog_count >= 4:
        score += 0.4
    elif blog_count >= 2:
        score += 0.25
    elif blog_count >= 1:
        score += 0.1
    weights_total += 0.4

    if _overview_has(item, ["반려", "애견", "펫", "동물"]):
        score += 0.25
    weights_total += 0.25

    if _overview_has(item, ["공원", "산책", "숲", "호수", "둘레길"]):
        score += 0.2
    weights_total += 0.2

    if _get_parking(item) == "yes":
        score += 0.15
    weights_total += 0.15

    return min(score / weights_total, 1.0) if weights_total else 0.0


def score_rainy_day(item: dict) -> float:
    """비오는 날 적합도 (0~1)"""
    score = 0.0
    weights_total = 0.0

    if _is_indoor(item):
        score += 0.4
    weights_total += 0.4

    indoor_kws = ["실내", "비오는날", "우천", "실내데이트", "실내놀이"]
    blog_count = _blog_keyword_count(item, indoor_kws)
    if blog_count >= 3:
        score += 0.3
    elif blog_count >= 1:
        score += 0.15
    weights_total += 0.3

    ct_id = int(item.get("contenttypeid", 0))
    if ct_id in (14, 38, 39):
        score += 0.2
    weights_total += 0.2

    if _get_parking(item) == "yes":
        score += 0.1
    weights_total += 0.1

    return min(score / weights_total, 1.0) if weights_total else 0.0


def score_group(item: dict) -> float:
    """단체/친구 모임 적합도 (0~1)"""
    score = 0.0
    weights_total = 0.0

    group_kws = ["단체", "친구", "모임", "회식", "워크숍", "동호회", "동창"]
    blog_count = _blog_keyword_count(item, group_kws)
    if blog_count >= 4:
        score += 0.3
    elif blog_count >= 2:
        score += 0.15
    weights_total += 0.3

    ct_id = int(item.get("contenttypeid", 0))
    if ct_id in (28, 39):
        score += 0.2
    weights_total += 0.2

    if _overview_has(item, ["단체", "수용", "단체석", "대형"]):
        score += 0.2
    weights_total += 0.2

    if _get_parking(item) == "yes":
        score += 0.15
    weights_total += 0.15

    if _overview_has(item, ["체험", "레포츠", "래프팅", "짚라인"]):
        score += 0.15
    weights_total += 0.15

    return min(score / weights_total, 1.0) if weights_total else 0.0


# ── 프로필 생성 ──────────────────────────────────

PROFILES = {
    "아이동반": (score_kid_friendly, 0.35),
    "데이트": (score_date, 0.35),
    "혼자여행": (score_solo, 0.4),
    "반려동물": (score_pet_friendly, 0.3),
    "비오는날": (score_rainy_day, 0.45),
    "단체모임": (score_group, 0.35),
}


def build_profile(item: dict) -> dict:
    """항목의 상황별 점수 + 태그 생성"""
    scores = {}
    situation_tags = []

    for name, (scorer, threshold) in PROFILES.items():
        score = round(scorer(item), 2)
        scores[name] = score
        if score >= threshold:
            situation_tags.append(name)

    return {
        "situation_scores": scores,
        "situation_tags": situation_tags,
    }
