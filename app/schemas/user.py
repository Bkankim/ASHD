"""User 관련 요청/응답 DTO를 정의하는 모듈입니다."""

from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """User 공통 필드를 담는 기본 스키마입니다."""

    email: EmailStr


class UserCreate(UserBase):
    """회원가입 요청에 사용하는 스키마입니다.

    초급자용 설명:
    - 비밀번호는 평문으로 입력받아 서버에서 해시로 변환합니다.
    - DB에는 password_hash만 저장되고, 평문 비밀번호는 저장하지 않습니다.
    """

    password: str


class UserRead(UserBase):
    """API 응답용 스키마입니다.

    - password_hash 같은 민감 정보는 포함하지 않습니다.
    """

    id: int
    created_at: datetime

    class Config:
        orm_mode = True
