import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# API 키 (.env)
TOUR_API_KEY = os.getenv("TOUR_API_KEY", "")

# JSON 설정 로드
_DIR = Path(__file__).parent
_cfg = json.loads((_DIR / "config.json").read_text(encoding="utf-8"))
_regions = json.loads((_DIR.parent / "regions.json").read_text(encoding="utf-8"))

# TourAPI 설정
TOUR_BASE_URL = _cfg["base_url"]
MOBILE_OS = _cfg["mobile_os"]
MOBILE_APP = _cfg["mobile_app"]
RESPONSE_TYPE = _cfg["response_type"]
REQUEST_DELAY = _cfg["request_delay"]
NUM_OF_ROWS = _cfg["num_of_rows"]
MAX_RETRIES = _cfg["max_retries"]

# 콘텐츠 타입 (JSON 키는 문자열이므로 int로 변환)
CONTENT_TYPES = {int(k): v for k, v in _cfg["content_types"].items()}

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
