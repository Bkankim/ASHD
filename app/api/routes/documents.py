"""문서 업로드 및 처리 Job 생성 라우터입니다."""

from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlmodel import Session

from app.api.dependencies.auth import get_current_user
from app.core.config import get_settings
from app.core.db import get_session
from app.extractors.llm import LLMFieldExtractor, build_llm_extractor
from app.models.document import Document
from app.models.job import DocumentProcessingJob
from app.models.user import User
from app.ocr.base import OCRClient
from app.ocr.external import build_ocr_client
from app.schemas.document import DocumentUploadResponse
from app.services.document_processing import process_document_job

router = APIRouter(prefix="/documents", tags=["documents"])

MAX_UPLOAD_BYTES = 10 * 1024 * 1024


# OCR 클라이언트를 의존성으로 제공합니다.
def get_ocr_client() -> OCRClient:
    """환경 변수에 따라 OCR 클라이언트를 선택합니다."""
    settings = get_settings()
    return build_ocr_client(settings.OCR_API_URL, settings.OCR_API_KEY, settings.OCR_TIMEOUT_SECONDS)


# LLM 추출기를 의존성으로 제공합니다.
def get_llm_extractor() -> LLMFieldExtractor:
    """환경 변수에 따라 LLM 추출기를 선택합니다."""
    return build_llm_extractor()


# 업로드 파일을 저장할 디렉터리를 준비합니다.
def _ensure_upload_dir(path_str: str) -> Path:
    """업로드 디렉터리를 생성하고 Path로 반환합니다."""
    path = Path(path_str)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _get_upload_size(upload: UploadFile) -> int:
    """업로드 파일 크기를 바이트 단위로 확인합니다."""
    file_obj = upload.file
    file_obj.seek(0, os.SEEK_END)
    size = file_obj.tell()
    file_obj.seek(0)
    return size


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    ocr_client: OCRClient = Depends(get_ocr_client),
    llm_extractor: LLMFieldExtractor = Depends(get_llm_extractor),
) -> DocumentUploadResponse:
    """이미지를 업로드하고 문서 처리 Job을 생성합니다.

    초급자용 설명:
    - 업로드는 202로 즉시 응답하고, 실제 OCR/추출 처리는 백그라운드에서 수행합니다.
    - 무료 PaaS의 요청 타임아웃을 피하기 위해 비동기 처리 구조를 사용합니다.
    """
    settings = get_settings()
    upload_dir = _ensure_upload_dir(settings.DOCUMENT_UPLOAD_DIR)
    file_size = _get_upload_size(file)
    if file_size > MAX_UPLOAD_BYTES:
        file.file.close()
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File is too large (max 10MB).",
        )
    suffix = Path(file.filename or "upload.bin").suffix or ".bin"
    safe_name = f"{uuid.uuid4().hex}{suffix}"
    file_path = upload_dir / safe_name

    # 파일을 로컬 디스크에 저장합니다.
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()

    # Document 레코드를 먼저 생성합니다.
    document = Document(
        user_id=current_user.id,
        title=file.filename,
        image_path=str(file_path),
        raw_text="",
    )
    session.add(document)
    session.commit()
    session.refresh(document)

    # Job 레코드를 생성합니다.
    job = DocumentProcessingJob(
        user_id=current_user.id,
        document_id=document.id,
        status="pending",
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    # 백그라운드에서 OCR/추출 파이프라인을 실행합니다.
    background_tasks.add_task(
        process_document_job,
        job_id=job.id,
        document_id=document.id,
        user_id=current_user.id,
        image_path=str(file_path),
        ocr_client=ocr_client,
        llm_extractor=llm_extractor,
    )

    return DocumentUploadResponse(job_id=job.id, document_id=document.id, status=job.status)
