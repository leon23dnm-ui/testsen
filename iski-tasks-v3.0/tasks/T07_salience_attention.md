# T07 — Salience + Attention (распределение по N)
DEPENDS: T01
FILES: src/iski/attention/{salience,attention}.py, tests/unit/test_salience.py, tests/unit/test_attention.py
СОДЕРЖИМОЕ:
- salience(nov,pe,lam_n,lam_e)=lam_n*nov+lam_e*pe   (M0: GR=Int=0)
- attention(sal,T_A)=softmax(sal/T_A, dim=0)
МАТЕМАТИКА: Sal_i=lambda_N Nov_i+lambda_E PE_i+lambda_G GR_i+lambda_I Int_i; Att_i=exp(Sal_i/T_A)/Sum_j exp(Sal_j/T_A); Sum Att=1; несколько фокусов = режим распределения.
ТЕСТЫ: sum(Att)==1 (rtol 1e-5); Sal_a>Sal_b => Att_a>Att_b.
DoD: 2 теста зелёные.
NEXT: T08
