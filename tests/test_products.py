"""Product CRUD 테스트."""

from datetime import datetime

from fastapi import status


def _auth(client, email="prod@example.com", password="pw1234"):
    client.post("/auth/register", json={"email": email, "password": password})
    token = client.post("/auth/login", json={"email": email, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_product_crud_flow(client):
    """제품 생성 → 조회 → 수정 → 삭제까지 한 사용자의 스코프로 동작하는지 확인합니다."""

    headers = _auth(client, email="user1@example.com")

    create_payload = {"title": "상품A", "amount": 10000}
    created = client.post("/products", json=create_payload, headers=headers)
    assert created.status_code == status.HTTP_201_CREATED
    product = created.json()
    assert product["title"] == "상품A"
    assert "user_id" in product
    pid = product["id"]

    # 목록 조회: 본인 제품만 나와야 함
    listed = client.get("/products", headers=headers).json()
    assert any(p["id"] == pid for p in listed)

    # 단건 조회
    got = client.get(f"/products/{pid}", headers=headers)
    assert got.status_code == status.HTTP_200_OK

    # 수정: updated_at이 갱신되는지 확인
    before_updated = got.json()["updated_at"]
    updated = client.put(f"/products/{pid}", json={"store": "새 상점"}, headers=headers)
    assert updated.status_code == status.HTTP_200_OK
    after_updated = updated.json()["updated_at"]
    assert after_updated != before_updated

    # 삭제 후 404
    deleted = client.delete(f"/products/{pid}", headers=headers)
    assert deleted.status_code == status.HTTP_204_NO_CONTENT
    not_found = client.get(f"/products/{pid}", headers=headers)
    assert not_found.status_code == status.HTTP_404_NOT_FOUND


def test_product_scope_other_user(client):
    """다른 사용자의 제품에 접근하면 404를 반환하는지 확인합니다."""

    headers1 = _auth(client, email="u1@example.com")
    headers2 = _auth(client, email="u2@example.com")

    created = client.post("/products", json={"title": "내 제품"}, headers=headers1).json()
    pid = created["id"]

    resp = client.get(f"/products/{pid}", headers=headers2)
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_product_requires_auth(client):
    """인증 없이 제품 API를 호출하면 401을 반환하는지 확인합니다."""

    resp = client.get("/products")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
