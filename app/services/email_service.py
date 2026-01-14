"""이메일 알림 발송을 담당하는 서비스 스켈레톤입니다."""

from typing import Sequence

from aiosmtplib import SMTP

from app.core.config import get_settings


# 이메일 알림 전송을 담당하는 함수입니다.
async def send_email(to_addresses: Sequence[str], subject: str, body: str) -> None:
    """간단한 텍스트 이메일을 발송하는 비동기 함수입니다.

    초급자용 설명:
    - SMTP 프로토콜을 이용해 메일을 전송합니다.
    - 실제 서비스에서는 TLS 설정, 에러 처리, HTML 템플릿 등을 추가해야 합니다.
    """

    # 설정은 호출 시점에 읽어, 테스트/환경에 따라 유연하게 동작하도록 합니다.
    settings = get_settings()
    from_address = settings.SMTP_FROM or settings.SMTP_USERNAME or ""

    message = f"""From: {from_address}\r
To: {', '.join(to_addresses)}\r
Subject: {subject}\r
\r
{body}
"""

    # 주의: 아래 코드는 예시이며, 실제 서비스에서는 예외 처리와 보안 설정이 더 필요합니다.
    async with SMTP(hostname=settings.SMTP_HOST, port=settings.SMTP_PORT, start_tls=True) as client:
        await client.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        await client.sendmail(from_address, list(to_addresses), message)
