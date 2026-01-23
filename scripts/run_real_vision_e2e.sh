#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
EMAIL="${EMAIL:-real-vision@example.com}"
PASSWORD="${PASSWORD:-pw1234}"
FILE_PATH="${FILE_PATH:-tests/쿠팡test.pdf}"

if [[ -z "${OCR_API_URL:-}" || -z "${OCR_API_KEY:-}" ]]; then
  echo "ERROR: OCR_API_URL/OCR_API_KEY 환경변수가 필요합니다." >&2
  exit 1
fi

if [[ ! -f "$FILE_PATH" ]]; then
  echo "ERROR: FILE_PATH not found: $FILE_PATH" >&2
  exit 1
fi

register() {
  curl -s -X POST "$BASE_URL/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" >/dev/null || true
}

login() {
  curl -s -X POST "$BASE_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}"
}

register
TOKEN=$(login | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

JOB_ID=$(curl -s -X POST "$BASE_URL/documents/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@$FILE_PATH;type=application/pdf" | \
  python -c "import sys, json; print(json.load(sys.stdin)['job_id'])")

for i in $(seq 1 45); do
  RESP=$(curl -s "$BASE_URL/jobs/$JOB_ID" -H "Authorization: Bearer $TOKEN")
  STATUS=$(echo "$RESP" | python -c "import sys, json; print(json.load(sys.stdin).get('status'))")
  ERROR=$(echo "$RESP" | python -c "import sys, json; print(json.load(sys.stdin).get('error'))")
  PRODUCT_ID=$(echo "$RESP" | python -c "import sys, json; print(json.load(sys.stdin).get('product_id'))")
  echo "try=$i status=$STATUS error=$ERROR product_id=$PRODUCT_ID"
  if [[ "$STATUS" == "completed" || "$STATUS" == "failed" ]]; then
    break
  fi
  sleep 2

done

if [[ "$STATUS" != "completed" ]]; then
  echo "FAILED: job_status=$STATUS" >&2
  exit 2
fi

curl -s "$BASE_URL/products/$PRODUCT_ID" -H "Authorization: Bearer $TOKEN" >/dev/null

echo "SUCCESS: job completed, product_id=$PRODUCT_ID"