"""API 응답에서 민감정보를 마스킹하는 미들웨어입니다."""

from __future__ import annotations

import json

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import FileResponse, Response, StreamingResponse

from app.core.redaction import redact_dict_keys, redact_in_structure


# 민감정보가 자주 담기는 키 목록입니다.
SENSITIVE_KEYS = {
    "raw_text",
    "parsed_fields",
    "evidence",
    "ocr_text",
    "llm_prompt",
    "llm_response",
    "error",
    "error_detail",
    "logs",
}

# 마스킹을 건너뛸 경로 prefix 목록입니다.
SKIP_PATH_PREFIXES = ["/auth"]



# raw_headers를 필터링합니다.
def _filter_raw_headers(
    raw_headers: list[tuple[bytes, bytes]],
    content_type: str | None = None,
) -> list[tuple[bytes, bytes]]:
    """raw_headers에서 content-length를 제거하고 content-type 중복을 방지합니다."""
    filtered: list[tuple[bytes, bytes]] = []
    seen_content_type = False

    for key_bytes, value_bytes in raw_headers:
        key = key_bytes.decode("latin-1").lower()
        if key == "content-length":
            # 바디가 바뀔 수 있으니 content-length는 제거합니다.
            continue
        if key == "content-type":
            if seen_content_type:
                # content-type은 1개만 남깁니다.
                continue
            seen_content_type = True
            filtered.append((key_bytes, value_bytes))
            continue
        # Set-Cookie 등 중복 헤더는 그대로 보존합니다.
        filtered.append((key_bytes, value_bytes))

    if not seen_content_type and content_type:
        filtered.append((b"content-type", content_type.encode("latin-1")))

    return filtered


# JSON 응답 본문을 마스킹하는 미들웨어입니다.
class RedactionMiddleware(BaseHTTPMiddleware):
    """JSON 응답에서 민감정보를 마스킹합니다."""

    # 요청/응답을 가로채어 JSON 응답만 처리합니다.
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # 스트리밍 응답은 건드리지 않습니다.
        if isinstance(response, (StreamingResponse, FileResponse)):
            return response

        # 특정 경로는 마스킹을 건너뜁니다.
        if any(request.url.path.startswith(prefix) for prefix in SKIP_PATH_PREFIXES):
            return response

        content_type = response.headers.get("content-type", "").lower()
        if "application/json" not in content_type:
            # 비JSON 응답은 그대로 반환합니다.
            return response

        body_chunks: list[bytes] = []
        async for chunk in response.body_iterator:
            body_chunks.append(chunk)
        body_bytes = b"".join(body_chunks)

        try:
            data = json.loads(body_bytes)
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 원문 바디를 그대로 반환합니다.
            content_type_value = response.headers.get("content-type", response.media_type)
            filtered = _filter_raw_headers(list(response.raw_headers), content_type_value)
            new_response = Response(
                content=body_bytes,
                status_code=response.status_code,
                media_type=response.media_type,
                background=response.background,
            )
            new_response.raw_headers = filtered
            return new_response

        # 특정 키는 우선 마스킹하고, 전체 구조도 한 번 더 마스킹합니다.
        if isinstance(data, dict):
            redacted = redact_dict_keys(data, SENSITIVE_KEYS)
        else:
            redacted = data
        redacted = redact_in_structure(redacted)

        new_body = json.dumps(redacted, ensure_ascii=False).encode("utf-8")
        content_type_value = response.headers.get("content-type", "application/json")
        filtered = _filter_raw_headers(list(response.raw_headers), content_type_value)
        new_response = Response(
            content=new_body,
            status_code=response.status_code,
            media_type=response.media_type or "application/json",
            background=response.background,
        )
        new_response.raw_headers = filtered
        return new_response
