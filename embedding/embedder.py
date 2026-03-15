"""임베딩 텍스트 구성 + 클러스터링"""

import logging
import re
from collections import Counter

import numpy as np
from pathlib import Path
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from .config import (
    OVERVIEW_MAX_CHARS,
    BLOG_SNIPPET_LIMIT,
    BLOG_SNIPPET_DESC_CHARS,
    K_RANGE_MIN,
    K_RANGE_MAX,
    CLUSTER_LABELS,
    CONTENT_TYPES,
)
from .client import get_embeddings

logger = logging.getLogger(__name__)


# ── 텍스트 구성 ──────────────────────────────────


def _clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"&[a-zA-Z]+;|&#\d+;", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def build_embed_text(item: dict) -> str:
    """임베딩용 텍스트 구성: 장소의 본질에 집중"""
    parts = []

    title = item.get("title", "")
    if title:
        parts.append(title)

    addr = item.get("addr1", "")
    if addr:
        addr_parts = addr.split()
        parts.append(" ".join(addr_parts[:2]))

    overview = _clean(item.get("overview", ""))
    if overview:
        parts.append(overview[:OVERVIEW_MAX_CHARS])

    snippets = item.get("blog_snippets", [])
    if snippets:
        blog_texts = []
        for s in snippets[:BLOG_SNIPPET_LIMIT]:
            t = _clean(s.get("title", ""))
            d = _clean(s.get("description", ""))
            blog_texts.append(f"{t} {d[:BLOG_SNIPPET_DESC_CHARS]}")
        parts.append(" ".join(blog_texts))

    return " ".join(parts)


# ── 클러스터링 ───────────────────────────────────


def find_optimal_k(embeddings: np.ndarray) -> int:
    """실루엣 점수로 최적 k 탐색"""
    k_range = range(K_RANGE_MIN, K_RANGE_MAX)
    best_k = K_RANGE_MIN
    best_score = -1

    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(embeddings)
        score = silhouette_score(embeddings, labels, sample_size=min(1000, len(embeddings)))
        logger.info(f"k={k}: silhouette={score:.3f}")
        if score > best_score:
            best_score = score
            best_k = k

    return best_k


def cluster(embeddings: np.ndarray, n_clusters: int) -> tuple[np.ndarray, np.ndarray]:
    """KMeans 클러스터링"""
    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = km.fit_predict(embeddings)
    return labels, km.cluster_centers_


def analyze_clusters(items: list[dict], labels: np.ndarray) -> dict:
    """클러스터별 특성 분석"""
    clusters = {}
    n_clusters = len(set(labels))

    for cluster_id in range(n_clusters):
        members = [items[i] for i in range(len(items)) if labels[i] == cluster_id]

        ct_dist = Counter(int(m.get("contenttypeid", 0)) for m in members)
        tag_freq = Counter()
        sit_freq = Counter()
        for m in members:
            tag_freq.update(m.get("tags", []))
            sit_freq.update(m.get("situation_tags", []))

        blog_words = Counter()
        for m in members:
            for s in m.get("blog_snippets", []):
                title = _clean(s.get("title", ""))
                blog_words.update(w for w in title.split() if len(w) >= 2)

        top_items = sorted(members, key=lambda x: x.get("blog_count", 0), reverse=True)[:5]

        clusters[cluster_id] = {
            "count": len(members),
            "content_types": ct_dist.most_common(5),
            "top_tags": tag_freq.most_common(10),
            "top_situations": sit_freq.most_common(5),
            "top_blog_words": blog_words.most_common(15),
            "representative": [m.get("title", "") for m in top_items],
        }

    return clusters


def apply_cluster_labels(items: list[dict], labels: np.ndarray) -> None:
    """클러스터 ID + vibe 라벨을 items에 적용"""
    for i, item in enumerate(items):
        cid = int(labels[i])
        item["cluster_id"] = cid
        label = CLUSTER_LABELS.get(cid, {"vibe": "기타", "desc": ""})
        item["vibe"] = label["vibe"]
        item["vibe_desc"] = label["desc"]


# ── 저장/로드 ────────────────────────────────────


def save_embeddings(path: Path, embeddings: list[list[float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(str(path), np.array(embeddings))


def load_embeddings(path: Path) -> np.ndarray | None:
    if path.exists():
        return np.load(str(path))
    return None
