#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_tasks_archive.py — сборщик архива iski-tasks-v3.0:
файлы-задания (work orders) для Devin Desktop, M0 ядра ISKI (БДКС/LDCS), SPEC v3.0 FROZEN.

Использование:
    python3 build_tasks_archive.py          # создать каталог iski-tasks-v3.0/
    python3 build_tasks_archive.py --zip    # дополнительно упаковать iski-tasks-v3.0.zip
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

ROOT = Path("iski-tasks-v3.0")
FILES: dict[str, str] = {}

# ─────────────────────────── корень архива ───────────────────────────
FILES["README.md"] = r"""
# Архив заданий Devin Desktop — M0 ядра ISKI (БДКС / LDCS), SPEC v3.0 FROZEN
Регламент:
1. Порядок строгий: T01 → T21. Одно задание = одна сессия Devin.
2. В начале сессии в Devin подаётся ТОЛЬКО текст файла задания + RULES.md.
3. Гейт между заданиями: `make test && make lint` зелёные. Не зелёные — правки в той же сессии.
4. Любое расхождение с математикой задания = дефект кода. Несоответствие SPEC → docs/ISSUE.template.md (M0-issue), математику НЕ менять.
5. Отчёт сессии: diff-сводка, вывод make test/lint, что добавлено в CHECKLIST.md, открытые issues, план следующего задания.
6. Финал (T21): iski-m0-v3.0.tar.gz (или .zip) + REPORT.md + заполненный CHECKLIST.md.
Шаблон задания: DEPENDS / FILES / СОДЕРЖИМОЕ (сигнатуры) / МАТЕМАТИКА / ЛОГИКА / ЗАПРЕТЫ / ТЕСТЫ / DoD / NEXT.
"""

FILES["RULES.md"] = r"""
# RULES (FROZEN v3.0) — нарушать запрещено
1. ONE SPACE E=R^D; ONE FIELD X in R^{N x K}; ONE ADAPTIVE GRAPH (W+/W-, задержки d).
2. Pipeline 22 шага, порядок заморожен (см. T17). Commit единственный (single writer), ring shift ПОСЛЕ commit.
3. Модули возвращают только Delta; каналы: dX,dW_plus,dW_minus,dE,dQ_elig,dM,dG,dS,dTheta; конфликт канала = SingleWriterViolation.
4. Snapshot: параллельные проекции Gamma из ОДНОГО Omega_t; запись в Gamma после фазы 0 запрещена.
5. GWS: порог Sal>theta + мягкие alpha. TopK в динамике ЗАПРЕЩЁН (только readout-метрики k_mass/k_eff).
6. Q_elig не читается L1; Attr не в fast critical path; slow-дельты ТОЛЬКО до candidate/commit.
7. F_forget -> {Keep, Archive}; Active -> PhysicalDelete запрещён; F_archive async вне тика.
8. Clocks: 1<=m<=s<=q; medium/structural/slow гейтятся по t%m/t%s/t%q; на неактивных тиках дельты пусты.
9. Весь рандом seeded (bootstrap, xi, encoder). Детерминизм: seed => идентичная траектория.
10. Запрещённые имена классов: Neuron, MemoryNode, ThoughtNode, EmotionNode, ConceptNode и любые когнитивные сущности.
11. Термины: элемент/поле/граф; тик; адаптация; readout. Не: нейрон/слой/инференс/обучение/генерация.
12. M0 — falsification-тест V1, не демо. Подкрутка Theta вне sweep-диапазонов запрещена.
"""

FILES["CHECKLIST.md"] = r"""
# CHECKLIST (заполняет исполнитель после каждого задания)
| T | Задание | Тесты зелёные | Внесено в operators.yaml | Issues |
|---|---------|---------------|--------------------------|--------|
| 01..21 | ... | [ ] | [ ] | ... |
"""

FILES["docs/ISSUE.template.md"] = r"""
# M0-issue NN
Где найдено (задание/тест): ...
Симптом (лог/график): ...
Гипотеза причины: реализация | параметры | спецификация
Предложение (НЕ меняет математику без решения куратора): ...
"""

# ─────────────────────────── задания T01–T21 ───────────────────────────
FILES["tasks/T01_env_skeleton.md"] = r"""
# T01 — Окружение и скелет пакета
DEPENDS: нет
FILES: pyproject.toml, Makefile, conftest.py, README.md, src/iski/**/__init__.py (core,graph,dynamics,attention,prediction,learning,memory,safety,runtime,io), tests/unit/, tests/integration/, experiments/m0/{plots,logs}, docs/
СОДЕРЖИМОЕ:
- pyproject: package iski, deps torch>=2.0,numpy,pyyaml,matplotlib; extras dev: pytest,ruff; packages.find where=["src"].
- Makefile (.RECIPEPREFIX = >): test / lint / run-m0 / clean.
- conftest.py: sys.path.insert(0, src).
ЛОГИКА: python3 -m venv .venv; pip install -e ".[dev]"; пустой pytest-набор зелёный.
ЗАПРЕТЫ: любой код модулей до T02..T18.
ТЕСТЫ: `make test` exit 0; `python -c "import iski"` без ошибок.
DoD: скелет импортируется, make-цели работают.
NEXT: T02
"""

FILES["tasks/T02_delta.md"] = r"""
# T02 — Контракт дельт (single-writer)
DEPENDS: T01
FILES: src/iski/core/delta.py, tests/unit/test_delta.py
СОДЕРЖИМОЕ:
- CHANNELS = ("dX","dW_plus","dW_minus","dE","dQ_elig","dM","dG","dS","dTheta")
- class SingleWriterViolation(RuntimeError)
- @dataclass(frozen=True) class Delta: поля CHANNELS = None; is_empty(); merge(other)->Delta
МАТЕМАТИКА: каналы = компоненты Omega=(E,X,W+,W-,Q_elig,M,G,S,Theta); правило заморозки: один writer на канал.
ЛОГИКА merge: for ch in CHANNELS: a,b=getattr(...); if a is not None and b is not None: raise SingleWriterViolation(ch); иначе объединить; вернуть frozen Delta.
ЗАПРЕТЫ: мутабельность Delta; merge без проверки конфликта.
ТЕСТЫ: присваивание полю -> FrozenInstanceError; merge двух dX -> raise; merge dX+dE ok; Delta().is_empty()==True. Команда: `pytest tests/unit/test_delta.py -q`.
DoD: 4 теста зелёные.
NEXT: T03
"""

FILES["tasks/T03_state_ring.md"] = r"""
# T03 — Состояние Omega + ring-buffer задержек
DEPENDS: T02
FILES: src/iski/core/state.py, tests/unit/test_state.py
СОДЕРЖИМОЕ: class OmegaState(cfg,E,X,graph,S,store,tick=0):
- поля + X_hist=zeros(Dmax+1,N,K), ptr=0
- delayed(d)->X_hist[(ptr-d)%(Dmax+1)]
- advance_ring(): ptr=(ptr+1)%L; X_hist[ptr]=X.clone()
- clone_for_candidate()->OmegaState (клон тензоров, графа, store)
- apply_delta(d): dX/dE/dS += ; dW_plus/dW_minus += ; dQ_elig := ; dM ops: ("add",item)|("rho",i,rho)|("status",i,st,t)|("del",i)
МАТЕМАТИКА: x_j[t-d_ji] читается из ring: idx=(ptr-d) mod (Dmax+1).
ЛОГИКА: apply_delta применяется ТОЛЬКО из candidate/commit/maintenance (вызывающие — позже).
ЗАПРЕТЫ: чтение X_hist вне delayed(); мутация X_hist напрямую.
ТЕСТЫ: clone независим; delayed(0)==текущий X после advance; apply_delta dX суммирует; dM ("add") увеличивает store. `pytest tests/unit/test_state.py -q`.
DoD: 4 теста зелёные.
NEXT: T04
"""

FILES["tasks/T04_snapshot_registry.md"] = r"""
# T04 — Snapshot (параллельные Gamma) + реестр операторов
DEPENDS: T03
FILES: src/iski/core/snapshots.py, src/iski/core/operators.py, tests/unit/test_snapshots.py, tests/unit/test_operators.py
СОДЕРЖИМОЕ:
- export_snapshot(state, metrics_cache)->dict{"X","E","W_eff","S","metrics_cache","frozen":True} (clone-проекции из ОДНОГО state, параллельно)
- load_registry(path)->list; validate_registry(specs): clock in {fast,medium,structural,slow}; level in 0..3; каналы in ALLOWED; writer канала уникален (иначе AssertionError)
МАТЕМАТИКА: Gamma_t^{k->l}=Proj_{ReadSet(k,l)}(Omega_t); все Gamma из одного Omega_t, без цепочек.
ЛОГИКА: pipeline (T17) вызывает export_snapshot первой фазой; после фазы 0 запись в Gamma запрещена (флаг frozen).
ТЕСТЫ: мутация state.X после экспорта не меняет Gamma["X"]; дубль writer в yaml-спеке -> AssertionError; clock="weekly" -> AssertionError.
DoD: 3 теста зелёные.
NEXT: T05
"""

FILES["tasks/T05_kernels_topology.md"] = r"""
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
"""

FILES["tasks/T06_dynamics.md"] = r"""
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
"""

FILES["tasks/T07_salience_attention.md"] = r"""
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
"""

FILES["tasks/T08_gws.md"] = r"""
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
"""

FILES["tasks/T09_prediction.md"] = r"""
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
"""

FILES["tasks/T10_elig_plast.md"] = r"""
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
"""

FILES["tasks/T11_memory_item.md"] = r"""
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
"""

FILES["tasks/T12_memory_modes.md"] = r"""
# T12 — F_mode: 5 уравнений жизненного цикла
DEPENDS: T11
FILES: src/iski/memory/modes.py, tests/unit/test_modes.py
СОДЕРЖИМОЕ: update_modes(rho[M,5],reuse,imp,surprise,pg,eta[9],dt,w_max)->rho'[M,5]:
d=clip(rho0*exp(-eta1*reuse)); a=clip(rho1+eta2*imp-eta3*(1-reuse)); c=clip(rho2+eta4*imp+eta5*pg);
f=clip(rho3+eta6*(1-reuse)-eta7*surprise); w=clip(rho4*exp(-rho0*dt)+eta8*reuse+eta9*imp,0,w_max)
МАТЕМАТИКА: замороженные 5 уравнений v3.0 (reuse up => decay down; surprise up => forget down).
ТЕСТЫ: reuse=1 vs 0 => d меньше; surprise=1 vs 0 => f меньше; w in [0,w_max]; все компоненты in [0,1] кроме w.
DoD: 4 теста зелёные.
NEXT: T13
"""

FILES["tasks/T13_forget_maint.md"] = r"""
# T13 — F_forget {Keep,Archive} + F_archive (async)
DEPENDS: T11
FILES: src/iski/memory/{forgetting,maintenance}.py, tests/unit/test_forgetting.py, tests/unit/test_maintenance.py
СОДЕРЖИМОЕ:
- forget_decision(w,forget_rho,imp,w_min,th_forget,th_I)->"archive"|"keep": archive если (w<w_min and imp<th_I) или (w<w_min and forget_rho>th_forget)
- archive_sweep(items,tick,T_archive)->[i]: status==1 and (tick-last_access)>T_archive
МАТЕМАТИКА: lifecycle Active->Archive->PhysicalDelete; прямой Active->PhysicalDelete запрещён.
ТЕСТЫ: таблица решений (4 кейса); sweep удаляет только status==1 и старые; активный элемент никогда не в списке.
DoD: 2 теста зелёные.
NEXT: T14
"""

FILES["tasks/T14_safety.md"] = r"""
# T14 — Hard-инварианты: check + project
DEPENDS: T03
FILES: src/iski/safety/invariants.py, tests/unit/test_invariants.py
СОДЕРЖИМОЕ:
- check(st,cfg)->[violations]: x_min/x_max; W_max для w_plus/w_minus; ||e_i||<=E_max; |M|<=M_max
- project(st,cfg): clamp X; clamp w_plus/w_minus в [0,W_max]; нормировка строк E при norm>E_max; clamp q_elig в [-q_max,q_max]
МАТЕМАТИКА: инварианты v3.0 (bounds); project вызывается ДО commit, после diagnostics.
ТЕСТЫ: выброс X за границу => после project check пуст; E-нормы <= E_max.
DoD: 2 теста зелёные.
NEXT: T15
"""

FILES["tasks/T15_scheduler_candidate.md"] = r"""
# T15 — Clocks + сборка кандидата
DEPENDS: T02,T03
FILES: src/iski/runtime/{scheduler,candidate}.py, tests/unit/test_scheduler.py, tests/unit/test_candidate.py
СОДЕРЖИМОЕ:
- class Clocks(m,s,q): assert 1<=m<=s<=q; active(t,clock): fast=True; medium=t%m==0; structural=t%s==0; slow=t%q==0
- assemble(state,deltas)->cand: cand=state.clone_for_candidate(); for d: cand.apply_delta(d) (конфликт каналов всплывает из Delta.merge-семантики apply)
МАТЕМАТИКА: Omega^cand=Omega_t (+) Sum Delta всех активных часов; неактивные часы => пустые дельты.
ТЕСТЫ: Clocks(50,10,200)->AssertionError; active(50,"medium") при m=10 True; assemble двух непересекающихся дельт применяет обе; конфликт -> raise.
DoD: 4 теста зелёные.
NEXT: T16
"""

FILES["tasks/T16_diagnostics.md"] = r"""
# T16 — Метрики: activity, H(X), s_ed, rho(J); Metrics_cache
DEPENDS: T03,T05
FILES: src/iski/runtime/diagnostics.py, tests/unit/test_diagnostics.py
СОДЕРЖИМОЕ: compute_metrics(st,eps,e_in,cfg)->dict:
activity=mean|X|; p=|X|.flatten()/sum; H=-sum(p log p) по p>0;
rn=||X||_row; alpha=rn/sum; ebar=alpha@E; s_ed=cos(ebar,e_in) if e_in else nan;
A=dense_abs; J=diag(1-Lambda)+Lambda*A; rho_j=max row-sum |J|; eps_norm
МАТЕМАТИКА: H(X)=-Sum p log p; ebar=Sum alpha_i e_i (readout цели/семантики); rho(J_F)<rho_max — устойчивость; s_ed>theta_warm в warm-up.
ТЕСТЫ: H in [0, log(N*K)]; e_in==ebar => s_ed==1; rho_j>=1-Lambda.
DoD: 3 теста зелёные.
NEXT: T17
"""

FILES["tasks/T17_pipeline.md"] = r"""
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
"""

FILES["tasks/T18_io_encoder.md"] = r"""
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
"""

FILES["tasks/T19_configs.md"] = r"""
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
"""

FILES["tasks/T20_run_m0.md"] = r"""
# T20 — M0 falsification-прогон V1 + REPORT
DEPENDS: T17,T18,T19
FILES: experiments/m0/run_m0.py, experiments/m0/REPORT.template.md
СОДЕРЖИМОЕ: bootstrap(): E нормированные randn(seed boot); W sparse p0 (без петель); delays randint[0,Dmax); X=0; store empty.
run_combo(eta_plast,Lambda): warm 1000 тиков с envelopes(words) + maintenance каждые T_maint; warm_ok=mean(s_ed[-200:])>theta_ed_warm;
auto 4000 тиков e_in=None; критерии: activity_band, entropy_band, rho_stable, no_recovery, nontrivial(std>1e-3);
sweep по m0.yaml; первый passing combo => вердикт НАЙДЕН; иначе НЕ НАЙДЕН; REPORT.md (таблица combo x критерии + вердикт); exit 0/1.
МАТЕМАТИКА: V1: A_min<||X||<A_max; H_min<H<H_max; rho(J)<rho_max; E[s_ed]>theta_warm; нет collapse/runaway/паразитного аттрактора (std-критерий).
ЗАПРЕТЫ: подкрутка Theta вне sweep; правка математики при вердикте НЕ НАЙДЕН (только M0-issue).
ТЕСТЫ: прогон с уменьшенными ticks (флаг fast) завершается <60 c и пишет REPORT.md.
DoD: REPORT.md существует, exit-code соответствует вердикту.
NEXT: T21
"""

FILES["tasks/T21_final_gate.md"] = r"""
# T21 — Финальный гейт и упаковка архива
DEPENDS: T01..T20
FILES: CHECKLIST.md (заполненный), iski-m0-v3.0.tar.gz или .zip, sha256
ЛОГИКА: make test; make lint; make run-m0; собрать plots; заполнить CHECKLIST по всем T;
упаковка (tar или zipfile) без venv/pycache; sha256sum.
DoD: все строки CHECKLIST зелёные либо имеют M0-issue; архив и хеш существуют; отчёт куратору: вердикт V1, список issues, план M1.
NEXT: — (конец)
"""


# ─────────────────────────── сборка ───────────────────────────
def build() -> int:
    for rel, content in FILES.items():
        path = ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.lstrip("\n"), encoding="utf-8")
    return len(FILES)


def zip_archive() -> Path:
    zip_path = Path("iski-tasks-v3.0.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(ROOT.rglob("*")):
            if path.is_file():
                zf.write(path, path.as_posix())
    return zip_path


def main() -> None:
    n = build()
    print(f"ARCHIVE READY: {n} files in {ROOT}/")
    if "--zip" in sys.argv[1:]:
        z = zip_archive()
        print(f"ZIP READY: {z} ({z.stat().st_size} bytes)")


if __name__ == "__main__":
    main()