"""인증/인가 관련 라우터 모듈입니다."""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from app.api.dependencies.auth import get_current_user
from app.core.config import get_settings
from app.core.db import get_session
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.notification import NotificationSettings
from app.models.user import User
from app.schemas.user import UserCreate, UserRead
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/auth", tags=["auth"])


class TokenResponse(BaseModel):
    """Access Token 응답 스키마입니다."""

    access_token: str
    token_type: str


class LoginRequest(BaseModel):
    """로그인 요청 스키마입니다."""

    email: EmailStr
    password: str


class ChangePasswordRequest(BaseModel):
    """비밀번호 변경 요청 스키마입니다."""

    current_password: str
    new_password: str


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def _get_user_by_email(session: Session, email: str) -> User | None:
    """이메일로 사용자 조회 후 반환합니다."""

    result = session.exec(select(User).where(User.email == email))
    return result.first()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, session: Session = Depends(get_session)) -> UserRead:
    """회원가입 엔드포인트.

    - 이메일 중복 검사 후 비밀번호를 해시해 저장합니다.
    - 가입 직후 NotificationSettings 기본 레코드를 생성합니다.
    """

    existing = _get_user_by_email(session, user_in.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    password_hash = get_password_hash(user_in.password)
    user = User(email=user_in.email, password_hash=password_hash)
    session.add(user)
    session.commit()
    session.refresh(user)

    # 가입 시 기본 알림 설정을 함께 생성 (1:1, 중복 방지)
    settings = NotificationSettings(
        user_id=user.id,
        email_enabled=True,
        telegram_enabled=False,
        warranty_days_before="[30, 7, 3]",
        refund_days_before="[3]",
    )
    session.add(settings)
    session.commit()

    return user


@router.post("/login", response_model=TokenResponse)
def login(
    login_req: LoginRequest,
    session: Session = Depends(get_session),
) -> TokenResponse:
    """로그인 엔드포인트 (JSON 바디)."""

    # JSON 바디로 받은 이메일/비밀번호를 검증합니다.
    user = _get_user_by_email(session, login_req.email)
    if not user or not verify_password(login_req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    settings = get_settings()
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        {"sub": str(user.id), "email": user.email},
        expires_delta=access_token_expires,
    )
    return TokenResponse(access_token=token, token_type="bearer")


@router.post("/change-password", status_code=status.HTTP_200_OK)
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> dict[str, str]:
    """비밀번호 변경 엔드포인트.

    - 현재 비밀번호를 확인한 뒤 새 비밀번호로 교체합니다.
    - 토큰만 있다고 해서 바로 변경하지 못하도록 현재 비밀번호 검증 단계를 둡니다.
    """

    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    current_user.password_hash = get_password_hash(payload.new_password)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return {"detail": "Password changed successfully"}
