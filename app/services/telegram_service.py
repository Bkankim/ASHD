"""텔레그램 알림 발송을 담당하는 서비스 스켈레톤입니다."""

import httpx

from app.core.config import settings


async def send_telegram_message(chat_id: int, text: str) -> None:
    """지정된 chat_id로 텔레그램 메시지를 전송하는 비동기 함수입니다.

    초급자용 설명:
    - 텔레그램 봇 API는 HTTP 요청으로 메시지를 보내는 방식입니다.
    - 이 함수는 '어떤 텍스트를 어떤 사용자에게 보낼지'만 신경 쓰고,
      토큰/엔드포인트 구성은 내부에서 처리합니다.
    """
    base_url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}

    async with httpx.AsyncClient() as client:
        await client.post(base_url, json=payload)
