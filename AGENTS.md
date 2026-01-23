# Repository Guidelines

## 프로젝트 구조 & 모듈 구성
- `app/`: FastAPI 백엔드(라우트/서비스/모델/스키마/코어 설정).
- `docs/`: 설계/운영 문서(PROJECT_OVERVIEW, SYSTEM_ARCHITECTURE, DEV_GUIDE 등).
- `tests/`: pytest 테스트(`test_*.py`).
- `tasks/`: PRD 및 작업 체크리스트.
- `scripts/`: 데모/유틸 스크립트(예: `scripts/demo.sh`).
- `outputs/`: 데모 결과(JSON 등). 민감정보 저장 금지.

## 빌드/테스트/개발 명령 (uv 기준)
- 의존성 설치: `uv sync`
- 로컬 실행: `uv run --active uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}`
- 테스트: `UV_CACHE_DIR=./.uv_cache uv run --active pytest`
- 데모: `bash scripts/demo.sh` (키 없으면 Mock OCR/LLM 경로)

## 코딩 스타일 & 네이밍
- Python 4-space, 타입 힌트 권장.
- 핵심 로직에는 한국어로 “무엇/왜” 주석을 남긴다.
- 함수는 한 가지 책임, 숨은 부작용 최소화.

## 테스트 가이드
- 프레임워크: pytest.
- 파일 규칙: `tests/test_*.py`, 함수는 `test_` 접두어.
- 외부 서비스 호출 금지(모킹/스텁 필수).

## 커밋/PR 가이드 (Conventional Commits)
- 형식: `<type>(선택 scope): <description>`
  - 예: `feat(api): add cron endpoint`, `fix(auth): handle invalid token`
- PR에는 요약/검증 커맨드/범위(In/Out) 명시, 문서/테스트 정합 유지.

## 보안 & 구성
- 실제 키/토큰 커밋 금지. `.env.example`만 예시 작성.
- OCR raw_text/parsed_fields/evidence는 마스킹 유지.
- 멀티테넌시: 모든 CRUD는 `current_user.id`로 스코프 강제, 타 사용자 접근은 404 은닉.

## 문서 우선순위
- 결정 순서: `AGENTS.md > tasks/prd-*.md > tasks/tasks-prd-*.md > docs/* > code`.
- 충돌 시 상위 문서를 기준으로 하위 문서를 먼저 정합한다.
