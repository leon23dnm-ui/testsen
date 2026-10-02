# T17 — Pipeline 22 шага + single-writer commit + maintenance
DEPENDS: T02..T16
FILES: src/iski/runtime/pipeline.py, tests/integration/test_{pipeline_order,tick_determinism,cache_usage}.py
СОДЕРЖИМОЕ: class Pipeline(state,clocks,cfg,head,hbuf,rng): metrics_cache,last_eps,last_e_in,log; tick(e_in,conf)->out; _memory_lifecycle(t,sal,eps)->Delta(dM); maintenance()
ЛОГИКА tick (порядок ЗАМОРОЖЕН, комментарии-номера обязательны):
01 snapshot=export_snapshot; 02 F_ext=conf*K(E,e_in)[:,None]*ones(K) или zeros; last_e_in=e_in;
03 nov=1-K(E,last_e_in); pe=|last_eps|.mean(-1); sal; att=softmax; 04 X_bc,S=gws_broadcast;
05 F_mem=store.projection; 06 h=head.encode; hbuf.push(t,h); xhat=head.predict(h);
07 prop=propagate; 08 L=laplacian; I_src=F_ext+F_mem+prop+(X_bc-X); xi; X_next=field_update; dX=X_next-X;
09 eps=X_next-xhat; last_eps=eps; head.train_step(hbuf.get(t-tau1),X_next);
10 dQ=update_eligibility (fast); deltas=[Delta(dX),Delta(dQ_elig=dQ)];
11 if medium: += plasticity_delta; if e_in: dE=e_align (mask K>theta_align, eta_E*(e_in-E)); += _memory_lifecycle;
12 if structural and metrics_cache is not None: pass (M0 stub, читает cache_{t-1});
14 cand=assemble; 15 metrics=compute_metrics; viol=check; 16 project(cand); 17 recovery-log;
18 self.state=cand (single writer); 19 state.advance_ring(); 20 out={ebar,metrics,viol,att,gws};
21 metrics_cache=metrics; log.append((t,metrics,len(viol))); tick+=1
maintenance(): idx=archive_sweep; apply_delta(Delta(dM=[("del",i)...])) — ВНЕ tick.
_memory_lifecycle: active items => reuse=exp(-(t-last_access)/50); imp,surprise через K(E,e_item) с X.mean(-1) и |eps|.mean(-1); pg=0; update_modes => ops ("rho",i,rho); if slow: forget_decision => ops ("status",i,1,t).
ЗАПРЕТЫ: изменение порядка шагов; запись в Omega вне шага 18; TopK; maintenance внутри tick.
ТЕСТЫ: order-log совпадает со списком 01..21; два прогона с одним seed => идентичные X (allclose); на t%s==0 structural видит metrics_cache предыдущего тика (assert не None после первого structural); e_in=None => F_ext==0 (траектория не зависит от payload).
DoD: 3 integration-теста зелёные.
NEXT: T18
