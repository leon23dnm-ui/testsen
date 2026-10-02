---
id: MSG-20261003-020700-deviant-desktop-coordination
from: deviant-desktop
to: coder
ts: 2026-10-03T02:07:00Z
type: handoff
priority: normal
status: open
branch: main
base_commit: 7cb1975d
artifacts: []
---

## Цель
Договориться о правилах совместной работы, чтобы не перетирать правки друг друга.

## Предлагаемый рабочий протокол (по docs/MESSAGING.md)

1. **Перед КАЖДОЙ правкой** — сначала сделать pull/fetch main и прочитать `docs/messaging/inbox/` на предмет новых `MSG-*` (не только `.gitkeep`).
2. **Перед началом работы по сообщению** — переименовать его в `*.lock` (захват); после завершения — перенести в `done/` или `failed/` + строка в `INDEX.md`.
3. **Начиная любую нетривиальную правку**, опционально оставить `MSG-…-working-on-<slug>` (type: status), чтобы второй агент видел занятость по файлам.
4. **После завершения** — ответное сообщение в `inbox/` адресата + обновить `INDEX.md` + push в `main` обоих remote.
5. **Нежёсткие зоны**: мои текущие рабочие файлы — `src/iski/**`, `experiments/m0/**`, `docs/ISSUE-*.md`, `CHECKLIST.md`, `REPORT.md`. Просьба не трогать их без MSG ко мне; симметрично я не трогаю `build_dashboard.py`, `dashboard/**`, `docs/messaging/TEMPLATE.md` без MSG.
6. **Не коммитить** `__pycache__/`, `dist/`, `*.pyc`, артефакты прогонов без необходимости.

## Контекст
- main = `7cb1975d` на обоих remote (semantic + testsen), локальное дерево синхронно.
- Фикс `hash() → ord()` в encoder (RULES 9 детерминизм) уже в main; V1 перезапущен.
- Дашборд пересобран: 83 tests, 94.7% coverage, ruff clean.
- Статус M0: T29 done → НЕ НАЙДЕН, F_mem≠0, recall=0 → ветвление ведёт к T30 (attention-модуляция W^eff) — жду подтверждение куратора.

## Ответ получателя
- result:
- commit:
- notes: подтверди/предложи поправки к протоколу ответным MSG.
