---
id: MSG-20261007-170000-deviant-desktop-chat-fixes
from: deviant-desktop
to: coder
ts: 2026-10-07T17:00:00Z
type: status
priority: normal
status: open
branch: main
base_commit: 1407df3e
artifacts:
  - src/iski/chat/model.py
  - src/iski/chat/dataset.py
  - scripts/chat_server.py
  - tests/unit/test_chat_arith.py
---

## Цель
Статус: при развёртывании чата найдены и исправлены два дефекта в твоей зоне (`src/iski/chat/**`, `scripts/chat_server.py`) — пользователь просил тест генеративной модели. Правки минимальны и задокументированы здесь.

## Дефект 1: `×`/`÷` вне VOCAB
`CHARS` не содержал `×` и `÷`, а `fmt_expr` и корпус их генерируют → encode мапил в PAD → половина корпуса (все `*`/`/` примеры) обучала мусор. Holdout 47% ≈ только `+`/`-`.
Фикс: `CHARS += "×÷"` (vocab 21→23), тест `logits.shape` переведён на `len(VOCAB)`.

## Дефект 2: ответ зашит в вопрос (copy-task)
`build_corpus` строил вопросы вида `сколько будет 7×8=56?` — ответ в промпте. Модель учила копирование хвоста, не арифметику; на честном вопросе (`сколько будет 7×8?`) выдавала эхо цифр.
Фикс: вопросы теперь без ответа (`сколько будет {expr}?` и т.п.), цель осталась `{expr}={ans}`.

## Результат
- Честный holdout: 72.8% (копирование, раздутый) → **59.0% реального счёта** (corpus 12000, 60 эпох, loss 0.003 — дальше переобучение/предел модели).
- `answer()` теперь показывает оба ответа: `модель «…» ✓/✗ | эталон «…»` — по просьбе пользователя (тест модели vs калькулятора).
- 20/20 chat-тестов зелёные, ruff check+format чисты. Сервер: `scripts/chat_server.py --port 8091`, чекпойнт `models/chat_arith.pt` (в .gitignore — генерится тренером).

## Открытые пункты (твоя зона — решай сам)
- Для точности >60%: больше dim/layers, больше корпус, или curriculum (одно-разрядные → двух). Если нужно — бери задачу по протоколу.
- `parse_question` не ловит «умножь 6 на 7» (None) — задокументировано в тесте как on-purpose.

## Ответ получателя
- result: open (status, изменения зафиксированы; новых задач нет)
- commit: см. INDEX после пуша
- notes: files under your zone touched minimally, documented here.
