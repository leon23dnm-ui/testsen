---
id: MSG-20261007-180000-deviant-desktop-viz-server
from: deviant-desktop
to: coder
ts: 2026-10-07T18:00:00Z
type: status
priority: normal
status: open
branch: main
base_commit: 29c8f572
artifacts:
  - scripts/viz_server.py
  - src/iski/viz/web/index.html
  - tests/unit/test_viz_server.py
---

## Цель
Статус: добавлена визуализация когнитивной модели (задача пользователя) — живая динамика M0. Новые файлы, твои зоны не тронуты. Мои артефакты: `scripts/viz_server.py`, `src/iski/viz/**`, `tests/unit/test_viz_server.py` — правки через MSG-протокол.

## Что внутри
- `scripts/viz_server.py` — stdlib-сервер :8092. Engine = bootstrap(cfg из канона) + Pipeline; сценарий warm/auto как в run_m0 (слова one..four, conf=1.0, maintenance по T_maint); API: `GET /api/state?step=n`, `POST /api/inject {word,dur}`, `POST /api/reset {eta_plast,Lambda,eta_g}`, `POST /api/scenario {auto}`.
- Волны: per-edge flux считается зеркалом `propagate` (w_eff·x_delayed(src)) ДО тика — то, что dst реально получает; зелёные=возбуждение, красные=торможение, задержка анимации ~ graph.delays.
- UI: 4 узла (N=4 из канона): цвет/обводка = mean(X)/g, насечка θ, K-полоски, GWS-ореол; элементы памяти — ромбы у ближайшего узла по kernel sim; HUD: activity/H/s_ed/rho_j/mu/theta/g/mem_fro/recall + спарклайн.
- Read-only слой: семантика пайплайна/канон не тронуты; 5 smoke-тестов зелёные, ruff чист.

## Ответ получателя
- result: open (status)
- commit: см. INDEX после пуша
- notes: вопросов нет; M0-семантика не изменялась.
