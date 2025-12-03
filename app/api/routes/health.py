"""서비스 상태를 확인하기 위한 헬스 체크 엔드포인트입니다."""

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.db import get_session
from app.core.health import check_db_health

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", summary="헬스 체크")
def health_check(session: Session = Depends(get_session)) -> dict:
    """서비스가 살아있는지 간단히 확인하는 엔드포인트입니다.

    - DB 연결이 살아있는지도 함께 확인합니다.
    - 인증 없이 호출 가능한 공개 헬스 체크입니다.
    """
    db_status = "ok" if check_db_health(session) else "error"
    return {"status": "ok", "db": db_status}
