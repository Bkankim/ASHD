"""문서 원문을 저장하는 모델 정의 모듈입니다."""

from datetime import datetime

from sqlmodel import Field, SQLModel

from app.core.time import utc_now

# 문서 원문을 저장하는 테이블입니다.
class Document(SQLModel, table=True):
    """업로드된 문서의 원문 텍스트를 저장합니다."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    product_id: int | None = Field(default=None, index=True, foreign_key="product.id")

    title: str | None = Field(default=None, max_length=255)
    image_path: str | None = Field(default=None, max_length=500)
    raw_text: str = Field(default="")
    parsed_fields: str = Field(default="{}")
    evidence: str | None = Field(default=None)

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
