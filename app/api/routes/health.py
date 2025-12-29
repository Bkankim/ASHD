"""서비스 상태를 확인하기 위한 헬스 체크 엔드포인트입니다."""

from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse, Response, StreamingResponse
from sqlmodel import Session

from app.core.config import get_settings
from app.core.db import get_session
from app.core.health import check_db_health

router = APIRouter(prefix="/health", tags=["health"])
_settings = get_settings()


@router.get("", summary="헬스 체크")
def health_check(session: Session = Depends(get_session)) -> dict:
    """서비스가 살아있는지 간단히 확인하는 엔드포인트입니다.

    - DB 연결이 살아있는지도 함께 확인합니다.
    - 인증 없이 호출 가능한 공개 헬스 체크입니다.
    """
    db_status = "ok" if check_db_health(session) else "error"
    return {"status": "ok", "db": db_status}


# prod 환경에서는 테스트용 라우트를 등록하지 않습니다.
if _settings.APP_ENV.lower() != "prod":
    # 텍스트 응답을 반환하는 헬스 체크입니다.
    @router.get("/plain", summary="헬스 체크 (텍스트)")
    def health_plain() -> Response:
        """텍스트 응답이 미들웨어를 통과하는지 확인하기 위한 엔드포인트입니다."""
        return Response(content="ok", media_type="text/plain")

    # 스트리밍 응답을 반환하는 헬스 체크입니다.
    @router.get("/stream", summary="헬스 체크 (스트리밍)")
    def health_stream() -> StreamingResponse:
        """스트리밍 응답이 마스킹 미들웨어에서 스킵되는지 확인합니다."""

        def _gen():
            yield b"ok"

        return StreamingResponse(_gen(), media_type="text/plain")

    # 쿠키 중복 헤더를 검증하는 헬스 체크입니다.
    @router.get("/cookies", summary="헬스 체크 (쿠키)")
    def health_cookies() -> JSONResponse:
        """Set-Cookie 중복 헤더 유지 여부를 검증하기 위한 엔드포인트입니다."""
        resp = JSONResponse({"status": "ok"})
        resp.set_cookie("cookie_a", "value_a")
        resp.set_cookie("cookie_b", "value_b")
        return resp

    # 깨진 JSON 응답을 반환하는 헬스 체크입니다.
    @router.get("/broken-json", summary="헬스 체크 (깨진 JSON)")
    def health_broken_json() -> Response:
        """JSON 파싱 실패 시에도 원문 바디가 유지되는지 확인합니다."""
        return Response(content=b'{"status": "ok"', media_type="application/json")
