"""문서 처리 Job 상태 조회 라우터입니다."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.api.dependencies.auth import get_current_user
from app.core.db import get_session
from app.models.job import DocumentProcessingJob
from app.models.user import User
from app.schemas.job import DocumentJobRead

router = APIRouter(prefix="/jobs", tags=["jobs"])


# 현재 사용자 소유의 Job을 조회하는 헬퍼입니다.
def _get_job_for_user(session: Session, job_id: int, user_id: int) -> DocumentProcessingJob | None:
    """user_id 기준으로 Job을 조회합니다."""
    statement = select(DocumentProcessingJob).where(
        DocumentProcessingJob.id == job_id,
        DocumentProcessingJob.user_id == user_id,
    )
    return session.exec(statement).first()


@router.get("/{job_id}", response_model=DocumentJobRead)
def get_job(
    job_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> DocumentProcessingJob:
    """Job 상태를 반환합니다."""
    job = _get_job_for_user(session, job_id, current_user.id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job
