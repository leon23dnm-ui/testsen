# T16 — Метрики: activity, H(X), s_ed, rho(J); Metrics_cache
DEPENDS: T03,T05
FILES: src/iski/runtime/diagnostics.py, tests/unit/test_diagnostics.py
СОДЕРЖИМОЕ: compute_metrics(st,eps,e_in,cfg)->dict:
activity=mean|X|; p=|X|.flatten()/sum; H=-sum(p log p) по p>0;
rn=||X||_row; alpha=rn/sum; ebar=alpha@E; s_ed=cos(ebar,e_in) if e_in else nan;
A=dense_abs; J=diag(1-Lambda)+Lambda*A; rho_j=max row-sum |J|; eps_norm
МАТЕМАТИКА: H(X)=-Sum p log p; ebar=Sum alpha_i e_i (readout цели/семантики); rho(J_F)<rho_max — устойчивость; s_ed>theta_warm в warm-up.
ТЕСТЫ: H in [0, log(N*K)]; e_in==ebar => s_ed==1; rho_j>=1-Lambda.
DoD: 3 теста зелёные.
NEXT: T17
