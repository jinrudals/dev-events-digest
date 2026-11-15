# Dev Events Digest — Design

## Goal
매주 월요일 10:00 KST에, 개발자가 참여할 수 있는 웨비나와 한국 내 오프라인 컨퍼런스를 주제별(AI, DevOps, Platform Engineering 등)로 정리해 이메일로 보낸다. 수신자는 본인 1명.

## Non-goals
- 다중 구독자 관리, 웹 UI, 서버 상시 운영, 알림 채널 다변화 (이메일만).

## Architecture
GitHub Actions 스케줄 워크플로 (`cron: "0 1 * * 1"` = 월 10:00 KST, `workflow_dispatch` 병행) 가 Python 파이프라인을 실행한다.

```
collect -> normalize -> dedupe -> filter -> classify(LLM) -> exclude-sent -> render -> send -> record
```

## Components
- `collectors/` — 소스당 파일 1개, 공통 인터페이스 `fetch() -> list[Event]`. 소스: Festa, Onoffmix, Meetup, CNCF 캘린더, AWS/Google Cloud/Microsoft 한국 행사. 한 소스 실패는 로그 + 메일 하단 경고로 처리하고 나머지는 진행.
- `models.py` — `Event(title, url, start, end, location, online, source, description)`.
- `pipeline/dedupe.py` — 정규화한 제목 + 날짜 기준 중복 제거.
- `pipeline/filter.py` — 향후 60일 이내, (온라인 또는 한국 오프라인) 행사만.
- `pipeline/classify.py` — LLM(GitHub Models)으로 `topics.yaml`의 주제 라벨 부여 + 한 줄 요약(한국어). 실패 시 키워드 매칭 fallback.
- `topics.yaml` — 주제 정의(이름, 설명, 키워드). 주제 추가는 이 파일만 수정.
- `state/sent.json` — 이미 알린 행사 URL 기록. 워크플로가 실행 후 커밋.
- `render.py` — 주제별 섹션 HTML 이메일(제목, 날짜, 온/오프라인, 장소, 링크, 요약), 이번 주 신규/임박순 정렬.
- `send.py` — SMTP(Gmail 앱 비밀번호) 발송. 시크릿은 GitHub Actions secrets.
- CLI: `python -m digest --dry-run` 은 발송 대신 HTML을 파일로 출력.

## Error handling
- 소스별 timeout/재시도(최대 2회), 실패 격리.
- LLM 실패 → 키워드 fallback.
- 행사 0건이어도 "이번 주 신규 행사 없음" 메일 발송.
- 발송 실패 → 워크플로 실패(GitHub 알림)로 인지.

## Testing
- 수집기: 저장된 샘플 응답 fixture 파싱 테스트(네트워크 미사용).
- dedupe/filter/classify fallback/render 단위 테스트.
- dry-run 으로 end-to-end 확인.

## Open items (구현 시 확정)
- 각 소스의 실제 접근 방식(API/RSS/HTML) 은 구현 단계에서 소스별로 조사해 결정한다. 스크래핑이 약관상 불가한 소스는 제외하고 보고한다.
