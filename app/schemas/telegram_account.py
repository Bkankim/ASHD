"""텔레그램 계정 연동 요청/응답 스키마를 정의하는 모듈입니다."""

from datetime import datetime

from pydantic import BaseModel


class TelegramAccountBase(BaseModel):
    """텔레그램 계정 공통 필드를 담는 스키마입니다."""

    chat_id: str
    username: str | None = None


class TelegramAccountCreate(TelegramAccountBase):
    """텔레그램 연동 생성 시 사용하는 스키마입니다.

    - user_id는 보통 인증된 사용자 컨텍스트에서 채워집니다.
    """

    pass


class TelegramAccountRead(TelegramAccountBase):
    """조회 응답용 스키마입니다."""

    id: int
    user_id: int
    linked_at: datetime

    class Config:
        orm_mode = True
