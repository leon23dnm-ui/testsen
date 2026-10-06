# Project Facts — iski

Этот файл содержит ТОЛЬКО проектные факты для репозитория.
Workflow (Dialog Coding Cycle), политики Council/Router/Expert/лимиты агентов живут в глобальной установке Devin и НЕ дублируются здесь.

Глобальный workflow запускается skill-ом `/dialog-coding-cycle` (или агент вызывает его сам для задач разработки). Проектные факты из этого файла автоматически попадают в контекст workflow, так как AGENTS.md репозитория — always-on.

## Build
- `pip install -e ".[dev]"`
- `make test`
- `make lint`

## Test
- `make test` — запуск `pytest tests/`
- `make lint` — запуск `ruff check .` и `ruff format --check .`
- `make run-m0` — запуск эксперимента M0 (T20/T21)
- `make clean` — очистка артефактов

## Local architecture
- Пакет `iski` располагается в `src/iski/`.
- Подмодули скелета: `core`, `graph`, `dynamics`, `attention`, `prediction`, `learning`, `memory`, `safety`, `runtime`, `io`.
- Тесты: `tests/unit/`, `tests/integration/`.
- Эксперименты: `experiments/m0/{plots,logs}`.
- Документация и issues: `docs/`.
- Стек: Python 3.13+, torch>=2.0, numpy, pyyaml, matplotlib.

## Local conventions
- Код оформляется по стилю ruff с длиной строки по умолчанию.
- Массовые правки файлов тестов/конфигов — только exact-match заменами с pre/post diff; при любом повреждении — немедленный restore из HEAD и перевнесение правок точными edits; regex-булк по тестам запрещён (инцидент T27).
- Git CLI не установлен; git-операции — через dulwich в `.venv` (`.venv\Scripts\python.exe -c "from dulwich import porcelain; ..."`). Remote: `git@github.com:INKkripto/semantic.git`, ветка `main`.
- `make` лежит в `.tools\make\bin\make.exe`; для `make test/lint` нужен `.venv\Scripts` в PATH.
- Каждая сессия решает ровно одно задание из `iski-tasks-v3.0/tasks/T01..T21`.
- Отчёт сессии включает: изменённые файлы, вывод `make test`/`make lint`, отклонения, строку в `CHECKLIST.md`, план следующего задания.

## Deploy
- Промежуточной деплой не предусмотрен; финальный артефакт — `iski-m0-v3.0.tar.gz`/`zip` + `REPORT.md` + заполненный `CHECKLIST.md`.

## Project constraints
- `iski-tasks-v3.0/RULES.md`, `README.md` и файлы задач — FROZEN, не изменяются.
- Не создавать классы когнитивных сущностей (Neuron, MemoryNode и т.п.).
- Модули возвращают только Delta; запись в Omega только в commit.
- Весь рандом seeded: seed => идентичная траектория.
- `torch.topk` в динамике запрещён; GWS = порог Sal + мягкие alpha.
- Подкрутка параметров вне диапазонов заданий запрещена.

## Запуск workflow
1. Убедиться, что глобальная установка Dialog Coding Cycle v1.7 на месте (skill `/dialog-coding-cycle` доступен).
2. Написать задачу в сессии Devin (режим Agent → Code).
3. При необходимости явно вызвать `/dialog-coding-cycle`.
4. Workflow использует факты из этого файла + глобальные политики.
