"""애플리케이션 헬스체크 유틸을 모아두는 모듈입니다."""
from sqlalchemy import text
from sqlmodel import Session


def check_db_health(session: Session) -> bool:
    """DB 연결이 살아있는지 확인하기 위해 아주 간단한 쿼리를 실행합니다.

    초급자용 설명:
    - DB에 접속이 가능한지 확인하려면 간단한 SELECT 1 같은 쿼리를 보내봅니다.
    - 쿼리가 예외 없이 실행되면 True를, 실패하면 False를 반환합니다.
    """

    try:
        session.exec(text("SELECT 1"))
        return True
    except Exception:
        return False
