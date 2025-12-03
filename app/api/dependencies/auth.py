"""인증 관련 FastAPI 의존성 모듈입니다."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlmodel import Session, select

from app.core.db import get_session
from app.core.security import decode_access_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> User:
    """Bearer 토큰을 검증하고 현재 사용자를 조회합니다.

    초급자용 설명:
    - Depends를 사용하면 라우트마다 인증 코드를 복붙하지 않고 공통 의존성으로 처리할 수 있습니다.
    - Authorization 헤더에서 Bearer 토큰을 읽어 JWT를 검증한 뒤 user를 DB에서 불러옵니다.
    """

    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_error
    except JWTError:
        raise credentials_error

    result = session.exec(select(User).where(User.id == int(user_id)))
    user = result.first()
    if not user:
        raise credentials_error

    return user
