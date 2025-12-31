"""cron 엔드포인트 보안 동작을 검증합니다."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.cron import router as cron_router
from app.core.config import get_settings


# 테스트 전용 앱을 생성하는 헬퍼입니다.
def _build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(cron_router)
    return app


# 시크릿 없이 403을 반환하는지 확인합니다.
def test_cron_forbidden_without_secret(monkeypatch) -> None:
    monkeypatch.setenv("CRON_SECRET", "")
    get_settings.cache_clear()
    app = _build_app()
    response = TestClient(app).post("/internal/cron/daily-alerts")
    assert response.status_code == 403


# 올바른 시크릿이면 501을 반환하는지 확인합니다.
def test_cron_authorized_returns_501(monkeypatch) -> None:
    monkeypatch.setenv("CRON_SECRET", "test-secret")
    get_settings.cache_clear()

    app = _build_app()
    response = TestClient(app).post(
        "/internal/cron/daily-alerts",
        headers={"X-CRON-SECRET": "test-secret"},
    )
    assert response.status_code == 501
