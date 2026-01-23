"""외부 OCR API를 호출하는 클라이언트를 정의하는 모듈입니다."""

from __future__ import annotations

import base64
import json
from pathlib import Path
import urllib.parse
import urllib.request

from app.ocr.base import OCRClient


# 외부 OCR API를 호출하는 실제 클라이언트입니다.
class ExternalOCRClient:
    """Google Cloud Vision OCR API에 이미지 데이터를 보내고 텍스트를 받습니다."""

    # base_url과 api_key를 받아 초기화합니다.
    def __init__(self, base_url: str, api_key: str, timeout: int = 15) -> None:
        if not base_url or not api_key:
            raise ValueError("OCR base_url/api_key is required")
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout

    # 이미지 파일을 외부 OCR API에 보내고 텍스트를 반환합니다.
    def extract_text(self, image_path: Path, pages: list[int] | None = None) -> str:
        """이미지 파일을 base64로 인코딩해 OCR API에 전달합니다.

        초급자용 설명:
        - Google Cloud Vision은 POST 요청의 JSON payload에 이미지(base64)를 전달합니다.
        - 응답은 responses 배열에 들어오며, fullTextAnnotation.text를 사용합니다.
        """
        is_pdf = image_path.suffix.lower() == ".pdf"
        payload = self._build_payload(image_path, pages=pages if is_pdf else None)
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url=self._build_request_url(for_pdf=is_pdf),
            data=body,
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return self._parse_response(data)

    # 이미지 파일을 읽어 OCR 요청용 payload를 구성합니다.
    def _build_payload(self, image_path: Path, pages: list[int] | None = None) -> dict:
        """이미지/PDF 파일을 base64로 인코딩해 전송할 payload를 구성합니다."""
        raw = image_path.read_bytes()
        encoded = base64.b64encode(raw).decode("utf-8")
        if image_path.suffix.lower() == ".pdf":
            request: dict = {
                "inputConfig": {"content": encoded, "mimeType": "application/pdf"},
                "features": [{"type": "DOCUMENT_TEXT_DETECTION"}],
            }
            if pages:
                request["pages"] = pages
            return {"requests": [request]}
        return {
            "requests": [
                {
                    "image": {"content": encoded},
                    "features": [{"type": "TEXT_DETECTION"}],
                }
            ]
        }

    # 요청 URL에 API Key를 쿼리 파라미터로 붙입니다.
    def _build_request_url(self, for_pdf: bool = False) -> str:
        """Google Vision API 호출을 위한 URL을 구성합니다."""
        parsed = urllib.parse.urlparse(self.base_url)
        query = urllib.parse.parse_qs(parsed.query)
        if "key" not in query:
            query["key"] = [self.api_key]
        new_query = urllib.parse.urlencode(query, doseq=True)
        path = parsed.path
        if for_pdf and "images:annotate" in path:
            path = path.replace("images:annotate", "files:annotate")
        return urllib.parse.urlunparse(parsed._replace(path=path, query=new_query))

    # OCR 응답에서 텍스트를 추출합니다.
    def _parse_response(self, data: dict) -> str:
        """Google Vision 응답에서 텍스트를 추출합니다."""
        responses = data.get("responses", [])
        if not responses:
            return ""

        image_responses: list[dict] = []
        # files:annotate 응답은 responses[].responses[] 구조입니다.
        if isinstance(responses[0], dict) and "responses" in responses[0]:
            for file_resp in responses:
                file_error = file_resp.get("error") if isinstance(file_resp, dict) else None
                if file_error:
                    # 파일 단위 오류는 원문을 노출하지 않고 고정 메시지로 처리합니다.
                    raise ValueError("VISION_FILE_ANNOTATE_ERROR")
                nested = file_resp.get("responses", []) if isinstance(file_resp, dict) else []
                image_responses.extend(nested)
        else:
            image_responses = responses

        texts: list[str] = []
        for item in image_responses:
            if not isinstance(item, dict):
                continue
            error = item.get("error")
            if error:
                raise ValueError(error.get("message", "OCR error"))

            full_text = item.get("fullTextAnnotation", {}).get("text", "")
            if full_text:
                texts.append(str(full_text))
                continue

            annotations = item.get("textAnnotations", [])
            if annotations:
                texts.append(str(annotations[0].get("description", "")))
        return "\n".join(texts)


# 키가 없을 때 사용하는 Mock OCR 클라이언트입니다.
class MockOCRClient:
    """외부 API 키가 없을 때 사용하는 Mock OCR입니다."""

    # 고정된 텍스트를 반환합니다.
    def extract_text(self, image_path: Path, pages: list[int] | None = None) -> str:
        """테스트/로컬 환경에서 사용할 예시 텍스트를 반환합니다."""
        return """상호: 테스트마트\n구매일: 2024-01-10\n금액: 12,000원\n주문번호: A-1004"""


# settings 값에 따라 실제/Mock 클라이언트를 선택합니다.
def build_ocr_client(base_url: str | None, api_key: str | None, timeout: int = 15) -> OCRClient:
    """환경 변수 유무에 따라 OCR 클라이언트를 선택합니다."""
    if base_url and api_key:
        return ExternalOCRClient(base_url=base_url, api_key=api_key, timeout=timeout)
    return MockOCRClient()
