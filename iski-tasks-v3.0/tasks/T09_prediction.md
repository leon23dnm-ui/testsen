# T09 — Enc_shared + Head_1 + ring B_h (delayed credit)
DEPENDS: T01
FILES: src/iski/prediction/{heads,buffer}.py, tests/unit/test_heads.py, tests/unit/test_buffer_h.py
СОДЕРЖИМОЕ:
- class PredHead(nn.Module): enc=Linear(NK,H); head=Linear(H,NK); encode(X)=tanh(enc(flatten)); predict(h); train_step(h_old,x_obs): SGD step по MSE(head(h_old),x_obs)
- class RingBufferH(cap): push(t,h); get(t)->h|None; eviction t-cap
МАТЕМАТИКА: h_t=Enc_shared(X_t); Xhat=P_sh(h)+R_1(h) (M0 R_1=0); eps=X_obs-Xhat; credit при tau<=tau_sync,max через B_h.
ТЕСТЫ: shapes encode/predict; buffer: get(t-cap-1)=None; train_step: loss монотонно падает на 20 повторах одной пары.
DoD: 3 теста зелёные.
NEXT: T10
