# SECURITY_PRIVACY.md

## 1. 민감정보 마스킹 정책

ASHD는 OCR 결과와 파싱 결과에 포함될 수 있는 개인정보를 보호하기 위해 **마스킹(레드액션)**을 기본 적용합니다.

핵심 원칙:

1. **추출 로직은 원문으로 수행**
   - 룰 기반 추출/LLM 추출은 정확도를 위해 원문 OCR 텍스트로 수행합니다.
2. **DB 저장 전 마스킹**
   - `raw_text`, `parsed_fields`, `evidence`, Job 에러/로그 등은 저장 직전에 마스킹합니다.
3. **API 응답 전 최후 안전망**
   - JSON 응답에서 민감정보가 남아있지 않도록 미들웨어에서 재마스킹합니다.
   - `/auth/*` 응답은 UX를 위해 마스킹 예외로 처리합니다.
   - 키 이름(예: email)으로 전역 예외를 두지 않으며, 경로 단위로만 예외를 둡니다.
4. **스트리밍/파일 응답은 스킵**
   - StreamingResponse/FileResponse는 미들웨어에서 건드리지 않습니다.
5. **헤더 보존**
   - Set-Cookie 중복 헤더를 포함한 원본 헤더를 최대한 보존합니다.
   - content-length는 재계산을 위해 제거하며, content-type은 1개만 남깁니다.
   - JSON 파싱 실패 시에는 바디를 변경하지 않고 그대로 반환합니다.

## 2. 마스킹 대상과 규칙

최소 마스킹 대상:

- 카드번호: 뒤 4자리만 유지
- 전화번호: 뒤 4자리만 유지
- 이메일: local-part 대부분 마스킹
- 승인번호/거래번호/가맹점번호/단말기ID: 전부 마스킹
- 주민번호: 앞 6자리만 유지, 뒤 7자리 마스킹
- 계좌번호: 전부 마스킹

정규식 오탐 방지 원칙:

- 카드/승인/계좌/주민번호는 **키워드 기반 + 패턴** 조합으로 마스킹
- 이메일/전화번호는 패턴 자체가 명확해 전역 적용

예시(마스킹 후):

- 카드번호: `1234-5678-9012-3456` → `****-****-****-3456`
- 전화번호: `010-1234-5678` → `***-****-5678`
- 이메일: `user@example.com` → `u***@example.com`
- 승인번호: `승인번호: 99887766` → `승인번호: ********`
- 주민번호: `900101-1234567` → `900101-*******`

## 3. 저장/응답 정책 적용 위치

저장 전(redaction at ingestion):

- `app/services/document_processing.py`
- `app/api/routes/products.py`
- `Document.parsed_fields`, `Document.evidence`, `Document.raw_text`
- `DocumentProcessingJob.error`

응답 전(redaction at egress):

- `app/api/middlewares/redaction.py`

### 3.1 REDACTION_STRICT (라벨 없는 카드번호 탐지)

`REDACTION_STRICT=true`인 경우, **라벨이 없는 카드번호 후보**도 추가로 마스킹합니다.

- 13~19자리 숫자(공백/하이픈 포함)를 후보로 보고,
- **Luhn 체크**로 유효성 검사를 통과한 경우에만 마스킹합니다.

이 모드는 과도한 마스킹을 줄이기 위한 보수적 옵션이며,
기본값은 `false`입니다.

## 4. 응답 헤더 보존 정책

- JSON 응답을 재구성할 때 `raw_headers`를 기반으로 헤더를 복원합니다.
- `Set-Cookie` 같은 중복 헤더가 유실되지 않도록 보존합니다.
- `content-length`는 재계산을 위해 제거합니다.

## 5. 테스트용 엔드포인트 정책

- `/health/plain`, `/health/stream`, `/health/cookies`는 **local/dev/test** 환경에서만 등록합니다.
- `APP_ENV=prod`인 경우 테스트용 엔드포인트는 노출되지 않습니다.
