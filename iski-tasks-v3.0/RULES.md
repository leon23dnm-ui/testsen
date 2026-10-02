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
