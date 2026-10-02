# T04 — Snapshot (параллельные Gamma) + реестр операторов
DEPENDS: T03
FILES: src/iski/core/snapshots.py, src/iski/core/operators.py, tests/unit/test_snapshots.py, tests/unit/test_operators.py
СОДЕРЖИМОЕ:
- export_snapshot(state, metrics_cache)->dict{"X","E","W_eff","S","metrics_cache","frozen":True} (clone-проекции из ОДНОГО state, параллельно)
- load_registry(path)->list; validate_registry(specs): clock in {fast,medium,structural,slow}; level in 0..3; каналы in ALLOWED; writer канала уникален (иначе AssertionError)
МАТЕМАТИКА: Gamma_t^{k->l}=Proj_{ReadSet(k,l)}(Omega_t); все Gamma из одного Omega_t, без цепочек.
ЛОГИКА: pipeline (T17) вызывает export_snapshot первой фазой; после фазы 0 запись в Gamma запрещена (флаг frozen).
ТЕСТЫ: мутация state.X после экспорта не меняет Gamma["X"]; дубль writer в yaml-спеке -> AssertionError; clock="weekly" -> AssertionError.
DoD: 3 теста зелёные.
NEXT: T05
