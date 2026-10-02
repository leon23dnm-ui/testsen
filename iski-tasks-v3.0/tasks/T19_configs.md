# T19 — Конфигурация: model/runtime/operators/bootstrap/m0
DEPENDS: T04
FILES: config/{model.yaml,runtime.yaml,operators.yaml,bootstrap.yaml}, config/experiments/m0.yaml, tests/unit/test_configs.py
СОДЕРЖИМОЕ (ключи): model: N=4,D=32,K=4,Dmax=8,Lambda,kappa,sigma,theta_gws,beta_g,T_A,xi_max,x_min/x_max,W_max,E_max,q_max,M_max,w_max,w_min,theta_forget,theta_I,T_archive,eta[9],eta_plast,lam_w,lam_elig,gate_thr,eta_E,theta_align,H_head,eta_head,tau1,lam_N,lam_E;
runtime: clocks{m:10,s:50,q:200}, seeds{boot:7,noise:11}, T_maint:500;
operators: реестр 8 записей (field_update,eligibility,plasticity,e_align,memory_lifecycle,head_train,structural_stub,diagnostics) с level/clock/reads/writes;
bootstrap: p0,warm_ticks:1000,auto_ticks:4000,A_min,A_max,H_min,H_max,rho_max,theta_ed_warm,K_no_rec,window;
m0: sweep{eta_plast:[...],Lambda:[...]}.
ЛОГИКА: test_configs: load_registry+validate_registry проходят; Clocks(m,s,q) из runtime не падает.
ТЕСТЫ: `pytest tests/unit/test_configs.py -q`.
DoD: конфиги валидны реестром и часами.
NEXT: T20
