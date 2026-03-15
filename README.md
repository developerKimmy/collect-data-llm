# collect-data

관광 데이터 수집 파이프라인. 외부 API에서 데이터를 수집하고 보강하여 RAG용 데이터셋을 만든다.

## 파이프라인 단계

```
tourapi/     →  kakao/      →  naver/      →  embedding/
목록+공통정보    전화/주소보강    주소검증+태깅    임베딩+클러스터링
```

| 단계 | 디렉토리 | 입력 | 출력 | API 제한 |
|------|---------|------|------|---------|
| 1 | `tourapi/` | - | items_list.jsonl, items_common.jsonl | 1,000건/일 |
| 2 | `kakao/` | items_common.jsonl | items_detail.jsonl | 무제한 |
| 3 | `naver/` | items_detail.jsonl | items_detail.jsonl (덮어쓰기) | 25,000건/일 |
| 4 | `embedding/` | items_detail.jsonl | embeddings.npy, tourism_chunks.jsonl | 토큰 과금 |

## 지역 설정

`regions.json`에서 관리한다. 새 도시를 추가하려면 areas에 지역 정보를 넣고 groups에 그룹을 만들면 된다.

```json
{
  "areas": {
    "전주": {"area_code": "37", "sigungu_code": "12"}
  },
  "groups": {
    "jeonju": ["전주"]
  }
}
```

## 데이터 저장 경로

```
data/{region}/
├── raw/
│   ├── items_list.jsonl       ← 1단계: 목록
│   ├── items_common.jsonl     ← 1단계: 공통정보
│   └── items_detail.jsonl     ← 2~3단계: 보강+태깅
└── processed/
    ├── embeddings.npy         ← 4단계: 임베딩 벡터
    └── tourism_chunks.jsonl   ← 4단계: RAG 청크
```

## 공통 모듈

- `regions.json` — 지역 코드, 그룹 설정
- 각 단계의 `storage.py` — JSONL 읽기/쓰기 (추후 공통 모듈로 분리 가능)
