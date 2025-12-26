"""헬스체크 엔드포인트 테스트."""


# 헬스 체크 JSON 응답을 검증합니다.
def test_health_check(client):
    """인증 없이도 /health가 200 OK와 db 상태를 반환하는지 확인합니다."""

    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "db" in data


# 텍스트 응답이 미들웨어에 의해 변형되지 않는지 확인합니다.
def test_health_plain_text(client):
    """JSON이 아닌 응답은 미들웨어가 그대로 통과시키는지 확인합니다."""
    resp = client.get("/health/plain")
    assert resp.status_code == 200
    assert resp.text == "ok"


# 스트리밍 응답이 미들웨어에서 스킵되는지 확인합니다.
def test_health_streaming(client):
    """스트리밍 응답이 미들웨어에서 스킵되는지 확인합니다."""
    resp = client.get("/health/stream")
    assert resp.status_code == 200
    assert resp.text == "ok"


def test_health_cookies(client):
    """Set-Cookie 중복 헤더가 유지되는지 확인합니다."""
    resp = client.get("/health/cookies")
    assert resp.status_code == 200
    cookies = resp.headers.get_list("set-cookie")
    assert len(cookies) >= 2
