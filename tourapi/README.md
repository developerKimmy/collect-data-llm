# tourapi — 1단계: TourAPI 데이터 수집

한국관광공사 TourAPI에서 관광지 목록과 공통정보(overview)를 수집한다.
데이터 변환 없이 API 응답을 그대로 저장한다.

## 파일 구조

```
tourapi/
├── config.json      설정값 (URL, 딜레이, 콘텐츠타입, 데이터경로)
├── config.py        .env API키 로드 + JSON 읽기
├── client.py        API 호출 + 응답 파싱
├── collector.py     수집 오케스트레이션
├── storage.py       JSONL 읽기/쓰기
└── __init__.py      외부 공개 API
```

## 데이터 흐름

```
TourAPI areaBasedList2
  → items_list.jsonl (지역 × 8개 콘텐츠타입 전수 조회)

TourAPI detailCommon2
  → items_common.jsonl (list 항목 + overview 등 공통정보 머지)
```

## 수집 대상 콘텐츠 타입

| ID | 이름 |
|----|------|
| 12 | 관광지 |
| 14 | 문화시설 |
| 15 | 축제공연행사 |
| 25 | 여행코스 |
| 28 | 레포츠 |
| 32 | 숙박 |
| 38 | 쇼핑 |
| 39 | 음식점 |

## Failsafe

### 이어받기
- **목록 수집**: (지역, 시군구, 콘텐츠타입) 조합 단위로 완료 여부 판별. 이미 수집된 조합은 스킵.
- **공통정보**: contentid 기준으로 수집 완료 항목 스킵. 429 에러 시 중단 후 다음 실행에서 이어서 수집.

### 응답 검증
- API 응답에 `response`, `body` 키 없으면 에러
- `contentid` 누락 항목 제외
- `overview` 누락 시 경고
- contentid 기준 중복 제거

### 재시도
- API 호출 실패 시 지수 백오프로 최대 3회 재시도
- 429 (일일 한도 초과)는 재시도 없이 즉시 중단

### 로깅
- `logging` 모듈 사용 (info/warning/error)

## 설정

### config.json

| 필드 | 설명 | 기본값 |
|------|------|--------|
| base_url | TourAPI 엔드포인트 | KorService2 URL |
| request_delay | 요청 간 대기(초) | 0.5 |
| num_of_rows | 페이지당 항목 수 | 1000 |
| max_retries | 최대 재시도 횟수 | 3 |
| content_types | 수집 대상 콘텐츠 타입 | 8개 |
| data_dir | 데이터 저장 루트 | "data" |

### .env

```
TOUR_API_KEY=your_decoding_key_here
```

## 출력 데이터

### items_list.jsonl

TourAPI areaBasedList2 응답 그대로. 주요 필드:

| 필드 | 예시 |
|------|------|
| contentid | "3074319" |
| contenttypeid | "12" |
| title | "갈마공원" |
| addr1 | "대전광역시 서구 한밭대로 664" |
| mapx, mapy | 경도, 위도 |
| firstimage | 대표 이미지 URL |
| cat1, cat2, cat3 | 분류 코드 |
| areacode, sigungucode | 지역 코드 |

### items_common.jsonl

items_list + detailCommon2 응답 머지. 추가되는 주요 필드:

| 필드 | 설명 |
|------|------|
| overview | 관광지 설명 (HTML) |
| homepage | 홈페이지 URL |
| tel, telname | 전화번호 |
| infocenter | 문의처 |
| restdate | 쉬는날 |
| usetime | 이용시간 |
| parking | 주차 정보 |
