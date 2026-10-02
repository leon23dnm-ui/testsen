# M0 falsification report

| combo | warm_ok | activity_band | entropy_band | rho_stable | no_recovery | nontrivial | pass |
|-------|---------|---------------|--------------|------------|-------------|------------|------|
| eta=0.01, Lambda=0.3, eta_g=0.0 |   | x |   | x | x | x |   |

## Вердикт

**НЕ НАЙДЕН**

## Диагностика (лог тика, среднее по тикам)

| combo | activity | H | s_ed | rho_j | eps_norm | gate_frac | mean_F_ext | mask_frac | w_fro | mean_g |
|-------|---|---|---|---|---|---|---|---|---|---|
| eta=0.01, Lambda=0.3, eta_g=0.0 | 0.0113 | 2.5880 | 0.0059 | 0.9405 | 1.2380 | 0.2381 | 0.0112 | 1.0000 | 0.7327 | 1.0000 |

## Наблюдения (диагностика, среднее по последним 100 тикам)

| combo | h_norm | node_spread | w_fro | wm_fro | mask_frac | gate_frac | s_ed | mem_fro | recall |
|-------|---|---|---|---|---|---|---|---|---|
| eta=0.01, Lambda=0.3, eta_g=0.0 | 0.9334 | 0.0037 | 0.7327 | 0.0645 | 1.0000 | 0.2381 | 0.0059 | 0.0005 | 0.0000 |

## Петля гомеостаза (конец прогона)

| combo | g_end | mu_end | theta_end | w_row | g*w_row | loop |
|-------|---|---|---|---|---|---|
| eta=0.01, Lambda=0.3, eta_g=0.0 | 1.0000 | 0.0950 | 0.0000 | 0.3813 | 0.3813 | open |
