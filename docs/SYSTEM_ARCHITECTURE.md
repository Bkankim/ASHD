# SYSTEM_ARCHITECTURE.md

## 1. 전체 아키텍처 개요

### 1.1 목표

ASHD v0.1은 **단일 FastAPI 애플리케이션 + 단일 RDB + 배치 알림 작업** 구조를 가진, 단순하지만 확장 가능한 웹 서비스 아키텍처를 지향합니다.
v0.2에서는 **RAG-lite(키워드 검색 + LLM 요약)** 레이어를 추가하여 확장합니다.

* 백엔드: FastAPI
* 데이터 계층: SQLModel 기반 RDB (초기에는 파일 기반 SQLite를 가정 가능)
* 비즈니스 로직: `app/services/` 모듈들
* 문서 처리 파이프라인: 서비스 레이어 중심(현 구현) + `app/graphs/`는 v0.2 대비 설계(런타임 필수 아님)
* 알림 채널: 이메일, 텔레그램
* 스케줄링: 외부 스케줄러가 `POST /internal/cron/daily-alerts` 호출 (무료 PaaS 표준)
* 실행/의존성 관리: `uv` + `pyproject.toml`

### 1.2 논리적 컴포넌트

1. **API 레이어 (FastAPI)**

   * 엔드포인트 정의 (`app/api/routes/health.py`, `products.py` 등)
   * 인증/인가, 요청 유효성 검사, 응답 직렬화 담당

2. **도메인 모델/스키마 레이어**

   * `app/models/` : SQLModel 기반 DB 테이블 정의 (User, Product, NotificationSettings, TelegramAccount, Document, DocumentChunk, Embedding, LLMCache 등)
   * `app/schemas/` : Pydantic 기반 요청/응답 DTO 정의

3. **서비스 레이어**

   * `app/services/` : 비즈니스 로직 구현

     * `document_processing.py` : 업로드 후 OCR/필드 추출 파이프라인
     * `email_service.py` : 이메일 발송
     * `telegram_service.py` : 텔레그램 메시지 발송
     * `notification_service.py` : DailyAlert 계산 및 알림 대상 도출

   * `app/ocr/` : 외부 OCR API 클라이언트
   * `app/extractors/` : 룰/LLM 기반 필드 추출 로직

4. **RAG-lite 레이어 (v0.2)**

   * `app/retrieval/` : 키워드 기반 검색(FTS/LIKE) Retriever
   * `app/llm/` : LLM Client 인터페이스 + Mock/외부 API 어댑터
   * `assistant` 서비스/엔드포인트: v0.2 예정(현재 v0.1 미구현)
   * `app/models/document*.py` : 문서/청크/임베딩/캐시 테이블(업그레이드 대비)

5. **그래프 레이어 (LangGraph, v0.2 대비)**

   * `app/graphs/document_ingest_graph.py` : 업로드 후 처리 과정을 그래프로 정의(현재 v0.1 런타임 필수 아님)
   * 노드 단위로 OCR, 파싱, 검증 등을 분리하는 확장 경로로 유지

6. **인프라/환경 레イヤ**

   * `app/core/config.py` : Pydantic Settings 기반 환경 설정
   * `pyproject.toml` + `uv` : 의존성/런타임 관리
   * (향후) `docs/DEV_GUIDE.md` : 실행/배포 방법 문서화

---

## 2. 런타임 컴포넌트

### 2.1 API 서버

* 프로세스: `uv run uvicorn app.main:app --reload`
* 주요 책임:

  * HTTP 요청 처리 (REST API)
  * 인증/인가 처리 (v0.1 기준: 이메일 + 비밀번호 + JWT)
  * 파일 업로드 (영수증/보증서 이미지)
  * 텔레그램 웹훅/연동 엔드포인트 (텔레그램 계정 연결 시)
  * RAG-lite 질의 응답(`/assistant/*`) 엔드포인트는 v0.2 이후 도입 예정

### 2.2 일일 알림 트리거 (외부 스케줄러)

* 무료 PaaS 전제: 서버 내부 스케줄러 대신 **외부 스케줄러(예: GitHub Actions)**가 HTTP로 호출
* 호출 엔드포인트: `POST /internal/cron/daily-alerts`
  * 헤더 `X-CRON-SECRET`(= `CRON_SECRET`) 필요, 없거나 틀리면 403
* 역할:

  * 호출 시 현재 날짜 기준으로 보증/환불 임박 항목 조회
  * `notification_service.run_daily_alerts()` → DailyAlert 계산 및 이메일/텔레그램 발송(설정 없으면 skip)

### 2.3 외부 서비스 의존성

1. **SMTP 서버**

   * 이메일 발송용
   * `app/core/config.py` 에서 호스트/포트/계정정보를 환경 변수로 주입

2. **텔레그램 Bot API**

   * 텔레그램 알림 발송용
   * `telegram_bot_token` 값을 `.env`에서 주입
   * `app/services/telegram_service.py`에서 HTTP 요청으로 메시지 전송

3. **OCR 외부 API (v0.1 기본)**

   * v0.1에서는 로컬 OCR 대신 **외부 OCR API** 호출을 기본으로 합니다.
   * `app/ocr/external.py`에 클라이언트를 두고, 키가 없으면 Mock으로 동작합니다.

4. **LLM API (v0.1 필드 추출 + v0.2 RAG-lite)**

   * v0.1에서는 OCR 결과 텍스트의 부족한 필드를 LLM(Solar API 등)으로 보완합니다.
   * v0.2에서는 RAG-lite 답변 생성에 사용합니다.
   * 키가 없으면 Mock LLM으로 동작하도록 설계합니다.

---

## 3. 디렉터리 구조와 역할

아래 구조는 **현재 리포 기준**으로 정리했습니다.

```text
.
├── README.md
├── pyproject.toml
├── .gitignore
├── .env.example
├── docs/
│   ├── PROJECT_OVERVIEW.md
│   ├── SYSTEM_ARCHITECTURE.md
│   ├── DATA_MODEL.md
│   ├── NOTIFICATION_DESIGN.md
│   ├── RAG_LITE_DESIGN.md
│   ├── PRD_V0_2_LLM_RAG_LITE.md
│   ├── API_EXAMPLES.md
│   ├── ROADMAP.md
│   └── DEV_GUIDE.md
└── app/
    ├── __init__.py
    ├── main.py
    ├── core/
    │   ├── __init__.py
    │   ├── config.py
    │   ├── db.py
    │   ├── health.py
    │   └── security.py
    ├── api/
    │   ├── __init__.py
    │   ├── dependencies/
    │   │   └── auth.py
    │   └── routes/
    │       ├── __init__.py
    │       ├── health.py
    │       ├── auth.py
    │       ├── documents.py
    │       ├── jobs.py
    │       ├── products.py
    │       ├── notification_settings.py
    │       ├── telegram_account.py
    ├── models/
    │   ├── __init__.py
    │   ├── user.py
    │   ├── product.py
    │   ├── notification.py
    │   ├── telegram_account.py
    │   ├── document.py
    │   ├── document_chunk.py
    │   ├── embedding.py
    │   ├── llm_cache.py
    │   └── job.py
    ├── schemas/
    │   ├── __init__.py
    │   ├── user.py
    │   ├── product.py
    │   ├── document.py
    │   ├── job.py
    │   ├── notification_settings.py
    │   ├── telegram_account.py
    ├── services/
    │   ├── __init__.py
    │   ├── document_processing.py
    │   ├── ocr_service.py
    │   ├── email_service.py
    │   ├── telegram_service.py
    │   ├── notification_service.py
    ├── ocr/
    │   ├── __init__.py
    │   ├── base.py
    │   └── external.py
    ├── extractors/
    │   ├── __init__.py
    │   ├── rule.py
    │   └── llm.py
    ├── retrieval/
    │   ├── __init__.py
    │   ├── base.py
    │   └── keyword.py
    ├── llm/
    │   ├── __init__.py
    │   ├── base.py
    │   ├── mock.py
    │   └── openai_compat.py
    └── graphs/
        ├── __init__.py
        └── document_ingest_graph.py
```

각 디렉터리/파일의 역할 요약:

* `app/main.py`: FastAPI 엔트리 포인트, 라우터 등록, uvicorn 실행 진입점
* `app/core/config.py`: 환경설정 (SMTP, 텔레그램 토큰 등)
* `app/api/routes/`: HTTP 엔드포인트 정의
* `app/models/`: SQLModel 기반 DB 테이블
* `app/schemas/`: Pydantic 스키마 (요청/응답 DTO)
* `app/services/`: 도메인 비즈니스 로직/외부 서비스 연동
* `app/graphs/`: LangGraph 기반 문서 처리 파이프라인 정의

### 3.1 파일 저장 제약(무료 PaaS)

* 무료 PaaS 로컬 파일시스템은 슬립/재시작/배포 시 소실될 수 있습니다(uploads/는 best-effort).
* 핵심 데이터는 DB에 저장된 `raw_text`/`parsed_fields`/`evidence`이며, 파일은 참고용입니다.
* 파일이 사라져도 알림/검색은 DB 텍스트로 계속 동작할 수 있지만, 원본 표시/다운로드는 “파일 없음” 안내가 필요합니다.
* v0.1은 업로드 직후 파일 존재를 전제로 Job을 실행하며, v0.2에서 외부 스토리지(S3/GCS 등) 이관을 검토합니다.

---

## 4. 주요 플로우 (시퀀스 관점)

### 4.1 제품/문서 등록 플로우 (이미지 업로드)

1. 사용자가 웹 UI에서 로그인 후, 영수증/보증서 이미지를 업로드
2. 클라이언트 → API 서버:

   * `POST /documents/upload` (파일 업로드)
3. API 레이어 (`app/api/routes/documents.py`):

   * 업로드된 파일을 로컬 디스크에 저장
   * `Document` + `DocumentProcessingJob` 레코드 생성
   * 202 응답으로 `job_id` 반환
   * 무료 PaaS 환경에서는 로컬 디스크가 영구 보장되지 않을 수 있어,
     v0.2에서 외부 스토리지(S3 등) 전환을 고려
4. 백그라운드 처리 (`app/services/document_processing.py`):

   * 외부 OCR API 호출 (`app/ocr/external.py`) → `raw_text` 저장
   * 룰 기반 필드 추출 → 부족한 필드만 LLM 보완 (`app/extractors/`)
   * `Product` 생성 + `Document.product_id` 연결
   * Job 상태를 `completed`로 변경
5. 클라이언트는 `GET /jobs/{id}`로 상태를 조회하고, 완료 후 제품 정보를 확인

### 4.2 Daily Alert 알림 플로우 (외부 cron 호출)

1. 외부 스케줄러(예: GitHub Actions)가 하루 1회 `POST /internal/cron/daily-alerts` 호출
   * 헤더 `X-CRON-SECRET`가 유효하지 않으면 403
2. `notification_service.run_daily_alerts()` 실행

   * 현재 날짜 기준으로 DB에서 Product/NotificationSettings 조회
   * 환불/보증 임박 조건(D-30, D-7, D-3 등) 충족 항목을 사용자별로 묶음
3. 전송 단계:

   * 이메일 설정이 모두 존재하면 `email_service.send_email()` 호출, 없으면 skip
   * 텔레그램 토큰/연동(chat_id)이 있으면 `telegram_service.send_telegram_message()` 호출, 없으면 skip
4. 실패/미구현 채널은 errors/skip 요약에 남기고 200 응답 유지(무료 PaaS 안정성 우선)

---

## 5. LangGraph 기반 문서 처리 아키텍처

v0.1에서는 `BackgroundTasks` 기반 처리 흐름을 우선 사용하며,
LangGraph는 향후 확장 시 참고할 **스켈레톤**으로 유지합니다.

### 5.1 상태 정의 (`DocumentState`)

`app/graphs/document_ingest_graph.py`에서 TypedDict 기반으로 상태를 정의합니다.

예시 필드:

* `image_path: str` : 업로드된 이미지 경로
* `raw_text: str` : OCR 결과 텍스트
* `parsed_fields: dict` : 파싱된 필드(구매일/금액/구매처 등)
* `messages: list[str]` : 디버깅/로그 메시지

### 5.2 기본 노드들

1. `node_ocr`

   * 입력: `DocumentState` (image_path 포함)
   * 처리: `ocr_service.extract_text_from_image()` 호출 → `raw_text` 채우기
   * 출력: 업데이트된 `DocumentState`

2. `node_parse`

   * 입력: `DocumentState` (raw_text 포함)
   * 처리: 정규식 또는 LLM 도입 전까지는 규칙 기반 파서로 `parsed_fields` 채우기
   * 출력: `parsed_fields`가 채워진 상태

### 5.3 그래프 구성

* `build_document_ingest_graph()` 함수에서:

  * `StateGraph(DocumentState)` 생성
  * 노드 등록: `ocr`, `parse`
  * 엣지 정의: `ocr` → `parse` → `END`
* API나 서비스 레이어에서 이 그래프를 호출할 때는:

  * 초기 상태를 구성하고
  * 그래프를 실행한 후
  * 최종 상태에서 `raw_text`, `parsed_fields`를 꺼내 Product 모델 업데이트에 사용

---

## 6. 데이터베이스 및 트랜잭션 전략 (초기)

### 6.1 DB 선택

* v0.1에서는 개발/테스트 용이성을 위해 **SQLite** (파일 기반)를 기본 가정할 수 있습니다.
* 이후 실제 서비스 환경에서는 PostgreSQL 등으로 마이그레이션을 검토합니다.

### 6.2 ORM/모델 계층

* SQLModel을 사용하여 모델/테이블을 동시에 정의합니다.
* `app/models/`에 주요 엔티티를 분리:

  * `User`
  * `Product`
  * `NotificationSettings`
  * `TelegramAccount`
* 구체적인 필드/관계 정의는 `docs/DATA_MODEL.md`와 동기화합니다.

### 6.3 트랜잭션

* API 요청 단위로 세션을 열고 닫는 패턴(예: FastAPI 의존성)을 사용합니다.
* 문서 업로드 + 그래프 처리의 경우:

  * Product 생성 후 그래프 실행 결과에 따라 업데이트를 같은 트랜잭션 안에서 수행할지,
  * 또는 비동기 처리/백그라운드 작업으로 분리할지 v0.1에서 단순성을 우선하여 결정합니다.

---

## 7. 비기능 요구사항과 아키텍처 상의 고려사항

### 7.1 단순성 우선

* 마이크로서비스가 아닌 단일 애플리케이션 구조를 유지합니다.
* 한 명의 개발자가 전체 코드를 이해/수정할 수 있는 수준의 모듈 분리를 목표로 합니다.

### 7.2 확장성

* 기능 확장 시, 다음과 같이 모듈 단위 확장을 염두에 둡니다.

  * 알림 채널 추가 → `services/`에 새로운 Notifier 모듈 추가
  * 고급 검색/요약 기능 → 별도 `graphs/` 또는 `services/llm_*.py`로 분리
  * Kakao 나에게 보내기 → 별도 서비스 모듈로 추가 후 `NOTIFICATION_DESIGN`/`ROADMAP`에 반영

### 7.3 설정/비밀정보 관리

* 모든 민감정보는 `.env`를 통해 주입하고, `app/core/config.py`에서만 참조합니다.
* 코드/문서에는 실제 키나 비밀번호를 절대 포함하지 않습니다.

---

## 8. 다른 문서와의 연계

* `AGENTS.md`

  * 이 아키텍처 문서보다 상위의 규칙/범위를 정의하는 헌법 문서
* `docs/PROJECT_OVERVIEW.md`

  * 제품/서비스 관점에서의 요구사항 및 범위 정의
* `docs/DATA_MODEL.md`

  * 여기서 언급한 모델 구조를 필드/타입 수준까지 정교화
* `docs/NOTIFICATION_DESIGN.md`

  * DailyAlert, Notifier 인터페이스, 채널별 템플릿 등을 상세히 정의

코드/설계 변경 시, 위 문서들과의 일관성을 항상 유지해야 합니다.
