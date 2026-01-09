"""cron 엔드포인트 보안 동작을 검증합니다."""

from datetime import date

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.cron import router as cron_router
from app.core.config import get_settings
from app.services.notification_service import DailyAlertsSummary


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


# 올바른 시크릿이면 200을 반환하는지 확인합니다.
def test_cron_authorized_returns_200(monkeypatch) -> None:
    monkeypatch.setenv("CRON_SECRET", "test-secret")
    get_settings.cache_clear()

    async def fake_run_daily_alerts(_session):
        return DailyAlertsSummary(
            date=date(2024, 1, 1),
            processed=1,
            email_targets=1,
            telegram_targets=0,
            email_sent=1,
            telegram_sent=0,
            skipped={"email": False, "telegram": True, "reason": "telegram_not_configured"},
            errors=[],
        )

    monkeypatch.setattr(
        "app.api.routes.cron.run_daily_alerts",
        fake_run_daily_alerts,
    )

    app = _build_app()
    response = TestClient(app).post(
        "/internal/cron/daily-alerts",
        headers={"X-CRON-SECRET": "test-secret"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["processed"] == 1
    assert payload["email_targets"] == 1
    assert payload["email_sent"] == 1
