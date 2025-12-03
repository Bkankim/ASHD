"""이메일 알림 발송을 담당하는 서비스 스켈레톤입니다."""

from typing import Sequence

from aiosmtplib import SMTP

from app.core.config import settings


async def send_email(to_addresses: Sequence[str], subject: str, body: str) -> None:
    """간단한 텍스트 이메일을 발송하는 비동기 함수입니다.

    초급자용 설명:
    - SMTP 프로토콜을 이용해 메일을 전송합니다.
    - 실제 서비스에서는 TLS 설정, 에러 처리, HTML 템플릿 등을 추가해야 합니다.
    """
    message = f"""From: {settings.smtp_username}\r
To: {', '.join(to_addresses)}\r
Subject: {subject}\r
\r
{body}
"""

    # 주의: 아래 코드는 예시이며, 실제 서비스에서는 예외 처리와 보안 설정이 더 필요합니다.
    async with SMTP(hostname=settings.smtp_host, port=settings.smtp_port, start_tls=True) as client:
        await client.login(settings.smtp_username, settings.smtp_password)
        await client.sendmail(settings.smtp_username, list(to_addresses), message)
