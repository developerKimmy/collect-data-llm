"""임베딩 + 클러스터링 + RAG 청크 생성 오케스트레이션"""

import logging

import numpy as np

from .config import CONTENT_TYPES
from .embedder import (
    build_embed_text, find_optimal_k, cluster,
    analyze_clusters, apply_cluster_labels,
    save_embeddings, load_embeddings,
)
from .processor import process_all
from .storage import load_jsonl, save_jsonl

logger = logging.getLogger(__name__)


def run_embedding(detail_path, embed_path) -> None:
    """임베딩 생성 + 클러스터링 + vibe 라벨 적용"""
    items = load_jsonl(detail_path)
    if not items:
        logger.warning("임베딩할 데이터가 없습니다.")
        return

    logger.info(f"전체: {len(items)}건")

    # 1. 임베딩
    embeddings = load_embeddings(embed_path)
    if embeddings is not None and len(embeddings) == len(items):
        logger.info(f"기존 임베딩 로드: {embeddings.shape}")
    else:
        logger.info("임베딩 생성 중...")
        texts = [build_embed_text(item) for item in items]
        from .client import get_embeddings
        emb_list = get_embeddings(texts)
        embeddings = np.array(emb_list)
        save_embeddings(embed_path, emb_list)
        logger.info(f"임베딩 완료: {embeddings.shape}")

    # 2. 최적 k 탐색
    logger.info("최적 클러스터 수 탐색...")
    best_k = find_optimal_k(embeddings)
    logger.info(f"최적 k = {best_k}")

    # 3. 클러스터링
    labels, centers = cluster(embeddings, best_k)
    logger.info(f"클러스터링 완료: {best_k}개 그룹")

    # 4. 분석 로그
    cluster_info = analyze_clusters(items, labels)
    for cid, info in sorted(cluster_info.items()):
        ct_names = [(CONTENT_TYPES.get(ct, "기타"), cnt) for ct, cnt in info["content_types"]]
        logger.info(
            f"클러스터 {cid} ({info['count']}건): "
            f"콘텐츠={', '.join(f'{n}({c})' for n, c in ct_names)} | "
            f"대표={', '.join(info['representative'][:3])}"
        )

    # 5. 클러스터 라벨 적용 + 저장
    apply_cluster_labels(items, labels)
    save_jsonl(detail_path, items)
    logger.info("클러스터 ID + vibe 라벨 저장 완료")


def run_process(detail_path, chunks_path) -> None:
    """RAG용 텍스트 청크 생성"""
    items = load_jsonl(detail_path)
    if not items:
        logger.warning("처리할 데이터가 없습니다.")
        return

    chunks = process_all(items)
    save_jsonl(chunks_path, chunks)
    logger.info(f"RAG 청크 생성 완료: {len(chunks)}건 → {chunks_path}")
