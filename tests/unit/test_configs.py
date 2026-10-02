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
