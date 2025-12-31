# Tasks: PRD Ops (Free PaaS Deployment + Scheduler)

## Relevant Files

- `app/main.py` - 앱 엔트리포인트/라우터 등록.
- `app/api/routes/health.py` - 헬스체크 라우트.
- `app/services/notification_service.py` - 일일 알림 계산 스켈레톤.
- `app/api/middlewares/redaction.py` - 응답 마스킹 정책.
- `app/core/config.py` - 환경 변수 설정.
- `docs/DEV_GUIDE.md` - 실행/운영 가이드.
- `docs/PROJECT_OVERVIEW.md` - v0.1 범위/운영 제약.
- `docs/SYSTEM_ARCHITECTURE.md` - 운영/스케줄링 구조 설명.
- `docs/API_EXAMPLES.md` - cron 호출 예시.
- `README.md` - Quickstart/운영 요약.
- `.env.example` - 배포 환경 변수 예시.

## Notes

- Implemented candidates (근거 확인됨):
  - `/health` 공개 엔드포인트 존재 (`app/api/routes/health.py`)
  - 마스킹 정책 및 `/auth` 예외 유지 (`app/api/middlewares/redaction.py`)
  - `generate_daily_alerts()` 스켈레톤 존재 (`app/services/notification_service.py`)
- Gaps/Questions:
  - `/internal/cron/*` 라우트 없음
  - 운영용 실행 커맨드/PORT 처리 문서화 필요
  - 무료 PaaS 제약(디스크 소실/슬립) 문서 정합성 필요

## Tasks

- [ ] 1.0 배포 실행 방식 고정
  - [x] 1.1 프로덕션 실행 커맨드/PORT 처리 문서화 (파일: `README.md`, `docs/DEV_GUIDE.md`; 검증: 문서 리뷰/rg)
    - 근거: `README.md`에 운영 실행 커맨드/PORT 설명 추가
    - 근거: `docs/DEV_GUIDE.md`에 5.3 운영 실행 섹션 추가
  - [x] 1.2 무료 PaaS 기준 ASGI 실행 방식 확정(uvicorn 단독) 및 문서 반영 (파일: `docs/DEV_GUIDE.md`; 검증: 문서 리뷰)
    - 근거: `docs/DEV_GUIDE.md`에 uvicorn 단독 ASGI 표준/비사용(gunicorn) 명시 및 실행 커맨드 정합

- [ ] 2.0 Cron 트리거 엔드포인트 구현(보안 포함)
  - [x] 2.1 `/internal/cron/daily-alerts` 라우트 추가 및 라우터 등록 (파일: `app/api/routes/cron.py`, `app/main.py`; 검증: pytest/간단 curl)
    - 근거: `app/api/routes/cron.py` 추가, `app/main.py`에 라우터 등록 + curl 501 확인 + pytest 통과
  - [x] 2.2 `CRON_SECRET` 검증 의존성 추가 및 설정/예시 반영 (파일: `app/core/config.py`, `.env.example`, `app/api/dependencies/cron.py`; 검증: pytest 403/501)
    - 근거: `tests/test_cron.py`에서 403/501 검증 + `UV_CACHE_DIR=/home/sweetbkan/ASHD/.uv_cache uv run pytest` 통과
  - [x] 2.3 `generate_daily_alerts()` 호출 + 요약 응답 반환 (파일: `app/api/routes/cron.py`; 검증: pytest)
    - 근거: `tests/test_cron.py`에서 200 응답/processed 확인 + `UV_CACHE_DIR=/home/sweetbkan/ASHD/.uv_cache uv run pytest` 통과
  - [ ] 2.4 문서에 cron 호출 예시 추가 (파일: `docs/DEV_GUIDE.md`, `docs/API_EXAMPLES.md`; 검증: 문서 리뷰)

- [ ] 3.0 무료 PaaS 제약 대응(파일 소실/슬립)
  - [ ] 3.1 업로드 파일 소실 시 graceful 처리 가이드/정책 정리 (파일: `docs/SYSTEM_ARCHITECTURE.md`, `docs/PROJECT_OVERVIEW.md`; 검증: 문서 리뷰)

- [ ] 4.0 운영 문서/체크리스트 정합화
  - [ ] 4.1 배포 환경 변수 목록 정리(특히 PORT, CRON_SECRET) (파일: `.env.example`, `docs/DEV_GUIDE.md`, `README.md`; 검증: 문서 리뷰)

- [ ] 5.0 스모크/테스트 검증
  - [ ] 5.1 cron 엔드포인트 테스트 추가/통과 확인 (파일: `tests/test_cron.py` 또는 기존 테스트; 검증: `UV_CACHE_DIR=/home/sweetbkan/ASHD/.uv_cache uv run pytest`)
