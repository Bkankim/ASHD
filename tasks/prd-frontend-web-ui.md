# PRD: Frontend Web UI (Static /app)

## 1. Introduction/Overview

v0.1 백엔드 API를 **웹 UI로 완주(회원가입 → 업로드 → Job 폴링 → Product 수정 → 알림 설정/텔레그램 연동)**할 수 있도록,
정적 UI(`/app`)를 동일 오리진으로 제공하는 것을 목표로 한다.

### Current Status / Evidence (근거)

- 인증 API: `POST /auth/register`, `POST /auth/login`, `POST /auth/change-password` 존재
  - 근거: `app/api/routes/auth.py`
- 문서 업로드: `POST /documents/upload` 202 + `job_id` 즉시 응답
  - 근거: `app/api/routes/documents.py`, `app/schemas/document.py`
- Job 조회: `GET /jobs/{job_id}` (status/error/product_id 포함)
  - 근거: `app/api/routes/jobs.py`, `app/schemas/job.py`
- 제품 CRUD: `GET/POST /products`, `GET/PUT/DELETE /products/{id}`
  - 근거: `app/api/routes/products.py`, `app/schemas/product.py`
- 알림 설정: `GET/PUT /notification-settings`
  - 근거: `app/api/routes/notification_settings.py`, `app/schemas/notification_settings.py`
- 텔레그램 연동: `GET/POST/DELETE /telegram-account`
  - 근거: `app/api/routes/telegram_account.py`, `app/schemas/telegram_account.py`
- 마스킹 정책: raw_text 등은 저장 전/응답 전 마스킹, `/auth/*`는 예외
  - 근거: `app/api/middlewares/redaction.py`, `app/core/redaction.py`

## 2. Goals (P0)

- 정적 UI(`/app`)로 Golden Path 완주 가능
- 동일 오리진 제공으로 CORS 없이 동작
- 업로드/Job 폴링 UX를 명확히 제공
- 민감정보 노출 없이 오류를 사용자 친화적으로 표시

## 3. Non-Goals (Out of Scope)

- SPA 프레임워크(React/Next) 도입 및 빌드 파이프라인
- `/assistant/*` 기반 자연어 질의/요약 UI (v0.2 예정)
- 고급 검색/필터링/페이징(기본 리스트만 제공)

## 4. Design Constraints (P0 설계 잠금)

- UI 제공 방식: **정적 UI(`/app`) 동일 오리진**
- 상태 모델: auth 토큰, 업로드 진행 상태, Job 상태(pending/processing/completed/failed), 제품 편집 상태
- 오류 표시 원칙: 민감정보 금지, 사용자 조치 가능한 요약 메시지

## 5. User Journey (Golden Path)

1) 회원가입/로그인 → access token 확보
2) 문서 업로드(이미지/PDF) → 202 + job_id
3) Job 폴링으로 완료 확인 → product_id 이동
4) 제품 상세에서 필드 확인/수정 저장
5) 알림 설정 저장 및 텔레그램 연동 상태 확인

## 6. IA / Pages (고정)

- `/app/login`
- `/app/upload`
- `/app/products`
- `/app/products/{id}`
- `/app/settings`
- `/app/telegram`

## 7. API 호출 시퀀스 (요약)

### 7.1 Login
- `POST /auth/login` (JSON: email, password)
- 응답: `{ access_token, token_type }`
- 실패: 401 → “이메일/비밀번호를 확인하세요”

### 7.2 Upload + Job
- `POST /documents/upload` (multipart, header: `Authorization: Bearer <token>`)
- 응답: `{ job_id, document_id, status }` (202)
- `GET /jobs/{job_id}` 폴링 → status 확인
  - completed: `product_id`로 상세 이동
  - failed: `error` 요약 + 재업로드 안내

### 7.3 Products
- `GET /products` → 리스트
- `GET /products/{id}` → 상세
- `PUT /products/{id}` → 수정 저장

### 7.4 Notification Settings
- `GET /notification-settings`
- `PUT /notification-settings` (리스트[int] 형태 유지)

### 7.5 Telegram Account
- `GET /telegram-account` (없으면 404)
- `POST /telegram-account` (chat_id/username)
- `DELETE /telegram-account`

## 8. Job 폴링 정책 (P0)

- 기본 간격: 2초
- 타임아웃: 90초 (초과 시 “처리 지연” 안내 + 수동 새로고침)
- completed 시 product_id 이동, failed 시 job.error 요약 표시

## 9. 업로드 정책 UI 반영

- 허용 파일: 이미지/PDF
- 제한: 10MB, PDF 최대 3페이지(초과 페이지 무시 + job.error 경고)
- 서버에서 MIME 강제 검증은 없음 → UI에서 확장자/accept로 1차 안내

## 10. Error Taxonomy (UI 메시지 요약)

- Auth(401): “로그인이 필요합니다”
- NotFound(404, 404 은닉): “데이터가 없습니다”
- Validation(400/413): “업로드 제한을 확인하세요”
- Processing failed: “처리에 실패했습니다. 다시 업로드하세요”
- Network: “네트워크 오류, 잠시 후 재시도”

## 11. 보안/프라이버시

- 토큰 저장: localStorage 허용(P0), innerHTML 금지(textContent 사용)
- raw_text는 마스킹된 상태로만 표시
- 타 사용자 접근은 404 은닉 → UI는 중립 메시지로 처리

## 12. Acceptance Criteria

- 로그인 → 업로드 → Job 완료 → 제품 수정까지 한 번에 완료
- 알림 설정/텔레그램 연동 페이지가 정상 동작
- 업로드 제한/에러 메시지가 사용자에게 명확히 보임

## 13. Open Questions

- [확실하지 않음] `/app` 정적 서빙 시 라우팅(해시/히스토리) 방식 선택
- [확실하지 않음] 업로드 진행률 표시 범위(표준 업로드 이벤트 사용 여부)

### Change Log

- v0.1 UI를 정적 `/app` 단일 오리진으로 고정하고, Golden Path 완주에 초점
- `/assistant/*`는 v0.2 예정으로 명시

### Next Steps (P0 3개)

1) 정적 `/app` 서빙 설계/스켈레톤 구현
2) 업로드 + Job 폴링 UI 구현
3) 제품 상세/수정 UI 구현

### P1/P2 Backlog

- SPA 프레임워크 도입(React/Next)
- 고급 검색/페이징/필터
- `/assistant/*` UI 연동
