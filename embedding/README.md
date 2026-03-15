# embedding — 4단계: 임베딩 + 클러스터링 + RAG 청크

OpenAI 임베딩으로 벡터를 생성하고, KMeans 클러스터링으로 취향 그룹을 만들고, RAG용 텍스트 청크를 생성한다.

## 파일 구조

```
embedding/
├── config.json      설정값 (모델, 배치, k범위, 클러스터 라벨, 콘텐츠타입)
├── config.py        .env API키 로드 + JSON 읽기
├── client.py        OpenAI 임베딩 API 호출
├── embedder.py      텍스트 구성 + 클러스터링 + 분석
├── processor.py     RAG용 텍스트 청크 생성
├── collector.py     임베딩 + 클러스터링 + 청크 오케스트레이션
├── storage.py       JSONL 읽기/쓰기
└── __init__.py      외부 공개 API
```

## 데이터 흐름

```
items_detail.jsonl (3단계 출력)
  ├── 임베딩 텍스트 구성 (제목 + 주소 + 개요 + 블로그)
  ├── OpenAI text-embedding-3-small → embeddings.npy
  ├── KMeans 클러스터링 → cluster_id
  ├── vibe 라벨 매핑 → vibe, vibe_desc
  │   → items_detail.jsonl (덮어쓰기)
  │
  └── RAG 청크 생성 (텍스트 + 메타데이터)
      → tourism_chunks.jsonl
```

## 두 가지 작업

### 임베딩 + 클러스터링 (run_embedding)

1. 항목별 텍스트 구성 → OpenAI 임베딩 (배치 100건씩)
2. 실루엣 점수로 최적 k 탐색 (기본 6~15)
3. KMeans 클러스터링
4. 클러스터별 특성 분석 (콘텐츠타입, 태그, 블로그 키워드)
5. vibe 라벨 매핑 (config.json의 cluster_labels)

### RAG 청크 생성 (run_process)

raw 데이터를 `{id, text, metadata}` 형태로 변환:
- **text**: HTML 제거, 헤더/주소/개요/연락처/상세정보를 읽기 좋은 텍스트로 조합
- **metadata**: 콘텐츠타입, 좌표, 지역, 카테고리 등 검색/필터용

## 보강되는 필드

| 필드 | 설명 |
|------|------|
| cluster_id | KMeans 클러스터 번호 |
| vibe | 취향 라벨 (예: "대전도심문화") |
| vibe_desc | 취향 설명 |

## 출력 파일

### embeddings.npy
- numpy 배열, shape: (항목수, 임베딩 차원)
- text-embedding-3-small 기준 1536차원

### tourism_chunks.jsonl
```json
{
  "id": "3074319",
  "text": "[관광지] 갈마공원\n주소: 대전광역시...\n개요: ...",
  "metadata": {"content_type": "관광지", "title": "갈마공원", ...}
}
```

## 설정

### config.json

| 필드 | 설명 | 기본값 |
|------|------|--------|
| embedding_model | OpenAI 임베딩 모델 | text-embedding-3-small |
| batch_size | 임베딩 배치 크기 | 100 |
| k_range_min/max | 클러스터 k 탐색 범위 | 6~16 |
| overview_max_chars | 임베딩용 개요 최대 글자수 | 800 |
| cluster_labels | 클러스터 → vibe 매핑 | 8개 |
| content_types | 콘텐츠 타입 코드 → 이름 | 8개 |
| area_codes | 지역 코드 → 이름 | 17개 |
| data_dir | 데이터 저장 루트 | "data" |

### .env

```
OPEN_AI_API_KEY=your_openai_api_key_here
```
