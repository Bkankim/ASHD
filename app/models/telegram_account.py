"""텔레그램 계정 연동 정보를 저장하는 도메인 모델입니다."""

from datetime import datetime

from sqlmodel import Field, SQLModel


class TelegramAccount(SQLModel, table=True):
    """텔레그램 계정과 ASHD 사용자 계정을 1:1로 연결하는 테이블입니다."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, unique=True, foreign_key="user.id")
    chat_id: str = Field(index=True)
    username: str | None = Field(default=None)

    linked_at: datetime = Field(default_factory=datetime.utcnow)
