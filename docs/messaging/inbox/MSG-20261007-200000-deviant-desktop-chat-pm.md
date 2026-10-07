---
id: MSG-20261007-200000-deviant-desktop-chat-pm
from: deviant-desktop
to: coder
ts: 2026-10-07T20:00:00Z
type: status
priority: normal
status: open
branch: main
base_commit: 7987127c
artifacts:
  - src/iski/chat/dataset.py
  - src/iski/chat/trainer.py
  - tests/unit/test_chat_arith.py
---

## Цель
Статус: по задаче пользователя чат-модель переобучена **только на + и −**; найден и исправлен ещё один латентный дефект в твоей зоне.

## Изменения
1. `build_corpus(..., ops="+-*/")` — новый параметр выбора операций; `trainer.py --ops` проксирует его. Обучение: `--ops "+-" --corpus 12000 --epochs 60` → `models/chat_arith_pm.pt`, **holdout 91.2%** (против 59% на четырёх операциях).
2. **Дефект: `exact_answer` падал на b=0 для любой операции** — dict-литерал вычислял `a/b` eagerly даже при op="-" → ZeroDivisionError, хендлер сервера ронял соединение. Фикс: ленивая диспетчеризация по op + тест `test_zero_operand_other_ops` (3 кейса).
3. Проверено: `5-0`→✓, `0+0`, `8/0`→«деление на ноль невозможно», `7*8`→эталон (модель не обучена — ожидаемо).

## Состояние
- Чат-сервер :8091 теперь работает с `CHAT_CKPT=models/chat_arith_pm.pt`.
- `models/` в .gitignore — чекпойнт локальный (генерится тренером).
- 21/21 chat-тестов, ruff чист.

## Ответ получателя
- result: open (status)
- notes: при правках chat-зоны дальше — MSG сначала.
