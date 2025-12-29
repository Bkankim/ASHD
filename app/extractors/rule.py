"""OCR 텍스트에서 룰 기반으로 필드를 추출하는 모듈입니다."""

from __future__ import annotations

from datetime import date, datetime
import re
from typing import Any


# 날짜 문자열을 date 객체로 변환하는 유틸 함수입니다.
def parse_date(value: str) -> date | None:
    """문자열에서 날짜를 파싱합니다.

    초급자용 설명:
    - OCR 결과는 다양한 포맷을 가질 수 있어 여러 패턴을 순서대로 시도합니다.
    - 실패하면 None을 반환해 '확실하지 않다'는 신호로 사용합니다.
    """
    value = value.strip()
    patterns = ["%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d"]
    for pattern in patterns:
        try:
            return datetime.strptime(value, pattern).date()
        except ValueError:
            continue
    return None


# 금액 문자열을 정수로 변환하는 유틸 함수입니다.
def parse_amount(value: str) -> int | None:
    """금액 문자열에서 숫자만 추출해 정수로 변환합니다."""
    cleaned = re.sub(r"[^0-9]", "", value)
    if not cleaned:
        return None
    return int(cleaned)


# OCR 텍스트에서 기본 필드를 추출합니다.
def extract_fields_with_rules(raw_text: str) -> dict[str, Any]:
    """간단한 정규식 룰로 제품 필드를 추출합니다.

    초급자용 설명:
    - 룰 기반 추출은 빠르고 비용이 없지만, 모든 케이스를 커버하기 어렵습니다.
    - 부족한 필드는 LLM 추출로 보완하도록 설계합니다.
    """
    fields: dict[str, Any] = {}
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    # 상호/매장명 추출
    for line in lines:
        if "상호" in line or "매장" in line or "판매처" in line:
            parts = re.split(r"[:：]", line, maxsplit=1)
            if len(parts) == 2:
                fields["store"] = parts[1].strip()
                break

    # 상품명/제품명 추출
    for line in lines:
        if "상품명" in line or "제품명" in line or "품목" in line:
            parts = re.split(r"[:：]", line, maxsplit=1)
            if len(parts) == 2:
                fields["title"] = parts[1].strip()
                break

    # 날짜(구매일) 추출
    date_match = re.search(r"(\d{4}[./-]\d{2}[./-]\d{2}|\d{8})", raw_text)
    if date_match:
        parsed = parse_date(date_match.group(1))
        if parsed:
            fields["purchase_date"] = parsed

    # 금액 추출
    amount_match = re.search(r"([0-9,]+)\s*원", raw_text)
    if amount_match:
        amount = parse_amount(amount_match.group(1))
        if amount is not None:
            fields["amount"] = amount

    # 주문번호 추출
    order_match = re.search(r"(주문번호|Order ID)[:\s]*([A-Za-z0-9-]+)", raw_text, re.IGNORECASE)
    if order_match:
        fields["order_id"] = order_match.group(2)

    # AS 연락처(전화번호) 추출
    phone_match = re.search(r"(\d{2,3}-\d{3,4}-\d{4})", raw_text)
    if phone_match:
        fields["as_contact"] = phone_match.group(1)

    # 환불/보증 기한 추출 (간단 룰)
    refund_match = re.search(r"환불[\s:]*([0-9./-]{8,10})", raw_text)
    if refund_match:
        parsed = parse_date(refund_match.group(1))
        if parsed:
            fields["refund_deadline"] = parsed

    warranty_match = re.search(r"보증[\s:]*([0-9./-]{8,10})", raw_text)
    if warranty_match:
        parsed = parse_date(warranty_match.group(1))
        if parsed:
            fields["warranty_end_date"] = parsed

    # 첫 줄이 있다면 title 대체값으로 사용합니다.
    if "title" not in fields and lines:
        fields["title"] = lines[0][:255]

    return fields
