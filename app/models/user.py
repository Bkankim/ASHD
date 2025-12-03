"""User 테이블을 정의하는 SQLModel 모델입니다."""

from datetime import datetime

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """서비스 사용자 계정을 표현하는 테이블입니다.

    초급자용 설명:
    - SQLModel 클래스에 table=True를 주면 실제 DB 테이블로 매핑됩니다.
    - 각 필드는 컬럼이 되고, 제약조건(기본키, 인덱스, unique)도 여기서 정의합니다.
    """

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
