# T03 — Состояние Omega + ring-buffer задержек
DEPENDS: T02
FILES: src/iski/core/state.py, tests/unit/test_state.py
СОДЕРЖИМОЕ: class OmegaState(cfg,E,X,graph,S,store,tick=0):
- поля + X_hist=zeros(Dmax+1,N,K), ptr=0
- delayed(d)->X_hist[(ptr-d)%(Dmax+1)]
- advance_ring(): ptr=(ptr+1)%L; X_hist[ptr]=X.clone()
- clone_for_candidate()->OmegaState (клон тензоров, графа, store)
- apply_delta(d): dX/dE/dS += ; dW_plus/dW_minus += ; dQ_elig := ; dM ops: ("add",item)|("rho",i,rho)|("status",i,st,t)|("del",i)
МАТЕМАТИКА: x_j[t-d_ji] читается из ring: idx=(ptr-d) mod (Dmax+1).
ЛОГИКА: apply_delta применяется ТОЛЬКО из candidate/commit/maintenance (вызывающие — позже).
ЗАПРЕТЫ: чтение X_hist вне delayed(); мутация X_hist напрямую.
ТЕСТЫ: clone независим; delayed(0)==текущий X после advance; apply_delta dX суммирует; dM ("add") увеличивает store. `pytest tests/unit/test_state.py -q`.
DoD: 4 теста зелёные.
NEXT: T04
