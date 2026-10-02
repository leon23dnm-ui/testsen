# T02 — Контракт дельт (single-writer)
DEPENDS: T01
FILES: src/iski/core/delta.py, tests/unit/test_delta.py
СОДЕРЖИМОЕ:
- CHANNELS = ("dX","dW_plus","dW_minus","dE","dQ_elig","dM","dG","dS","dTheta")
- class SingleWriterViolation(RuntimeError)
- @dataclass(frozen=True) class Delta: поля CHANNELS = None; is_empty(); merge(other)->Delta
МАТЕМАТИКА: каналы = компоненты Omega=(E,X,W+,W-,Q_elig,M,G,S,Theta); правило заморозки: один writer на канал.
ЛОГИКА merge: for ch in CHANNELS: a,b=getattr(...); if a is not None and b is not None: raise SingleWriterViolation(ch); иначе объединить; вернуть frozen Delta.
ЗАПРЕТЫ: мутабельность Delta; merge без проверки конфликта.
ТЕСТЫ: присваивание полю -> FrozenInstanceError; merge двух dX -> raise; merge dX+dE ok; Delta().is_empty()==True. Команда: `pytest tests/unit/test_delta.py -q`.
DoD: 4 теста зелёные.
NEXT: T03
