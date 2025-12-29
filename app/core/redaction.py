"""민감정보 마스킹(레드액션) 유틸을 제공하는 모듈입니다."""

from __future__ import annotations

import os
import re
from typing import Any

try:
    from pydantic import BaseModel
except Exception:  # pydantic 미설치 환경을 대비합니다.
    BaseModel = object  # type: ignore


# 카드 관련 키워드 목록입니다.
_CARD_KEYWORDS = ["카드", "신용", "체크", "결제", "CARD", "카드번호"]

# 승인/거래/가맹/단말기 관련 키워드 목록입니다.
_APPROVAL_KEYWORDS = [
    "승인번호",
    "원거래번호",
    "거래번호",
    "가맹점번호",
    "가맹번호",
    "단말기",
    "단말기ID",
    "TID",
    "MID",
]

# 계좌번호 관련 키워드 목록입니다.
_ACCOUNT_KEYWORDS = ["계좌", "계좌번호", "은행", "ACCOUNT"]

# 카드번호 후보(숫자/공백/하이픈 포함)를 찾는 정규식입니다.
_CARD_LOOSE_PATTERN = re.compile(r"\b(?:\d[ -]?){11,18}\d\b")

# 카드번호 형식(4-4-4-4 또는 4 4 4 4)을 찾는 정규식입니다.
_CARD_STRICT_PATTERN = re.compile(r"\b\d{4}[ -]\d{4}[ -]\d{4}[ -]\d{4}\b")

# 승인/거래/가맹/단말기 번호 뒤 숫자열을 찾는 정규식입니다.
_APPROVAL_PATTERN = re.compile(
    r"(승인번호|원거래번호|거래번호|가맹점번호|가맹번호|단말기ID|단말기|TID|MID)(\s*[:：]?\s*)([0-9*\- ]{4,})",
    re.IGNORECASE,
)

# 계좌번호 뒤 숫자열을 찾는 정규식입니다.
_ACCOUNT_PATTERN = re.compile(r"(계좌번호|계좌|ACCOUNT)(\s*[:：]?\s*)([0-9*\- ]{6,})", re.IGNORECASE)

# 전화번호(휴대폰/지역번호)를 찾는 정규식입니다.
_PHONE_PATTERN = re.compile(r"\b(01[016789]|0\d{1,2})[- .]?\d{3,4}[- .]?\d{4}\b")

# 주민번호 형태(YYMMDD-XXXXXXX)를 찾는 정규식입니다.
_RRN_PATTERN = re.compile(r"\b(\d{6})-?(\d{7})\b")

# 주민번호 관련 키워드 목록입니다.
_RRN_KEYWORDS = ["주민번호", "주민등록", "주민", "RRN"]

# 이메일 주소 형태를 찾는 정규식입니다.
_EMAIL_PATTERN = re.compile(r"\b([A-Za-z0-9._%+-]{1,64})@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")


# strict 모드 여부를 확인합니다.
def _is_strict_enabled() -> bool:
    """환경 변수 또는 설정값으로 strict 모드를 확인합니다."""
    raw = os.getenv("REDACTION_STRICT")
    if raw is not None:
        return raw.lower() in ("1", "true", "yes", "on")

    try:
        from app.core.config import get_settings

        return bool(get_settings().REDACTION_STRICT)
    except Exception:
        return False


# 문자열에 특정 키워드가 포함되어 있는지 판단합니다.
def _contains_keyword(text: str, keywords: list[str]) -> bool:
    """키워드 목록 중 하나라도 포함되면 True를 반환합니다."""
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


# 숫자만 남긴 뒤 마스킹하고 원래 형식을 유지합니다.
def _mask_digits_keep_last(raw: str, keep_last: int) -> str:
    """뒤쪽 일부 자리만 남기고 숫자를 마스킹합니다."""
    digits = re.sub(r"\D", "", raw)
    if not digits:
        return raw
    if len(digits) <= keep_last:
        masked_digits = "*" * len(digits)
    else:
        masked_digits = ("*" * (len(digits) - keep_last)) + digits[-keep_last:]

    result = []
    index = 0
    for char in raw:
        if char.isdigit():
            result.append(masked_digits[index])
            index += 1
        else:
            result.append(char)
    return "".join(result)


# 숫자 전체를 마스킹합니다.
def _mask_digits_all(raw: str) -> str:
    """숫자를 모두 '*'로 마스킹합니다."""
    result = []
    for char in raw:
        if char.isdigit():
            result.append("*")
        else:
            result.append(char)
    return "".join(result)


# 승인/거래/가맹/단말기 번호를 마스킹합니다.
def _mask_keyword_number(match: re.Match[str]) -> str:
    """키워드 뒤 숫자열을 전부 마스킹합니다."""
    keyword = match.group(1)
    separator = match.group(2)
    number = match.group(3)
    return f"{keyword}{separator}{_mask_digits_all(number)}"


# 주민번호 패턴을 마스킹합니다.
def _mask_rrn(match: re.Match[str]) -> str:
    """주민번호 뒤 7자리를 마스킹합니다."""
    front = match.group(1)
    return f"{front}-*******"


# 이메일 주소를 마스킹합니다.
def _mask_email(match: re.Match[str]) -> str:
    """이메일 아이디를 대부분 마스킹합니다."""
    local = match.group(1)
    domain = match.group(2)
    if len(local) <= 1:
        masked = "*"
    else:
        masked = local[0] + "***"
    return f"{masked}@{domain}"


# 카드번호 패턴을 마스킹합니다.
def _mask_card(match: re.Match[str]) -> str:
    """카드번호는 뒤 4자리만 남기고 마스킹합니다."""
    return _mask_digits_keep_last(match.group(0), keep_last=4)


# 전화번호 패턴을 마스킹합니다.
def _mask_phone(match: re.Match[str]) -> str:
    """전화번호는 뒤 4자리만 남기고 마스킹합니다."""
    return _mask_digits_keep_last(match.group(0), keep_last=4)


# Luhn 검증을 수행합니다.
def _luhn_check(number: str) -> bool:
    """카드번호 후보가 유효한지 Luhn 알고리즘으로 검사합니다."""
    if not number.isdigit():
        return False
    total = 0
    reverse_digits = list(reversed(number))
    for index, char in enumerate(reverse_digits):
        digit = int(char)
        if index % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


# strict 모드에서 라벨 없는 카드번호 후보를 마스킹합니다.
def _mask_card_candidates_strict(line: str) -> str:
    """라벨 없이 등장하는 카드번호 후보를 Luhn 검사 후 마스킹합니다."""
    matches = list(_CARD_LOOSE_PATTERN.finditer(line))
    if not matches:
        return line

    result: list[str] = []
    last_index = 0
    for match in matches:
        raw = match.group(0)
        replacement = raw
        if "*" not in raw:
            digits = re.sub(r"\D", "", raw)
            if 13 <= len(digits) <= 19 and _luhn_check(digits):
                replacement = _mask_digits_keep_last(raw, keep_last=4)

        result.append(line[last_index : match.start()])
        result.append(replacement)
        last_index = match.end()

    result.append(line[last_index:])
    return "".join(result)


# 민감정보를 마스킹한 텍스트를 반환합니다.
def redact_text(text: str, strict: bool | None = None) -> str:
    """텍스트 내 민감정보를 찾아 마스킹합니다.

    초급자용 설명:
    - 이메일/전화번호/주민번호는 패턴 자체가 명확해 전역 적용합니다.
    - 카드번호/승인번호/계좌번호는 키워드가 있는 라인에서만 강하게 마스킹합니다.
    - 영수증에는 숫자가 많아 과도한 마스킹을 피하기 위해 문맥 기반을 사용합니다.
    """
    if not text:
        return text

    strict_enabled = _is_strict_enabled() if strict is None else strict
    lines = text.splitlines()
    redacted_lines = []

    for line in lines:
        redacted = line

        # 승인/거래/가맹/단말기 번호는 키워드 패턴으로 마스킹합니다.
        redacted = _APPROVAL_PATTERN.sub(_mask_keyword_number, redacted)

        # 계좌번호는 키워드 패턴으로 마스킹합니다.
        redacted = _ACCOUNT_PATTERN.sub(_mask_keyword_number, redacted)

        # 카드번호는 키워드가 있거나, 4-4-4-4 형식이면 마스킹합니다.
        if _contains_keyword(redacted, _CARD_KEYWORDS):
            redacted = _CARD_LOOSE_PATTERN.sub(_mask_card, redacted)
        redacted = _CARD_STRICT_PATTERN.sub(_mask_card, redacted)

        # strict 모드에서는 라벨 없는 카드번호 후보도 추가로 마스킹합니다.
        if strict_enabled:
            redacted = _mask_card_candidates_strict(redacted)

        # 이메일/전화번호는 전역 패턴으로 마스킹합니다.
        redacted = _EMAIL_PATTERN.sub(_mask_email, redacted)
        redacted = _PHONE_PATTERN.sub(_mask_phone, redacted)

        # 주민번호는 키워드가 있는 라인에서만 마스킹합니다.
        if _contains_keyword(redacted, _RRN_KEYWORDS):
            redacted = _RRN_PATTERN.sub(_mask_rrn, redacted)

        redacted_lines.append(redacted)

    return "\n".join(redacted_lines)


# dict/list/tuple/set/모델 등을 재귀적으로 마스킹합니다.
def redact_in_structure(obj: Any, skip_keys: set[str] | None = None, strict: bool | None = None) -> Any:
    """자료 구조 내부의 문자열을 재귀적으로 마스킹합니다."""
    if isinstance(obj, str):
        return redact_text(obj, strict=strict)
    if isinstance(obj, list):
        return [redact_in_structure(item, skip_keys=skip_keys, strict=strict) for item in obj]
    if isinstance(obj, tuple):
        return tuple(redact_in_structure(item, skip_keys=skip_keys, strict=strict) for item in obj)
    if isinstance(obj, set):
        return {redact_in_structure(item, skip_keys=skip_keys, strict=strict) for item in obj}
    if isinstance(obj, dict):
        redacted: dict = {}
        for key, value in obj.items():
            if skip_keys and key in skip_keys:
                redacted[key] = value
            else:
                redacted[key] = redact_in_structure(value, skip_keys=skip_keys, strict=strict)
        return redacted
    if isinstance(obj, BaseModel):
        return redact_in_structure(obj.dict(), skip_keys=skip_keys, strict=strict)
    return obj


# 특정 키를 우선적으로 마스킹합니다.
def redact_dict_keys(
    obj: dict,
    keys_to_redact: set[str],
    skip_keys: set[str] | None = None,
    strict: bool | None = None,
) -> dict:
    """dict의 특정 키에 대해 우선적으로 마스킹을 적용합니다."""
    redacted: dict = {}
    for key, value in obj.items():
        if skip_keys and key in skip_keys:
            redacted[key] = value
            continue
        if key in keys_to_redact:
            redacted[key] = redact_in_structure(value, skip_keys=skip_keys, strict=strict)
        elif isinstance(value, dict):
            redacted[key] = redact_dict_keys(value, keys_to_redact, skip_keys=skip_keys, strict=strict)
        else:
            redacted[key] = value
    return redacted
