"""TelegramAccount 관련 테스트."""

from datetime import datetime

from fastapi import status


def _auth(client, email="tg@example.com", password="pw1234"):
    client.post("/auth/register", json={"email": email, "password": password})
    token = client.post("/auth/login", json={"email": email, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_telegram_upsert_and_linked_at(client):
    """텔레그램 계정 upsert 시 linked_at이 갱신되고 telegram_enabled가 true가 되는지 확인합니다."""

    headers = _auth(client)

    first = client.post("/telegram-account", json={"chat_id": "12345", "username": "alice"}, headers=headers)
    assert first.status_code == status.HTTP_201_CREATED
    first_data = first.json()
    first_linked = first_data["linked_at"]

    # NotificationSettings가 true로 바뀌었는지 확인
    settings = client.get("/notification-settings", headers=headers).json()
    assert settings["telegram_enabled"] is True

    # 동일 user로 upsert 시 linked_at이 갱신
    second = client.post("/telegram-account", json={"chat_id": "67890", "username": "alice2"}, headers=headers)
    assert second.status_code == status.HTTP_201_CREATED
    second_data = second.json()
    assert second_data["chat_id"] == "67890"
    assert second_data["linked_at"] != first_linked


def test_telegram_get_and_delete(client):
    """등록 후 조회, 삭제 후 404를 반환하는지 확인합니다."""

    headers = _auth(client, email="tg2@example.com")
    client.post("/telegram-account", json={"chat_id": "55555", "username": "bob"}, headers=headers)

    got = client.get("/telegram-account", headers=headers)
    assert got.status_code == status.HTTP_200_OK

    deleted = client.delete("/telegram-account", headers=headers)
    assert deleted.status_code == status.HTTP_204_NO_CONTENT

    not_found = client.get("/telegram-account", headers=headers)
    assert not_found.status_code == status.HTTP_404_NOT_FOUND

    # 해제 후 telegram_enabled가 false인지 확인
    settings = client.get("/notification-settings", headers=headers).json()
    assert settings["telegram_enabled"] is False


def test_telegram_validation(client):
    """chat_id가 비어 있거나 너무 짧으면 422를 반환하는지 확인합니다."""

    headers = _auth(client, email="tg3@example.com")
    bad1 = client.post("/telegram-account", json={"chat_id": "", "username": "x"}, headers=headers)
    assert bad1.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    bad2 = client.post("/telegram-account", json={"chat_id": "1", "username": "x"}, headers=headers)
    assert bad2.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
