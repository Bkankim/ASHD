"""문서 처리 Job 스키마 모듈입니다."""

from datetime import datetime

from pydantic import BaseModel


# Job 응답 스키마입니다.
class DocumentJobRead(BaseModel):
    """Job 상태 조회 응답 형식을 정의합니다."""

    id: int
    status: str
    error: str | None
    document_id: int | None
    product_id: int | None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
