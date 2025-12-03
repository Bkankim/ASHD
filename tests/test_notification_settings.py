"""NotificationSettings 관련 테스트."""

from fastapi import status


def _auth(client, email="notify@example.com", password="pw1234"):
    client.post("/auth/register", json={"email": email, "password": password})
    token = client.post("/auth/login", json={"email": email, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_notification_settings_create_and_read_defaults(client):
    """최초 GET 시 기본 알림 설정이 생성되고 반환되는지 확인합니다."""

    headers = _auth(client)
    resp = client.get("/notification-settings", headers=headers)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["email_enabled"] is True
    assert data["telegram_enabled"] is False
    assert data["warranty_days_before"] == [30, 7, 3]
    assert data["refund_days_before"] == [3]


def test_notification_settings_update_lists(client):
    """리스트[int]로 값을 보내면 응답에서도 리스트로 유지되는지 확인합니다."""

    headers = _auth(client, email="notify2@example.com")
    resp = client.put(
        "/notification-settings",
        json={
            "email_enabled": False,
            "telegram_enabled": True,
            "warranty_days_before": [14, 3],
            "refund_days_before": [2],
        },
        headers=headers,
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["email_enabled"] is False
    assert data["telegram_enabled"] is True
    assert data["warranty_days_before"] == [14, 3]
    assert data["refund_days_before"] == [2]


def test_notification_settings_requires_auth(client):
    """인증 없이 접근 시 401을 반환하는지 확인합니다."""

    resp = client.get("/notification-settings")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
