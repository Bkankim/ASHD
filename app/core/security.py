"""인증/보안 관련 유틸 모듈입니다.

v0.1에서는 bcrypt 기반 비밀번호 해시와 단순 JWT Access Token만 사용합니다.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

# bcrypt 해시 설정 (passlib이 내부에서 안전한 솔트를 자동 생성/검증)
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
)


def get_password_hash(plain_password: str) -> str:
    """평문 비밀번호를 안전하게 해시합니다.

    초급자용 설명:
    - 평문 비밀번호를 DB에 저장하면 유출 시 큰 사고가 납니다.
    - bcrypt 같은 해시 함수를 사용하면, 해시값만 저장되어 유출 피해를 줄일 수 있습니다.
    """

    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """입력한 비밀번호가 저장된 해시와 일치하는지 검증합니다."""

    return pwd_context.verify(plain_password, password_hash)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """JWT Access Token을 생성합니다.

    초급자용 설명:
    - 토큰에 user_id, email 등 최소 정보를 담아 클라이언트에 전달합니다.
    - 만료 시간을 두어, 토큰이 영구적으로 사용되지 않도록 합니다.
    """

    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """JWT를 디코드하고 페이로드를 반환합니다.

    - 서명 검증에 실패하거나 토큰이 만료되면 JWTError를 발생시킵니다.
    """

    settings = get_settings()
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
