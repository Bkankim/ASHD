"""보증/환불 임박 알림을 계산하고, 각 채널로 보내는 서비스 스켈레톤입니다."""

from dataclasses import dataclass
from datetime import date
from typing import List


@dataclass
class DailyAlertItem:
    """알림 대상이 되는 단일 제품 정보를 담는 데이터 구조입니다."""

    product_id: int
    title: str
    purchase_date: date | None
    refund_deadline: date | None
    warranty_end_date: date | None


@dataclass
class DailyAlert:
    """특정 사용자에 대한 하루치 알림 정보를 담는 데이터 구조입니다."""

    user_id: int
    email: str | None
    items: List[DailyAlertItem]


async def generate_daily_alerts() -> list[DailyAlert]:
    """오늘 기준으로 보증/환불 임박 상품을 찾아 DailyAlert 리스트를 생성합니다.

    현재는 실제 DB를 조회하지 않고, TODO로 남겨둔 상태입니다.

    초급자용 설명:
    - 이 함수는 '어떤 사용자가 어떤 제품에 대해 알림을 받아야 하는지'
      도메인 관점에서만 결정합니다.
    - 실제 이메일/텔레그램 전송은 별도의 모듈에서 담당하게 분리하는 것이 좋습니다.
    """
    # TODO: DB에서 Product, NotificationSettings 등을 조회하여 실제 DailyAlert 리스트를 구성
    return []
