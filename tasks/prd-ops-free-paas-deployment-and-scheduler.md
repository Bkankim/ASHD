# PRD: Ops (Free PaaS Deployment + Scheduler)

## 1. Introduction/Overview

ASHD v0.1을 **무료 PaaS(0원 운영)** 환경에서 실제로 운영하기 위한 배포/운영/스케줄링 정책을 정의한다.
이 PRD는 “문서 처리 파이프라인은 이미 구현 완료”된 상태를 전제로, **운영 안정성**과 **비용 0원**을 우선한다.

### Current Status / Evidence (근거)

- FastAPI 엔트리포인트는 `app.main:create_app()` 형태로 구성되어 있다.
  - 근거: `app/main.py`
- 헬스체크 `/health` 라우트가 존재한다.
  - 근거: `app/api/routes/health.py`
- 알림 계산 로직 스켈레톤 `generate_daily_alerts()`가 존재한다(아직 TODO 상태).
  - 근거: `app/services/notification_service.py`
- 마스킹 정책(저장 전 + 응답 전)과 `/auth` 예외가 구현되어 있다.
  - 근거: `app/api/middlewares/redaction.py`, `app/core/redaction.py`, `docs/SECURITY_PRIVACY.md`
- 스케줄러 HTTP 엔드포인트는 **현재 없음**.
  - 근거: `app/api/routes/*` 내 `/internal/cron/*` 없음(코드 검색)

## 2. Goals

- 무료 PaaS에서도 **앱이 죽지 않는 운영 구조**를 고정한다.
- 일일 알림 트리거는 **외부 cron → HTTP 호출** 방식으로 단순화한다.
- 운영 환경에서 **민감정보 마스킹과 /auth 예외 정책**을 유지한다.
- 파일 저장/DB 영속성 제약을 **문서로 명시**하고, 기능이 깨지지 않도록 안내한다.

## 3. User Stories

- 운영자는 외부 스케줄러(GitHub Actions 등)로 **일 1회 알림 트리거**를 호출한다.
- 운영자는 헬스체크로 **서비스 상태를 확인**한다.
- 사용자 데이터는 **무료 환경 제약을 이해한 상태**에서 최소 기능이 유지된다.

## 4. Functional Requirements

1) 배포 실행 정책
- 무료 PaaS 기본 실행 커맨드 예시를 문서에 고정한다.
  - `uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}`
  - reload는 **운영 환경에서 사용하지 않는다**.
- `PORT` 환경 변수가 있으면 해당 포트를 사용한다.

2) Cron 트리거 엔드포인트
- `POST /internal/cron/daily-alerts`
  - 헤더: `X-CRON-SECRET` (필수)
  - 인증 실패 시 403 반환
  - 성공 시 `generate_daily_alerts()` 호출 및 요약 결과 반환(민감정보 없이 count 중심)
- 엔드포인트는 **무료 cron 호출**과 궁합이 좋도록 단순하게 설계한다.

3) 무료 PaaS 제약 대응
- 로컬 디스크(uploads/)는 영구 보장이 없음을 문서에 명시한다.
- 이미지 파일이 소실되더라도 API 응답이 **깨지지 않도록** 허용(예: image_path만 남고 파일 접근 실패는 무시).

4) 보안 정책
- `/internal/cron/*`는 반드시 시크릿 토큰으로 보호한다.
- raw_text/parsed_fields/evidence는 **저장 전 + 응답 전 마스킹 유지**.
- `/auth/*`는 마스킹 예외 정책 유지.

5) 문서/운영 가이드
- 배포 환경 변수 목록, PORT 처리, healthcheck, cron 호출 방법을 문서에 추가한다.

## 5. Non-Goals (Out of Scope)

- 유료 DB/스토리지/유료 큐 도입
- RAG/assistant 기능
- 고가용성/멀티 리전 배포
- 복잡한 스케줄러(내부 워커/메시지 큐)

## 6. Design Considerations (Optional)

- 무료 PaaS는 **슬립/콜드스타트**가 가능하므로, 외부 cron 호출이 실패할 수 있다.
- DB는 기본 SQLite 유지하되, `DATABASE_URL` 교체로 Postgres 전환 가능하게 한다.

## 7. Technical Considerations (Optional)

### API / Security

- Cron 엔드포인트는 `X-CRON-SECRET` 헤더 기반으로 보호한다.
- 응답에는 상세 사용자 정보/제품 목록을 포함하지 않는다(요약만).

### Storage

- 업로드 파일은 v0.1에서 로컬 저장을 유지한다.
- 파일이 소실될 수 있음을 문서에 명시하고, 장애로 이어지지 않게 처리한다.

## 8. Success Metrics

- 외부 cron 호출로 `/internal/cron/daily-alerts`가 200을 반환한다.
- 마스킹 정책이 유지되며, /auth 예외가 그대로 동작한다.
- README/DEV_GUIDE/PROJECT_OVERVIEW 문서가 운영 정책과 일치한다.

## 9. Open Questions

- [확실하지 않음] 무료 PaaS의 구체 선택(Render/Fly.io 등)과 스토리지 제약 범위.
- [확실하지 않음] HTTPS/도메인 연결을 어디까지 문서화할지.

### Change Log

- 무료 PaaS 운영 정책과 cron 트리거 설계를 PRD로 분리하여 고정.
- 외부 cron + 시크릿 보호 요구사항을 명시.
- 로컬 디스크 영속성 제약을 리스크로 명시.

### Next Steps (P0 3개)

1) `/internal/cron/daily-alerts` 엔드포인트 추가 + 시크릿 인증.
2) 배포 실행 커맨드/PORT 처리 문서 업데이트.
3) 무료 PaaS 제약(파일 소실/슬립)을 문서에 반영.

### P1/P2 Backlog

- cron 실패 시 재시도/알림(이메일 또는 로깅) 추가.
- 외부 스토리지로 업로드 파일 이관.
- 배포 자동화(최소 CI/CD 파이프라인) 문서화.
