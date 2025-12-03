"""헬스체크 엔드포인트 테스트."""


def test_health_check(client):
    """인증 없이도 /health가 200 OK와 db 상태를 반환하는지 확인합니다."""

    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "db" in data
