# DEV_GUIDE.md

## 1. 개발 환경 개요

ASHD는 **uv + FastAPI + SQLModel**을 기반으로 하는 단일 웹 애플리케이션입니다.
이 문서는 로컬 개발 환경을 빠르게 준비하고, 서버/배치 작업을 실행하는 방법을 정의합니다.

* 언어: Python 3.10 이상
* 패키지/실행 관리: `uv`
* 웹 프레임워크: FastAPI
* ORM/모델: SQLModel
* DB (v0.1): SQLite (파일 기반, sync)

---

## 2. 사전 준비 사항 (로컬 머신)

### 2.1 필수 설치 항목

1. **Python 3.10+**

   * `python --version`으로 버전 확인
2. **uv**

   * 패키지/가상환경 관리 도구

```bash
# uv 설치
pip install uv

# 설치 확인
uv --version
```

3. (선택) Git

```bash
# 리포 클론 예시
git clone <your-ashd-repo-url> ASHD
cd ASHD
```

---

## 3. 의존성 설치

### 3.1 uv 기반 설치

프로젝트 루트( `pyproject.toml` 이 위치한 디렉토리 )에서 다음 명령을 실행합니다.

```bash
# 프로젝트 의존성 설치 + 가상환경 자동 생성
uv sync
```

이 명령은:

* `pyproject.toml`을 읽어서 필요한 패키지들을 설치하고,
* ASHD 전용 가상환경을 자동으로 관리합니다.

> 주의: 별도 `pip install -r requirements.txt` 는 사용하지 않습니다.
> 의존성 추가/업데이트도 모두 `uv`를 통해 수행합니다.

표준 개발 실행 커맨드(프로젝트 루트에서 실행):

```bash
uv sync
uv run uvicorn app.main:app --reload
```

---

## 4. 환경 변수 설정

민감 정보(API 키, SMTP 계정, 텔레그램 토큰 등)는 **코드에 직접 작성하지 않고**,
`.env` 파일 또는 환경 변수로 주입합니다.

또한 OCR 텍스트 등에는 민감정보가 포함될 수 있어, 저장/응답 전에 마스킹됩니다.
자세한 정책은 `docs/SECURITY_PRIVACY.md`를 참고하세요.

응답 마스킹 정책 요약:

- JSON 응답만 마스킹합니다.
- `/auth/*` 응답은 마스킹 예외입니다.
- 스트리밍/파일 응답은 미들웨어에서 스킵됩니다.
- prod 환경에서는 테스트용 엔드포인트가 등록되지 않습니다.
- Set-Cookie 중복 헤더는 보존하며, content-type은 1개만 유지합니다.
- JSON 파싱에 실패하면 응답 바디를 변경하지 않고 그대로 반환합니다.
- 키 이름으로 마스킹 예외를 두지 않고, 경로(`/auth/*`) 단위로만 예외를 둡니다.

### 4.1 예시 `.env` 구조

프로젝트 루트에 `.env` 파일을 생성하고, 아래와 유사하게 값을 채웁니다.

```env
# 예시: 기본 설정
APP_ENV=local
APP_DEBUG=true
PORT=8000                  # PaaS가 주는 포트를 주입 (운영 시 필수)

# DB 설정 (v0.1: sync SQLite 예시, 운영 시 PostgreSQL URL로 교체)
DATABASE_URL=sqlite:///./ashd.db

# 민감정보 마스킹 설정 (라벨 없는 카드번호 후보까지 탐지할지 여부)
REDACTION_STRICT=false

# cron 보호 시크릿 (외부 스케줄러 호출 시 필수)
CRON_SECRET=

# 이메일 (SMTP) 설정 예시
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your_smtp_username
SMTP_PASSWORD=your_smtp_password
SMTP_FROM=ashd@example.com

# LLM/RAG-lite 설정 예시 (키가 없으면 Mock 동작)
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your_api_key
LLM_MODEL=gpt-4o-mini
LLM_DAILY_QUOTA=20
LLM_CACHE_TTL_MINUTES=1440
RAG_TOP_K=5
ASSISTANT_ALERTS_ENABLED=false

# OCR 외부 API 설정 예시 (Google Vision, 키가 없으면 Mock OCR 동작)
OCR_API_URL=https://vision.googleapis.com/v1/images:annotate
OCR_API_KEY=your_ocr_api_key
OCR_TIMEOUT_SECONDS=15
DOCUMENT_UPLOAD_DIR=uploads

# 텔레그램 봇 설정 예시
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

> 실제 값은 사용자가 직접 채워야 하며, 이 리포지토리에 커밋되지 않도록 `.gitignore`에 `.env`가 포함되어 있어야 합니다.

OCR 응답 파싱 정책(요약):

- Google Vision `images:annotate` 응답의 `fullTextAnnotation.text`를 우선 사용합니다.
- `fullTextAnnotation`이 비어 있으면 `textAnnotations[0].description`을 fallback으로 사용합니다.

문서 업로드 정책(요약):

- 업로드 파일은 이미지 또는 PDF만 지원합니다.
- 파일 크기 제한: **10MB 초과는 413(Payload Too Large)**로 거부합니다.
- PDF는 **최대 3페이지까지만 OCR 처리**하며, 3p 초과는 무시되고 `job.error`에 경고가 기록됩니다.

### 4.2 설정 로딩

* `app/core/config.py` 에서 Pydantic Settings 등을 통해 위 환경 변수를 로딩합니다.
* 코드에서 직접 `os.environ[...]` 를 남발하지 않고, 설정 객체를 통해 접근하는 것을 기본 원칙으로 합니다.
* 예시는 `.env.example`를 참고하고, 실제 값은 개발자가 직접 채워야 합니다.

---

## 5. 개발 서버 실행 방법

### 5.1 FastAPI 서버 실행

프로젝트 루트에서:

```bash
uv run uvicorn app.main:app --reload
```

* `uv run` : ASHD 전용 가상환경 안에서 명령을 실행
* `uvicorn app.main:app --reload` : FastAPI 앱을 개발 모드로 실행 (코드 변경 시 자동 재시작)

### 5.2 동작 확인

서버가 정상 실행되면 브라우저에서 다음 주소로 접속합니다.

* 헬스체크:
  `http://localhost:8000/health`

* API 문서(Swagger UI):
  `http://localhost:8000/docs`

정상적으로 `{ "status": "ok" }` 등의 응답이 나오고,
Swagger UI에서 엔드포인트 목록이 표시되면 개발 서버가 올바르게 동작하는 것입니다.

### 5.3 운영 실행(무료 PaaS 기준)

v0.1 무료 PaaS 운영 기준에서 **ASGI 서버는 uvicorn 단독 실행을 표준으로 고정**합니다.
gunicorn(또는 다른 프로세스 매니저) 기반 구성은 v0.1 문서에 포함하지 않습니다.

무료 PaaS 환경에서는 포트가 고정되지 않을 수 있으므로, `PORT` 환경 변수를 사용하는 방식을 권장합니다.

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

* 운영 환경에서는 `--reload`를 사용하지 않습니다.
* PaaS가 제공하는 `PORT` 환경 변수가 있으면 해당 포트로 바인딩합니다.
* uvicorn 단독 실행은 무료 PaaS에서 **설정 최소화/운영 단순화**를 우선하기 위함입니다.

---

## 6. DB 초기화 및 마이그레이션 (초기 버전 가이드)

> v0.1에서는 단순성을 위해, 별도의 마이그레이션 도구 없이 SQLModel의 `create_all` 방식 등으로 스키마를 생성할 수 있습니다.
> 기본은 sync SQLite(`sqlite:///./ashd.db`)이며, 운영에서 PostgreSQL을 쓰려면 `.env`의 `DATABASE_URL`만 교체하면 됩니다.

### 6.1 DB 초기화 스크립트 예시

(실제 구현 시) `app/db_init.py`와 같은 스크립트를 만들어 사용할 수 있습니다.

예시 개념:

```python
# app/db_init.py (개념 예시 코드)

from sqlmodel import SQLModel
from app.core.database import engine


def init_db() -> None:
    """DB 스키마를 생성하는 초기화 함수입니다.
    
    초기에 테이블을 모두 생성해 두기 위해 사용합니다.
    실제 운영 단계에서는 Alembic 등 마이그레이션 도구로 대체할 수 있습니다.
    """

    SQLModel.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
```

이후, 프로젝트 루트에서 다음과 같이 실행할 수 있습니다.

```bash
uv run python app/db_init.py
```

> 실제 `database.py`/`engine` 구조 등은 구현 시점에 맞추어 이 문서를 보완해야 합니다.

### 6.2 테스트 DB와 세션 격리

* 테스트는 `tests/conftest.py`에서 별도 SQLite 파일로 엔진을 생성하고, `get_session` 의존성을 override하여 실제 DB(`ashd.db`)와 격리합니다.
* TestClient를 사용해 API 레벨 테스트를 수행하며, 각 테스트는 깨끗한 세션을 사용합니다.
* 운영/개발 요청 처리에서는 `app/core/db.py`의 `get_session` 의존성이 요청마다 세션을 열고 닫습니다.

테스트 실행 시 UV 캐시 권한 문제가 발생한다면 아래처럼 캐시 디렉터리를 지정할 수 있습니다.

```bash
UV_CACHE_DIR=/home/sweetbkan/ASHD/.uv_cache uv run pytest
```

---

## 7. Daily Alert 배치 작업 실행

v0.1에서 Daily Alert 배치 작업은 **하루 1회 수동/스케줄 실행**을 가정합니다.

### 7.1 엔트리 포인트 스케치

(실제 구현 파일명 예시) `app/run_daily_notifications.py`:

```python
# app/run_daily_notifications.py (개념 예시 코드)

from app.services.notification_service import generate_daily_alerts
from app.services.email_service import send_email
from app.services.telegram_service import send_telegram_message


async def run_daily_notifications() -> None:
    """하루치 보증/환불 알림을 생성하고, 이메일/텔레그램으로 발송하는 배치 작업입니다."""

    alerts = await generate_daily_alerts()

    for alert in alerts:
        # 이메일 발송
        if alert.email:
            subject, body = render_email_template(alert)
            await send_email([alert.email], subject, body)

        # 텔레그램 발송 (사용자별 chat_id 조회 필요)
        # chat_id = ...
        # text = render_telegram_message(alert)
        # await send_telegram_message(chat_id, text)


if __name__ == "__main__":
    import asyncio

    asyncio.run(run_daily_notifications())
```

위 개념 코드에 맞춰 실제 구현을 진행한 후,
프로젝트 루트에서 다음과 같이 실행할 수 있습니다.

```bash
uv run python app/run_daily_notifications.py
```

### 7.2 cron 등으로 스케줄링 (운영 환경)

무료 PaaS 환경에서는 **외부 cron이 HTTP로 호출**하는 방식을 권장합니다.

* 설정 위치: `CRON_SECRET` 환경 변수(예: PaaS 환경 변수 설정)
* 호출 엔드포인트: `POST /internal/cron/daily-alerts`

예시(로컬/운영 공통):

```bash
curl -X POST "https://<your-domain>/internal/cron/daily-alerts" \\
  -H "X-CRON-SECRET: <cron-secret>"
```

* CRON_SECRET이 없거나 틀리면 403을 반환합니다.
* 성공 시 200과 요약 JSON을 반환합니다.

GitHub Actions로 매일 1회 호출하고 싶다면 아래 기준을 권장합니다.

* 워크플로우 예시: `.github/workflows/daily-alerts.yml`
* Secrets: `DEPLOY_URL`, `CRON_SECRET`

---

## 8. 테스트 실행 가이드 (초기)

> 아직 구체적인 테스트 구조가 정해지지 않았다면, 아래는 기본 권장 사항입니다.

### 8.1 pytest 기반 테스트

1. `pyproject.toml`에 `pytest` 의존성이 추가되어 있다고 가정합니다.
2. 테스트 파일은 `tests/` 디렉토리 하위에 배치합니다.

예시 구조:

```text
.
└── tests/
    ├── __init__.py
    ├── test_health.py
    └── test_notifications.py
```

실행 방법:

```bash
uv run pytest
```

* `tests/` 하위에 헬스체크/인증/제품/알림/텔레그램 연동에 대한 API 테스트가 있습니다.
* 테스트 실행 시 테스트용 SQLite DB를 사용하므로, 로컬 개발 DB는 변경되지 않습니다.

테스트가 정착되면, CI(예: GitHub Actions)에서 `uv run pytest`를 그대로 사용할 수 있습니다.

---

## 9. 의존성 추가/업데이트 규칙

새로운 패키지를 추가해야 할 때는 **반드시 `uv`를 사용**합니다.

### 9.1 패키지 추가 예시

```bash
# 예: httpx를 추가하고 싶을 때
uv add httpx
```

* `pyproject.toml` 및 `uv.lock`가 자동으로 갱신됩니다.
* 수동으로 `pyproject.toml`만 수정하는 것은 피하고, 가능하면 `uv add`를 우선 사용합니다.

### 9.2 패키지 업데이트 예시

```bash
# 예: 모든 패키지 업데이트 (필요 시)
uv sync --upgrade
```

> 대규모 업데이트 전에는 브랜치 분리 후 테스트를 충분히 수행하는 것을 권장합니다.

---

## 10. 개발 워크플로 요약

1. 리포 클론

   * `git clone` → `cd ASHD`
2. uv 설치 확인

   * `uv --version`
3. 의존성 설치

   * `uv sync`
4. `.env` 작성

   * DB/SMTP/텔레그램 설정 값 채우기
5. DB 초기화 (필요한 경우)

   * `uv run python app/db_init.py`
6. 개발 서버 실행

   * `uv run uvicorn app.main:app --reload`
7. Daily Alert 배치 수동 테스트

   * `uv run python app/run_daily_notifications.py`
8. 테스트 실행 (있다면)

   * `uv run pytest`

이 과정을 따르면, 새로운 개발자 또는 에이전트도 ASHD 프로젝트를 빠르게 실행하고 기능을 개발할 수 있습니다.
