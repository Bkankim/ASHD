# PRD: Document Processing (Upload + OCR + LLM + Jobs)

## 1. Introduction/Overview

ASHD v0.1에서 **문서 업로드 → Job 생성(202 + job_id) → 외부 OCR → 룰 기반 필드 추출 → 필요 시 LLM 보완 추출 → Document/Product 업데이트 → Job 완료**까지의 파이프라인을 정의한다. 이 PRD는 **현재 구현된 코드/테스트를 근거로 최신화**하며, 무료 PaaS 제약(타임아웃/리소스) 하에서 안정적으로 동작하도록 요구사항을 정리한다.

### Current Status / Evidence (근거)

- 업로드 엔드포인트 `/documents/upload`는 **202 + job_id**를 반환한다.
  - 근거: `app/api/routes/documents.py`, `app/schemas/document.py`
- Job 조회 `/jobs/{id}`는 **status/error/document_id/product_id/created_at/updated_at**를 반환한다.
  - 근거: `app/api/routes/jobs.py`, `app/schemas/job.py`
- Job 상태 전이: `pending` → `processing` → `completed` 또는 `failed`.
  - 근거: `app/services/document_processing.py`
- OCR은 외부 API(현재 Google Cloud Vision) 기본, 키가 없으면 Mock fallback.
  - 근거: `app/ocr/external.py` (`build_ocr_client`), `docs/DEV_GUIDE.md`
- LLM 보완 추출은 **필수 필드 누락 시만** 수행.
  - 근거: `app/services/document_processing.py`의 `REQUIRED_FIELDS`/`needs_llm`
- LLM은 Solar(OpenAI compatible) 기반, 키가 없으면 Mock fallback.
  - 근거: `app/extractors/llm.py` (`build_llm_extractor`)
- raw_text/parsed_fields/evidence/job.error는 **저장 전 + 응답 전 마스킹** 적용.
  - 근거: `app/services/document_processing.py`, `app/api/middlewares/redaction.py`, `docs/SECURITY_PRIVACY.md`
- 테스트 통과 확인됨.
  - 근거: `tests/test_documents.py`, 실행 커맨드: `UV_CACHE_DIR=/home/sweetbkan/ASHD/.uv_cache uv run pytest`

## 2. Goals

- 업로드 요청은 빠르게 반환(202 + job_id)하고, 무거운 OCR/추출은 백그라운드 처리한다.
- 외부 OCR + 룰 기반 추출 + LLM 보완 추출을 통해 핵심 필드를 안정적으로 확보한다.
- Document/Product/Job 업데이트 타이밍과 상태 전이를 명확히 정의한다.
- 무료 PaaS 제약(타임아웃/리소스)을 고려해 동기 처리/로컬 OCR을 배제한다.
- 민감정보(raw_text 등)가 DB/응답/로그에 원문으로 남지 않도록 마스킹 정책을 적용한다.

## 3. User Stories

- 사용자는 영수증/보증서 이미지를 업로드하고 즉시 job_id를 받는다.
- 사용자는 job_id로 처리 상태를 조회하고 완료 시 제품 정보가 자동 생성/연결되었음을 확인한다.
- 키가 없거나 실패가 발생해도 Mock fallback을 통해 기본 흐름은 유지된다.

## 4. Functional Requirements

1) 업로드 요청/응답
- `POST /documents/upload`
  - 입력: **이미지 + PDF** 파일 업로드(multipart).
  - 응답: **202 + job_id/document_id/status**.
- 파일 크기 제한: **10MB 초과는 413(Payload Too Large)로 거부**.
- PDF 처리: **최대 3페이지까지만 OCR 후 텍스트를 합쳐 처리**.
  - 3p 초과는 **초과 페이지 무시 + 경고 메시지를 job.error에 축약 기록(실패 처리 아님)**으로 처리한다.
  - 대안(전체 페이지 처리)은 Open Questions에 남긴다.

2) Job 상태 조회
- `GET /jobs/{id}`
  - 응답 스키마: `DocumentJobRead` (id/status/error/document_id/product_id/created_at/updated_at)
  - 소유자 검증(user_id 스코프 필수)
- 상태 전이: `pending` → `processing` → `completed` 또는 `failed`.

3) OCR 호출/응답 파싱
- 외부 OCR API(현재 Google Cloud Vision)를 기본으로 사용.
- OCR 응답 포맷 변화에 대비해 **어댑터/파서 레이어**를 둔다.
- OCR 실패 시:
  - Job 상태는 `failed`로 전환.
  - 에러 메시지는 저장 전 마스킹.
  - 키가 없을 경우 Mock OCR로 fallback하여 파이프라인 유지.

4) 필드 추출 규칙
- 1차: 룰 기반 추출(`extract_fields_with_rules`).
- 2차: **필수 필드 누락 시에만** LLM 보완 추출.
- 필수 필드: `title`, `purchase_date`, `amount`, `store`.

5) 저장 모델 및 업데이트 규칙
- Document: 업로드 즉시 생성, `raw_text/parsed_fields/evidence`는 저장 전 마스킹.
- Product: **항상 새 Product 생성**(현재 동작 유지).
- Document.product_id는 생성된 Product로 연결.
- Job: 상태/에러/연결 정보 업데이트.

6) 마스킹 정책 적용 시점
- 저장 전: `raw_text`, `parsed_fields`, `evidence`, `job.error` 마스킹.
- 응답 전: JSON 응답 마스킹 미들웨어 적용(/auth 제외).

7) 권한/에러 응답
- 모든 문서/Job API는 인증 필요(Authorization Bearer 토큰).
- 401: 미인증, 404: 소유자 불일치/없는 리소스, 413/422: 파일 크기/유효성.

## 5. Non-Goals (Out of Scope)

- 로컬 OCR(서버 리소스 제약으로 v0.1 제외).
- **자연어 질의/RAG 검색/벡터DB 운영**(v0.2 이후).
- 고비용 인프라(유료 큐/워커) 의존.

## 6. Design Considerations (Optional)

- 업로드 즉시 응답 후 비동기 처리 구조로 타임아웃을 회피한다.
- PDF는 최대 3페이지 제한으로 처리 비용을 제어한다.
- RAG 업그레이드 대비 구조만 선반영(Document/Chunk 등 스키마 유지).

## 7. Technical Considerations (Optional)

### Data Model / Storage

- Document: raw_text/parsed_fields/evidence 보관(마스킹 적용).
- DocumentProcessingJob: status/error/product_id 등 상태 관리.
- Product: 문서 처리 결과로 생성.
- DocumentChunk/Embedding/LLMCache는 v0.2 대비 구조만 유지(검색/임베딩은 비목표).

### Current Status / Evidence (요약)

- 구현 근거 파일: `app/api/routes/documents.py`, `app/api/routes/jobs.py`, `app/services/document_processing.py`, `app/ocr/external.py`, `app/extractors/rule.py`, `app/extractors/llm.py`, `app/models/document.py`, `app/models/job.py`.
- 테스트: `tests/test_documents.py`.
- 실행 커맨드: `UV_CACHE_DIR=/home/sweetbkan/ASHD/.uv_cache uv run pytest`.

## 8. Success Metrics

- 업로드 → Job completed → Product 생성/연결 E2E 흐름이 안정적으로 통과한다.
- 외부 OCR/LLM 키가 없더라도 Mock fallback으로 테스트가 통과한다.
- 문서/스키마/테스트/README가 서로 불일치하지 않는다.

## 9. Open Questions

- [확실하지 않음] `job.error`를 경고 메시지에도 사용하는 것이 적절한지(전용 warning 필드 필요 여부).
- [확실하지 않음] 외부 OCR이 PDF 다페이지를 지원하는지(지원 범위에 따라 처리 방식 변경 필요).
- [확실하지 않음] 무료 PaaS 환경에서 업로드 파일 영구 보관이 보장되지 않을 수 있음.

### Change Log

- PDF 3p 정책을 “초과 페이지 무시 + 경고 기록”으로 확정.
- 업로드 파일 크기 10MB 제한 요구사항을 명시.
- v0.1 범위에서 LLM은 “보완 추출” 용도로 포함됨을 명확화.
- `docs/PROJECT_OVERVIEW.md` 문구 정합성(LLM 보완 추출 포함 / RAG 제외) 반영.
- 10MB 제한과 PDF 3p 경고 정책을 코드/테스트에 반영.

### Next Steps (P0 3개)

1) [완료] PDF 3p 제한/경고 기록 정책을 코드에 반영하고 테스트 추가.
2) [완료] 업로드 파일 크기 10MB 제한 적용 및 413 테스트 추가.
3) [완료] `PROJECT_OVERVIEW.md` 문구 정합성 수정(LLM 보완 추출 포함 / RAG 제외).

### P1/P2 Backlog

- Job 재시도 엔드포인트(`POST /jobs/{id}/retry`) 도입.
- Product 중복/갱신 정책(기존 Product 업데이트/병합) 도입.
- 외부 스토리지(S3 등)로 업로드 파일 이관.
- PDF 전체 페이지 처리 옵션(운영 비용 검토 후).
