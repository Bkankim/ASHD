"""Product 관련 요청/응답 스키마 정의 모듈입니다."""

from datetime import date, datetime

from pydantic import BaseModel


class ProductBase(BaseModel):
    """Product 공통 필드를 담는 기본 스키마입니다.

    초급자용 설명:
    - DB 모델(SQLModel)과 분리해, 요청/응답에서 필요한 필드만 노출합니다.
    - 필수/선택 필드를 구분해 입력 검증을 쉽게 합니다.
    """

    title: str
    product_category: str | None = None
    purchase_date: date | None = None
    amount: int | None = None
    store: str | None = None
    order_id: str | None = None
    refund_deadline: date | None = None
    warranty_end_date: date | None = None
    as_contact: str | None = None
    image_path: str | None = None
    raw_text: str | None = None


class ProductCreate(ProductBase):
    """제품 생성 시 사용하는 스키마입니다.

    - user_id는 보통 인증된 사용자 컨텍스트에서 주입하므로 입력값에 포함하지 않습니다.
    """
    pass


class ProductUpdate(BaseModel):
    """제품 수정 시 사용하는 스키마입니다.

    - 부분 업데이트를 허용하기 위해 모든 필드를 선택적으로 둡니다.
    """

    title: str | None = None
    product_category: str | None = None
    purchase_date: date | None = None
    amount: int | None = None
    store: str | None = None
    order_id: str | None = None
    refund_deadline: date | None = None
    warranty_end_date: date | None = None
    as_contact: str | None = None
    image_path: str | None = None
    raw_text: str | None = None


class ProductRead(ProductBase):
    """제품 조회 응답용 스키마입니다.

    - DB 모델에서 필요한 정보만 노출하며, password_hash 같은 민감 정보는 존재하지 않습니다.
    """

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
