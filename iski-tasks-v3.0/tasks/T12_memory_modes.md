# T12 — F_mode: 5 уравнений жизненного цикла
DEPENDS: T11
FILES: src/iski/memory/modes.py, tests/unit/test_modes.py
СОДЕРЖИМОЕ: update_modes(rho[M,5],reuse,imp,surprise,pg,eta[9],dt,w_max)->rho'[M,5]:
d=clip(rho0*exp(-eta1*reuse)); a=clip(rho1+eta2*imp-eta3*(1-reuse)); c=clip(rho2+eta4*imp+eta5*pg);
f=clip(rho3+eta6*(1-reuse)-eta7*surprise); w=clip(rho4*exp(-rho0*dt)+eta8*reuse+eta9*imp,0,w_max)
МАТЕМАТИКА: замороженные 5 уравнений v3.0 (reuse up => decay down; surprise up => forget down).
ТЕСТЫ: reuse=1 vs 0 => d меньше; surprise=1 vs 0 => f меньше; w in [0,w_max]; все компоненты in [0,1] кроме w.
DoD: 4 теста зелёные.
NEXT: T13
