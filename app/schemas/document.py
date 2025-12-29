"""문서 업로드 관련 스키마 모듈입니다."""

from pydantic import BaseModel


# 문서 업로드 응답 스키마입니다.
class DocumentUploadResponse(BaseModel):
    """문서 업로드 후 반환되는 응답 형식을 정의합니다."""

    job_id: int
    document_id: int
    status: str


# Job 상태 응답을 위한 베이스 스키마입니다.
