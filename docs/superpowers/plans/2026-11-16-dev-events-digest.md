# Dev Events Digest Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 매주 월요일 10:00 KST에 주제별 개발자 웨비나/한국 오프라인 컨퍼런스 목록을 이메일로 보낸다.

**Architecture:** GitHub Actions 스케줄이 Python 파이프라인(collect → dedupe → filter → classify → exclude-sent → render → send → record)을 실행한다. 수집기는 소스별 독립 모듈이며 실패가 격리된다.

**Tech Stack:** Python 3.12, pytest, httpx, beautifulsoup4, PyYAML, Jinja2, GitHub Models(OpenAI 호환 API), smtplib, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-16-dev-events-digest-design.md`

## Global Constraints

- 스케줄: `cron: "0 1 * * 1"` (= 월 10:00 KST) + `workflow_dispatch`
- 대상 기간: 향후 60일 이내; 온라인 또는 한국 오프라인 행사만
- 수신자 1명, 알림은 이메일(SMTP)만; 시크릿은 GitHub Actions secrets
- 주제는 `topics.yaml`로만 추가/수정
- 이미 알린 행사는 `state/sent.json`(URL 목록)로 제외
- LLM 실패 시 키워드 fallback; 소스 1개 실패가 전체를 중단시키지 않음
- 이메일/요약 언어: 한국어; CLI `python -m digest --dry-run`은 발송 대신 HTML 파일 출력

## Review Focus

- 행사 0건 → "이번 주 신규 행사 없음" 메일 발송 (Task 5)
- 시작일이 오늘/60일 경계, 종료일만 지난 행사 (Task 3)
- 타임존 없는 날짜 문자열 → KST로 간주 (Task 1)
- 제목은 같고 URL이 다른 중복 (Task 3)
- LLM이 목록에 없는 주제/깨진 JSON 반환 (Task 4)

---

### Task 1: Project scaffold + Event model

**Files:**
- Create: `pyproject.toml`, `digest/__init__.py`, `digest/models.py`, `topics.yaml`, `tests/test_models.py`

**Interfaces:**
- Produces: `@dataclass Event(title: str, url: str, start: datetime, end: datetime | None, location: str, online: bool, source: str, description: str = "", topics: list[str] = [], summary: str = "")`; `KST = ZoneInfo("Asia/Seoul")`; `parse_kst(s: str) -> datetime` (naive → KST 부여, ISO 8601)

- [ ] **Step 1:** `tests/test_models.py`: `test_parse_kst_naive_gets_kst` (`parse_kst("2026-12-01T14:00").tzinfo == KST`), `test_parse_kst_keeps_explicit_offset` (`"...+00:00"` 유지).
- [ ] **Step 2:** `pytest tests/test_models.py -v` → FAIL (모듈 없음)
- [ ] **Step 3:** `pyproject.toml`(deps 위 스택, pytest 설정), `digest/models.py` 구현. `topics.yaml`에 `ai`, `devops`, `platform-engineering`, `cloud`, `security` 정의(`name`, `description`, `keywords`).
- [ ] **Step 4:** `pytest tests/test_models.py -v` → PASS
- [ ] **Step 5:** commit `feat: scaffold project and Event model`

### Task 2: Collectors

**Files:**
- Create: `digest/collectors/__init__.py`, `base.py`, `festa.py`, `onoffmix.py`, `meetup.py`, `cncf.py`, `cloud_vendors.py`, `tests/fixtures/<source>.*`, `tests/test_collectors.py`

**Interfaces:**
- Consumes: `Event`, `parse_kst`
- Produces: `class Collector(Protocol): name: str; def fetch(self) -> list[Event]`; `ALL_COLLECTORS: list[Collector]`; `collect_all(collectors=ALL_COLLECTORS) -> tuple[list[Event], list[str]]` (이벤트, 실패 소스 이름들); HTTP는 timeout 15s, 최대 2회 재시도.

- [ ] **Step 1:** 소스별로 접근 방식(공식 API/RSS/ICS/HTML) 조사 후 약관상 스크래핑 불가 소스는 제외하고 사용자에게 보고. 실제 응답 샘플을 `tests/fixtures/`에 저장.
- [ ] **Step 2:** 테스트: 소스별 `test_<source>_parses_fixture`(fixture → 기대 Event 수·첫 title/start/online), `test_collect_all_isolates_failure`(하나가 예외 → 나머지 이벤트 반환 + 실패 이름 목록에 포함). 네트워크 미사용(파서는 `parse(raw) -> list[Event]`로 분리).
- [ ] **Step 3:** `pytest tests/test_collectors.py -v` → FAIL
- [ ] **Step 4:** 수집기와 `collect_all` 구현.
- [ ] **Step 5:** `pytest tests/test_collectors.py -v` → PASS
- [ ] **Step 6:** commit `feat: add event collectors`

### Task 3: Dedupe + filter

**Files:**
- Create: `digest/pipeline/__init__.py`, `dedupe.py`, `filter.py`, `tests/test_dedupe_filter.py`

**Interfaces:**
- Consumes: `Event`, `KST`
- Produces: `dedupe(events: list[Event]) -> list[Event]` (정규화 제목[소문자·공백/구두점 제거] + 시작 날짜 동일 시 중복; URL 같아도 중복; 먼저 온 것 유지); `filter_events(events, now: datetime, days: int = 60) -> list[Event]` (`(end or start) >= now` 이고 `start <= now+days`; `online or 한국 location`; 한국 판별은 location에 한국 도시/“Korea”/“한국” 포함)

- [ ] **Step 1:** 테스트: `test_dedupe_same_title_date_different_url`, `test_dedupe_same_url`, `test_filter_excludes_past`, `test_filter_includes_ongoing_by_end_date`, `test_filter_boundary_day_60_included_61_excluded`, `test_filter_excludes_overseas_offline`, `test_filter_keeps_online_anywhere`.
- [ ] **Step 2:** `pytest tests/test_dedupe_filter.py -v` → FAIL
- [ ] **Step 3:** 구현.
- [ ] **Step 4:** `pytest tests/test_dedupe_filter.py -v` → PASS
- [ ] **Step 5:** commit `feat: add dedupe and filter`

### Task 4: Classifier

**Files:**
- Create: `digest/pipeline/classify.py`, `tests/test_classify.py`

**Interfaces:**
- Consumes: `Event`, `topics.yaml`
- Produces: `load_topics(path="topics.yaml") -> list[Topic]` (`Topic(name, description, keywords)`); `keyword_classify(event, topics) -> list[str]` (키워드 매칭, 없으면 `["other"]`); `classify(events, topics, llm=default_llm) -> list[Event]` (`llm(prompt: str) -> str`는 JSON `[{"url":..., "topics":[...], "summary":"..."}]` 반환 기대; topics는 정의된 이름만 허용, 아니면 폐기 후 키워드 fallback; 예외/깨진 JSON → 전체 fallback, summary는 description 첫 문장). `default_llm`은 GitHub Models(`GITHUB_TOKEN`) 호출.

- [ ] **Step 1:** 테스트(llm은 가짜 함수 주입): `test_classify_uses_llm_topics_and_summary`, `test_classify_drops_unknown_topic_falls_back`, `test_classify_broken_json_falls_back_to_keywords`, `test_classify_llm_exception_falls_back`, `test_keyword_classify_no_match_is_other`.
- [ ] **Step 2:** `pytest tests/test_classify.py -v` → FAIL
- [ ] **Step 3:** 구현 (이벤트 20개씩 배치 호출).
- [ ] **Step 4:** `pytest tests/test_classify.py -v` → PASS
- [ ] **Step 5:** commit `feat: add LLM classifier with keyword fallback`

### Task 5: Sent state + render + send

**Files:**
- Create: `digest/state.py`, `digest/render.py`, `digest/templates/digest.html.j2`, `digest/send.py`, `tests/test_state_render_send.py`

**Interfaces:**
- Consumes: `Event`
- Produces: `load_sent(path="state/sent.json") -> set[str]`, `save_sent(urls: set[str], path)`, `exclude_sent(events, sent) -> list[Event]`; `render_html(events: list[Event], failed_sources: list[str], today: date) -> str` (주제별 섹션, 시작일 오름차순, 행사 0건이면 "이번 주 신규 행사 없음", 실패 소스 경고 하단 표시); `send_email(html: str, subject: str)` (env `SMTP_HOST/PORT/USER/PASSWORD`, `MAIL_TO`; smtplib SSL).

- [ ] **Step 1:** 테스트: `test_exclude_sent_removes_known_urls`, `test_load_sent_missing_file_is_empty`, `test_render_groups_by_topic_sorted_by_start`, `test_render_empty_says_no_new_events`, `test_render_lists_failed_sources`, `test_send_email_builds_message` (smtplib mock으로 To/Subject/HTML 확인).
- [ ] **Step 2:** `pytest tests/test_state_render_send.py -v` → FAIL
- [ ] **Step 3:** 구현.
- [ ] **Step 4:** `pytest tests/test_state_render_send.py -v` → PASS
- [ ] **Step 5:** commit `feat: add state, rendering and email sending`

### Task 6: CLI + GitHub Actions workflow

**Files:**
- Create: `digest/__main__.py`, `.github/workflows/weekly.yml`, `README.md`, `tests/test_cli.py`

**Interfaces:**
- Consumes: 모든 이전 Task
- Produces: `main(argv: list[str] | None = None) -> int`; `--dry-run`은 `out/digest.html`에 쓰고 발송·state 기록 안 함; 정상 실행은 발송 성공 후에만 `save_sent` 호출.

- [ ] **Step 1:** 테스트: `test_dry_run_writes_html_and_does_not_send_or_record`, `test_run_records_sent_only_after_successful_send` (파이프라인 단계 monkeypatch).
- [ ] **Step 2:** `pytest tests/test_cli.py -v` → FAIL
- [ ] **Step 3:** `main` 구현. 워크플로: cron `0 1 * * 1` + `workflow_dispatch`, `permissions: contents: write, models: read`, 파이프라인 실행 후 `state/sent.json` 변경 시 커밋·푸시. README에 필요한 secrets(`SMTP_*`, `MAIL_TO`) 및 로컬 dry-run 방법 기재.
- [ ] **Step 4:** `pytest -v` 전체 → PASS; `python -m digest --dry-run` 로 실제 `out/digest.html` 생성 확인.
- [ ] **Step 5:** commit `feat: add CLI and weekly workflow`
