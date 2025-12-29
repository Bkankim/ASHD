"""문서 업로드/Job 처리 플로우를 검증하는 테스트 모듈입니다."""

from pathlib import Path

from fastapi import status

from app.api.routes import documents
from app.models.document import Document
from app.models.job import DocumentProcessingJob
from app.models.product import Product


# Mock OCR 클라이언트입니다.
class MockOCR:
    """테스트용 OCR 클라이언트로 고정된 텍스트를 반환합니다."""

    # 파일 경로를 받아 고정된 텍스트를 반환합니다.
    def extract_text(self, image_path: Path, pages: list[int] | None = None) -> str:
        """룰 기반 추출에 필요한 최소 정보만 포함한 텍스트를 반환합니다."""
        return (
            "상품명: 테스트이어폰\n"
            "구매일: 2024-01-10\n"
            "금액: 12,000원\n"
            "카드번호: 1234-5678-9012-3456\n"
            "승인번호: 99887766\n"
            "전화: 01012345678\n"
            "이메일: user@example.com\n"
            "주민번호: 900101-1234567\n"
        )


# Mock LLM 추출기입니다.
class MockLLMExtractor:
    """부족한 필드를 LLM이 보완했다고 가정하는 Mock입니다."""

    # raw_text를 받아 고정된 필드 dict를 반환합니다.
    def extract(self, raw_text: str) -> dict:
        """store 필드를 채워주는 응답을 반환합니다."""
        return {"store": "LLM-상점"}


# 에러를 발생시키는 Mock OCR 클라이언트입니다.
class MockOCRError:
    """에러 메시지에 민감정보를 포함한 OCR Mock입니다."""

    def extract_text(self, image_path: Path, pages: list[int] | None = None) -> str:
        """카드번호가 포함된 오류를 발생시킵니다."""
        raise ValueError("승인번호: 99887766 카드번호: 1234-5678-9012-3456")


# PDF 페이지 제한 테스트용 OCR 클라이언트입니다.
class MockPDFOCR:
    """PDF 처리 시 전달되는 페이지 제한을 검증합니다."""

    def __init__(self) -> None:
        self.pages_seen: list[int] | None = None

    def extract_text(self, image_path: Path, pages: list[int] | None = None) -> str:
        """pages 파라미터를 기록하고 고정 텍스트를 반환합니다."""
        self.pages_seen = pages
        return "상품명: PDF테스트\n구매일: 2024-01-11\n금액: 1,000원"


# 문서 업로드 → Job 완료 → Product 생성 플로우를 검증합니다.
# 문서 업로드 플로우를 검증합니다.
def test_document_upload_job_flow(client, app, db_session, make_user_and_token):
    """문서 업로드 시 Job이 생성되고 Product가 업데이트되는지 확인합니다."""
    app.dependency_overrides[documents.get_ocr_client] = lambda: MockOCR()
    app.dependency_overrides[documents.get_llm_extractor] = lambda: MockLLMExtractor()

    try:
        auth = make_user_and_token()
        headers = auth["headers"]

        response = client.post(
            "/documents/upload",
            files={"file": ("receipt.jpg", b"fake-image-bytes", "image/jpeg")},
            headers=headers,
        )
        assert response.status_code == 202
        payload = response.json()
        job_id = payload["job_id"]

        # Job 상태 조회
        job_resp = client.get(f"/jobs/{job_id}", headers=headers)
        assert job_resp.status_code == 200
        job_data = job_resp.json()
        assert job_data["status"] == "completed"

        # DB에서 Product가 생성되었는지 확인
        job = db_session.get(DocumentProcessingJob, job_id)
        assert job is not None
        assert job.product_id is not None

        product = db_session.get(Product, job.product_id)
        assert product is not None
        assert product.store == "LLM-상점"
        # raw_text에 민감정보 원문이 남아 있지 않은지 확인합니다.
        assert "1234-5678-9012-3456" not in (product.raw_text or "")
        assert "01012345678" not in (product.raw_text or "")
        assert "***" in (product.raw_text or "")

        document = db_session.get(Document, job.document_id)
        assert document is not None
        # 문서 raw_text도 마스킹되어야 합니다.
        assert "900101-1234567" not in (document.raw_text or "")
        # evidence/parsed_fields에도 원문이 노출되지 않는지 확인합니다.
        assert "user@example.com" not in (document.parsed_fields or "")
        assert "01012345678" not in (document.parsed_fields or "")
        assert "99887766" not in (document.evidence or "")

        # API 응답에서도 원문 민감정보가 노출되지 않는지 확인합니다.
        products_resp = client.get("/products", headers=headers)
        assert products_resp.status_code == 200
        response_text = products_resp.text
        assert "1234-5678-9012-3456" not in response_text
        assert "01012345678" not in response_text
        assert "user@example.com" not in response_text
        assert "900101-1234567" not in response_text
    finally:
        app.dependency_overrides.pop(documents.get_ocr_client, None)
        app.dependency_overrides.pop(documents.get_llm_extractor, None)


# Job 응답에서도 민감정보가 노출되지 않는지 확인합니다.
def test_job_response_redaction(client, db_session, make_user_and_token):
    """Job error 필드에 민감정보가 있어도 응답에서 마스킹되는지 확인합니다."""
    auth = make_user_and_token()
    user_id = auth["user"]["id"]

    job = DocumentProcessingJob(
        user_id=user_id,
        status="failed",
        error="승인번호: 99887766 카드번호: 1234-5678-9012-3456",
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    resp = client.get(f"/jobs/{job.id}", headers=auth["headers"])
    assert resp.status_code == 200
    assert "99887766" not in resp.text
    assert "1234-5678-9012-3456" not in resp.text


# OCR 실패 시 Job.error가 저장 전에 마스킹되는지 확인합니다.
def test_job_error_redacted_on_failure(client, app, db_session, make_user_and_token):
    """OCR 에러 메시지가 DB에 원문으로 저장되지 않는지 확인합니다."""
    app.dependency_overrides[documents.get_ocr_client] = lambda: MockOCRError()
    app.dependency_overrides[documents.get_llm_extractor] = lambda: MockLLMExtractor()

    try:
        auth = make_user_and_token()
        headers = auth["headers"]

        response = client.post(
            "/documents/upload",
            files={"file": ("receipt.jpg", b"fake-image-bytes", "image/jpeg")},
            headers=headers,
        )
        assert response.status_code == 202
        job_id = response.json()["job_id"]

        job = db_session.get(DocumentProcessingJob, job_id)
        assert job is not None
        assert job.status == "failed"
        assert job.error is not None
        assert "99887766" not in job.error
        assert "1234-5678-9012-3456" not in job.error
    finally:
        app.dependency_overrides.pop(documents.get_ocr_client, None)
        app.dependency_overrides.pop(documents.get_llm_extractor, None)


# 업로드 파일 크기 제한을 검증합니다.
def test_document_upload_too_large(client, make_user_and_token):
    """10MB 초과 파일 업로드 시 413을 반환하는지 확인합니다."""
    auth = make_user_and_token()
    headers = auth["headers"]

    payload = b"a" * (10 * 1024 * 1024 + 1)
    response = client.post(
        "/documents/upload",
        files={"file": ("big.pdf", payload, "application/pdf")},
        headers=headers,
    )
    assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE


# PDF 3p 제한 경고를 검증합니다.
def test_document_pdf_page_limit_warning(client, app, db_session, make_user_and_token):
    """PDF 3p 초과 시 경고가 기록되는지 확인합니다."""
    pdf_ocr = MockPDFOCR()
    app.dependency_overrides[documents.get_ocr_client] = lambda: pdf_ocr
    app.dependency_overrides[documents.get_llm_extractor] = lambda: MockLLMExtractor()

    try:
        auth = make_user_and_token()
        headers = auth["headers"]

        # 간단한 PDF 바이너리(페이지 마커 4개)를 만들어 업로드합니다.
        pdf_bytes = b"%PDF-1.4\n" + b"/Type /Page\n" * 4
        response = client.post(
            "/documents/upload",
            files={"file": ("sample.pdf", pdf_bytes, "application/pdf")},
            headers=headers,
        )
        assert response.status_code == 202
        job_id = response.json()["job_id"]

        job = db_session.get(DocumentProcessingJob, job_id)
        assert job is not None
        assert job.status == "completed"
        assert job.error is not None
        assert "PDF pages truncated" in job.error
        assert pdf_ocr.pages_seen == [1, 2, 3]
    finally:
        app.dependency_overrides.pop(documents.get_ocr_client, None)
        app.dependency_overrides.pop(documents.get_llm_extractor, None)
