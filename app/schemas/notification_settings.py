"""알림 설정 요청/응답 스키마를 정의하는 모듈입니다."""

from datetime import datetime
from typing import List, Optional
import json

from pydantic import BaseModel, validator


class NotificationSettingsBase(BaseModel):
    """알림 설정 공통 필드를 담는 기본 스키마입니다.

    초급자용 설명:
    - DB에는 JSON 문자열로 저장하지만, API에서는 리스트[int] 형태로 다루면 더 직관적입니다.
    - 서비스 계층에서 json.dumps/loads로 변환해 모델과 스키마 간 매핑을 수행할 수 있습니다.
    """

    email_enabled: bool = True
    telegram_enabled: bool = False
    warranty_days_before: List[int] = [30, 7, 3]
    refund_days_before: List[int] = [3]

    @validator("warranty_days_before", "refund_days_before", pre=True)
    def parse_json_string(cls, v):
        """DB에서 JSON 문자열이 들어와도 리스트로 변환하여 응답 일관성을 유지합니다."""
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass
        return v


class NotificationSettingsUpdate(NotificationSettingsBase):
    """부분 수정용 스키마입니다.

    - 모든 필드를 선택적으로 두어 일부만 업데이트할 수 있게 합니다.
    """

    email_enabled: Optional[bool] = None
    telegram_enabled: Optional[bool] = None
    warranty_days_before: Optional[List[int]] = None
    refund_days_before: Optional[List[int]] = None


class NotificationSettingsRead(NotificationSettingsBase):
    """조회 응답용 스키마입니다."""

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
