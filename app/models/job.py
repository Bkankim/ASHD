"""문서 처리 작업(Job) 모델을 정의하는 모듈입니다."""

from datetime import datetime

from sqlmodel import Field, SQLModel

from app.core.time import utc_now

# 문서 처리 작업 상태를 저장하는 테이블입니다.
class DocumentProcessingJob(SQLModel, table=True):
    """문서 업로드 후 OCR/추출 상태를 관리하는 Job 모델입니다."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    document_id: int | None = Field(default=None, index=True, foreign_key="document.id")
    product_id: int | None = Field(default=None, index=True, foreign_key="product.id")

    status: str = Field(default="pending", index=True, max_length=20)
    error: str | None = Field(default=None)

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
