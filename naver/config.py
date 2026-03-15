import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# API 키 (.env)
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")

# JSON 설정 로드
_DIR = Path(__file__).parent
_cfg = json.loads((_DIR / "config.json").read_text(encoding="utf-8"))
_regions = json.loads((_DIR.parent / "regions.json").read_text(encoding="utf-8"))

# Naver API 설정
LOCAL_URL = _cfg["local_url"]
BLOG_URL = _cfg["blog_url"]
TIMEOUT = _cfg["timeout"]
REQUEST_DELAY = _cfg["request_delay"]
BLOG_DISPLAY = _cfg["blog_display"]
BLOG_THRESHOLD = _cfg["blog_threshold"]

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
