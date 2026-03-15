# naver — 3단계: 네이버 주소 검증 + 블로그 태깅

네이버 지역검색 API로 카카오 주소를 교차검증하고, 블로그 API로 키워드를 추출하여 태깅한다.

## 파일 구조

```
naver/
├── config.json      설정값 (URL, 딜레이, 블로그 표시건수)
├── config.py        .env API키 로드 + JSON 읽기
├── client.py        네이버 검색 API 호출 (지역 + 블로그)
├── tagger.py        규칙 기반 태깅 + 블로그 키워드 추출
├── profiler.py      상황별 점수 산출 (6가지 프로필)
├── collector.py     검증 + 태깅 오케스트레이션
├── storage.py       JSONL 읽기/쓰기
└── __init__.py      외부 공개 API
```

## 데이터 흐름

```
items_detail.jsonl (2단계 출력)
  ├── 네이버 지역검색 → 카카오 vs 네이버 주소 교차검증
  ├── 네이버 블로그검색 → blog_snippets, blog_count 추가
  ├── 규칙 태깅 → tags (콘텐츠타입 + overview 키워드)
  ├── 블로그 태깅 → tags (분위기/특징 키워드)
  └── 상황 프로파일링 → situation_scores, situation_tags
  → items_detail.jsonl (덮어쓰기)
```

## 두 가지 작업

### 주소 검증 (enrich_with_naver)
카카오 주소와 네이버 주소를 동/리/읍/면 단위로 비교한다.

| 결과 | 의미 |
|------|------|
| match | 동 단위 일치 |
| partial | 구 단위 일치 (동은 다름) |
| mismatch | 불일치 — 로그로 경고 |
| kakao_missing | 카카오 주소 없음 |
| naver_missing | 네이버 결과 없음 |
| both_empty | 둘 다 없음 |

### 태깅 (enrich_with_tags)

**규칙 태그** — 콘텐츠 타입 + overview 키워드:
자연, 역사, 사찰, 카페, 공원, 박물관, 온천, 캠핑, 시장

**블로그 태그** — 블로그 스니펫에서 추출:
가족, 데이트, 혼밥, 산책, 힐링, 야경, 벚꽃, 단풍, 전망, 무료, 포토, 주차, 맛집

**상황 프로필** — 6가지 상황별 점수 (0~1):

| 상황 | 임계값 | 주요 시그널 |
|------|--------|------------|
| 아이동반 | 0.35 | 주차, 유모차, 블로그 키워드, 무료 |
| 데이트 | 0.35 | 블로그 키워드, 카페, 야경, 포토 |
| 혼자여행 | 0.40 | 블로그 키워드, 카페, 산책, 실내, 대중교통 |
| 반려동물 | 0.30 | 블로그 키워드, 야외, 주차 |
| 비오는날 | 0.45 | 실내, 블로그 키워드, 문화시설/쇼핑/음식점 |
| 단체모임 | 0.35 | 블로그 키워드, 음식점/레포츠, 수용인원, 체험 |

## 보강되는 필드

| 필드 | 출처 |
|------|------|
| naver_phone | 네이버 지역검색 |
| naver_category | 네이버 지역검색 |
| naver_address | 네이버 지역검색 |
| naver_road_address | 네이버 지역검색 |
| naver_place_name | 네이버 지역검색 |
| naver_link | 네이버 지역검색 |
| blog_snippets | 네이버 블로그검색 |
| blog_count | 네이버 블로그검색 |
| tags | 규칙 + 블로그 태깅 |
| situation_scores | 상황 프로파일링 |
| situation_tags | 상황 프로파일링 |

## 설정

### config.json

| 필드 | 설명 | 기본값 |
|------|------|--------|
| local_url | 네이버 지역검색 엔드포인트 | local.json URL |
| blog_url | 네이버 블로그검색 엔드포인트 | blog.json URL |
| timeout | 요청 타임아웃(초) | 10 |
| request_delay | 요청 간 대기(초) | 0.5 |
| blog_display | 블로그 검색 결과 수 | 10 |
| blog_threshold | 블로그 태그 최소 등장 횟수 | 3 |
| data_dir | 데이터 저장 루트 | "data" |

### .env

```
NAVER_CLIENT_ID=your_client_id_here
NAVER_CLIENT_SECRET=your_client_secret_here
```
