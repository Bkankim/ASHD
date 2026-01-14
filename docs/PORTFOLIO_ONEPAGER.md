# ASHD Portfolio One-Pager

## What
영수증·택배라벨·보증서를 업로드하면 OCR → 필드 추출(룰+LLM 보완) → 상품 저장 → 알림 트리거까지 처리하는 무료 PaaS 친화 백엔드. 업로드 202+job_id 응답, 백그라운드 Job에서 OCR/보완/저장을 수행한다.

## Why (Pain points)
1) 영수증 분실로 환불/AS 기한을 놓침  
2) 이메일/텔레그램 등 채널별 알림 설정 번거로움  
3) 무료/저사양 환경에서 돌릴 수 있는 경량 파이프라인 필요

## How (Pipeline)
- Ingest: `/documents/upload` → job 생성  
- OCR: Google Vision 호환(키 없으면 Mock) `app/ocr/external.py`  
- Postprocess: 룰 기반 `app/extractors/rule.py` + LLM 보완 `app/extractors/llm.py`  
- Storage: SQLite (Document/Product/NotificationSettings 등)  
- Notification: `/internal/cron/daily-alerts` (X-CRON-SECRET) → `app/services/notification_service.py`  
- Diagram 텍스트: Ingest → OCR → 룰/LLM → DB → cron 트리거 → 이메일/텔레그램 전송

## Proof (샘플 출력)
`outputs/demo_result.json` 예시:
```json
{
  "job": {"status": "completed", "product_id": 3},
  "products": [{"title": "LLM-보완-제품", "store": "LLM-상점"}],
  "documents": [{"title": "demo-sample.jpg", "raw_text": "상호: 테스트마트 ..."}]
}
```

## Engineering Decisions (5)
1) 무료 PaaS 기준: uvicorn 단독, 외부 스케줄러 호출(cURL/GitHub Actions)  
2) OCR/LLM: 키 없으면 Mock 경로로 자동 전환(네트워크/비용 절약)  
3) 마스킹: 저장 전/응답 전 이중 적용, `/auth` 예외만 유지  
4) 파일 소실 대비: uploads는 best-effort, 핵심 데이터는 DB 텍스트 기반  
5) CRUD 멀티테넌시: 모든 쿼리에 user_id 스코프 강제, 타 사용자 접근은 404 은닉

## Limits & Next
- 한계: Swagger 인증 UX 불편, utcnow/lifespan 경고, 로컬 파일 영속성 약함  
- Next: (1) lifespan 전환 및 경고 정리 (2) 외부 스토리지(S3/GCS) 옵션 (3) cron 호출용 GitHub Actions 워크플로우 샘플 추가
