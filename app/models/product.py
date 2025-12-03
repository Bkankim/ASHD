"""Product(제품/문서) 도메인 모델 정의 모듈입니다."""

from datetime import date, datetime

from sqlmodel import Field, SQLModel


class Product(SQLModel, table=True):
    """영수증/보증서 기반으로 관리되는 제품 정보를 나타내는 모델입니다.

    초급자용 설명:
    - table=True를 주면 SQLModel이 실제 DB 테이블과 1:1 매핑합니다.
    - user_id를 FK로 두어, 각 제품이 어떤 사용자 소유인지(멀티테넌시)를 강제할 수 있습니다.
    """

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")

    title: str = Field(max_length=255)
    product_category: str | None = Field(default=None, index=True, max_length=100)

    purchase_date: date | None = Field(default=None, index=True)
    amount: int | None = Field(default=None)
    store: str | None = Field(default=None, index=True, max_length=255)
    order_id: str | None = Field(default=None, index=True, max_length=255)

    refund_deadline: date | None = Field(default=None, index=True)
    warranty_end_date: date | None = Field(default=None, index=True)

    as_contact: str | None = Field(default=None, max_length=255)

    image_path: str | None = Field(default=None, max_length=500)
    raw_text: str | None = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
