"""텔레그램 계정 연동 라우터입니다."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel import Session, select

from app.api.dependencies.auth import get_current_user
from app.core.db import get_session
from app.models.notification import NotificationSettings
from app.models.telegram_account import TelegramAccount
from app.models.user import User
from app.schemas.telegram_account import TelegramAccountCreate, TelegramAccountRead

router = APIRouter(prefix="/telegram-account", tags=["telegram-account"])


def _get_account_for_user(session: Session, user_id: int) -> TelegramAccount | None:
    """현재 사용자 텔레그램 연동 정보를 조회합니다."""

    result = session.exec(select(TelegramAccount).where(TelegramAccount.user_id == user_id))
    return result.first()


def _get_or_create_settings(session: Session, user_id: int) -> NotificationSettings:
    """NotificationSettings가 없으면 기본값으로 생성 후 반환합니다."""

    result = session.exec(select(NotificationSettings).where(NotificationSettings.user_id == user_id))
    settings = result.first()
    if not settings:
        settings = NotificationSettings(
            user_id=user_id,
            email_enabled=True,
            telegram_enabled=False,
            warranty_days_before="[30, 7, 3]",
            refund_days_before="[3]",
        )
        session.add(settings)
        session.commit()
        session.refresh(settings)
    return settings


@router.get("", response_model=TelegramAccountRead)
def get_account(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TelegramAccount:
    """현재 사용자 텔레그램 연동 정보를 조회합니다."""

    account = _get_account_for_user(session, current_user.id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Telegram account not linked")
    return account


@router.post("", response_model=TelegramAccountRead, status_code=status.HTTP_201_CREATED)
def upsert_account(
    payload: TelegramAccountCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TelegramAccount:
    """텔레그램 계정을 등록/갱신합니다. (user당 1개)"""

    # chat_id가 비어 있지 않은지 검증합니다.
    if not payload.chat_id or not payload.chat_id.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="chat_id is required")
    if len(payload.chat_id.strip()) < 3:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="chat_id is too short")

    account = _get_account_for_user(session, current_user.id)
    if account:
        account.chat_id = payload.chat_id
        account.username = payload.username
        account.linked_at = datetime.utcnow()
    else:
        account = TelegramAccount(
            user_id=current_user.id,
            chat_id=payload.chat_id,
            username=payload.username,
        )
        session.add(account)

    # 텔레그램 연동 시 알림 설정을 활성화합니다.
    settings = _get_or_create_settings(session, current_user.id)
    settings.telegram_enabled = True
    settings.updated_at = datetime.utcnow()
    session.add(settings)
    session.commit()
    session.refresh(account)
    return account


@router.delete("", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_account(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Response:
    """텔레그램 연동을 해제합니다."""

    account = _get_account_for_user(session, current_user.id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Telegram account not linked")

    session.delete(account)
    # 연동 해제 시 알림 설정도 비활성화합니다.
    settings = _get_or_create_settings(session, current_user.id)
    settings.telegram_enabled = False
    settings.updated_at = datetime.utcnow()
    session.add(settings)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
