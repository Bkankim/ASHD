"""UTC 시간 헬퍼를 제공하는 모듈입니다."""

from datetime import datetime, timezone


# UTC 기준 naive datetime을 반환합니다.
def utc_now() -> datetime:
    """UTC 기준 naive datetime을 반환합니다.

    초급자용 설명:
    - datetime.utcnow() 경고를 피하면서도 기존 DB 스키마(naive datetime)와 호환됩니다.
    - timezone.utc를 붙였다가 tzinfo를 제거해 naive UTC로 저장합니다.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
