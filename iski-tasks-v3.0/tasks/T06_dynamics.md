# T06 — Распространение с задержками + уравнение поля + шум
DEPENDS: T03,T05
FILES: src/iski/dynamics/{propagation,update,noise}.py, tests/unit/test_{propagation,update,noise}.py
СОДЕРЖИМОЕ:
- propagate(graph,state,n,k): out=zeros; for d in unique(delays): m=delays==d; src,dst; out.index_add_(0,dst, w_eff[m][:,None]*state.delayed(d)[src])
- field_update(X,I_src,Lam,kappa,L,xi): X + Lam*(-X + tanh(I_src - kappa*(L@X))) + xi
- make_rng(seed); xi(rng,shape,xi_max)=(rand*2-1)*xi_max
МАТЕМАТИКА: x_i[n+1]=x_i[n]+(dt/tau)[-x_i+Phi(I_i+Sum_j W_ji^eff x_j[n-d_ji]-kappa L X)]+xi; Phi=tanh (M0).
ЛОГИКА: источники I_src складывает pipeline (T17): F_ext+F_mem+prop+(X_bc-X).
ТЕСТЫ: 2 узла/1 ребро d=1: сверка с ручным расчётом; I=0,W=0 => затухание; xi seeded и |xi|<=xi_max.
DoD: 3 файла тестов зелёные.
NEXT: T07
