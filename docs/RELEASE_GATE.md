# RELEASE_GATE (Step 1 실행 기록)

> 문서 우선순위: AGENTS.md > tasks/prd-*.md > tasks/tasks-prd-*.md > docs/* > code
> 실행/검증은 실제 커맨드 기준이며, 비밀키/토큰은 포함하지 않습니다.

## 1) 서버 기동 확인 (PORT 바인딩)
실행 커맨드:
```bash
env UV_CACHE_DIR=/home/sweetbkan/ASHD/.uv_cache \
  timeout 3s uv run --active uvicorn app.main:app --host 0.0.0.0 --port 8000
```
핵심 출력:
```
Started server process
Application startup complete.
Uvicorn running on http://0.0.0.0:8000
Shutting down
```

## 2) 테스트 (pytest)
실행 커맨드:
```bash
UV_CACHE_DIR=/home/sweetbkan/ASHD/.uv_cache uv run --active pytest
```
요약 결과:
```
44 passed, 151 warnings
```

## 3) 업로드 → Job 폴링 → Product 생성 (TestClient 스모크)
아래 스크립트로 실제 실행 완료:
```bash
env UV_CACHE_DIR=/home/sweetbkan/ASHD/.uv_cache \
  DATABASE_URL=sqlite:///./release_gate.db \
  OCR_API_URL= OCR_API_KEY= \
  LLM_BASE_URL= LLM_API_KEY= \
  CRON_SECRET=test-secret \
  uv run --active python - <<'PY'
import time
from pathlib import Path
from fastapi.testclient import TestClient
from sqlmodel import SQLModel

from app.core.config import get_settings
from app.core.db import engine
from app.main import create_app

get_settings.cache_clear()
app = create_app()

with TestClient(app) as client:
    SQLModel.metadata.create_all(engine)

    email = "release_gate@example.com"
    password = "pw1234"

    client.post("/auth/register", json={"email": email, "password": password})
    login = client.post("/auth/login", json={"email": email, "password": password})

    access_token = login.json().get("access_token")
    headers = {"Authorization": f"Bearer {access_token}"}

    sample_path = Path("tests/KakaoTalk_20260114_193527354.jpg")
    with sample_path.open("rb") as f:
        upload = client.post(
            "/documents/upload",
            headers=headers,
            files={"file": (sample_path.name, f, "image/jpeg")},
        )

    job_id = upload.json().get("job_id")
    for _ in range(10):
        job = client.get(f"/jobs/{job_id}", headers=headers).json()
        if job.get("status") in ("completed", "failed"):
            break
        time.sleep(0.5)

    print("job_status", job.get("status"))
    print("job_error", job.get("error"))

    cron_no = client.post("/internal/cron/daily-alerts")
    cron_wrong = client.post("/internal/cron/daily-alerts", headers={"X-CRON-SECRET": "wrong"})
    cron_ok = client.post("/internal/cron/daily-alerts", headers={"X-CRON-SECRET": "test-secret"})

    print("cron_no", cron_no.status_code)
    print("cron_wrong", cron_wrong.status_code)
    print("cron_ok", cron_ok.status_code)
PY
```
실행 결과 요약:
- 로그인 성공: `login_status 200`
- 업로드 성공: `upload_status 202`
- Job 완료: `job_status completed`, `job_error None`

## 4) Cron 엔드포인트 3케이스
- 시크릿 없음: 403
- 시크릿 오답: 403
- 시크릿 정답: 200

## 5) 성공 기준 체크
- [x] 서버 기동(0.0.0.0:8000) 가능
- [x] pytest 전체 통과
- [x] 업로드 → Job 완료 확인
- [x] cron 3케이스(403/403/200)

> 비밀키/토큰은 문서에 포함하지 않았습니다.

## 7) Step2 재실행 결과 (요약)
- pytest: 44 passed, 151 warnings
- 업로드→job 완료: `job_status completed`, `job_error None`
- cron 3케이스: 403/403/200

## 6) 작업트리 위생 결정(커밋/제외 원칙)
- 커밋 대상: AGENTS.md, docs/RELEASE_GATE.md, handoff/*.md (민감정보 없음 기준), docs/INCONSISTENCIES.md
- 제외 대상: .serena/, handoff/state/*, handoff_ashd_production.zip
- 처리 방식: .gitignore에 .serena/·handoff/state/·handoff_ashd_production.zip 추가


## 8) UI 스모크 체크리스트 (수동)
- [ ] /app/login.html 로그인 성공
- [ ] /app/upload.html 업로드 → job completed → product 이동
- [ ] /app/upload.html PDF 업로드 → job completed 확인
- [ ] /app/product.html 제품 수정 저장
- [ ] /app/settings.html 알림 설정 저장
- [ ] /app/telegram.html 연동 조회/해제 확인

관찰: 이 환경에서는 브라우저 수동 검증을 수행할 수 없어 미실행. 로컬 브라우저에서 확인 필요.
추가: PDF OCR 파서 단위 테스트(`tests/test_ocr_parser.py`)는 통과(실제 UI PDF 업로드는 로컬 확인 필요).
상태: pending (사용자 확인 필요)


## 9) PDF E2E (Mock Vision 응답) 결과
- 파일: tests/쿠팡test.pdf
- 결과: job_status completed, job_error None, product_id 생성 확인
- 방법: TestClient + ExternalOCRClient + files:annotate 중첩 응답 mock (원문/키 미노출)

## 10) Release Gate 정의 (A/B)

### Gate A (항상 실행)
- pytest 전체 통과
- Mock Vision 기반 PDF E2E 통과
  - 근거: `tests/test_ocr_parser.py`, 본 문서의 “PDF E2E (Mock Vision)” 결과

### Gate B (실제 Vision 수동 E2E)
> CI 금지. 배포 전/후 수동 1회만 수행한다.

**Real Vision 전환 조건(코드 근거)**
- `OCR_API_URL`과 `OCR_API_KEY`가 모두 설정되면 `ExternalOCRClient` 사용
- 둘 중 하나라도 없으면 `MockOCRClient` 사용
- 근거: `app/ocr/external.py` → `build_ocr_client`

**필수 환경변수(값은 기록 금지)**
- `OCR_API_URL`, `OCR_API_KEY`
- `SECRET_KEY` (앱 기동 필수)

**실행 커맨드(복붙용, 키/토큰 값은 넣지 말 것)**
```bash
# 서버 기동 (필수 env 주입)
OCR_API_URL=<PLACEHOLDER> \
OCR_API_KEY=<PLACEHOLDER> \
SECRET_KEY=<PLACEHOLDER> \
UV_CACHE_DIR=/home/sweetbkan/ASHD/.uv_cache \
uv run --active uvicorn app.main:app --host 0.0.0.0 --port 8000

# 수동 E2E (별도 터미널)
OCR_API_URL=<PLACEHOLDER> \
OCR_API_KEY=<PLACEHOLDER> \
BASE_URL=http://127.0.0.1:8000 \
FILE_PATH=tests/쿠팡test.pdf \
EMAIL=real-vision@example.com \
PASSWORD=pw1234 \
bash scripts/run_real_vision_e2e.sh
```

**기대 결과(성공 기준)**
- `/documents/upload` → 202 + job_id
- `/jobs/{id}` → status=completed, error=null
- product_id 생성 확인

**실패 시 점검**
- Vision API 활성화 여부/결제 계정/키 제한(HTTP referrer 제한 등)
- OCR_API_URL이 `images:annotate`인지, PDF는 `files:annotate`로 자동 전환되는지
- 네트워크 차단/프록시 여부

> 보안: 키/토큰/원문 텍스트는 로그/문서에 절대 기록하지 않는다.


## 11) 로컬 테스트 PDF 처리
- tests/쿠팡test.pdf 는 저작권/민감 가능성 때문에 커밋하지 않으며, 특정 파일만 gitignore 처리한다.
