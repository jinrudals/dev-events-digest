# Dev Events Digest

매주 월요일 10:00 KST에 개발자 웨비나/한국 오프라인 컨퍼런스를 주제별로 정리해 GitHub Pages로 발행하고 RSS로 알립니다 (GitHub Actions).

- 사이트: https://jinrudals.github.io/dev-events-digest/
- RSS: https://jinrudals.github.io/dev-events-digest/feed.xml (Feedly 등 리더 앱에 등록하면 푸시 알림)

## 소스
- [Dev-Event](https://github.com/brave-people/Dev-Event) 큐레이션 목록 (한국 개발자 행사)
- Onoffmix 검색 결과 (공개 목록 페이지)
- CNCF Community (KCD, Meetup 등; 한국/온라인만 남김)

Festa·Meetup·클라우드 3사는 공개 API/허용된 피드가 없어 제외했습니다. 소스 추가는 `digest/collectors/`에 `Collector`를 구현하고 `ALL_COLLECTORS`에 등록하세요.

## 설정
1. 저장소 Settings → Pages → Source를 **GitHub Actions**로 설정합니다 (비공개 저장소는 유료 플랜 필요).
2. 주제는 `topics.yaml`에서 추가/수정합니다.
3. Actions 탭에서 `weekly-digest`를 `dry_run`으로 한 번 실행해 결과를 확인하세요.

LLM 분류/요약은 GitHub Models(`GITHUB_TOKEN`)를 사용하며, 실패하면 키워드 분류로 대체됩니다. Secrets는 필요 없습니다.

## 로컬 실행
```bash
pip install -e ".[dev]"
pytest
python -m digest --dry-run   # out/digest.html 생성 (발행/상태 기록 없음)
```
`GITHUB_TOKEN`을 설정하면 로컬에서도 LLM 분류가 동작합니다.

이미 알린 행사는 `state/sent.json`에, 최근 20주 이력은 `state/history.json`에 기록됩니다.
