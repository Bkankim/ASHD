"""OCR 클라이언트 인터페이스를 정의하는 모듈입니다."""

from pathlib import Path
from typing import Protocol


# OCR 클라이언트가 따라야 하는 인터페이스입니다.
class OCRClient(Protocol):
    """이미지 파일에서 텍스트를 추출하는 인터페이스입니다."""

    # 이미지 경로를 받아 OCR 텍스트를 반환합니다.
    def extract_text(self, image_path: Path, pages: list[int] | None = None) -> str:
        ...
