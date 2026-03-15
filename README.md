# collect-data-llm

한국 관광 데이터 수집 파이프라인. 외부 API에서 관광지 데이터를 수집하고 보강하여 RAG용 데이터셋을 만든다.

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

## 설치

```bash
pip install requests python-dotenv tqdm openai scikit-learn numpy
```

## 환경 변수

프로젝트 루트(이 레포의 상위 디렉토리)에 `.env` 파일을 만들고 API 키를 설정한다.

```
TOUR_API_KEY=your_tour_api_key
KAKAO_MAP_API_KEY=your_kakao_api_key
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret
OPEN_AI_API_KEY=your_openai_api_key
```

## 데이터 저장 경로

데이터는 이 레포의 상위 디렉토리 기준 `data/{region}/`에 저장된다.

```
../data/{region}/
├── raw/
│   ├── items_list.jsonl       ← 1단계: 목록
│   ├── items_common.jsonl     ← 1단계: 공통정보
│   └── items_detail.jsonl     ← 2~3단계: 보강+태깅
└── processed/
    ├── embeddings.npy         ← 4단계: 임베딩 벡터
    └── tourism_chunks.jsonl   ← 4단계: RAG 청크
```

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

## 디렉토리 구조

```
├── regions.json          지역 코드 + 그룹 설정
├── tourapi/              1단계: TourAPI 수집
│   ├── config.json       API 설정
│   ├── config.py         환경 변수 + JSON 로드
│   ├── client.py         API 호출 + 응답 파싱
│   ├── collector.py      수집 오케스트레이션
│   └── storage.py        JSONL 읽기/쓰기
├── kakao/                2단계: 카카오 보강
│   ├── config.json
│   ├── config.py
│   ├── client.py         카카오 로컬 API 호출
│   ├── collector.py      보강 + 좌표 검증
│   └── storage.py
├── naver/                3단계: 네이버 검증 + 태깅
│   ├── config.json
│   ├── config.py
│   ├── client.py         네이버 지역/블로그 API 호출
│   ├── collector.py      주소 검증 + 태깅 오케스트레이션
│   ├── tagger.py         규칙 태깅 + 블로그 키워드 추출
│   ├── profiler.py       6가지 상황 프로파일링
│   └── storage.py
└── embedding/            4단계: 임베딩 + 클러스터링
    ├── config.json
    ├── config.py
    ├── client.py         OpenAI 임베딩 API 호출
    ├── embedder.py       텍스트 구성 + 클러스터링
    ├── processor.py      RAG용 텍스트 청크 생성
    ├── collector.py      임베딩 + 청크 오케스트레이션
    └── storage.py
```
