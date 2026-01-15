"""보증/환불 임박 알림을 계산하고, 각 채널로 보내는 서비스 모듈입니다."""

from dataclasses import dataclass
from datetime import date
import json
from typing import List

from sqlmodel import Session, select

from app.core.config import AppSettings, get_settings
from app.models.notification import NotificationSettings
from app.models.product import Product
from app.models.telegram_account import TelegramAccount
from app.models.user import User
from app.services.email_service import send_email
from app.services.telegram_service import send_telegram_message


# 알림 대상 제품 정보를 담는 데이터 구조입니다.
@dataclass
class DailyAlertItem:
    """알림 대상이 되는 단일 제품 정보를 담는 데이터 구조입니다."""

    product_id: int
    title: str
    purchase_date: date | None
    refund_deadline: date | None
    warranty_end_date: date | None
    amount: int | None = None
    store: str | None = None


# 사용자별 알림 묶음을 표현하는 데이터 구조입니다.
@dataclass
class DailyAlert:
    """특정 사용자에 대한 하루치 알림 정보를 담는 데이터 구조입니다."""

    user_id: int
    email: str | None
    telegram_chat_id: str | None
    items: List[DailyAlertItem]


# 일일 알림 실행 결과를 요약하는 데이터 구조입니다.
@dataclass
class DailyAlertsSummary:
    """일일 알림 실행 결과를 요약하는 데이터 구조입니다."""

    date: date
    processed: int
    email_targets: int
    telegram_targets: int
    email_sent: int
    telegram_sent: int
    skipped: dict[str, bool | str | None]
    errors: List[str]


# 알림 기준 일수를 JSON 문자열에서 파싱합니다.
def _parse_days(value: str, fallback: list[int]) -> list[int]:
    """JSON 문자열을 리스트[int]로 변환합니다.

    초급자용 설명:
    - DB에는 문자열로 저장되므로, 알림 계산 시에는 리스트로 변환해야 합니다.
    - 파싱이 실패하면 기본값을 사용해 서비스가 깨지지 않게 합니다.
    """

    try:
        parsed = json.loads(value)
        if isinstance(parsed, list) and all(isinstance(v, int) for v in parsed):
            return parsed
    except Exception:
        pass
    return fallback


# 특정 날짜가 알림 기준에 해당하는지 판단합니다.
def _is_due(target: date | None, days_before: list[int], today: date) -> bool:
    """목표 날짜가 오늘 기준 D-N 조건에 맞는지 확인합니다."""

    if target is None:
        return False
    days_left = (target - today).days
    return days_left in days_before


# 제품 목록에서 알림 대상만 추려 DailyAlertItem으로 변환합니다.
def _collect_due_items(
    products: list[Product],
    today: date,
    warranty_days: list[int],
    refund_days: list[int],
) -> list[DailyAlertItem]:
    """보증/환불 기한이 임박한 제품만 선별합니다."""

    items: list[DailyAlertItem] = []
    for product in products:
        is_warranty_due = _is_due(product.warranty_end_date, warranty_days, today)
        is_refund_due = _is_due(product.refund_deadline, refund_days, today)
        if not (is_warranty_due or is_refund_due):
            continue

        items.append(
            DailyAlertItem(
                product_id=product.id or 0,
                title=product.title,
                purchase_date=product.purchase_date,
                refund_deadline=product.refund_deadline,
                warranty_end_date=product.warranty_end_date,
                amount=product.amount,
                store=product.store,
            )
        )
    return items


# 사용자에게 보낼 간단한 텍스트 메시지를 생성합니다.
def _format_alert_message(alert: DailyAlert, today: date) -> str:
    """알림 메시지를 상세하게 구성합니다."""

    lines = [
        "🔔 [ASHD] 환불/보증 임박 알림",
        f"📅 {today.isoformat()}",
        "",
        "아래 항목의 기한이 다가오고 있습니다:",
        "",
    ]
    for item in alert.items:
        lines.append(f"📦 {item.title}")
        if item.amount:
            lines.append(f"   💵 금액: {item.amount:,}원")
        if item.store:
            lines.append(f"   🏪 구매처: {item.store}")
        if item.refund_deadline:
            days_left = (item.refund_deadline - today).days
            lines.append(f"   ⏰ 환불 마감: {item.refund_deadline} (D-{days_left})")
        if item.warranty_end_date:
            days_left = (item.warranty_end_date - today).days
            lines.append(f"   🛡️ 보증 만료: {item.warranty_end_date} (D-{days_left})")
        lines.append("")
    
    lines.append("⚠️ 기한 내에 처리하세요!")
    return "\n".join(lines)


# SMTP 설정이 충분한지 판단합니다.
def _is_email_configured(settings: AppSettings) -> bool:
    """SMTP 설정이 모두 존재하는지 확인합니다."""

    return all(
        [
            settings.SMTP_HOST,
            settings.SMTP_PORT,
            settings.SMTP_USERNAME,
            settings.SMTP_PASSWORD,
            settings.SMTP_FROM,
        ]
    )


# 텔레그램 설정이 충분한지 판단합니다.
def _is_telegram_configured(settings: AppSettings) -> bool:
    """텔레그램 봇 토큰이 있는지 확인합니다."""

    return bool(settings.TELEGRAM_BOT_TOKEN)


# 오늘 기준으로 보증/환불 임박 상품을 찾아 DailyAlert 리스트를 생성합니다.
async def generate_daily_alerts(
    session: Session,
    today: date | None = None,
) -> list[DailyAlert]:
    """오늘 기준 알림 대상을 계산합니다.

    초급자용 설명:
    - 이 함수는 DB를 조회해서 “누가, 어떤 제품에 대해” 알림을 받아야 하는지 계산합니다.
    - 실제 전송은 send_daily_alerts에서 처리하도록 분리해 책임을 나눕니다.
    """

    base_date = today or date.today()
    alerts: list[DailyAlert] = []

    settings_list = session.exec(select(NotificationSettings)).all()
    for settings in settings_list:
        user = session.exec(select(User).where(User.id == settings.user_id)).first()
        if not user:
            continue

        warranty_days = _parse_days(settings.warranty_days_before, [30, 7, 3])
        refund_days = _parse_days(settings.refund_days_before, [3])

        products = session.exec(select(Product).where(Product.user_id == settings.user_id)).all()
        items = _collect_due_items(products, base_date, warranty_days, refund_days)
        if not items:
            continue

        email = user.email if settings.email_enabled else None
        telegram_chat_id: str | None = None
        if settings.telegram_enabled:
            account = session.exec(
                select(TelegramAccount).where(TelegramAccount.user_id == settings.user_id)
            ).first()
            if account:
                telegram_chat_id = account.chat_id

        alerts.append(
            DailyAlert(
                user_id=settings.user_id,
                email=email,
                telegram_chat_id=telegram_chat_id,
                items=items,
            )
        )

    return alerts


# 알림 리스트를 각 채널로 발송하고 요약을 반환합니다.
async def send_daily_alerts(
    alerts: list[DailyAlert],
    today: date | None = None,
    settings: AppSettings | None = None,
) -> DailyAlertsSummary:
    """알림 전송을 수행하고 집계 결과를 반환합니다.

    초급자용 설명:
    - 외부 설정이 없으면 전송을 건너뛰고, 실패 대신 안전한 요약을 반환합니다.
    - 한 사용자 전송 실패가 전체 cron을 죽이지 않도록 예외를 잡아 집계만 남깁니다.
    """

    base_date = today or date.today()
    config = settings or get_settings()

    email_targets = sum(1 for alert in alerts if alert.email)
    telegram_targets = sum(1 for alert in alerts if alert.telegram_chat_id)

    skipped: dict[str, bool | str | None] = {"email": False, "telegram": False, "reason": None}
    errors: list[str] = []

    email_configured = _is_email_configured(config)
    telegram_configured = _is_telegram_configured(config)

    if email_targets and not email_configured:
        skipped["email"] = True
    if telegram_targets and not telegram_configured:
        skipped["telegram"] = True

    if skipped["email"] and skipped["telegram"]:
        skipped["reason"] = "email_and_telegram_not_configured"
    elif skipped["email"]:
        skipped["reason"] = "email_not_configured"
    elif skipped["telegram"]:
        skipped["reason"] = "telegram_not_configured"

    email_sent = 0
    telegram_sent = 0

    if email_configured:
        for alert in alerts:
            if not alert.email:
                continue
            try:
                subject = f"[ASHD] {base_date.isoformat()} 알림"
                body = _format_alert_message(alert, base_date)
                await send_email([alert.email], subject, body)
                email_sent += 1
            except Exception:
                errors.append(f"email_failed_user_{alert.user_id}")

    if telegram_configured:
        for alert in alerts:
            if not alert.telegram_chat_id:
                continue
            try:
                chat_id = int(alert.telegram_chat_id)
            except ValueError:
                errors.append(f"telegram_invalid_chat_id_user_{alert.user_id}")
                continue

            try:
                text = _format_alert_message(alert, base_date)
                await send_telegram_message(chat_id, text)
                telegram_sent += 1
            except Exception:
                errors.append(f"telegram_failed_user_{alert.user_id}")

    return DailyAlertsSummary(
        date=base_date,
        processed=len(alerts),
        email_targets=email_targets,
        telegram_targets=telegram_targets,
        email_sent=email_sent,
        telegram_sent=telegram_sent,
        skipped=skipped,
        errors=errors,
    )


# 알림 계산과 발송을 한 번에 실행하는 진입점입니다.
async def run_daily_alerts(
    session: Session,
    today: date | None = None,
) -> DailyAlertsSummary:
    """알림 계산과 전송을 한 번에 수행합니다."""

    alerts = await generate_daily_alerts(session, today=today)
    return await send_daily_alerts(alerts, today=today)
