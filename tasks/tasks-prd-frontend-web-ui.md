# Tasks: PRD Frontend Web UI (Static /app)

## Relevant Files

- `app/main.py` - FastAPI 엔트리포인트(라우터/정적 서빙 등록 대상)
- `app/api/routes/auth.py` - 로그인/회원가입 API
- `app/api/routes/documents.py` - 업로드 202 + job_id
- `app/api/routes/jobs.py` - Job 폴링
- `app/api/routes/products.py` - 제품 리스트/상세/수정
- `app/api/routes/notification_settings.py` - 알림 설정
- `app/api/routes/telegram_account.py` - 텔레그램 연동
- `app/schemas/*.py` - 요청/응답 스키마
- `docs/API_EXAMPLES.md` - API 사용 예시
- `docs/DEV_GUIDE.md` - 실행/운영 가이드
- `tasks/prd-frontend-web-ui.md` - UI PRD

## Notes

- Implemented candidates (근거 확인됨):
  - 로그인/업로드/Job/제품/알림/텔레그램 API는 이미 구현되어 있음
  - 정적 UI(`/app`)는 아직 미구현 → Step4에서 구현

## Tasks

- [ ] 1.0 정적 UI 서빙 구조 확정
  - [ ] 1.1 `/app` 정적 파일 서빙 스켈레톤 추가 (파일: `app/main.py`, `app/api/routes/*` 또는 `app/static/*`; 검증: 브라우저에서 `/app` 로드)
  - [ ] 1.2 라우팅 전략 결정(해시/히스토리) 및 문서화 (파일: `tasks/prd-frontend-web-ui.md` 업데이트; 검증: 문서 리뷰)

- [ ] 2.0 로그인/회원가입 화면
  - [ ] 2.1 로그인 폼(POST /auth/login) + 토큰 저장(localStorage) (파일: `/app` 정적 UI; 검증: 로그인 후 토큰 저장 확인)
  - [ ] 2.2 회원가입 폼(POST /auth/register) + 성공/실패 UX (파일: `/app` 정적 UI; 검증: 201/409 분기 표시)
  - [ ] 2.3 로그아웃/토큰 제거 UX (파일: `/app` 정적 UI; 검증: 토큰 삭제 후 401 처리)

- [ ] 3.0 업로드 + Job 폴링
  - [ ] 3.1 업로드 폼(파일 제한 안내: 10MB/PDF 3p) + 기본 검증 (파일: `/app` 정적 UI; 검증: 제한 안내 표시)
  - [ ] 3.2 업로드 202 처리 + job_id 수신 (파일: `/app` 정적 UI; 검증: 업로드 후 job_id 표시)
  - [ ] 3.3 Job 폴링(2초 간격, 90초 타임아웃) + 상태 표시 (파일: `/app` 정적 UI; 검증: 완료/실패 UI 전환)
  - [ ] 3.4 completed 시 product_id로 이동, failed 시 요약 메시지 (파일: `/app` 정적 UI; 검증: 상태별 메시지)

- [ ] 4.0 제품 리스트
  - [ ] 4.1 `GET /products` 호출 및 리스트 렌더링 (파일: `/app` 정적 UI; 검증: 리스트 표시)
  - [ ] 4.2 빈 목록/에러 처리(404 은닉 포함) (파일: `/app` 정적 UI; 검증: 안내 메시지 표시)

- [ ] 5.0 제품 상세/수정
  - [ ] 5.1 `GET /products/{id}` 상세 표시 (파일: `/app` 정적 UI; 검증: 상세 필드 렌더링)
  - [ ] 5.2 `PUT /products/{id}` 수정 저장 (파일: `/app` 정적 UI; 검증: 저장 성공/실패 메시지)
  - [ ] 5.3 raw_text 마스킹 표시 확인 (파일: `/app` 정적 UI; 검증: 마스킹된 텍스트만 표시)

- [ ] 6.0 알림 설정
  - [ ] 6.1 `GET /notification-settings` 조회 (파일: `/app` 정적 UI; 검증: 기본값 표시)
  - [ ] 6.2 `PUT /notification-settings` 수정 (파일: `/app` 정적 UI; 검증: 리스트[int] 입력 유지)

- [ ] 7.0 텔레그램 연동
  - [ ] 7.1 `GET /telegram-account` 조회(없으면 404) (파일: `/app` 정적 UI; 검증: 미연동 안내)
  - [ ] 7.2 `POST /telegram-account` 연동 (파일: `/app` 정적 UI; 검증: 201 응답 표시)
  - [ ] 7.3 `DELETE /telegram-account` 해제 (파일: `/app` 정적 UI; 검증: 상태 비활성 표시)

- [ ] 8.0 UI 스모크 체크리스트
  - [ ] 8.1 Golden Path 수동 점검 체크리스트 추가 (파일: `docs/RELEASE_GATE.md` 또는 별도 문서; 검증: 문서 리뷰)
  - [ ] 8.2 에러 분류표(Error Taxonomy) UI 메시지 매핑 정리 (파일: `/app` 문서 또는 PRD; 검증: 문서 리뷰)
