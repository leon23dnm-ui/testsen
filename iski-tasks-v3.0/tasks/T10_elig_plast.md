# T10 — Eligibility (fast) + пластичность (medium)
DEPENDS: T02,T03,T05
FILES: src/iski/learning/{eligibility,plasticity}.py, tests/unit/test_eligibility.py, tests/unit/test_plasticity.py
СОДЕРЖИМОЕ:
- update_eligibility(graph,state,lam,gate_thr,qmax)->q_new: a=X.mean(-1); a_mean; per edge: a_src=state.delayed(d).mean(-1)[src]; psi=(a_dst-a_mean)*(a_src-a_mean); gate=|a_dst*a_src|>gate_thr; q=clip((1-lam)*q+gate*psi, -qmax, qmax)
- plasticity_delta(graph,eps,eta,lam_w)->Delta: eps_node=eps.mean(-1); dw=eta*q_elig*eps_node[dst]; dW_plus=relu(dw)-lam_w*w_plus; dW_minus=relu(-dw)-lam_w*w_minus
МАТЕМАТИКА: Q'=clip((1-lam)Q+gate*psi); psi=(x_i-xbar)(x_j-xbar); диапазон [-Q_max,Q_max]; DeltaW_plast=F_plast(Q_{t+1},eps_{t+1},nu,C) (M0 nu=const).
ЗАПРЕТЫ: чтение Q_elig модулями L1/attention.
ТЕСТЫ: коактивация => |q| растёт; покой => затухание к 0; dw>0 => только dW_plus; eps=0 => дельты только decay.
DoD: 4 теста зелёные.
NEXT: T11
