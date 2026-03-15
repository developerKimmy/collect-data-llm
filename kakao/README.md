# kakao — 2단계: 카카오 로컬 API 보강

카카오 로컬 API로 TourAPI 데이터에 전화번호, 카테고리, 주소를 보강한다.

## 파일 구조

```
kakao/
├── config.json      설정값 (URL, 거리 임계값, 타임아웃)
├── config.py        .env API키 로드 + JSON 읽기
├── client.py        카카오 로컬 API 호출 (search_place, extract_info)
├── collector.py     보강 오케스트레이션 (enrich_with_kakao)
├── storage.py       JSONL 읽기/쓰기
└── __init__.py      외부 공개 API
```

## 데이터 흐름

```
items_common.jsonl (1단계 출력)
  → 카카오 로컬 검색 (제목+지역 → 실패 시 주소로 재검색)
  → 좌표 거리 검증 (1km 이내만 매칭)
  → items_detail.jsonl (append)
```

## 보강되는 필드

| 필드 | 설명 |
|------|------|
| kakao_phone | 전화번호 |
| kakao_category | 카테고리 (예: "음식점 > 한식") |
| kakao_place_url | 카카오맵 장소 URL |
| kakao_place_name | 카카오 장소명 |
| kakao_address | 지번 주소 |
| kakao_road_address | 도로명 주소 |
| kakao_lng, kakao_lat | 경도, 위도 |
| addr2 | 비어있으면 카카오 지번 주소로 보완 |

## Failsafe

- **이어받기**: contentid 기준으로 이미 보강된 항목 스킵
- **좌표 검증**: TourAPI 좌표와 카카오 좌표가 1km 초과 시 매칭 거부 + 경고
- **재검색**: 제목+지역으로 실패 시 주소로 재검색
- **응답 검증**: documents 키 없으면 경고
- **로깅**: 매칭 실패 건수 집계

## 설정

### config.json

| 필드 | 설명 | 기본값 |
|------|------|--------|
| search_url | 카카오 로컬 검색 엔드포인트 | keyword.json URL |
| max_distance_km | 좌표 매칭 허용 거리(km) | 1.0 |
| timeout | 요청 타임아웃(초) | 10 |
| data_dir | 데이터 저장 루트 | "data" |

### .env

```
KAKAO_MAP_API_KEY=your_kakao_api_key_here
```
