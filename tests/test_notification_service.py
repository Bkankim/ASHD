"""일일 알림 발송 로직을 검증합니다."""

from datetime import date

import pytest

from app.core.config import AppSettings
from app.services.notification_service import DailyAlert, DailyAlertItem, send_daily_alerts


# 테스트용 알림 데이터를 구성하는 헬퍼입니다.
def _build_alert(email: str | None, telegram_chat_id: str | None) -> DailyAlert:
    return DailyAlert(
        user_id=1,
        email=email,
        telegram_chat_id=telegram_chat_id,
        items=[
            DailyAlertItem(
                product_id=1,
                title="테스트 제품",
                purchase_date=None,
                refund_deadline=None,
                warranty_end_date=None,
            )
        ],
    )


@pytest.mark.anyio
# 설정이 없으면 이메일/텔레그램 발송을 건너뛴다는 점을 검증합니다.
async def test_send_daily_alerts_skips_without_config(monkeypatch) -> None:
    settings = AppSettings(
        SECRET_KEY="test",
        SMTP_HOST=None,
        SMTP_PORT=None,
        SMTP_USERNAME=None,
        SMTP_PASSWORD=None,
        SMTP_FROM=None,
        TELEGRAM_BOT_TOKEN=None,
    )

    async def fail_send_email(*_args, **_kwargs):
        raise AssertionError("이메일 전송은 호출되면 안 됩니다.")

    async def fail_send_telegram(*_args, **_kwargs):
        raise AssertionError("텔레그램 전송은 호출되면 안 됩니다.")

    monkeypatch.setattr("app.services.notification_service.send_email", fail_send_email)
    monkeypatch.setattr("app.services.notification_service.send_telegram_message", fail_send_telegram)

    alerts = [_build_alert(email="user@example.com", telegram_chat_id="123")]
    summary = await send_daily_alerts(alerts, today=date(2024, 1, 1), settings=settings)

    assert summary.email_sent == 0
    assert summary.telegram_sent == 0
    assert summary.skipped["email"] is True
    assert summary.skipped["telegram"] is True


@pytest.mark.anyio
# 이메일 설정이 있으면 email_sent가 증가하는지 확인합니다.
async def test_send_daily_alerts_sends_email(monkeypatch) -> None:
    settings = AppSettings(
        SECRET_KEY="test",
        SMTP_HOST="smtp.example.com",
        SMTP_PORT=587,
        SMTP_USERNAME="user",
        SMTP_PASSWORD="pass",
        SMTP_FROM="noreply@example.com",
    )

    calls = []

    async def fake_send_email(*_args, **_kwargs):
        calls.append("sent")

    monkeypatch.setattr("app.services.notification_service.send_email", fake_send_email)

    alerts = [_build_alert(email="user@example.com", telegram_chat_id=None)]
    summary = await send_daily_alerts(alerts, today=date(2024, 1, 1), settings=settings)

    assert summary.email_targets == 1
    assert summary.email_sent == 1
    assert len(calls) == 1
    assert summary.skipped["email"] is False


@pytest.mark.anyio
# 텔레그램 설정이 있으면 telegram_sent가 증가하는지 확인합니다.
async def test_send_daily_alerts_sends_telegram(monkeypatch) -> None:
    settings = AppSettings(
        SECRET_KEY="test",
        TELEGRAM_BOT_TOKEN="test-token",
    )

    calls = []

    async def fake_send_telegram(*_args, **_kwargs):
        calls.append("sent")

    monkeypatch.setattr("app.services.notification_service.send_telegram_message", fake_send_telegram)

    alerts = [_build_alert(email=None, telegram_chat_id="123")]
    summary = await send_daily_alerts(alerts, today=date(2024, 1, 1), settings=settings)

    assert summary.telegram_targets == 1
    assert summary.telegram_sent == 1
    assert len(calls) == 1
    assert summary.skipped["telegram"] is False
