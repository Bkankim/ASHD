"""OpenAI 호환 API를 호출하는 LLM 클라이언트 모듈입니다."""

from __future__ import annotations

import json
import urllib.request
from typing import Any


# OpenAI 호환 API로 텍스트를 생성하는 클라이언트입니다.
class OpenAICompatibleLLMClient:
    """OpenAI-compatible API를 호출해 응답 텍스트를 반환합니다."""

    # base_url, api_key, model을 받아 클라이언트를 초기화합니다.
    def __init__(self, base_url: str, api_key: str, model: str, timeout: int = 20) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    # 질문과 근거를 받아 LLM 응답을 반환합니다.
    def generate(self, question: str, evidence: list[dict[str, Any]] | None = None) -> str:
        """질문과 근거를 결합해 LLM 응답을 생성합니다."""
        messages = [
            {"role": "system", "content": "너는 OCR 텍스트에서 필드를 추출하는 도우미야."},
            {"role": "user", "content": self._build_prompt(question, evidence)},
        ]
        payload = {"model": self.model, "messages": messages}
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url=f"{self.base_url}/chat/completions",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return self._parse_response(data)

    # 질문과 근거를 사람이 읽기 쉬운 형태로 합칩니다.
    def _build_prompt(self, question: str, evidence: list[dict[str, Any]] | None) -> str:
        """질문과 evidence를 합쳐 하나의 프롬프트 문자열을 만듭니다."""
        parts = [question]
        if evidence:
            snippets = [item.get("snippet", "") for item in evidence if item.get("snippet")]
            if snippets:
                parts.append("\n근거:\n" + "\n".join(snippets))
        return "\n".join(parts)

    # LLM 응답에서 텍스트를 추출합니다.
    def _parse_response(self, data: dict) -> str:
        """OpenAI 호환 응답에서 message.content를 꺼냅니다."""
        choices = data.get("choices", [])
        if not choices:
            return ""
        message = choices[0].get("message", {})
        return str(message.get("content", "")).strip()
