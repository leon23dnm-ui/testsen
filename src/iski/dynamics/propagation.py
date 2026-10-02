import torch


def propagate(graph, state, n: int, k: int) -> torch.Tensor:
    """Вычислить вход I_src от распространения с задержками по графу.

    out[dst] += sum_{src,d} W_eff(src->dst,d) * x_src[t-d]
    """
    out = torch.zeros(n, k, dtype=torch.float64)

    w_eff = torch.as_tensor(graph.w_eff(), dtype=torch.float64)
    src_all = graph.edge_index[0]
    dst_all = graph.edge_index[1]
    delays = graph.delays

    for d in sorted(set(delays.tolist())):
        mask = delays == d
        src = torch.from_numpy(src_all[mask]).long()
        dst = torch.from_numpy(dst_all[mask]).long()
        w = w_eff[mask]

        delayed = torch.as_tensor(state.delayed(int(d)), dtype=torch.float64)
        contrib = w.unsqueeze(1) * delayed[src]
        out.index_add_(0, dst, contrib)

    return out
