import yaml

from iski.core.operators import load_registry, validate_registry
from iski.runtime.scheduler import Clocks


def test_operators_registry_valid():
    specs = load_registry("config/operators.yaml")
    validate_registry(specs)


def test_runtime_clocks_valid():
    with open("config/runtime.yaml", encoding="utf-8") as f:
        runtime = yaml.safe_load(f)
    c = runtime["clocks"]
    Clocks(c["m"], c["s"], c["q"])


def test_model_config_loads():
    with open("config/model.yaml", encoding="utf-8") as f:
        model = yaml.safe_load(f)
    assert model["N"] == 4
    assert len(model["eta"]) == 9


def test_canonical_values():
    """Каноническая таблица куратора (решения по ISSUE-001 и ISSUE-002)."""
    with open("config/model.yaml", encoding="utf-8") as f:
        model = yaml.safe_load(f)
    with open("config/bootstrap.yaml", encoding="utf-8") as f:
        bootstrap = yaml.safe_load(f)

    assert model["W_max"] == 2.0
    assert model["sigma"] == 0.5
    assert model["Lam"] == 0.5
    assert model["xi_max"] == 0.1
    assert model["mu_star"] == 0.1
    assert model["beta_h"] == 0.05
    assert model["eta_theta"] == 0.01
    assert model["eta_g"] == 0.05
    assert model["g_min"] == 0.5
    assert model["g_max"] == 5.0
    assert bootstrap["p0"] == 0.5
    assert bootstrap["w_init_max"] == 0.5
    assert bootstrap["theta_ed_warm"] == 0.15
    assert bootstrap["H_max"] == 2.5
    assert bootstrap["rho_max"] == 1.5
