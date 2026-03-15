import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# API 키 (.env)
OPENAI_API_KEY = os.getenv("OPEN_AI_API_KEY", "")

# JSON 설정 로드
_DIR = Path(__file__).parent
_cfg = json.loads((_DIR / "config.json").read_text(encoding="utf-8"))
_regions = json.loads((_DIR.parent / "regions.json").read_text(encoding="utf-8"))

# OpenAI 임베딩 설정
EMBEDDING_MODEL = _cfg["embedding_model"]
BATCH_SIZE = _cfg["batch_size"]
K_RANGE_MIN = _cfg["k_range_min"]
K_RANGE_MAX = _cfg["k_range_max"]
OVERVIEW_MAX_CHARS = _cfg["overview_max_chars"]
BLOG_SNIPPET_LIMIT = _cfg["blog_snippet_limit"]
BLOG_SNIPPET_DESC_CHARS = _cfg["blog_snippet_desc_chars"]

# 클러스터 라벨
CLUSTER_LABELS = {int(k): v for k, v in _cfg["cluster_labels"].items()}

# 콘텐츠 타입 + 지역 코드 (processor에서 사용)
CONTENT_TYPES = {int(k): v for k, v in _cfg["content_types"].items()}
AREA_CODES = _cfg["area_codes"]

# INTRO 필드 라벨 (processor에서 사용)
INTRO_LABELS = {
    "infocenter": "문의및안내", "infocenterfood": "문의및안내",
    "infocenterculture": "문의및안내", "infocenterlodging": "문의및안내",
    "infocenterleports": "문의및안내", "infocentershopping": "문의및안내",
    "infocentertourcourse": "문의및안내",
    "restdate": "쉬는날", "restdatefood": "쉬는날", "restdateculture": "쉬는날",
    "restdateleports": "쉬는날", "restdateshopping": "쉬는날",
    "usetime": "이용시간", "usetimeculture": "이용시간", "usetimeleports": "이용시간",
    "opentimefood": "영업시간", "opentime": "영업시간",
    "parking": "주차시설", "parkingculture": "주차시설", "parkingleports": "주차시설",
    "parkingfood": "주차시설", "parkinglodging": "주차시설", "parkingshopping": "주차시설",
    "parkingfee": "주차요금", "parkingfeeleports": "주차요금",
    "usefee": "이용요금", "usefeeleports": "입장료", "usetimefestival": "이용요금",
    "chkbabycarriage": "유모차대여", "chkbabycarriageculture": "유모차대여",
    "chkbabycarriageleports": "유모차대여", "chkbabycarriageshopping": "유모차대여",
    "chkcreditcard": "신용카드", "chkcreditcardculture": "신용카드",
    "chkcreditcardleports": "신용카드", "chkcreditcardfood": "신용카드",
    "chkcreditcardshopping": "신용카드",
    "chkpet": "애완동물", "chkpetculture": "애완동물",
    "chkpetleports": "애완동물", "chkpetshopping": "애완동물",
    "firstmenu": "대표메뉴", "treatmenu": "취급메뉴",
    "reservationfood": "예약안내", "reservation": "예약안내",
    "reservationlodging": "예약안내",
}

# 지역 설정
AREA_PRESETS = {
    name: {"name": name, **codes}
    for name, codes in _regions["areas"].items()
}
REGION_GROUPS = _regions["groups"]

# 경로
PROJECT_DIR = _DIR.parent.parent


def get_data_dirs(region: str = "daejeon"):
    """지역별 데이터 경로 반환"""
    base = PROJECT_DIR / _cfg["data_dir"] / region
    return base / "raw", base / "processed"
