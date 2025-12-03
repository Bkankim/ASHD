"""알림 설정 CRUD 라우터입니다."""

import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.api.dependencies.auth import get_current_user
from app.core.db import get_session
from app.models.notification import NotificationSettings
from app.models.user import User
from app.schemas.notification_settings import (
    NotificationSettingsRead,
    NotificationSettingsUpdate,
)

router = APIRouter(prefix="/notification-settings", tags=["notification-settings"])


def _get_settings_for_user(session: Session, user_id: int) -> Optional[NotificationSettings]:
    """현재 사용자 알림 설정을 조회합니다."""

    result = session.exec(select(NotificationSettings).where(NotificationSettings.user_id == user_id))
    return result.first()


def _list_to_json_str(value) -> str:
    """리스트를 JSON 문자열로 변환합니다."""

    return json.dumps(value) if not isinstance(value, str) else value


@router.get("", response_model=NotificationSettingsRead)
def read_settings(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> NotificationSettings:
    """사용자 알림 설정을 조회합니다. 없으면 기본값으로 생성합니다."""

    settings = _get_settings_for_user(session, current_user.id)
    if not settings:
        settings = NotificationSettings(
            user_id=current_user.id,
            email_enabled=True,
            telegram_enabled=False,
            warranty_days_before="[30, 7, 3]",
            refund_days_before="[3]",
        )
        session.add(settings)
        session.commit()
        session.refresh(settings)
    return settings


@router.put("", response_model=NotificationSettingsRead)
def update_settings(
    payload: NotificationSettingsUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> NotificationSettings:
    """사용자 알림 설정을 수정합니다."""

    settings = _get_settings_for_user(session, current_user.id)
    if not settings:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification settings not found")

    data = payload.dict(exclude_unset=True)
    if "email_enabled" in data:
        settings.email_enabled = data["email_enabled"]
    if "telegram_enabled" in data:
        settings.telegram_enabled = data["telegram_enabled"]
    if "warranty_days_before" in data:
        settings.warranty_days_before = _list_to_json_str(data["warranty_days_before"])
    if "refund_days_before" in data:
        settings.refund_days_before = _list_to_json_str(data["refund_days_before"])

    settings.updated_at = datetime.utcnow()
    session.add(settings)
    session.commit()
    session.refresh(settings)
    return settings
