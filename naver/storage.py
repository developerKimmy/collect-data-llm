"""JSONL 파일 읽기/쓰기"""

import json
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    """JSONL 파일 로드"""
    if not path.exists():
        return []

    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return items


def save_jsonl(path: Path, items: list[dict]) -> None:
    """JSONL 파일로 저장 (덮어쓰기)"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def append_jsonl(path: Path, item: dict) -> None:
    """JSONL 파일에 한 줄 추가"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")


def load_ids(path: Path, key: str = "contentid") -> set[str]:
    """JSONL에서 특정 키의 값 집합 로드"""
    return {str(item.get(key, "")) for item in load_jsonl(path)}
