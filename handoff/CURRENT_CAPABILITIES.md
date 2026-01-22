# CURRENT_CAPABILITIES (백엔드 구현 요약)

## 문서 업로드/처리
- 업로드(이미지+PDF) → 202 + job_id 즉시 응답
- 백그라운드 Job에서 OCR → 룰 기반 파싱 → 필수 필드 누락 시 LLM 보완 → Product 저장
- 업로드 제한: 10MB, PDF 최대 3페이지(초과 페이지 무시 + job.error 경고)

## 데이터 저장/정합
- OCR 결과 텍스트(raw_text) 저장
- parsed_fields/evidence 저장 및 마스킹 적용
- 멀티테넌시: current_user.id로 스코프, 타 사용자 접근은 404 은닉

## 알림/스케줄링
- 외부 스케줄러가 `/internal/cron/daily-alerts` 호출
- X-CRON-SECRET 헤더로 보호
- 이메일/텔레그램 설정이 없는 경우 skip/no-op

## 보안/프라이버시
- raw_text/parsed_fields/evidence/job.error는 저장 전 마스킹
- 응답 직전 마스킹 미들웨어 적용 (`/auth/*` 예외)

## v0.1 제외
- assistant/RAG 기반 자연어 질의/요약은 제외
- 단, 필드 추출 보완용 LLM은 포함

## 테스트
- pytest 전체 통과(최근: 44 passed, 151 warnings)
- 주요 테스트: `tests/test_documents.py`, `tests/test_cron.py`, `tests/test_redaction*.py`
