# T08 — GWS broadcast: порог + мягкие веса (TopK ЗАПРЕЩЁН)
DEPENDS: T05,T07
FILES: src/iski/attention/gws.py, tests/unit/test_gws.py
СОДЕРЖИМОЕ: gws_broadcast(E,X,sal,theta,sigma,beta)->(X_bcast,S):
S=sal>theta; if none: return X,S; idx=nonzero(S); alpha=sal[idx]/sal[idx].sum();
B=sum_pos alpha[pos]*kernel_similarity(E,E[i],sigma)[:,None]*X[i][None,:]; return X+beta*B,S
МАТЕМАТИКА: B_t^GWS=Sum_{i in S} alpha_i K(E,e_i) (x)_i; X^bcast=X+beta_G B; S={i:Sal_i>theta_GWS}.
ЗАПРЕТЫ: torch.topk в этом модуле и вообще в динамике.
ТЕСТЫ: S пусто => X_bcast==X; sum(alpha)==1; ||X_bcast-X||<=beta*||B||+eps.
DoD: 3 теста зелёные.
NEXT: T09
