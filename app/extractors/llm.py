"""LLM 기반 필드 추출 모듈입니다."""

from __future__ import annotations

import json
from typing import Protocol

from app.core.config import get_settings
from app.llm.openai_compat import OpenAICompatibleLLMClient


# LLM 필드 추출기가 따라야 하는 인터페이스입니다.
class LLMFieldExtractor(Protocol):
    """OCR 텍스트에서 구조화된 필드를 반환하는 인터페이스입니다."""

    # raw_text를 입력받아 구조화된 필드를 반환합니다.
    def extract(self, raw_text: str) -> dict:
        ...


# Solar(OpenAI 호환) API를 사용하는 LLM 추출기입니다.
class SolarLLMFieldExtractor:
    """Solar(OpenAI-compatible) API로 필드를 추출합니다."""

    # base_url, api_key, model을 받아 초기화합니다.
    def __init__(self, base_url: str, api_key: str, model: str, timeout: int = 20) -> None:
        self.client = OpenAICompatibleLLMClient(base_url=base_url, api_key=api_key, model=model, timeout=timeout)

    # raw_text를 전달해 JSON 형태의 필드를 반환합니다.
    def extract(self, raw_text: str) -> dict:
        """LLM에게 JSON 형태로 필드를 추출해 달라고 요청합니다."""
        prompt = (
            "다음 OCR 텍스트에서 제품 정보를 JSON으로 추출해줘.\n"
            "필드는 title, purchase_date, amount, store, order_id, refund_deadline, "
            "warranty_end_date, as_contact, product_category 만 포함해.\n"
            "날짜는 YYYY-MM-DD 형식, amount는 숫자만 포함해.\n"
            "없으면 null로 반환해.\n"
        )
        # evidence에 raw_text를 넣어 LLM이 참고할 수 있게 합니다.
        response = self.client.generate(question=prompt, evidence=[{"snippet": raw_text}])
        return _parse_json_response(response)


# 키가 없을 때 사용하는 Mock 추출기입니다.
class MockLLMFieldExtractor:
    """LLM 키가 없을 때 테스트용으로 쓰는 Mock 구현입니다."""

    # 고정된 필드를 반환합니다.
    def extract(self, raw_text: str) -> dict:
        """예시 필드를 반환해 파이프라인 흐름을 확인합니다."""
        return {"title": "LLM-보완-제품", "store": "LLM-상점"}


# 응답 문자열에서 JSON 블록을 파싱합니다.
def _parse_json_response(text: str) -> dict:
    """LLM 응답에서 JSON을 추출합니다.

    초급자용 설명:
    - LLM이 코드 블록 등으로 응답할 수 있어, JSON 영역만 잘라 파싱합니다.
    - 파싱 실패 시 빈 dict를 반환해 파이프라인을 중단시키지 않습니다.
    """
    if not text:
        return {}

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}

    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return {}


# 설정 값에 따라 실제/Mock 추출기를 선택합니다.
def build_llm_extractor() -> LLMFieldExtractor:
    """환경 변수 유무에 따라 LLM 추출기를 선택합니다."""
    settings = get_settings()
    if settings.LLM_BASE_URL and settings.LLM_API_KEY:
        return SolarLLMFieldExtractor(
            base_url=settings.LLM_BASE_URL,
            api_key=settings.LLM_API_KEY,
            model=settings.LLM_MODEL,
        )
    return MockLLMFieldExtractor()
