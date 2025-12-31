"""cron 트리거 라우트를 정의합니다.

초급자용 설명:
- 무료 PaaS 환경에서는 외부 cron이 HTTP로 호출하는 방식을 사용합니다.
- 아직 시크릿 검증(2.2)과 실행 로직(2.3)을 붙이지 않았으므로 501을 반환합니다.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.cron import verify_cron_secret

router = APIRouter(prefix="/internal/cron", tags=["cron"])


@router.post("/daily-alerts")
# 일일 알림 트리거 엔드포인트(스켈레톤)입니다.
def trigger_daily_alerts(_: None = Depends(verify_cron_secret)) -> dict[str, str]:
    """일일 알림 트리거 엔드포인트(스켈레톤)입니다.

    현재 단계에서는 보안(시크릿 검증)과 실행 로직이 연결되지 않았으므로 501을 반환합니다.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=(
            "task 2.2에서 CRON_SECRET 보호 추가 예정, "
            "task 2.3에서 실행 로직 연결 예정"
        ),
    )
