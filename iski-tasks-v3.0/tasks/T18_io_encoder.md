# T18 — Envelope, InputBuffer, hash-encoder (M0)
DEPENDS: T01
FILES: src/iski/io/{envelope,buffer}.py, src/iski/encoders/hash_text.py, tests/unit/test_io.py
СОДЕРЖИМОЕ:
- @dataclass Envelope(payload,source_id,t_capture,t_encode,confidence,metadata)
- class InputBuffer: push(env); pop_ready(t)->list
- encode_text(text,D,seed): v=zeros(64); v[hash(ch)%64]+=1; e=v@R(seed); e/=||e||
МАТЕМАТИКА: phi_text: Raw->R^D; provenance сохраняется в Envelope (source_id, t_capture, confidence).
ТЕСТЫ: pop_ready пустого буфера -> []; encoder детерминирован; ||e||==1.
DoD: 3 теста зелёные.
NEXT: T19
