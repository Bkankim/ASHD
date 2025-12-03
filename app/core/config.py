"""Pydantic v1 BaseSettings로 환경 변수를 관리하는 모듈입니다.

v0.1에서는 단순성을 위해 pydantic<2로 고정했습니다.
추후 PostgreSQL 등 외부 DB를 쓰고 싶다면 DATABASE_URL만 교체하면 됩니다.
추후 pydantic v2로 올릴 때는 pydantic-settings 기반으로 마이그레이션하면 됩니다.
"""

from functools import lru_cache
from typing import Optional

from pydantic import BaseSettings


class AppSettings(BaseSettings):
    """애플리케이션 전역 설정을 담는 클래스입니다.

    초급자용 설명:
    - .env 또는 환경 변수에서 값을 읽어옵니다.
    - get_settings()를 통해 싱글톤 인스턴스를 재사용합니다.
    - 비밀정보를 코드에 하드코딩하지 않고 안전하게 분리합니다.
    """

    # 기본 실행 환경 플래그
    APP_ENV: str = "local"
    APP_DEBUG: bool = True

    # 데이터베이스 설정 (v0.1: sync SQLite 기본, 운영 시 PostgreSQL URL로 교체 가능)
    DATABASE_URL: str = "sqlite:///./ashd.db"
    # JWT/토큰 설정 (v0.1: 단순 Access Token만 사용)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_ALGORITHM: str = "HS256"

    # 보안/서명 키 (반드시 .env에서 설정)
    SECRET_KEY: str

    # 이메일(SMTP) 설정
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: Optional[str] = None

    # 텔레그램 봇 설정
    TELEGRAM_BOT_TOKEN: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """환경 변수를 읽어 Settings 싱글톤을 반환합니다."""

    return AppSettings()
