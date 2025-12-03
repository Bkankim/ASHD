"""이미지에서 텍스트를 추출하는 OCR 서비스 스켈레톤입니다."""

from pathlib import Path


def extract_text_from_image(image_path: Path) -> str:
    """이미지 파일 경로를 입력받아 텍스트를 추출하는 함수입니다.

    현재는 실제 OCR 엔진을 호출하지 않고,
    TODO로 남겨둔 상태입니다.

    초급자용 설명:
    - 나중에 이 함수 안에서 Tesseract 또는 클라우드 OCR API를 호출하도록 구현하면 됩니다.
    - 이 레이어를 따로 만들어두면, OCR 엔진을 교체할 때도 이 함수만 수정하면 됩니다.
    """
    # TODO: Tesseract 또는 외부 OCR 서비스 연동 코드 작성
    return ""  # 현재는 빈 문자열을 반환합니다.
