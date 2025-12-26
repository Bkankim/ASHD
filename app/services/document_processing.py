"""문서 업로드 후 OCR/추출 파이프라인을 실행하는 서비스 모듈입니다."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from sqlmodel import Session

import app.core.db as db
from app.core.redaction import redact_in_structure, redact_text
from app.core.time import utc_now
from app.extractors.llm import LLMFieldExtractor
from app.extractors.rule import extract_fields_with_rules, parse_amount, parse_date
from app.models.document import Document
from app.models.job import DocumentProcessingJob
from app.models.product import Product
from app.ocr.base import OCRClient


# LLM 보완 여부를 판단할 때 사용하는 필드 목록입니다.
REQUIRED_FIELDS = ["title", "purchase_date", "amount", "store"]

# PDF 최대 처리 페이지 수입니다.
PDF_PAGE_LIMIT = 3


# 룰 기반 추출 결과를 기준으로 LLM 보완이 필요한지 판단합니다.
def needs_llm(fields: dict[str, Any]) -> bool:
    """필수 필드가 비어 있으면 LLM 보완이 필요하다고 판단합니다."""
    return any(not fields.get(key) for key in REQUIRED_FIELDS)


# LLM 결과와 룰 결과를 합칩니다.
def merge_fields(rule_fields: dict[str, Any], llm_fields: dict[str, Any]) -> dict[str, Any]:
    """룰 기반 결과를 우선으로 하고, 비어 있는 필드를 LLM으로 보완합니다."""
    merged = dict(rule_fields)
    for key, value in llm_fields.items():
        if key not in merged or merged.get(key) in (None, ""):
            merged[key] = value
    return merged


# LLM/룰 결과를 Product 필드 타입에 맞게 정규화합니다.
def normalize_fields(fields: dict[str, Any]) -> dict[str, Any]:
    """문자열 형태의 필드를 Product에 맞는 타입으로 변환합니다."""
    normalized: dict[str, Any] = dict(fields)

    # 날짜 문자열은 date 객체로 변환합니다.
    for key in ["purchase_date", "refund_deadline", "warranty_end_date"]:
        value = normalized.get(key)
        if isinstance(value, str):
            parsed = parse_date(value)
            if parsed:
                normalized[key] = parsed

    # 금액 문자열은 정수로 변환합니다.
    amount_value = normalized.get("amount")
    if isinstance(amount_value, str):
        parsed_amount = parse_amount(amount_value)
        if parsed_amount is not None:
            normalized["amount"] = parsed_amount

    return normalized


# 필드 dict를 JSON 저장용으로 직렬화합니다.
def serialize_fields(fields: dict[str, Any]) -> dict[str, Any]:
    """date 객체를 ISO 문자열로 바꿔 JSON 저장이 가능하도록 합니다."""
    serialized: dict[str, Any] = {}
    for key, value in fields.items():
        if hasattr(value, "isoformat"):
            serialized[key] = value.isoformat()
        else:
            serialized[key] = value
    return serialized


# PDF 파일 여부를 판단합니다.
def _is_pdf(path: Path) -> bool:
    """확장자로 PDF 여부를 간단히 확인합니다."""
    return path.suffix.lower() == ".pdf"


# PDF 페이지 수를 대략적으로 계산합니다.
def _count_pdf_pages(path: Path) -> int | None:
    """PDF 내부 마커를 기반으로 페이지 수를 추정합니다."""
    try:
        data = path.read_bytes()
    except OSError:
        return None

    # '/Type /Page' 패턴을 세서 대략적인 페이지 수를 추정합니다.
    matches = re.findall(rb"/Type\s*/Page(?!s)", data)
    if not matches:
        return None
    return len(matches)


# PDF 처리 정책에 따라 OCR에 전달할 페이지 목록을 결정합니다.
def _select_pdf_pages(path: Path) -> tuple[list[int], str | None]:
    """PDF 처리 페이지 목록과 경고 메시지를 반환합니다."""
    page_count = _count_pdf_pages(path)
    if page_count is None:
        # 페이지 수를 알 수 없으면 정책상 1~3페이지로 제한합니다.
        return [1, 2, 3], None

    if page_count > PDF_PAGE_LIMIT:
        warning = f"PDF pages truncated: processed {PDF_PAGE_LIMIT} of {page_count}"
        return list(range(1, PDF_PAGE_LIMIT + 1)), warning

    return list(range(1, page_count + 1)), None


# 업로드된 문서를 처리하는 백그라운드 작업입니다.
def process_document_job(
    job_id: int,
    document_id: int,
    user_id: int,
    image_path: str,
    ocr_client: OCRClient,
    llm_extractor: LLMFieldExtractor,
) -> None:
    """OCR → 필드 추출 → 제품 업데이트까지 처리하고 Job 상태를 갱신합니다."""
    with Session(db.engine) as session:
        job = session.get(DocumentProcessingJob, job_id)
        if not job:
            return

        # 1) 작업 상태를 processing으로 변경합니다.
        job.status = "processing"
        job.updated_at = utc_now()
        session.add(job)
        session.commit()

        try:
            # 2) OCR로 raw_text를 추출합니다.
            file_path = Path(image_path)
            pdf_pages: list[int] | None = None
            warning_message: str | None = None
            if _is_pdf(file_path):
                pdf_pages, warning_message = _select_pdf_pages(file_path)
            raw_text = ocr_client.extract_text(file_path, pages=pdf_pages)
            if not raw_text.strip():
                raise ValueError("OCR returned empty text")

            document = session.get(Document, document_id)
            if not document:
                raise ValueError("Document not found")

            # OCR 원문은 DB에 저장하기 전 반드시 마스킹합니다.
            redacted_raw_text = redact_text(raw_text)
            document.raw_text = redacted_raw_text
            document.updated_at = utc_now()

            # 3) 룰 기반 추출을 수행합니다.
            rule_fields = extract_fields_with_rules(raw_text)

            # 4) 부족한 필드는 LLM으로 보완합니다.
            llm_fields: dict[str, Any] = {}
            if needs_llm(rule_fields):
                llm_fields = llm_extractor.extract(raw_text)

            merged_fields = merge_fields(rule_fields, llm_fields)
            normalized_fields = normalize_fields(merged_fields)

            # 5) Product를 생성/업데이트합니다.
            title = normalized_fields.get("title") or "미분류 제품"
            product = Product(
                user_id=user_id,
                title=title,
                product_category=normalized_fields.get("product_category"),
                purchase_date=normalized_fields.get("purchase_date"),
                amount=normalized_fields.get("amount"),
                store=normalized_fields.get("store"),
                order_id=normalized_fields.get("order_id"),
                refund_deadline=normalized_fields.get("refund_deadline"),
                warranty_end_date=normalized_fields.get("warranty_end_date"),
                as_contact=normalized_fields.get("as_contact"),
                image_path=image_path,
                raw_text=redacted_raw_text,
            )
            session.add(product)
            session.commit()
            session.refresh(product)

            # 6) Document에 파싱 결과와 연결 정보를 저장합니다.
            document.product_id = product.id
            serialized_fields = serialize_fields(normalized_fields)
            redacted_fields = redact_in_structure(serialized_fields)
            document.parsed_fields = json.dumps(redacted_fields, ensure_ascii=False)
            evidence_payload = {
                "rule_fields": list(rule_fields.keys()),
                "llm_fields": list(llm_fields.keys()),
            }
            document.evidence = json.dumps(redact_in_structure(evidence_payload), ensure_ascii=False)
            session.add(document)

            # 7) Job 완료 처리
            job.status = "completed"
            job.error = redact_text(warning_message) if warning_message else None
            job.product_id = product.id
            job.updated_at = utc_now()
            session.add(job)
            session.commit()
        except Exception as exc:
            # 실패 시 상태를 failed로 바꾸고 에러 메시지를 저장합니다.
            job.status = "failed"
            job.error = redact_text(str(exc))
            job.updated_at = utc_now()
            session.add(job)
            session.commit()
