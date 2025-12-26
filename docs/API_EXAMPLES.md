# API_EXAMPLES.md

## 인증

### 회원가입
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "pw1234"
}
```

### 로그인 (JWT Access Token 발급)
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "pw1234"
}
```
응답 예:
```json
{
  "access_token": "<jwt-token>",
  "token_type": "bearer"
}
```

## Authorization 헤더 예시
다른 보호된 엔드포인트 호출 시:
```
Authorization: Bearer <access_token>
```

## Products
### 제품 생성
```http
POST /products
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "노트북",
  "amount": 1500000,
  "purchase_date": "2024-01-10",
  "store": "온라인몰"
}
```
> 응답에 포함되는 `raw_text`는 **민감정보 마스킹된 형태**로만 반환됩니다.

## Documents
### 문서 업로드 (OCR 비동기 처리)
```http
POST /documents/upload
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

file=<image or pdf file>
```
> 파일 타입: 이미지(`image/*`) 또는 PDF(`application/pdf`)
응답 예:
```json
{
  "job_id": 1,
  "document_id": 1,
  "status": "pending"
}
```

### Job 상태 조회
```http
GET /jobs/1
Authorization: Bearer <access_token>
```
응답 예:
```json
{
  "id": 1,
  "status": "completed",
  "error": null,
  "document_id": 1,
  "product_id": 10,
  "created_at": "2024-01-10T12:00:00",
  "updated_at": "2024-01-10T12:00:05"
}
```

## NotificationSettings
### 설정 업데이트
```http
PUT /notification-settings
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "email_enabled": true,
  "telegram_enabled": true,
  "warranty_days_before": [30, 7, 3],
  "refund_days_before": [3]
}
```

## TelegramAccount
### 텔레그램 계정 등록/갱신
```http
POST /telegram-account
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "chat_id": "123456789",
  "username": "mytelegram"
}
```

## Assistant (RAG-lite)
### 질문하기
```http
POST /assistant/ask
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "question": "이 제품 환불 기한이 언제야?"
}
```

### 알림 미리보기
```http
POST /assistant/alerts/preview
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "base_date": "2024-01-10"
}
```
