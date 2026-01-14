"""cron 트리거용 보안 의존성을 제공합니다.

초급자용 설명:
- 외부 cron이 호출할 때 X-CRON-SECRET 헤더를 확인합니다.
- 설정된 CRON_SECRET과 일치하지 않으면 403을 반환합니다.
"""

import secrets

from fastapi import HTTPException, Request, status

from app.core.config import get_settings


# cron 호출 시크릿을 검증하는 의존성 함수입니다.
def verify_cron_secret(request: Request) -> None:
    """cron 호출 시크릿을 검증합니다.

    v0.1 정책:
    - CRON_SECRET이 비어 있으면 무조건 거부(403)합니다.
    - 헤더 값과 설정 값이 안전 비교로 일치해야 통과합니다.
    """
    settings = get_settings()
    expected = settings.CRON_SECRET or ""
    provided = request.headers.get("X-CRON-SECRET", "")

    if not expected:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")

    if not secrets.compare_digest(provided, expected):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
