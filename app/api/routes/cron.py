"""cron 트리거 라우트를 정의합니다.

초급자용 설명:
- 무료 PaaS 환경에서는 외부 cron이 HTTP로 호출하는 방식을 사용합니다.
- 아직 시크릿 검증(2.2)과 실행 로직(2.3)을 붙이지 않았으므로 501을 반환합니다.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.cron import verify_cron_secret
from app.services.notification_service import generate_daily_alerts

router = APIRouter(prefix="/internal/cron", tags=["cron"])


@router.post("/daily-alerts")
# 일일 알림 트리거 엔드포인트(스켈레톤)입니다.
async def trigger_daily_alerts(_: None = Depends(verify_cron_secret)) -> dict[str, int | str]:
    """일일 알림 트리거 엔드포인트입니다.

    현재는 알림 생성까지만 수행하고, 실제 발송은 별도 단계로 분리합니다.
    """
    try:
        alerts = await generate_daily_alerts()
    except Exception as exc:  # 복구 가능한 수준에서만 오류를 포장
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="internal error",
        ) from exc

    email_targets = sum(1 for alert in alerts if alert.email)
    return {
        "status": "ok",
        "processed": len(alerts),
        "email_targets": email_targets,
        "telegram_targets": 0,
    }
