# ENV Keys (인수인계용)

아래는 `.env.example` 기준 정리입니다. 실제 키/토큰은 절대 커밋하지 않습니다.

## 필수 (로컬/운영 공통)
- APP_ENV: 실행 환경 구분 (예: local/dev/prod)
- APP_DEBUG: 디버그 모드 여부
- PORT: PaaS 포트 (예: 8000)
- DATABASE_URL: 기본 sqlite, 운영 시 Postgres URL 가능
- SECRET_KEY: JWT 서명용 시크릿
- CRON_SECRET: `/internal/cron/daily-alerts` 보호용 (헤더 X-CRON-SECRET)

## OCR/LLM (선택이지만 기능에 영향)
- OCR_API_URL: Google Vision OCR 엔드포인트
- OCR_API_KEY: Google Cloud API Key
- OCR_TIMEOUT_SECONDS: OCR 요청 타임아웃(초)
- LLM_BASE_URL: OpenAI 호환 API base URL
- LLM_API_KEY: LLM API 키
- LLM_MODEL: 기본 모델명

## 업로드/저장
- DOCUMENT_UPLOAD_DIR: 업로드 파일 저장 경로(예: uploads)

## 알림 채널 (선택)
- SMTP_HOST / SMTP_PORT / SMTP_USERNAME / SMTP_PASSWORD / SMTP_FROM
- TELEGRAM_BOT_TOKEN

## 예시 포맷
```
APP_ENV=local
APP_DEBUG=true
PORT=8000
DATABASE_URL=sqlite:///./ashd.db
SECRET_KEY=<PLACEHOLDER>
CRON_SECRET=<PLACEHOLDER>
OCR_API_URL=https://vision.googleapis.com/v1/images:annotate
OCR_API_KEY=<PLACEHOLDER>
LLM_BASE_URL=<PLACEHOLDER>
LLM_API_KEY=<PLACEHOLDER>
LLM_MODEL=gpt-4o-mini
```
