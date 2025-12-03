"""DB 엔진과 세션 의존성을 정의하는 모듈입니다.

v0.1에서는 sync SQLModel + SQLite를 사용합니다.
추후 PostgreSQL로 전환할 때는 DATABASE_URL만 바꾸면 됩니다.
"""

from functools import lru_cache
from typing import Generator, Optional

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import get_settings


def _is_sqlite_url(url: str) -> bool:
    """SQLite URL 여부를 단순 검사합니다."""

    return url.startswith("sqlite")


@lru_cache(maxsize=1)
def get_engine():
    """애플리케이션 전역에서 재사용할 SQLModel 엔진을 생성합니다."""

    settings = get_settings()
    connect_args: Optional[dict[str, object]] = None

    # SQLite 전용 옵션: FastAPI 스레드에서 동일 연결을 공유하려면 check_same_thread를 꺼야 합니다.
    if _is_sqlite_url(settings.DATABASE_URL):
        connect_args = {"check_same_thread": False}

    # 운영 환경에서 PostgreSQL 등으로 전환할 때는 DATABASE_URL만 변경하면 됩니다.
    return create_engine(settings.DATABASE_URL, connect_args=connect_args or {})


# 모듈 레벨에서 엔진을 만들어 두면 import 시 한 번만 생성되어 재사용됩니다.
engine = get_engine()


def get_session() -> Generator[Session, None, None]:
    """FastAPI 의존성으로 사용할 세션 제공 함수입니다.

    - 요청이 들어올 때마다 새로운 DB 세션을 만들고(yield 이전),
      응답 후 with 블록을 빠져나오면서 세션이 자동으로 닫힙니다.
    - 이 패턴 덕분에 세션 누수 없이 요청 단위로 깨끗한 연결을 사용할 수 있습니다.
    """

    with Session(engine) as session:
        yield session
