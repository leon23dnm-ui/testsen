# T05 — Ядра сходства + разреженный граф (COO)
DEPENDS: T03
FILES: src/iski/core/kernels.py, src/iski/graph/topology.py, tests/unit/test_kernels.py, tests/unit/test_topology.py
СОДЕРЖИМОЕ:
- kernel_similarity(E,e,sigma)=exp(-||E-e||^2/(2 sigma^2))  -> [N]
- @dataclass GraphCOO(edge_index[2,E], w_plus[E], w_minus[E], delays[E]int, q_elig[E]): w_eff()=w_plus-w_minus; clone(); dense_abs(n): A[dst,src]+=|w_eff|; laplacian(n)=diag(A.sum(1))-A
МАТЕМАТИКА: W^eff,(d)=W+(d)-W-(d); L=D_g-|W_eff| (диффузия -kappa L X).
ТЕСТЫ: K(e_i,e_i)=1; монотонное убывание с ||e_i-e||; w_eff знак; строки laplacian суммируются в 0.
DoD: 4 теста зелёные.
NEXT: T06
