"""ASHD 서비스의 FastAPI 엔트리 포인트입니다.

이 모듈은 다음 역할을 합니다.
1. FastAPI 애플리케이션 인스턴스를 생성합니다.
2. 라우터(health, products 등)를 등록합니다.
3. uvicorn으로 실행할 수 있도록 __main__ 블록을 제공합니다.
"""

from fastapi import Depends, FastAPI
from sqlmodel import Session, SQLModel

# from app.api.routes import auth, health, notification_settings, products, telegram_account
from app.api.routes import (
    auth,
    health,
    notification_settings,
    products,
    telegram_account as telegram_account_routes,  # 라우터에 별칭
)
from app.core.config import get_settings
from app.core.db import engine, get_session
from app.core.health import check_db_health
from app.models import notification, product, telegram_account, user  # noqa: F401


def create_app() -> FastAPI:
    """FastAPI 애플리케이션 인스턴스를 생성하는 함수입니다.

    초급자 입장에서:
    - 이 함수는 '앱을 어떻게 구성할지'를 한 곳에서 정의하도록 도와줍니다.
    - 나중에 테스트할 때도 이 함수를 호출해서 동일한 앱 인스턴스를 만들 수 있습니다.
    """
    app = FastAPI(
        title="ASHD API",
        description="AS/환불/보증 관리 서비스 ASHD의 백엔드 API",
        version="0.1.0",
    )

    # 설정을 한 번만 로드해 애플리케이션 상태에 저장합니다.
    app.state.settings = get_settings()

    # 앱 시작 시 DB 테이블을 생성합니다.
    # 주의: 모델이 정의된 모듈이 import되어 있어야 메타데이터에 반영됩니다.
    @app.on_event("startup")
    def on_startup() -> None:
        SQLModel.metadata.create_all(engine)

    # 간단한 DB 세션 의존성 사용 예시 (디버그용)
    @app.get("/debug/db-ping")
    def db_ping(session: Session = Depends(get_session)) -> dict[str, str]:
        # 요청이 들어올 때마다 세션이 주입되고, 응답 후 자동으로 닫힙니다.
        is_alive = check_db_health(session)
        return {"status": "ok" if is_alive else "error"}

    # 헬스 체크 및 도메인 관련 라우터 등록
    app.include_router(health.router)
    app.include_router(products.router)
    app.include_router(notification_settings.router)
    # app.include_router(telegram_account.router)
    app.include_router(telegram_account_routes.router)
    app.include_router(auth.router)

    return app


app = create_app()


if __name__ == "__main__":
    # 이 블록은 'python -m app.main' 형태로 실행할 때 사용됩니다.
    # 개발 환경에서는 보통 'uv run uvicorn app.main:app --reload' 명령을 사용합니다.
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
