# CHECKLIST (заполняет исполнитель после каждого задания)
| T | Задание | Тесты зелёные | Внесено в operators.yaml | Issues |
|---|---------|---------------|--------------------------|--------|
| 01 | Окружение и скелет пакета | [x] | N/A | - |
| 02 | Контракт дельт (single-writer) | [x] | N/A | - |
| 03 | Состояние Omega + ring-buffer задержек | [x] | N/A | - |
| 04 | Snapshot + реестр операторов | [x] | N/A | - |
| 05 | Ядра сходства + разреженный граф (COO) | [x] | N/A | - |
| 06 | Распространение с задержками + уравнение поля + шум | [x] | N/A | - |
| 07 | Salience + Attention (распределение по N) | [x] | N/A | - |
| 08 | GWS broadcast: порог + мягкие веса | [x] | N/A | - |
| 09 | Enc_shared + Head_1 + ring B_h (delayed credit) | [x] | N/A | - |
| 10 | Eligibility (fast) + пластичность (medium) | [x] | N/A | - |
| 11 | Элемент памяти + bounded store + F_mem | [x] | N/A | - |
| 12 | F_mode: 5 уравнений жизненного цикла | [x] | N/A | - |
| 13 | F_forget {Keep,Archive} + F_archive (async) | [x] | N/A | - |
| 14 | Hard-инварианты: check + project | [x] | N/A | - |
| 15 | Clocks + сборка кандидата | [x] | N/A | - |
| 16 | Метрики: activity, H(X), s_ed, rho(J) | [x] | N/A | - |
| 17 | Pipeline 22 шага + commit + maintenance | [x] | N/A | - |
| 18 | Envelope, InputBuffer, hash-encoder | [x] | N/A | - |
| 19 | Конфигурация: model/runtime/operators/bootstrap/m0 | [x] | N/A | - |
| 20 | M0 falsification-прогон V1 + REPORT | [x] | N/A | - |
| 21 | Финальный гейт и упаковка архива | [x] | N/A | полный V1 запущен, вердикт НЕ НАЙДЕН |
| 22 | Гомеостаз (mu, theta, g) + расширенная диагностика | [x] | [x] | повторный V1 (fast): НЕ НАЙДЕН; p0 0->0.5; ISSUE-001 |
| 24 | Конфиг-аудит + w_init_max/W_max + повторный fast-V1 | [x] | N/A | fast-V1: 5/6, только entropy_band fail; ISSUE-002 |
| 25 | Каноника H_max/rho_max + fast-V1 6/6 + полный V1 | [x] | N/A | fast 6/6 (НАЙДЕН); полный V1: НЕ НАЙДЕН (warm_ok, entropy_band); seed-фикс torch в bootstrap |
| 26 | Ингибиторный bootstrap (w_minus, второй набор рёбер) | [x] | N/A | fast-V1: НЕ НАЙДЕН (warm_ok, entropy_band); полный V1 не запускался (<6/6); ISSUE-003 |
| 27 | Канон: p_I=rho_I*p0, xi_max=0.01, единый Lambda, fail-fast | [x] | N/A | ребейзлайн fast-V1: НЕ НАЙДЕН (warm_ok, entropy_band); sweep Lambda невырожден; полный V1 не запускался; правило: regex-булк по тестам запрещён (restore из HEAD при повреждении) |
| 28 | Упразднение fast-гейта + full-horizon rebaseline + диагностика петли g | [x] | N/A | полный V1 (24 комбо): НЕ НАЙДЕН (warm_ok ~-0.025 marginal, entropy_band -0.24); петля g: mu->mu* через theta, g*w_row=0.38-0.47; ISSUE-003 амендирован |
| 29 | F_form: формирование памяти (Novelty/theta_form, cap M_max) + диагностика F_mem/recall | [x] | N/A | полный V1: НЕ НАЙДЕН (warm_ok, entropy_band); F_mem!=0 (0.12-0.14), recall=0; ветвление -> T30: attention-модуляция W^eff |
