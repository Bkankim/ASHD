# NEXT_STEPS_PRODUCTION (1주일 내 프로덕션 플랜)

## P0 (1주일 내 필수)
1) 프론트엔드 MVP 화면
   - 로그인/회원가입, 문서 업로드+Job 폴링, 목록/상세, 알림 설정, 텔레그램 연동
2) 배포 체크리스트
   - PORT/CRON_SECRET/DATABASE_URL/SECRET_KEY/OCR/LLM/SMTP/TELEGRAM 환경변수
   - DB 초기화/마이그레이션(스키마 생성) 루틴 확인
3) 운영 최소 관측
   - Job 실패 원인 로그, cron 실패 로그, 외부 OCR/LLM 오류 카운트

## P1 (2~4주)
1) Swagger 인증 UX 개선(토큰 입력 UX)
2) 파일 영속화(S3/GCS 등) 옵션 도입
3) 리마인드 메시지 템플릿 고도화(다국어/템플릿)

## 백로그/정리
- FastAPI lifespan 전환
- datetime.utcnow 경고 제거
- PDF 페이지 수 계산 정확도 개선
