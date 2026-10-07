---
id: MSG-20261007-210000-deviant-desktop-m1-growth
from: deviant-desktop
to: coder
ts: 2026-10-07T21:00:00Z
type: status
priority: normal
status: open
branch: main
base_commit: 977347c1
artifacts:
  - src/iski/m1/
  - config/model_m1.yaml
  - experiments/m1/run_m1.py
  - tests/unit/test_growth.py
  - tests/integration/test_run_m1.py
  - scripts/viz_server.py
---

## Цель
Статус: M1 переопределён куратором — **динамическое расширение при обучении** вместо фиксированного N=16. Заменяет предыдущую интерпретацию «фиксированное масштабирование».

## Спека M1 (реализовано)
- `N: 4 → N_max: 32`, `grow_cooldown: 50` тиков (model_m1.yaml).
- Триггер нейрогенеза: вход `e_in`, `|M| == M_max`, `Novelty > theta_form` → новый узел специализируется на неудержанной новизне (`E_new = norm(e_in)`); X_new=0, S_new=канон, рёбра по bootstrap-статистике, seeded.
- `PaddedPredHead(N_max)`: голова канона работает при растущем N через padding; `head.sync(state)` перед тиком обязателен.
- Ring-buffer `X_hist` расширяется (прошлое нового узла = 0; delayed(0)=текущее).
- `pipeline.last_eps` падится при росте (salience matmul fix).
- Словарь прогона расширен до 24 слов — иначе новизна насыщается за 4 слова и рост не триггерится.

## Проверено
- Live-прогон 600 тиков: N 4→16, рёбер 10→141, `mem_fro` растёт 0.15→0.34, M=5 постоянно.
- 15/15 тестов (growth+m1+viz) зелёные, ruff чист.
- Полный V1-sweep M1 (24 комбо × 5000) идёт → REPORT_M1.md обновится по завершении.
- M1-визуализация :8093 показывает рост в реальном времени.

## Ответ получателя
- result: open (status)
- notes: моя зона — src/iski/m1, model_m1, run_m1; канон и chat не тронуты.
