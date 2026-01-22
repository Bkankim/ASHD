# KNOWN_WARNINGS (P1 관리)

이 문서는 Step2 불일치 정리 이후, 운영 리스크 성격의 경고를 요약한 목록입니다.

## 상위 경고 3종
1) FastAPI `on_event` deprecation
- 근거: pytest warnings에서 `app/main.py`의 `@app.on_event("startup")` 경고
- 대응 계획(P1): FastAPI lifespan 이벤트로 전환

2) `datetime.utcnow()` deprecation
- 근거: sqlmodel/route에서 utcnow 사용 경고
- 대응 계획(P1): timezone-aware `datetime.now(datetime.UTC)` 또는 공용 헬퍼로 교체

3) HTTP status deprecation (413/422)
- 근거: `HTTP_413_REQUEST_ENTITY_TOO_LARGE`, `HTTP_422_UNPROCESSABLE_ENTITY` 경고
- 대응 계획(P1): FastAPI 권장 상수로 교체

> P1 항목은 동작 변경 없이 문서/테스트 정합성 유지 범위에서 순차 처리합니다.
