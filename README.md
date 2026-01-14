# ASHD

ASHD(Almost Service Handling Disorder)는
AS / 환불 / 보증 관리가 잘 안 되는 사람들을 위한
웹 기반 관리 서비스입니다.

이 프로젝트는 다음과 같은 기능을 목표로 합니다.

- 영수증/택배 라벨/보증서 이미지 업로드
- 구매일, 금액, 구매처, 보증 종료일, 환불 마감일 정리
- 이메일 및 텔레그램 알림으로 AS/환불/보증 기간 리마인드

상세 설계 문서는 docs/ 디렉터리 내 .md 파일들을 참고하세요.

## Quickstart

```bash
uv sync
uv run uvicorn app.main:app --reload
```

## 운영 실행(무료 PaaS 기준)

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

* 운영 환경에서는 `--reload`를 사용하지 않습니다.
* PaaS가 제공하는 `PORT` 환경 변수를 우선 사용합니다.

## 주요 환경 변수(운영 시)

- `PORT` : PaaS가 주는 포트에 바인딩
- `CRON_SECRET` : `/internal/cron/daily-alerts` 호출 시 `X-CRON-SECRET` 헤더로 전달
- `DATABASE_URL`, `SECRET_KEY`
- `OCR_API_URL`, `OCR_API_KEY`, `DOCUMENT_UPLOAD_DIR`
- `LLM_BASE_URL`, `LLM_API_KEY`
- `SMTP_*`, `TELEGRAM_BOT_TOKEN`
- 상세 예시는 `.env.example`, `docs/DEV_GUIDE.md`를 참고하세요.
