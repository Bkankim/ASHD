"""마스킹 미들웨어 회귀 테스트."""

import uuid


# JSON 응답의 content-type이 중복되지 않는지 확인합니다.
def test_json_content_type_single(client):
    """JSON 응답은 content-type 헤더가 1개만 유지되는지 확인합니다."""
    resp = client.get("/health")
    assert resp.status_code == 200
    content_types = resp.headers.get_list("content-type")
    assert len(content_types) == 1
    assert "application/json" in content_types[0].lower()


# 스트리밍 응답이 그대로 유지되는지 확인합니다.
def test_streaming_response_passthrough(client):
    """스트리밍 응답은 미들웨어가 건드리지 않는지 확인합니다."""
    resp = client.get("/health/stream")
    assert resp.status_code == 200
    assert resp.text == "ok"
    content_types = resp.headers.get_list("content-type")
    assert len(content_types) == 1
    assert "text/plain" in content_types[0].lower()


# /auth 응답은 마스킹에서 제외되는지 확인합니다.
def test_auth_response_not_redacted(client):
    """회원가입 응답에서 email이 마스킹되지 않는지 확인합니다."""
    email = f"user-{uuid.uuid4().hex}@example.com"
    payload = {"email": email, "password": "password123"}
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 201
    assert resp.json()["email"] == email


# 깨진 JSON 응답이 원문 그대로 유지되는지 확인합니다.
def test_broken_json_passthrough(client):
    """JSON 파싱 실패 시 원문 바디가 유지되는지 확인합니다."""
    resp = client.get("/health/broken-json")
    assert resp.status_code == 200
    assert resp.text == '{"status": "ok"'
    content_types = resp.headers.get_list("content-type")
    assert len(content_types) == 1
    assert "application/json" in content_types[0].lower()
