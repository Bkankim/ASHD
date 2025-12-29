"""민감정보 마스킹 유틸 테스트 모듈입니다."""

from app.core.redaction import redact_text


# 카드번호 마스킹을 확인합니다.
def test_redact_card_number_with_keyword():
    """카드번호가 키워드와 함께 있을 때 마스킹되는지 확인합니다."""
    text = "카드번호: 1234-5678-9012-3456"
    redacted = redact_text(text)
    assert "1234-5678-9012-3456" not in redacted
    assert "3456" in redacted


# 전화번호 마스킹을 확인합니다.
def test_redact_phone_number():
    """전화번호가 뒤 4자리만 남는지 확인합니다."""
    text = "전화: 01012345678"
    redacted = redact_text(text)
    assert "01012345678" not in redacted
    assert redacted.endswith("5678")


# 전화번호 변형을 마스킹하는지 확인합니다.
def test_redact_phone_number_variations():
    """지역번호/공백 포함 전화번호도 마스킹되는지 확인합니다."""
    text = "문의: 02-123-4567 / 010 1234 5678"
    redacted = redact_text(text)
    assert "02-123-4567" not in redacted
    assert "010 1234 5678" not in redacted


# 이메일 마스킹을 확인합니다.
def test_redact_email():
    """이메일 로컬 파트가 마스킹되는지 확인합니다."""
    text = "문의: user@example.com"
    redacted = redact_text(text)
    assert "user@example.com" not in redacted
    assert "@example.com" in redacted


# 승인번호 마스킹을 확인합니다.
def test_redact_approval_number():
    """승인번호가 전부 마스킹되는지 확인합니다."""
    text = "승인번호: 99887766"
    redacted = redact_text(text)
    assert "99887766" not in redacted


# 거래/단말기 번호도 마스킹되는지 확인합니다.
def test_redact_transaction_and_terminal_numbers():
    """거래번호/단말기ID가 마스킹되는지 확인합니다."""
    text = "거래번호: 2023-9988 단말기ID: 123456"
    redacted = redact_text(text)
    assert "2023-9988" not in redacted
    assert "123456" not in redacted


# 주민번호 마스킹을 확인합니다.
def test_redact_rrn():
    """주민번호 뒤 7자리가 마스킹되는지 확인합니다."""
    text = "주민번호: 900101-1234567"
    redacted = redact_text(text)
    assert "900101-1234567" not in redacted
    assert "900101-*******" in redacted


# 계좌번호 마스킹을 확인합니다.
def test_redact_account_number():
    """계좌번호가 전부 마스킹되는지 확인합니다."""
    text = "계좌번호: 110-123-456789"
    redacted = redact_text(text)
    assert "110-123-456789" not in redacted


# 오탐 방지를 확인합니다.
def test_redact_does_not_mask_barcode_and_amount():
    """바코드/금액/날짜는 마스킹하지 않는지 확인합니다."""
    text = "바코드 8801045570068 금액 1,600 날짜 2014-01-21"
    redacted = redact_text(text)
    assert "8801045570068" in redacted
    assert "1,600" in redacted
    assert "2014-01-21" in redacted


# strict 모드에서 라벨 없는 카드번호도 마스킹되는지 확인합니다.
def test_redact_strict_unlabeled_card_number():
    """strict 모드에서 라벨 없는 카드번호 후보가 마스킹되는지 확인합니다."""
    text = "결제내역 4111111111111111"
    redacted = redact_text(text, strict=True)
    assert "4111111111111111" not in redacted
    assert redacted.endswith("1111")


# strict 모드에서도 Luhn 실패 숫자는 그대로 두는지 확인합니다.
def test_redact_strict_luhn_fail():
    """Luhn 체크 실패 숫자는 strict 모드에서도 마스킹하지 않습니다."""
    text = "코드 4111111111111112"
    redacted = redact_text(text, strict=True)
    assert "4111111111111112" in redacted
