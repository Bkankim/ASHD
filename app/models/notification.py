"""알림 설정(Preferences) 모델을 정의하는 모듈입니다."""

from datetime import datetime

from sqlmodel import Field, SQLModel


class NotificationSettings(SQLModel, table=True):
    """사용자별 알림 설정을 저장하는 모델입니다.

    초급자용 설명:
    - user_id를 unique로 두어 1:1 관계를 강제합니다.
    - 알림 미리 알림일은 간단히 JSON 문자열로 저장합니다.
      (필요하면 나중에 배열 타입이나 별도 테이블로 확장 가능합니다.)
    """

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, unique=True, foreign_key="user.id")

    email_enabled: bool = Field(default=True)
    telegram_enabled: bool = Field(default=False)

    # 보증/환불 임박 기준(일 수)을 JSON 문자열로 저장
    warranty_days_before: str = Field(default="[30, 7, 3]")
    refund_days_before: str = Field(default="[3]")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
