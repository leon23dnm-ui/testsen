---
id: MSG-YYYYMMDD-HHMMSS-coder-slug
from: coder            # coder | deviant-desktop
to: deviant-desktop    # адресат
ts: 2026-10-03T00:00:00Z
type: task             # task | question | review | status | handoff
priority: normal       # low | normal | high | block
status: open           # open | in-progress | done | failed
branch: qwen-code-rebase
base_commit: d64c656
artifacts: []          # файлы, которые получатель НЕ должен трогать
---

## Цель
<!-- Один абзац: что нужно получить на выходе. -->

## Контекст
<!-- Что уже сделано, где смотреть (пути, docs/ISSUE-*.md, REPORT.md). -->

## Ограничения
- Не менять src/iski/safety/** без явного разрешения.
- После изменений: `python -m pytest` и `ruff check src tests` должны быть чистыми.

## Критерии приёмки (Definition of Done)
- [ ] pytest: 0 failed
- [ ] ruff check/format: чисто
- [ ] дашборд пересобран (`python build_dashboard.py`) — если менялся код/тесты

## Ответ получателя
- result:
- commit:
- notes:
