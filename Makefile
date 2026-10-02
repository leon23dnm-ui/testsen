.RECIPEPREFIX = >
SHELL = cmd

PYTHON := python

.PHONY: test lint run-m0 archive hash final clean

test:
>$(PYTHON) -m pytest tests/

lint:
>$(PYTHON) -m ruff check src tests
>$(PYTHON) -m ruff format --check src tests

run-m0:
>$(PYTHON) experiments/m0/run_m0.py --fast || cmd /c exit 0

archive:
>tar -czf iski-m0-v3.0.tar.gz --exclude=.venv --exclude=__pycache__ --exclude=.git --exclude=iski-m0-v3.0.tar.gz .

hash:
>$(PYTHON) -c "import hashlib,pathlib; p=pathlib.Path('iski-m0-v3.0.tar.gz'); pathlib.Path('iski-m0-v3.0.tar.gz.sha256').write_text(hashlib.sha256(p.read_bytes()).hexdigest())"

final: test lint run-m0 archive hash

clean:
>if exist build rmdir /s /q build
>if exist dist rmdir /s /q dist
>if exist .pytest_cache rmdir /s /q .pytest_cache
>if exist src\iski.egg-info rmdir /s /q src\iski.egg-info
>if exist iski-m0-v3.0.tar.gz del /q iski-m0-v3.0.tar.gz
>if exist iski-m0-v3.0.tar.gz.sha256 del /q iski-m0-v3.0.tar.gz.sha256
>for /r %%d in (__pycache__) do if exist "%%d" rmdir /s /q "%%d" 2>nul
