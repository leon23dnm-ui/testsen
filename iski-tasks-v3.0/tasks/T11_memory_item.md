# T11 — Элемент памяти + bounded store + F_mem
DEPENDS: T05
FILES: src/iski/memory/{item,store}.py, tests/unit/test_item.py, tests/unit/test_store.py
СОДЕРЖИМОЕ:
- @dataclass MemoryItem(e[D],x[K],rho[5],status=0,t_create=0,last_access=0); property w=rho[4]; clone()
- class MemoryStore(items,m_max): clone(); projection(E,sigma,k)=Sum_{status==0} w_k*K(E,e_k)[:,None]*x_k[None,:]
МАТЕМАТИКА: F_t^mem=Sum_k w_k K(E_t,e_k^mem) (x)_k^mem; |M|<=M_max; w===rho[4] (дубля запрещён).
ТЕСТЫ: empty store => F_mem==0; shape [N,K]; item.w is rho[4] value; clone независим.
DoD: 4 теста зелёные.
NEXT: T12
