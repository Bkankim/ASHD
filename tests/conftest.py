"""공통 테스트 픽스처를 정의합니다.

초급자용 설명:
- 이 파일의 픽스처는 모든 테스트 파일에서 자동으로 사용할 수 있습니다.
- 테스트마다 독립적인 SQLite DB를 사용해, 실제 개발 DB(ashd.db)를 건드리지 않습니다.
"""

import os
import uuid
from typing import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

import sys
from pathlib import Path

# __file__ 기준으로 프로젝트 루트(/home/sweetbkan/ASHD)를 찾아서 sys.path에 추가합니다.
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    # sys.path 맨 앞에 넣어 우선순위를 높입니다.
    sys.path.insert(0, str(ROOT_DIR))

import app.core.db as db
import app.main as main
from app.main import create_app


# 테스트 전용 SQLite 엔진을 제공하는 픽스처입니다.
@pytest.fixture
def test_engine(tmp_path) -> Iterator:
    """테스트 전용 SQLite 엔진을 생성합니다.

    - tmp_path 아래에 임시 DB 파일을 만들고, 테스트가 끝나면 자동 정리됩니다.
    - check_same_thread=False 옵션으로 FastAPI/TestClient에서 스레드 공유를 허용합니다.
    """

    test_db_path = tmp_path / "test_ashd.db"
    engine = create_engine(f"sqlite:///{test_db_path}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    yield engine


# 테스트용 FastAPI 앱을 제공하는 픽스처입니다.
@pytest.fixture
def app(test_engine):
    """테스트용 FastAPI 앱을 생성합니다.

    - main/core 모듈의 엔진을 테스트 엔진으로 교체합니다.
    - DB 세션 의존성(get_session)을 테스트 세션으로 override 합니다.
    """

    db.engine = test_engine
    main.engine = test_engine

    def get_session_override():
        with Session(test_engine) as session:
            yield session

    application = create_app()
    application.dependency_overrides[db.get_session] = get_session_override
    return application


# TestClient를 제공하는 픽스처입니다.
@pytest.fixture
def client(app):
    """FastAPI TestClient 픽스처입니다."""

    return TestClient(app)


# 테스트 전용 DB 세션을 제공하는 픽스처입니다.
@pytest.fixture
def db_session(test_engine):
    """테스트용 DB 세션을 제공합니다."""

    with Session(test_engine) as session:
        yield session


# 테스트용 사용자와 토큰을 만드는 헬퍼 픽스처입니다.
@pytest.fixture
def make_user_and_token(client):
    """테스트 사용자 생성 + 액세스 토큰 발급 헬퍼.

    - 무작위 이메일로 회원가입 후 로그인하여 토큰을 반환합니다.
    - 헤더에 바로 넣어 쓸 수 있도록 Authorization 값을 함께 제공합니다.
    """

    def _make(password: str = "test-password"):
        email = f"test-{uuid.uuid4().hex}@example.com"
        reg = client.post("/auth/register", json={"email": email, "password": password})
        assert reg.status_code == 201
        user = reg.json()

        login = client.post("/auth/login", json={"email": email, "password": password})
        assert login.status_code == 200
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        return {"email": email, "password": password, "token": token, "headers": headers, "user": user}

    return _make
