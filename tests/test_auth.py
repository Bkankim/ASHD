"""인증 관련 엔드포인트 테스트."""

from fastapi import status


def test_register_and_duplicate(client):
    """회원가입 성공 후 같은 이메일로 가입 시 409를 반환하는지 확인합니다."""

    email = "dup@example.com"
    payload = {"email": email, "password": "password123"}

    first = client.post("/auth/register", json=payload)
    assert first.status_code == status.HTTP_201_CREATED
    data = first.json()
    assert data["email"] == email
    assert "id" in data

    dup = client.post("/auth/register", json=payload)
    assert dup.status_code == status.HTTP_409_CONFLICT


def test_login_success_and_failure(client):
    """로그인 성공/실패 케이스를 검증합니다."""

    email = "login@example.com"
    password = "pw1234"
    client.post("/auth/register", json={"email": email, "password": password})

    ok = client.post("/auth/login", json={"email": email, "password": password})
    assert ok.status_code == status.HTTP_200_OK
    assert "access_token" in ok.json()

    bad_pw = client.post("/auth/login", json={"email": email, "password": "wrong"})
    assert bad_pw.status_code == status.HTTP_401_UNAUTHORIZED

    bad_email = client.post("/auth/login", json={"email": "none@example.com", "password": "pw"})
    assert bad_email.status_code == status.HTTP_401_UNAUTHORIZED


def test_change_password_flow(client, make_user_and_token):
    """비밀번호 변경 후 새 비밀번호로 로그인되고, 이전 비밀번호는 실패하는지 확인합니다."""

    user = make_user_and_token(password="oldpw123")
    headers = user["headers"]

    change = client.post(
        "/auth/change-password",
        json={"current_password": "oldpw123", "new_password": "newpw456"},
        headers=headers,
    )
    assert change.status_code == status.HTTP_200_OK

    # 새 비밀번호로 로그인 성공
    ok = client.post("/auth/login", json={"email": user["email"], "password": "newpw456"})
    assert ok.status_code == status.HTTP_200_OK

    # 이전 비밀번호는 실패
    fail = client.post("/auth/login", json={"email": user["email"], "password": "oldpw123"})
    assert fail.status_code == status.HTTP_401_UNAUTHORIZED


def test_change_password_wrong_current(client, make_user_and_token):
    """현재 비밀번호가 틀리면 400을 반환하는지 확인합니다."""

    user = make_user_and_token(password="oldpw123")
    headers = user["headers"]

    resp = client.post(
        "/auth/change-password",
        json={"current_password": "badpw", "new_password": "newpw456"},
        headers=headers,
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST


def test_change_password_unauthenticated(client):
    """토큰 없이 비밀번호 변경을 시도하면 401을 반환하는지 확인합니다."""

    resp = client.post(
        "/auth/change-password",
        json={"current_password": "pw", "new_password": "pw2"},
    )
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
