# T14 — Hard-инварианты: check + project
DEPENDS: T03
FILES: src/iski/safety/invariants.py, tests/unit/test_invariants.py
СОДЕРЖИМОЕ:
- check(st,cfg)->[violations]: x_min/x_max; W_max для w_plus/w_minus; ||e_i||<=E_max; |M|<=M_max
- project(st,cfg): clamp X; clamp w_plus/w_minus в [0,W_max]; нормировка строк E при norm>E_max; clamp q_elig в [-q_max,q_max]
МАТЕМАТИКА: инварианты v3.0 (bounds); project вызывается ДО commit, после diagnostics.
ТЕСТЫ: выброс X за границу => после project check пуст; E-нормы <= E_max.
DoD: 2 теста зелёные.
NEXT: T15
