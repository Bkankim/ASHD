"""cron 엔드포인트 보안 동작을 검증합니다."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.cron import router as cron_router
from app.core.config import get_settings
from app.services.notification_service import DailyAlert, DailyAlertItem


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
def test_cron_authorized_returns_200(monkeypatch) -> None:
    monkeypatch.setenv("CRON_SECRET", "test-secret")
    get_settings.cache_clear()

    async def fake_generate_daily_alerts():
        return [
            DailyAlert(
                user_id=1,
                email="user@example.com",
                items=[
                    DailyAlertItem(
                        product_id=1,
                        title="테스트 제품",
                        purchase_date=None,
                        refund_deadline=None,
                        warranty_end_date=None,
                    )
                ],
            ),
        ]

    monkeypatch.setattr(
        "app.api.routes.cron.generate_daily_alerts",
        fake_generate_daily_alerts,
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
