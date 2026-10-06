import numpy as np
import torch

from iski.attention.attention import attention
from iski.attention.gws import gws_broadcast
from iski.attention.salience import salience
from iski.core.delta import Delta
from iski.core.kernels import kernel_similarity
from iski.core.snapshots import export_snapshot
from iski.dynamics.homeostasis import homeostasis_update
from iski.dynamics.noise import xi
from iski.dynamics.propagation import propagate
from iski.dynamics.update import field_update
from iski.learning.eligibility import update_eligibility
from iski.learning.plasticity import plasticity_delta
from iski.memory.forgetting import forget_decision
from iski.memory.formation import create_memory, formation_decision
from iski.memory.maintenance import archive_sweep
from iski.memory.modes import update_modes
from iski.memory.store import MemoryStore
from iski.runtime.candidate import assemble
from iski.runtime.diagnostics import compute_metrics, gate_fraction, tick_metrics
from iski.safety.invariants import check, project


class Pipeline:
    """Frozen 22-step pipeline M0."""

    REQUIRED_CFG = (
        "sigma",
        "theta_gws",
        "beta_g",
        "T_A",
        "lam_N",
        "lam_E",
        "Lambda",
        "kappa",
        "xi_max",
        "lam_elig",
        "gate_thr",
        "q_max",
        "eta",
        "eta_plast",
        "lam_w",
        "theta_align",
        "eta_E",
        "w_max",
        "w_min",
        "theta_forget",
        "theta_I",
        "T_archive",
        "tau1",
        "M_max",
        "mu_star",
        "beta_h",
        "eta_theta",
        "eta_g",
        "g_min",
        "g_max",
        "theta_form",
        "w_mem_init",
    )

    def __init__(self, state, clocks, cfg, head, hbuf, rng):
        missing = [k for k in self.REQUIRED_CFG if not hasattr(cfg, k)]
        if missing:
            raise KeyError(f"cfg missing required keys: {missing}")

        self.state = state
        self.clocks = clocks
        self.cfg = cfg
        self.head = head
        self.hbuf = hbuf
        self.rng = rng

        self.metrics_cache = None
        self.last_eps = np.zeros_like(state.X)
        self.last_e_in = None
        self.log = []
        self._order = []

    def _append(self, n: int) -> None:
        self._order.append(f"{n:02d}")

    def _e_align(self, E: np.ndarray, e_in: np.ndarray) -> np.ndarray:
        theta = self.cfg.theta_align
        eta = self.cfg.eta_E
        K = kernel_similarity(E, e_in, self.cfg.sigma)
        dE = np.zeros_like(E)
        mask = K > theta
        dE[mask] = eta * (e_in - E[mask])
        return dE

    def _memory_lifecycle(self, t: int, sal: np.ndarray, eps: np.ndarray):
        ops = []
        sigma = self.cfg.sigma
        eta_modes = self.cfg.eta
        w_max = self.cfg.w_max
        w_min = self.cfg.w_min
        th_forget = self.cfg.theta_forget
        th_I = self.cfg.theta_I

        x_mean = self.state.X.mean(-1)
        eps_mean = np.abs(eps).mean(-1)

        for i, item in enumerate(self.state.store):
            if item.status != 0:
                continue
            reuse = float(np.exp(-(t - item.last_access) / 50.0))
            K = kernel_similarity(self.state.E, item.e, sigma)
            imp = float((K * x_mean).mean())
            surprise = float((K * eps_mean).mean())
            pg = 0.0
            rho_new = update_modes(
                item.rho[None, :],
                reuse,
                imp,
                surprise,
                pg,
                eta_modes,
                dt=1.0,
                w_max=w_max,
            )[0]
            ops.append(("rho", i, rho_new))
            w = float(rho_new[4])
            forget_rho = float(rho_new[3])
            decision = forget_decision(w, forget_rho, imp, w_min, th_forget, th_I)
            if self.clocks.active(t, "slow") and decision == "archive":
                ops.append(("status", i, 1, t))
            item.last_access = t
        return ops

    def maintenance(self) -> None:
        T_archive = self.cfg.T_archive
        idx = archive_sweep(self.state.store, self.state.tick, T_archive)
        if idx:
            ops = [("del", i) for i in reversed(idx)]
            self.state.apply_delta(Delta(dM=ops))

    def tick(self, e_in, conf):
        t = self.state.tick
        N, K = self.state.X.shape
        X = self.state.X
        E = self.state.E
        graph = self.state.graph
        store = self.state.store

        # 01 snapshot
        self._append(1)
        _ = export_snapshot(self.state, self.metrics_cache)

        # 02 F_ext
        self._append(2)
        if e_in is not None:
            K_sim = kernel_similarity(E, e_in, self.cfg.sigma)
            F_ext = float(conf) * K_sim[:, None] * np.ones(K)
            self.last_e_in = e_in
        else:
            F_ext = np.zeros((N, K))

        # 03 nov, pe, sal, att
        self._append(3)
        if self.last_e_in is not None:
            nov = 1.0 - kernel_similarity(E, self.last_e_in, self.cfg.sigma)
        else:
            nov = np.zeros(N)
        pe = np.abs(self.last_eps).mean(-1)
        sal = salience(nov, pe, self.cfg.lam_N, self.cfg.lam_E)
        att = attention(sal, self.cfg.T_A)

        # 04 GWS broadcast
        self._append(4)
        X_bc_t, gws_mask = gws_broadcast(
            E,
            X,
            sal,
            self.cfg.theta_gws,
            self.cfg.sigma,
            self.cfg.beta_g,
        )
        X_bc = X_bc_t.numpy() if isinstance(X_bc_t, torch.Tensor) else X_bc_t

        # 05 F_mem
        self._append(5)
        F_mem = MemoryStore(store, self.cfg.M_max).projection(E, self.cfg.sigma, K)

        # 06 h, hbuf, xhat
        self._append(6)
        h = self.head.encode(X)
        self.hbuf.push(t, h)
        xhat_t = self.head.predict(h).reshape(N, K)
        xhat = xhat_t.detach().numpy() if isinstance(xhat_t, torch.Tensor) else xhat_t

        # 07 propagate
        self._append(7)
        prop_t = propagate(graph, self.state, N, K)
        prop = prop_t.numpy() if isinstance(prop_t, torch.Tensor) else prop_t

        # 08 Laplacian, field update
        self._append(8)
        L = graph.laplacian(N)
        I_src = F_ext + F_mem + prop + (X_bc - X)
        xi_t = xi(self.rng, X.shape, self.cfg.xi_max)
        X_next_t = field_update(
            X,
            I_src,
            self.cfg.Lambda,
            self.cfg.kappa,
            L,
            xi_t,
            g=self.state.S[:, 2],
            theta=self.state.S[:, 1],
        )
        X_next = X_next_t.numpy() if isinstance(X_next_t, torch.Tensor) else X_next_t
        dX = X_next - X

        # 09 eps, train head
        self._append(9)
        eps = X_next - xhat
        self.last_eps = eps
        tau1 = self.cfg.tau1
        h_old = self.hbuf.get(t - tau1)
        if h_old is not None:
            self.head.train_step(h_old, X_next)

        # 10 eligibility
        self._append(10)
        dQ = update_eligibility(
            graph,
            self.state,
            self.cfg.lam_elig,
            self.cfg.gate_thr,
            self.cfg.q_max,
        )
        deltas = [Delta(dX=dX), Delta(dQ_elig=dQ)]

        # 11 medium / e_in / memory lifecycle
        self._append(11)
        if self.clocks.active(t, "medium"):
            deltas.append(
                plasticity_delta(
                    graph,
                    eps,
                    self.cfg.eta_plast,
                    self.cfg.lam_w,
                )
            )
            deltas.append(homeostasis_update(self.state.S, self.state.X, self.cfg))
        dM_ops = []
        if self.clocks.active(t, "medium") and e_in is not None:
            decision, k = formation_decision(
                e_in,
                self.state.store,
                self.cfg.theta_form,
                self.cfg.sigma,
                self.cfg.M_max,
            )
            if decision == "form":
                dM_ops.append(("add", create_memory(e_in, X_next_t, self.cfg, t)))
            elif k >= 0:
                self.state.store[k].last_access = t
        if e_in is not None:
            dE = self._e_align(E, e_in)
            deltas.append(Delta(dE=dE))
        dM_ops += self._memory_lifecycle(t, sal, eps)
        if dM_ops:
            deltas.append(Delta(dM=dM_ops))

        # 12 structural stub
        self._append(12)
        if self.clocks.active(t, "structural") and self.metrics_cache is not None:
            pass

        # 13 (no frozen action, placeholder for numbering)
        self._append(13)

        # 14 assemble candidate
        self._append(14)
        cand = assemble(self.state, deltas)

        # 15 metrics
        self._append(15)
        metrics = compute_metrics(cand, eps, e_in, self.cfg)
        recall_count = sum(
            1
            for item in self.state.store
            if float(np.max(kernel_similarity(E, item.e, self.cfg.sigma))) > 0.3
        )
        metrics.update(
            tick_metrics(
                F_ext,
                gws_mask,
                gate_fraction(self.state, graph, self.cfg.gate_thr),
                cand.graph,
                cand.S,
                cand.X,
                float(np.linalg.norm(F_mem)),
                float(recall_count),
            )
        )

        # 16 check + project
        self._append(16)
        viol = check(cand, self.cfg)
        project(cand, self.cfg)

        # 17 recovery log
        self._append(17)
        if viol:
            pass

        # 18 commit (single writer)
        self._append(18)
        self.state = cand

        # 19 advance ring
        self._append(19)
        self.state.advance_ring()

        # 20 output
        self._append(20)
        rn = np.linalg.norm(self.state.X, axis=1)
        alpha = rn / rn.sum() if rn.sum() > 0 else np.full(N, 1.0 / N)
        ebar = alpha @ self.state.E
        out = {
            "ebar": ebar,
            "metrics": metrics,
            "viol": viol,
            "att": att,
            "gws": gws_mask,
        }

        # 21 cache + log + tick
        self._append(21)
        self.metrics_cache = metrics
        self.log.append((t, metrics, len(viol)))
        self.state.tick = t + 1

        return out
