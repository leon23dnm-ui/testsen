# T15 — Clocks + сборка кандидата
DEPENDS: T02,T03
FILES: src/iski/runtime/{scheduler,candidate}.py, tests/unit/test_scheduler.py, tests/unit/test_candidate.py
СОДЕРЖИМОЕ:
- class Clocks(m,s,q): assert 1<=m<=s<=q; active(t,clock): fast=True; medium=t%m==0; structural=t%s==0; slow=t%q==0
- assemble(state,deltas)->cand: cand=state.clone_for_candidate(); for d: cand.apply_delta(d) (конфликт каналов всплывает из Delta.merge-семантики apply)
МАТЕМАТИКА: Omega^cand=Omega_t (+) Sum Delta всех активных часов; неактивные часы => пустые дельты.
ТЕСТЫ: Clocks(50,10,200)->AssertionError; active(50,"medium") при m=10 True; assemble двух непересекающихся дельт применяет обе; конфликт -> raise.
DoD: 4 теста зелёные.
NEXT: T16
