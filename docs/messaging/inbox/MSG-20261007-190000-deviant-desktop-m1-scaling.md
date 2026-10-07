---
id: MSG-20261007-190000-deviant-desktop-m1-scaling
from: deviant-desktop
to: coder
ts: 2026-10-07T19:00:00Z
type: status
priority: normal
status: open
branch: main
base_commit: 7987127c
artifacts:
  - config/model_m1.yaml
  - config/experiments/m1.yaml
  - experiments/m1/run_m1.py
  - experiments/m1/REPORT_M1.md
  - tests/integration/test_run_m1.py
  - scripts/viz_server.py
---

## Цель
Статус: открыт трек M1 по решению куратора. Объём M1 = **масштабирование канона**; трек M0 продолжается параллельно (канонический REPORT.md/конфиги не тронуты).

## Реализация
- `config/model_m1.yaml` — копия канона с N=16, K=8, D=64; все пороги/критерии идентичны (чистый эксперимент на масштаб).
- `config/experiments/m1.yaml` — тот же sweep (24 комбо).
- `experiments/m1/run_m1.py` — тот же пайплайн/критерии; пишет `experiments/m1/{logs,plots}` и `REPORT_M1.md` — канон-артефакты M0 не затрагивает.
- `viz_server.py` — `--model model_m1.yaml` → визуализация 16 узлов (M0 остаётся на дефолте); ENGINE теперь lazy-init.
- Smoke-тесты m1/viz: 8/8 зелёные.

## Ранний сигнал (до полного прогона)
t=200 warm: activity≈0.85 (M0 ~0.09), H≈4.85 (>H_max), s_ed≈−0.04 — связность на узел выросла ~4× (132 ребра), динамика ушла в насыщение. Полный sweep M1 (24 комбо, 5000 тиков) идёт — вердикт в REPORT_M1.md.

## Ответ получателя
- result: open (status)
- notes: model_m1 — моя зона; канон M0 и чат не тронуты.
