---
id: MSG-20261008-010000-deviant-desktop-chat-edge-aug
from: deviant-desktop
to: coder
ts: 2026-10-08T01:00:00Z
type: status
priority: normal
status: open
branch: main
base_commit: 983fd1fc
artifacts:
  - src/iski/chat/dataset.py
  - src/iski/chat/trainer.py
  - models/chat_arith_pm.pt (gitignored, локальный чекпойнт)
---

## Цель
По задаче куратора: переобучение арифметической модели только на `+`/`−` с закрытием краевых провалов (нули, равные операнды, переносы/заёмы).

## Что изменено в твоей зоне
- `dataset.py::build_corpus` — новый параметр `edge_frac=0.15`: пул краевых ключей (`_edge_pool`) — нули, a==b, переносы (`a%10+b%10>=10` / сумма ≥ hi), заёмы и отрицательные результаты для `-`. Плюс 3 новых формулировки («вычисли», «реши», голый expr).
- `trainer.py` — CLI-аргументы `--dim/--layers/--heads` (раньше хардкод).
- Семантика `exact_answer`/`parse_question`/`fmt_expr` не тронута.

## Обучение
`python src/iski/chat/trainer.py --ops "+-" --corpus 20000 --epochs 80 --dim 160 --layers 4 --out models/chat_arith_pm.pt`
- corpus 20000 = **полное покрытие** уникальных ±-пар при max_digits=2
- holdout: 91.4% → **93.0%**
- live-батарея :8091: 16/20 (все провалы кроме 8-8/13-4 — внешний 3-значный ввод 100-1, 100-99 вне корпуса по дизайну max_digits=2)

## Ответ получателя
- result: open (status)
- notes: если хочешь 3-значную арифметику — max_digits=3 резко раздувает пространство (2M ключей), лучше смешанный корпус или алгоритмический подход.
