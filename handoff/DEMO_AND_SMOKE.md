# DEMO & SMOKE (복붙 실행 세트)

## 1) 로컬 실행 (uvicorn)
```bash
UV_CACHE_DIR=./.uv_cache \
uv run --active uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

## 2) 회원가입/로그인 → 토큰 발급
```bash
EMAIL="user@example.com"
PW="pw1234"

# 회원가입 (이미 있으면 409 가능)
curl -s -X POST "http://127.0.0.1:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"${PW}\"}"

# 로그인 → access_token
TOKEN=$(curl -s -X POST "http://127.0.0.1:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"${PW}\"}" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

echo "TOKEN=${TOKEN}" 
```

## 3) 문서 업로드 → 202 + job_id
```bash
FILE="</absolute/path/to/receipt.jpg>"  # 이미지/PDF 가능
RESP=$(curl -s -X POST "http://127.0.0.1:8000/documents/upload" \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "file=@${FILE}" \
  -H "accept: application/json")

echo "$RESP"
JOB_ID=$(echo "$RESP" | python3 -c "import sys,json;print(json.load(sys.stdin)['job_id'])")
```

## 4) Job 상태 폴링
```bash
for i in {1..10}; do
  J=$(curl -s "http://127.0.0.1:8000/jobs/${JOB_ID}" \
    -H "Authorization: Bearer ${TOKEN}")
  STATUS=$(echo "$J" | python3 -c "import sys,json;print(json.load(sys.stdin).get('status'))")
  ERROR=$(echo "$J"  | python3 -c "import sys,json;print(json.load(sys.stdin).get('error'))")
  echo "try=${i} status=${STATUS} error=${ERROR}"
  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then break; fi
  sleep 2
 done
```

## 5) Products 조회
```bash
curl -s "http://127.0.0.1:8000/products" \
  -H "Authorization: Bearer ${TOKEN}"
```

## 6) Cron 트리거 호출 (/internal/cron/daily-alerts)
```bash
CRON_SECRET="<PLACEHOLDER>"

# 시크릿 없음 → 403
curl -i -X POST "http://127.0.0.1:8000/internal/cron/daily-alerts"

# 시크릿 틀림 → 403
curl -i -X POST "http://127.0.0.1:8000/internal/cron/daily-alerts" \
  -H "X-CRON-SECRET: wrong"

# 시크릿 정상 → 200
curl -i -X POST "http://127.0.0.1:8000/internal/cron/daily-alerts" \
  -H "X-CRON-SECRET: ${CRON_SECRET}"
```

## 7) 테스트
```bash
UV_CACHE_DIR=./.uv_cache uv run --active pytest
```
