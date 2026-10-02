# T01 — Окружение и скелет пакета
DEPENDS: нет
FILES: pyproject.toml, Makefile, conftest.py, README.md, src/iski/**/__init__.py (core,graph,dynamics,attention,prediction,learning,memory,safety,runtime,io), tests/unit/, tests/integration/, experiments/m0/{plots,logs}, docs/
СОДЕРЖИМОЕ:
- pyproject: package iski, deps torch>=2.0,numpy,pyyaml,matplotlib; extras dev: pytest,ruff; packages.find where=["src"].
- Makefile (.RECIPEPREFIX = >): test / lint / run-m0 / clean.
- conftest.py: sys.path.insert(0, src).
ЛОГИКА: python3 -m venv .venv; pip install -e ".[dev]"; пустой pytest-набор зелёный.
ЗАПРЕТЫ: любой код модулей до T02..T18.
ТЕСТЫ: `make test` exit 0; `python -c "import iski"` без ошибок.
DoD: скелет импортируется, make-цели работают.
NEXT: T02
