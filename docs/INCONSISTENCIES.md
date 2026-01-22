# INCONSISTENCIES (Step 2 불일치 정리)

> 기준 우선순위: AGENTS.md > tasks/prd-*.md > tasks/tasks-prd-*.md > docs/* > code
> 단일 기준 결정: AGENTS + 실제 동작(테스트/스모크) + tasks/tasks-prd

| ID | 축(A~F) | Claim(문서/라인) | Reality(코드/테스트 근거) | 단일 기준 결론 | 조치(P0/P1) | 상태 |
|---|---|---|---|---|---|---|
| INC-001 | A | docs/API_EXAMPLES.md: `/assistant/*` 예시 / docs/SYSTEM_ARCHITECTURE.md: assistant 서비스/라우트 언급 | app/api/routes에 assistant 없음, app/services/assistant.py 없음 | v0.1은 assistant/RAG 제외(AGENTS/PROJECT_OVERVIEW). 문서에서 v0.2 예정으로 표기 | P0 문서 수정(assistant 섹션 v0.2 예정으로 조정) | resolved |
| INC-002 | D | tasks/prd-ops-free-paas-deployment-and-scheduler.md: cron 엔드포인트 없음, daily alerts 스켈레톤 TODO | app/api/routes/cron.py 존재, tests/test_cron.py 200/403 검증 | 실제 동작 기준으로 PRD 현황 갱신 | P0 문서 수정(PRD Current Status 갱신) | resolved |
| INC-003 | B | docs/PROJECT_OVERVIEW.md/DEV_GUIDE.md: 업로드 타입 이미지/PDF만 지원 | app/api/routes/documents.py는 MIME 강제 검증 없음(확장자 기반 처리) | 정책은 이미지/PDF 지원이지만 서버 레벨 MIME 검증은 미구현 | P1 코드 개선(파일 타입 검증 추가) 또는 문서에 “비보장” 주석 | open |
| INC-004 | E | docs/DEV_GUIDE.md의 `.env` 예시에 LLM_DAILY_QUOTA/RAG_TOP_K 등 추가 키 | app/core/config.py에는 해당 키 없음, .env.example에도 없음 | AppSettings/.env.example 기준으로 문서 정합 | P0 문서 수정(예시 키 정리) | resolved |
| INC-005 | C | docs/PROJECT_OVERVIEW.md/ SYSTEM_ARCHITECTURE.md: uploads best-effort, 핵심은 DB 텍스트 | app/models/document.py에 raw_text/parsed_fields 저장, 파일 서빙 라우트 없음 | 정책/구현 일치(파일 소실 시 텍스트 기반 유지) | 문서 유지 | ok |
| INC-006 | F | AGENTS.md: 모든 CRUD는 current_user.id 스코프 + 404 은닉 | app/api/routes/*에서 user_id 필터 + 404 처리 확인 | 정책/구현 일치 | 유지 | ok |

## 메모
- P1 항목은 docs/KNOWN_WARNINGS.md에 대응 계획으로 기록한다.
