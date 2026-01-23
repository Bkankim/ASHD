# ASHD — 영수증·보증서 관리 MVP (무료 PaaS 데모용)

## 1) 한 줄 소개
- 영수증·택배라벨·보증서를 업로드하면 OCR → 필드 추출(룰+LLM 보완) → 상품/알림 관리까지 이어지는 경량 백엔드.
- 대상: “AS/환불/보증 기간을 놓치기 쉬운 개인 사용자”, 무료 PaaS 환경에서 바로 데모 가능.

## 2) 데모 흐름 한 장 요약
- 입력: 이미지/PDF(≤10MB, PDF 최대 3p) 업로드 → 202 + job_id 즉시 응답
- 처리: 백그라운드 Job에서 Mock/외부 OCR → 룰 기반 필드 파싱 → 부족 시 LLM 보완 → Product 저장
- 출력: Documents/Products 조회, cron 트리거 `/internal/cron/daily-alerts`(X-CRON-SECRET 보호)로 알림 후보 집계
- 스크린샷 자리: `docs/images/demo-*` (필요 시 추가)

## 3) 핵심 기능 / 제한
- 동작: 업로드·OCR(키 없으면 Mock)·필드 추출(룰+LLM 보완)·상품 생성·알림 설정/텔레그램 계정 CRUD·cron 트리거.
- 제한: Swagger 자물쇠(OAuth2 password)는 토큰 입력이 어려워 curl/Postman 권장. 외부 키 없으면 알림 전송은 스킵/요약만.

## 4) 아키텍처(파일 경로 포함)
- Ingest: `/documents/upload` (`app/api/routes/documents.py`) → Job 생성(`app/models/job.py`)
- OCR: `app/ocr/external.py`(Google Vision, 키 없으면 Mock)  
- 필드 추출: 룰 `app/extractors/rule.py` + LLM 보완 `app/extractors/llm.py` (키 없으면 Mock)
- 저장/인덱스: SQLite(`DATABASE_URL`), 모델 `app/models/document.py`, `app/models/product.py`
- API/UI: FastAPI 엔드포인트 `app/main.py`, cron `app/api/routes/cron.py`
- 알림: 계산 `app/services/notification_service.py`, 트리거 `/internal/cron/daily-alerts`(X-CRON-SECRET 헤더)
- 마스킹: `app/core/redaction.py`, 미들웨어 `app/api/middlewares/redaction.py`

## 5) 빠른 실행(Quickstart: 10분 내 데모)
```bash
# 0. 필수: uv 설치(https://github.com/astral-sh/uv), Python 3.12+
uv sync

# 1. 데모(키 없이 Mock OCR/LLM) — 단일 커맨드
bash scripts/demo.sh
# 결과: outputs/demo_result.json, demo DB: outputs/demo.db

# 2. 서버 실행(로컬)
UV_CACHE_DIR=./.uv_cache uv run --active uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```
키를 넣고 실환경 흐름을 보고 싶다면 `.env`에 OCR/LLM/SMTP/Telegram 키를 채운 뒤 다시 실행.

## 6) 설치(로컬)
- 시스템 의존성(apt 예시): `requirements.txt` 참고 (curl, sqlite3 등 경량 패키지)
- Python 의존성: `uv sync` (pyproject.toml 기반)
- 환경설정: `.env.example` 복사 후 필요한 키만 채움(없으면 Mock 경로로 자동 fallback)

## 7) 테스트/품질
```bash
UV_CACHE_DIR=./.uv_cache uv run --active pytest
```
현재 44 passed, Deprecation warning(utcnow, on_event)은 backlog로 유지.

## 8) 보안/프라이버시
- 저장 전/응답 전 이중 마스킹(`raw_text/parsed_fields/evidence/job.error`), `/auth/*` 예외 유지.
- OCR/LLM 키가 없으면 Mock으로 동작해 외부 전송을 피함.
- cron 엔드포인트는 `X-CRON-SECRET` 헤더로 보호.

## 9) Roadmap / 리스크 / 대응
- Roadmap: (1) lifespan 전환 및 utcnow 정리 (2) Swagger 인증 UX 개선 (3) 외부 스토리지(S3/GCS) 옵션 추가
- 리스크: 무료 PaaS 디스크 소실 가능, 외부 키 없을 때 기능 축소, Swagger 인증 불편
- 대응: uploads는 best-effort, 핵심 데이터는 DB 텍스트; Mock 경로 제공; curl 예제 제공

## 10) 10분 발표용 스크립트(예시)
1) 문제: 영수증을 잃어 환불/AS 놓치는 사용자.
2) 해결: 업로드→OCR→룰+LLM 보완→알림으로 기간 관리.
3) 데모: `bash scripts/demo.sh` 로 파이프라인 한 번에 실행, 결과 JSON 제시.
4) 아키텍처: Ingest→OCR/LLM→DB→cron 알림, 파일 소실에도 텍스트 기반 유지.
5) 보안/프라이버시: 이중 마스킹, cron 시크릿.
6) 운영: 무료 PaaS, uvicorn 단독, 외부 스케줄러(cURL/GitHub Actions) 호출.
7) 한계/Next: 디스크 영속성, 경고 정리, 외부 스토리지/Swagger UX 개선.
