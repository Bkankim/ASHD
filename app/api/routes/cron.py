"""cron 트리거 라우트를 정의합니다.

초급자용 설명:
- 무료 PaaS 환경에서는 외부 cron이 HTTP로 호출하는 방식을 사용합니다.
- CRON_SECRET 검증을 통과한 요청만 처리합니다.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.api.dependencies.cron import verify_cron_secret
from app.core.db import get_session
from app.services.notification_service import run_daily_alerts

router = APIRouter(prefix="/internal/cron", tags=["cron"])


@router.post("/daily-alerts")
# 일일 알림을 계산/발송하는 트리거 엔드포인트입니다.
async def trigger_daily_alerts(
    _: None = Depends(verify_cron_secret),
    session: Session = Depends(get_session),
) -> dict[str, object]:
    """일일 알림 트리거 엔드포인트입니다.

    - 알림 계산과 전송을 수행한 뒤 요약 결과만 반환합니다.
    - 민감정보/상세 목록은 반환하지 않습니다.
    """
    try:
        summary = await run_daily_alerts(session)
    except Exception as exc:  # 복구 가능한 수준에서만 오류를 포장
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="internal error",
        ) from exc

    return {
        "status": "ok",
        "date": summary.date.isoformat(),
        "processed": summary.processed,
        "email_targets": summary.email_targets,
        "telegram_targets": summary.telegram_targets,
        "email_sent": summary.email_sent,
        "telegram_sent": summary.telegram_sent,
        "skipped": summary.skipped,
        "errors": summary.errors,
    }
