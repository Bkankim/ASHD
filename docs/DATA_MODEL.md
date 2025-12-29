# DATA_MODEL.md

## 1. 데이터 모델 개요

ASHD 데이터 모델은 다음 엔티티들을 중심으로 설계됩니다.

* `User` : 서비스 사용자 계정
* `Product` : 영수증/보증서/택배라벨 기반으로 관리되는 "제품/구매" 단위
* `NotificationSettings` : 사용자별 알림 설정
* `TelegramAccount` : 사용자별 텔레그램 계정 연동 정보
* `Document` : 업로드 문서 원문 텍스트
* `DocumentChunk` : 문서 분할 청크
* `Embedding` : 임베딩 벡터 저장(업그레이드 경로)
* `LLMCache` : LLM 응답 캐시
* `DocumentProcessingJob` : 문서 처리 Job 상태

RDBMS는 초기에는 **SQLite**(파일 기반)를 가정하고, 향후 PostgreSQL 등의 RDB로 확장 가능합니다. ORM 계층은 **SQLModel**을 사용하며, HTTP 요청/응답 DTO는 Pydantic 스키마(`app/schemas/`)로 분리합니다.

---

## 2. 공통 설계 원칙

1. **기본 키**

   * 모든 테이블은 정수형 자동 증가 기본 키 `id`를 사용합니다.

2. **시간 필드**

   * 생성/갱신 시간은 `datetime` 타입으로 관리하며, 기본값은 `datetime.utcnow`를 사용합니다.
   * DB/애플리케이션 레벨에서는 UTC 기준을 기본으로 가정합니다.

3. **소유 관계(멀티 테넌시)**

   * 모든 `Product`, `NotificationSettings`, `TelegramAccount`, `Document`, `DocumentChunk`, `Embedding`, `LLMCache`, `DocumentProcessingJob`는 반드시 특정 `User`에 속합니다.
   * `user_id` 외래 키를 통해 사용자별 데이터를 명확히 분리합니다.

4. **인덱스**

   * 조회 빈도가 높은 필드는 SQLModel의 `Field(index=True)` 옵션으로 인덱스를 생성합니다.
   * 예: 이메일, 사용자 ID, 날짜(보증/환불 기한), 주문번호, 상점명 등

5. **스키마 일관성**

   * 이 문서의 정의는 다음 코드와 **1:1로 일치**해야 합니다.

     * `app/models/user.py`
     * `app/models/product.py`
     * `app/models/notification.py`
     * `app/models/telegram_account.py`
     * `app/models/document.py`
     * `app/models/document_chunk.py`
     * `app/models/embedding.py`
     * `app/models/llm_cache.py`
     * `app/models/job.py`
   * 코드 변경 시 반드시 이 문서를 함께 업데이트합니다.

---

## 3. 엔티티 상세 정의

### 3.1 User

* 파일: `app/models/user.py`
* 설명: ASHD 서비스에 로그인하는 사용자 계정 정보

#### 3.1.1 필드 정의

| 필드명             | 타입         | NULL 허용 | 기본값                     | 제약/인덱스                      | 설명                   |
| --------------- | ---------- | ------- | ----------------------- | --------------------------- | -------------------- |
| `id`            | `int`      | No      | `None` (auto increment) | `primary_key=True`          | 사용자 고유 ID            |
| `email`         | `str`      | No      | -                       | `index=True`, `unique=True` | 로그인/알림용 이메일 주소       |
| `password_hash` | `str`      | No      | -                       | -                           | 비밀번호 해시 값 (평문 저장 금지) |
| `created_at`    | `datetime` | No      | `datetime.utcnow()`     | -                           | 계정 생성 시각 (UTC)       |

#### 3.1.2 관계

* 1:N 관계

  * `User` 1명 : `Product` N개
* 1:1 관계

  * `User` 1명 : `NotificationSettings` 1개
  * `User` 1명 : `TelegramAccount` 0 또는 1개

---

### 3.2 Product

* 파일: `app/models/product.py`
* 설명: 영수증/보증서/택배라벨 기반으로 관리되는 단일 제품/구매 기록

#### 3.2.1 필드 정의

| 필드명                 | 타입             | NULL 허용 | 기본값                     | 제약/인덱스                      | 설명                                |
| ------------------- | -------------- | ------- | ----------------------- | --------------------------- | --------------------------------- |
| `id`                | `int`          | No      | `None` (auto increment) | `primary_key=True`          | 제품 고유 ID                          |
| `user_id`           | `int`          | No      | -                       | `index=True`, `foreign_key="user.id"` | 소유 사용자 ID (`User.id`)             |
| `title`             | `str`          | No      | -                       | -                           | 제품명 (사용자 시점에서 알아보기 쉬운 이름)         |
| `product_category`  | `str \| None`  | Yes     | `None`                  | `index=True`                | 제품 카테고리 (예: "전자제품", "가전", "의류" 등) |
| `purchase_date`     | `date \| None` | Yes     | `None`                  | `index=True`                | 구매일                               |
| `amount`            | `int \| None`  | Yes     | `None`                  | -                           | 구매 금액 (원 단위)                      |
| `store`             | `str \| None`  | Yes     | `None`                  | `index=True`                | 구매처 이름 (쇼핑몰/오프라인 상점명)             |
| `order_id`          | `str \| None`  | Yes     | `None`                  | `index=True`                | 주문번호/영수증 번호 (있을 경우)               |
| `refund_deadline`   | `date \| None` | Yes     | `None`                  | `index=True`                | 환불/교환 가능 마감일                      |
| `warranty_end_date` | `date \| None` | Yes     | `None`                  | `index=True`                | 보증 종료일                            |
| `as_contact`        | `str \| None`  | Yes     | `None`                  | -                           | AS 문의 연락처 (전화번호/URL 등)            |
| `image_path`        | `str \| None`  | Yes     | `None`                  | -                           | 원본 이미지 저장 경로 (로컬/S3 등)            |
| `raw_text`          | `str \| None`  | Yes     | `None`                  | -                           | OCR 원문 텍스트(민감정보 마스킹 적용)        |
| `created_at`        | `datetime`     | No      | `datetime.utcnow()`     | -                           | 레코드 생성 시각 (UTC)                   |
| `updated_at`        | `datetime`     | No      | `datetime.utcnow()`     | -                           | 레코드 마지막 수정 시각 (UTC)               |

#### 3.2.2 인덱스/조회 패턴

* 자주 사용될 조회 패턴:

  * 특정 사용자에 대한 제품 목록: `WHERE user_id = ?`
  * 보증/환불 임박 제품 조회: `WHERE warranty_end_date`/`refund_deadline` 기준 날짜 범위 조회
  * 특정 상점/카테고리별 필터링: `WHERE store = ?`, `WHERE product_category = ?`

#### 3.2.3 도메인 규칙 (개념적)

* `purchase_date` 없이도 등록은 가능하지만, 보증/환불 계산 정확도가 떨어질 수 있습니다.
* `refund_deadline`/`warranty_end_date`는

  * OCR/파싱으로 자동 추출한 값 + 사용자의 수동 입력/수정을 모두 허용합니다.
* 상태 계산(예: "보증 임박", "환불 가능" 등)은 DB에 별도 컬럼으로 저장하지 않고,

  * 애플리케이션 레벨에서 `현재 날짜 + deadline` 기준으로 계산하는 것을 기본으로 합니다.

---

### 3.3 NotificationSettings

* 파일: `app/models/notification.py`
* 설명: 사용자별 알림 설정 값 (어떤 채널로, 얼마나 미리 알릴지 등)

#### 3.3.1 필드 정의

| 필드명                    | 타입         | NULL 허용 | 기본값                 | 제약/인덱스                                 | 설명                                    |
| ---------------------- | ---------- | ------- | ------------------- |-----------------------------------------| ------------------------------------- |
| `id`                   | `int`      | No      | `None`              | `primary_key=True`                      | 알림 설정 고유 ID                           |
| `user_id`              | `int`      | No      | -                   | `index=True`, `unique=True`, `foreign_key="user.id"` | 사용자 ID (1:1 관계)                       |
| `email_enabled`        | `bool`     | No      | `True`              | -                                       | 이메일 알림 활성화 여부                         |
| `telegram_enabled`     | `bool`     | No      | `False`             | -                                       | 텔레그램 알림 활성화 여부                        |
| `warranty_days_before` | `str`      | No      | `"[30, 7, 3]"`      | -                                       | 보증 종료 며칠 전에 알릴지에 대한 리스트를 JSON 문자열로 저장 |
| `refund_days_before`   | `str`      | No      | `"[3]"`             | -                                       | 환불 마감 며칠 전에 알릴지에 대한 리스트를 JSON 문자열로 저장 |
| `created_at`           | `datetime` | No      | `datetime.utcnow()` | -                                       | 레코드 생성 시각 (UTC)                       |
| `updated_at`           | `datetime` | No      | `datetime.utcnow()` | -                                       | 레코드 마지막 수정 시각 (UTC)                   |

#### 3.3.2 도메인 규칙

* `user_id`는 `User.id`와 1:1로 매핑됩니다.

  * 하나의 사용자당 하나의 `NotificationSettings`만 존재합니다.
* `warranty_days_before` / `refund_days_before`는

  * **저장 방식:** JSON 문자열 (예: `"[30, 7, 3]"`)
  * **로딩 방식:** 애플리케이션에서 `json.loads` 등을 사용해 `list[int]`로 변환하여 사용합니다.
  * 추후 필요 시 별도 테이블로 정규화하거나, `ARRAY` 타입 등을 사용하는 방향으로 확장 가능합니다.

---

### 3.4 TelegramAccount

* 파일: `app/models/telegram_account.py`
* 설명: 사용자별 텔레그램 계정과의 연결 정보를 저장

#### 3.4.1 필드 정의

| 필드명         | 타입            | NULL 허용 | 기본값                 | 제약/인덱스                                    | 설명                            |
| ----------- | ------------- | ------- | ------------------- |-------------------------------------------| ----------------------------- |
| `id`        | `int`         | No      | `None`              | `primary_key=True`                        | 텔레그램 연동 레코드 ID                |
| `user_id`   | `int`         | No      | -                   | `index=True`, `unique=True`, `foreign_key="user.id"` | 사용자 ID (1:1 관계)               |
| `chat_id`   | `str`         | No      | -                   | `index=True`                              | 텔레그램 chat_id (문자열로 저장)          |
| `username`  | `str \| None` | Yes     | `None`              | -                                         | 텔레그램 사용자 이름 (선택)              |
| `linked_at` | `datetime`    | No      | `datetime.utcnow()` | -                                         | 텔레그램 계정 연동 완료 시각              |

#### 3.4.2 도메인 규칙

* 하나의 `User`는 최대 하나의 `TelegramAccount`만 가질 수 있습니다.
* 텔레그램 연동/해제 플로우는 다음과 같이 구성됩니다.

  * 사용자가 텔레그램 봇과 대화 시작 → `/start` 명령 등으로 연동 요청
  * 서버 측에서 해당 `chat_id`를 현재 로그인 사용자와 매핑 → `TelegramAccount` 생성/업데이트
  * 알림 발송 시 `TelegramAccount.chat_id`를 사용하여 메시지를 전송

---

### 3.5 Document

* 파일: `app/models/document.py`
* 설명: 업로드된 문서의 원문 텍스트를 저장

#### 3.5.1 필드 정의

| 필드명        | 타입            | NULL 허용 | 기본값                 | 제약/인덱스                               | 설명                    |
|------------|---------------|---------|----------------------|----------------------------------------|-----------------------|
| `id`       | `int`         | No      | `None`               | `primary_key=True`                     | 문서 고유 ID             |
| `user_id`  | `int`         | No      | -                    | `index=True`, `foreign_key="user.id"`  | 소유 사용자 ID            |
| `product_id` | `int \| None` | Yes     | `None`               | `index=True`, `foreign_key="product.id"` | 연결된 제품 ID (선택)     |
| `title`    | `str \| None` | Yes     | `None`               | -                                      | 문서 제목 (선택)          |
| `image_path` | `str \| None` | Yes   | `None`               | -                                      | 업로드 이미지 저장 경로    |
| `raw_text` | `str`         | No      | `""`                 | -                                      | 원문 텍스트(민감정보 마스킹 적용) |
| `parsed_fields` | `str`    | No      | `"{}"`               | -                                      | 파싱된 필드를 JSON 문자열로 저장 (민감정보 마스킹 적용) |
| `evidence` | `str \| None` | Yes     | `None`               | -                                      | 추출 근거(룰/LLM 목록 등) JSON 문자열 (민감정보 마스킹 적용) |
| `created_at` | `datetime`  | No      | `datetime.utcnow()`  | -                                      | 생성 시각 (UTC)          |
| `updated_at` | `datetime`  | No      | `datetime.utcnow()`  | -                                      | 수정 시각 (UTC)          |

---

### 3.6 DocumentChunk

* 파일: `app/models/document_chunk.py`
* 설명: 문서를 작은 단위로 분할한 청크 저장

#### 3.6.1 필드 정의

| 필드명         | 타입        | NULL 허용 | 기본값                 | 제약/인덱스                               | 설명               |
|-------------|-----------|---------|----------------------|----------------------------------------|------------------|
| `id`        | `int`     | No      | `None`               | `primary_key=True`                     | 청크 고유 ID        |
| `user_id`   | `int`     | No      | -                    | `index=True`, `foreign_key="user.id"`  | 소유 사용자 ID       |
| `document_id` | `int`   | No      | -                    | `index=True`, `foreign_key="document.id"` | 문서 ID            |
| `content`   | `str`     | No      | `""`                 | -                                      | 청크 텍스트          |
| `position`  | `int`     | No      | `0`                  | -                                      | 문서 내 위치         |
| `created_at` | `datetime` | No    | `datetime.utcnow()`  | -                                      | 생성 시각 (UTC)     |

---

### 3.7 Embedding

* 파일: `app/models/embedding.py`
* 설명: 문서/청크 임베딩 벡터 저장 (v0.2에서는 vector_json NULL 허용)

#### 3.7.1 필드 정의

| 필드명          | 타입            | NULL 허용 | 기본값                 | 제약/인덱스                               | 설명                           |
|--------------|---------------|---------|----------------------|----------------------------------------|------------------------------|
| `id`         | `int`         | No      | `None`               | `primary_key=True`                     | 임베딩 고유 ID                  |
| `user_id`    | `int`         | No      | -                    | `index=True`, `foreign_key="user.id"`  | 소유 사용자 ID                 |
| `document_id` | `int \| None` | Yes     | `None`               | `index=True`, `foreign_key="document.id"` | 문서 ID (선택)                |
| `chunk_id`   | `int \| None` | Yes     | `None`               | `index=True`, `foreign_key="documentchunk.id"` | 청크 ID (선택)           |
| `embedding_model` | `str \| None` | Yes | `None`             | -                                      | 임베딩 모델명                 |
| `vector_json` | `str \| None` | Yes    | `None`               | -                                      | 벡터 JSON (v0.2 NULL 허용)    |
| `created_at` | `datetime`    | No      | `datetime.utcnow()`  | -                                      | 생성 시각 (UTC)               |

---

### 3.8 LLMCache

* 파일: `app/models/llm_cache.py`
* 설명: LLM 응답 캐시 저장 (온디맨드 + 캐시 전략)

#### 3.8.1 필드 정의

| 필드명        | 타입         | NULL 허용 | 기본값                 | 제약/인덱스                               | 설명                     |
|------------|------------|---------|----------------------|----------------------------------------|------------------------|
| `id`       | `int`      | No      | `None`               | `primary_key=True`                     | 캐시 고유 ID              |
| `user_id`  | `int`      | No      | -                    | `index=True`, `foreign_key="user.id"`  | 소유 사용자 ID             |
| `cache_key` | `str`     | No      | -                    | `index=True`                           | 캐시 키                  |
| `question` | `str`      | No      | `""`                 | -                                      | 원문 질문                |
| `answer`   | `str`      | No      | `""`                 | -                                      | 응답 텍스트              |
| `evidence_json` | `str` | No      | `""`                 | -                                      | evidence JSON           |
| `model_name` | `str \| None` | Yes | `None`             | -                                      | LLM 모델명               |
| `created_at` | `datetime` | No    | `datetime.utcnow()`  | -                                      | 생성 시각 (UTC)          |
| `expires_at` | `datetime \| None` | Yes | `None`          | -                                      | 만료 시각 (선택)         |

---

### 3.9 DocumentProcessingJob

* 파일: `app/models/job.py`
* 설명: 문서 업로드 후 OCR/추출 처리 상태를 저장하는 Job 테이블

#### 3.9.1 필드 정의

| 필드명        | 타입            | NULL 허용 | 기본값                 | 제약/인덱스                               | 설명                     |
|------------|---------------|---------|----------------------|----------------------------------------|------------------------|
| `id`       | `int`         | No      | `None`               | `primary_key=True`                     | Job 고유 ID             |
| `user_id`  | `int`         | No      | -                    | `index=True`, `foreign_key="user.id"`  | 소유 사용자 ID            |
| `document_id` | `int \| None` | Yes  | `None`               | `index=True`, `foreign_key="document.id"` | 대상 문서 ID (선택)      |
| `product_id` | `int \| None` | Yes  | `None`               | `index=True`, `foreign_key="product.id"` | 연결된 제품 ID (선택)    |
| `status`   | `str`         | No      | `"pending"`          | `index=True`                           | 처리 상태(pending/processing/completed/failed) |
| `error`    | `str \| None` | Yes     | `None`               | -                                      | 실패 시 에러 메시지 (민감정보 마스킹 적용) |
| `created_at` | `datetime`  | No      | `datetime.utcnow()`  | -                                      | 생성 시각 (UTC)          |
| `updated_at` | `datetime`  | No      | `datetime.utcnow()`  | -                                      | 수정 시각 (UTC)          |

## 4. 비테이블 도메인 객체 (코드 전용)

일부 구조는 DB 테이블이 아니라, **알림/도메인 로직에서만 사용하는 데이터 구조**로 존재합니다.

### 4.1 DailyAlertItem / DailyAlert

* 파일: `app/services/notification_service.py`
* 타입: `@dataclass` 기반 파이썬 클래스
* 역할: 하루치 알림(Daily Alert)을 표현하는 in-memory 구조체

```python
@dataclass
class DailyAlertItem:
    product_id: int
    title: str
    purchase_date: date | None
    refund_deadline: date | None
    warranty_end_date: date | None


@dataclass
class DailyAlert:
    user_id: int
    email: str | None
    items: list[DailyAlertItem]
```

* 이 구조체들은:

  * 매일 배치 작업에서 `generate_daily_alerts()`가 반환하는 결과 형식으로 사용
  * DB에 그대로 저장되지 않으며, 알림 생성 후 폐기되는 일회성 구조입니다.
* 향후 알림 이력 저장이 필요할 경우,

  * `NotificationLog` 등의 별도 테이블을 정의하고 이 문서에 추가해야 합니다.

---

## 5. 모델 간 관계 요약

### 5.1 관계 다이어그램 (텍스트 표현)

* `User (1)` —— `(N) Product`
* `User (1)` —— `(1) NotificationSettings`
* `User (1)` —— `(0..1) TelegramAccount`
* `User (1)` —— `(N) Document`
* `User (1)` —— `(N) DocumentChunk`
* `User (1)` —— `(N) Embedding`
* `User (1)` —— `(N) LLMCache`
* `Document (1)` —— `(N) DocumentChunk`

즉, 한 사용자는 여러 제품을 가질 수 있고, 알림 설정과 텔레그램 계정은 최대 하나씩 가집니다.

---

## 6. 코드와의 정합성 체크리스트

코드 변경 시에는 아래 항목들을 체크해야 합니다.

1. `app/models/*.py`에 필드가 추가/수정/삭제되었는가?

   * 그렇다면 이 `DATA_MODEL.md`의 해당 테이블 정의를 함께 업데이트해야 합니다.

2. 인덱스/제약 조건이 변경되었는가?

   * `index=True`, `unique=True`, `nullable` 등 변경사항을 문서의 테이블에도 반영해야 합니다.

3. 새로운 엔티티(예: `NotificationLog`)가 추가되었는가?

   * 이 문서의 3.x 섹션에 새로운 엔티티 정의를 추가해야 합니다.

4. 비테이블 도메인 객체가 중요한 역할을 하도록 확장되었는가?

   * 예: DailyAlert 구조가 복잡해졌다면 4.x 섹션을 확장하거나 새로운 하위 섹션을 추가합니다.

---

## 7. 향후 확장 아이디어 (참고용)

아래 항목들은 당장 v0.1에 포함되지는 않지만, 데이터 모델 설계 시 미리 염두에 두면 좋은 확장 포인트입니다.

1. **NotificationLog 테이블**

   * 실제 발송된 알림 이력(채널, 발송 시각, 성공/실패 여부 등)을 저장하는 테이블

2. **ProductTag / Category 테이블 분리**

   * 제품 카테고리를 별도 테이블로 분리하고, 다대다 태그 구조를 지원하는 방향

3. **LLM/RAG 관련 테이블** (미래 버전)

   * 문서 임베딩, 검색 인덱스, 요약 결과 캐시 등을 저장하는 테이블

이러한 확장은 `docs/ROADMAP.md`와 함께 논의한 후, 실제로 도입될 때 이 문서에 정식으로 추가해야 합니다.
