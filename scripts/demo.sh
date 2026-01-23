#!/usr/bin/env bash
set -euo pipefail

# ASHD demo: Mock OCR/LLM 경로로 전체 파이프라인 실행(TestClient 기반)
# 요구: uv(https://github.com/astral-sh/uv) + Python 3.12+, 로컬에서 네트워크/키 없이 실행 가능

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

export UV_CACHE_DIR="${UV_CACHE_DIR:-$ROOT_DIR/.uv_cache}"
export DATABASE_URL="${DATABASE_URL:-sqlite:///./outputs/demo.db}"
# 키를 비워두면 Mock OCR/LLM 사용, 채워두면 실제 호출
export OCR_API_URL="${OCR_API_URL:-}"
export OCR_API_KEY="${OCR_API_KEY:-}"
export LLM_BASE_URL="${LLM_BASE_URL:-}"
export LLM_API_KEY="${LLM_API_KEY:-}"

mkdir -p outputs

PY_CMD=("uv" "run" "--active" "python" "-")

"${PY_CMD[@]}" <<'PY'
import json, os, time
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import create_app
from sqlmodel import SQLModel
from app.core.db import engine

# 샘플 파일: 기본은 tests 폴더 이미지, 없으면 임시 텍스트 생성
sample = Path(os.environ.get("DEMO_FILE", "tests/KakaoTalk_20260114_193527354.jpg"))
if not sample.exists():
    sample.parent.mkdir(parents=True, exist_ok=True)
    sample.write_text("샘플 텍스트 영수증\n금액: 12000원\n구매일: 2024-01-10")
mime = "application/pdf" if sample.suffix.lower() == ".pdf" else "image/jpeg"

app = create_app()
SQLModel.metadata.create_all(engine)
client = TestClient(app)

email = "demo@example.com"
password = "demo1234"
client.post("/auth/register", json={"email": email, "password": password})
token = client.post("/auth/login", json={"email": email, "password": password}).json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

resp = client.post(
    "/documents/upload",
    headers=headers,
    files={"file": (sample.name, sample.read_bytes(), mime)},
)
resp.raise_for_status()
job_id = resp.json()["job_id"]

job_resp = {}
for _ in range(12):
    job_resp = client.get(f"/jobs/{job_id}", headers=headers).json()
    if job_resp.get("status") in {"completed", "failed"}:
        break
    time.sleep(0.5)

docs_call = client.get("/documents", headers=headers)
docs_resp = docs_call.json() if docs_call.status_code == 200 else {"detail": "documents route unavailable"}
products_resp = client.get("/products", headers=headers).json()

out = {
    "job": job_resp,
    "documents": docs_resp,
    "products": products_resp,
    "notes": "키가 없으면 Mock OCR/LLM 결과가 저장됩니다.",
}
Path("outputs/demo_result.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

print("=== Demo Summary ===")
print(f"Job status: {job_resp.get('status')}, product_id: {job_resp.get('product_id')}")
print(f"Documents: {len(docs_resp)}, Products: {len(products_resp)}")
print("Result saved to outputs/demo_result.json")
PY
