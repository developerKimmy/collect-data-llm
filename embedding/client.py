"""OpenAI 임베딩 API 클라이언트"""

import logging

from openai import OpenAI

from .config import OPENAI_API_KEY, EMBEDDING_MODEL, BATCH_SIZE

logger = logging.getLogger(__name__)

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if not OPENAI_API_KEY:
            raise RuntimeError("OPEN_AI_API_KEY가 설정되지 않음")
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """OpenAI 임베딩 배치 호출"""
    client = _get_client()
    all_embeddings = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        try:
            resp = client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
            batch_emb = [d.embedding for d in resp.data]
            all_embeddings.extend(batch_emb)
            logger.info(f"임베딩: {min(i + BATCH_SIZE, len(texts))}/{len(texts)}")
        except Exception as e:
            logger.error(f"임베딩 실패 (batch {i}~{i + len(batch)}): {e}")
            raise

    return all_embeddings
