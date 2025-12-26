## Relevant Files

- `app/api/routes/documents.py` - 문서 업로드 엔드포인트 및 Job 생성.
- `app/api/routes/jobs.py` - Job 상태 조회 엔드포인트.
- `app/services/document_processing.py` - OCR/추출/저장 파이프라인 핵심 로직.
- `app/ocr/external.py` - 외부 OCR API 클라이언트 및 Mock fallback.
- `app/extractors/rule.py` - 룰 기반 필드 추출.
- `app/extractors/llm.py` - LLM 보완 추출 및 Mock fallback.
- `app/models/document.py` - Document 모델(raw_text/parsed_fields/evidence).
- `app/models/job.py` - DocumentProcessingJob 모델(status/error).
- `app/models/product.py` - 문서 처리 결과로 생성되는 Product.
- `app/schemas/document.py` - 업로드 응답 스키마.
- `app/schemas/job.py` - Job 조회 응답 스키마.
- `tests/test_documents.py` - 문서 업로드/Job 흐름 테스트.
- `docs/PROJECT_OVERVIEW.md` - v0.1 범위 문서 정합성 수정 필요.
- `docs/SYSTEM_ARCHITECTURE.md` - 문서 처리 파이프라인 설계 문서.
- `docs/DATA_MODEL.md` - Document/Job 스키마 정합성 확인.
- `docs/API_EXAMPLES.md` - 업로드/Job API 예시.
- `docs/DEV_GUIDE.md` - 실행/환경 변수/테스트 커맨드.
- `docs/SECURITY_PRIVACY.md` - 마스킹 정책 문서.
- `.env.example` - OCR/LLM 키 및 환경 변수 예시.

### Notes

- Implemented candidates (근거 확인됨):
  - `/documents/upload` 202 + job_id, `/jobs/{id}` 응답 스키마
  - 외부 OCR + Mock fallback, LLM 보완 추출(필수 필드 누락 시)
  - Document/Product/Job 업데이트 + 마스킹 적용
  - 테스트: `tests/test_documents.py`
- Gaps/Questions:
  - PDF 최대 3p 처리/경고 기록, 업로드 10MB 제한은 PRD 요구사항이지만 코드 반영 여부는 확인 필요.
  - `PROJECT_OVERVIEW.md`의 LLM/RAG 문구 정합성 수정 필요.

## Tasks

- [ ] 1.0 업로드/Job API 요구사항 정합성 점검
  - [x] 1.1 `/documents/upload` 응답 스키마(202 + job_id/document_id/status) 확인 (파일: `app/api/routes/documents.py`, `app/schemas/document.py`; 검증: `tests/test_documents.py` 또는 curl)
    - 근거: `app/api/routes/documents.py`의 `DocumentUploadResponse` 반환, `app/schemas/document.py` 스키마 정의
    - 근거: `tests/test_documents.py::test_document_upload_job_flow`에서 202 + job_id 사용 확인
  - [x] 1.2 업로드 파일 타입(이미지+PDF) 문서 정합성 반영 (파일: `docs/PROJECT_OVERVIEW.md`, `docs/API_EXAMPLES.md`; 검증: 문서 리뷰)
    - 근거: `docs/PROJECT_OVERVIEW.md`에 이미지/PDF 업로드 명시
    - 근거: `docs/API_EXAMPLES.md` 문서 업로드 섹션에 이미지/PDF 타입 추가
  - [x] 1.3 10MB 업로드 제한 적용 + 413 테스트 추가 (파일: `app/api/routes/documents.py`, `tests/test_documents.py`; 검증: pytest 413 케이스 통과)
  - [x] 1.4 `/jobs/{id}` 응답 스키마/상태 전이 문서 정합성 점검 (파일: `app/schemas/job.py`, `docs/API_EXAMPLES.md`; 검증: `tests/test_documents.py`)
    - 근거: `app/schemas/job.py`의 `DocumentJobRead` 필드와 `docs/API_EXAMPLES.md` 응답 예시 일치
    - 근거: `tests/test_documents.py::test_document_upload_job_flow`에서 status/completed 확인

- [ ] 2.0 OCR 연동 + Mock fallback 정책 정리
  - [ ] 2.1 외부 OCR 요청/응답 파서 정책 확인 및 문서화 (파일: `app/ocr/external.py`, `docs/DEV_GUIDE.md`; 검증: 코드 리뷰)
  - [ ] 2.2 OCR 키 누락 시 Mock fallback 동작 근거 정리 (파일: `app/ocr/external.py`, `tests/test_documents.py`; 검증: 테스트 로그/코드 확인)
  - [ ] 2.3 PDF 3p 제한 처리 지점 결정(업로드 단계 vs OCR 단계) 및 정책 문서화 (파일: `app/api/routes/documents.py`, `app/services/document_processing.py`, PRD; 검증: 문서 리뷰)
  - [ ] 2.4 OCR 실패 시 Job status/error 처리 규칙 확인 및 테스트 근거 정리 (파일: `app/services/document_processing.py`, `tests/test_documents.py`; 검증: 실패 케이스 테스트)

- [ ] 3.0 룰 기반 추출 + LLM 보완 조건 확정
  - [ ] 3.1 필수 필드 정의(`REQUIRED_FIELDS`) 확인 및 PRD/문서 반영 (파일: `app/services/document_processing.py`, PRD; 검증: 코드 리뷰)
  - [ ] 3.2 누락 시에만 LLM 보완 추출되는지 확인 (파일: `app/services/document_processing.py`; 검증: `tests/test_documents.py` 근거 정리)
  - [ ] 3.3 LLM 키 누락 시 Mock fallback 동작 문서화 (파일: `app/extractors/llm.py`, `docs/DEV_GUIDE.md`; 검증: 코드 리뷰)

- [ ] 4.0 Document/Product/Job 저장 규칙 및 마스킹 보장
  - [ ] 4.1 Document raw_text/parsed_fields/evidence 저장 전 마스킹 확인 (파일: `app/services/document_processing.py`; 검증: `tests/test_documents.py`)
  - [ ] 4.2 Product는 항상 새 레코드 생성 정책 유지 (파일: `app/services/document_processing.py`, PRD; 검증: 코드 리뷰)
  - [ ] 4.3 PDF 3p 초과 경고(job.error) 기록 및 마스킹 적용 (파일: `app/services/document_processing.py`; 검증: `tests/test_documents.py` 경고/마스킹 테스트 추가)
  - [ ] 4.4 응답 전 마스킹 미들웨어 적용 범위 확인(`/documents`, `/jobs`) (파일: `app/api/middlewares/redaction.py`; 검증: 응답 텍스트 검사 테스트)

- [ ] 5.0 비기능 요구사항(무료 PaaS/운영 안정성)
  - [ ] 5.1 업로드는 202로 즉시 반환되고, OCR/추출은 비동기 처리됨을 문서화 (파일: PRD, `docs/PROJECT_OVERVIEW.md`; 검증: 문서 리뷰)
  - [ ] 5.2 로컬 저장(외부 스토리지 v0.2) 정책과 리스크 문서화 (파일: PRD, `docs/SYSTEM_ARCHITECTURE.md`; 검증: 문서 리뷰)
  - [ ] 5.3 재시도 없음 정책 확인 및 Backlog 제안 정리 (파일: PRD; 검증: 문서 리뷰)

- [ ] 6.0 테스트/문서 정합성 점검
  - [ ] 6.2 PDF 3p 제한/경고 처리 테스트 추가 (파일: `tests/test_documents.py`; 검증: 초과 페이지 경고/마스킹 확인)
  - [ ] 6.3 `PROJECT_OVERVIEW.md`의 LLM 문구를 “RAG 제외 + 보완 추출 포함”으로 정합 (파일: `docs/PROJECT_OVERVIEW.md`; 검증: 문서 리뷰)
  - [ ] 6.4 `docs/DEV_GUIDE.md`/`docs/API_EXAMPLES.md` 정책 반영 (파일: 문서; 검증: 문서 리뷰)
  - [ ] 6.5 `UV_CACHE_DIR=/home/sweetbkan/ASHD/.uv_cache uv run pytest` 실행 기록 (검증: 테스트 로그 캡처)
