"""OCR 응답 파서 테스트입니다."""

from app.ocr.external import ExternalOCRClient


def _client() -> ExternalOCRClient:
    """파서 테스트용 OCR 클라이언트를 생성합니다."""
    return ExternalOCRClient(base_url="https://vision.googleapis.com/v1/images:annotate", api_key="test")


def test_parse_images_annotate_shape():
    """images:annotate 응답 형식에서 텍스트가 추출되는지 확인합니다."""
    data = {
        "responses": [
            {
                "textAnnotations": [
                    {"description": "이미지 텍스트"},
                ]
            }
        ]
    }
    assert _client()._parse_response(data) == "이미지 텍스트"


def test_parse_files_annotate_shape():
    """files:annotate 응답 형식(중첩)에서 텍스트가 추출되는지 확인합니다."""
    data = {
        "responses": [
            {
                "responses": [
                    {"fullTextAnnotation": {"text": "PDF 텍스트"}},
                ]
            }
        ]
    }
    assert _client()._parse_response(data) == "PDF 텍스트"
