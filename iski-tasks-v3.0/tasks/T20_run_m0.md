# T20 — M0 falsification-прогон V1 + REPORT
DEPENDS: T17,T18,T19
FILES: experiments/m0/run_m0.py, experiments/m0/REPORT.template.md
СОДЕРЖИМОЕ: bootstrap(): E нормированные randn(seed boot); W sparse p0 (без петель); delays randint[0,Dmax); X=0; store empty.
run_combo(eta_plast,Lambda): warm 1000 тиков с envelopes(words) + maintenance каждые T_maint; warm_ok=mean(s_ed[-200:])>theta_ed_warm;
auto 4000 тиков e_in=None; критерии: activity_band, entropy_band, rho_stable, no_recovery, nontrivial(std>1e-3);
sweep по m0.yaml; первый passing combo => вердикт НАЙДЕН; иначе НЕ НАЙДЕН; REPORT.md (таблица combo x критерии + вердикт); exit 0/1.
МАТЕМАТИКА: V1: A_min<||X||<A_max; H_min<H<H_max; rho(J)<rho_max; E[s_ed]>theta_warm; нет collapse/runaway/паразитного аттрактора (std-критерий).
ЗАПРЕТЫ: подкрутка Theta вне sweep; правка математики при вердикте НЕ НАЙДЕН (только M0-issue).
ТЕСТЫ: прогон с уменьшенными ticks (флаг fast) завершается <60 c и пишет REPORT.md.
DoD: REPORT.md существует, exit-code соответствует вердикту.
NEXT: T21
