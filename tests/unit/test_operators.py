import pytest

from iski.core.operators import load_registry, validate_registry


def test_registry_duplicate_writer_raises(tmp_path):
    data = """
- name: op1
  clock: fast
  level: 0
  channels: [dX]
- name: op2
  clock: fast
  level: 1
  channels: [dX]
"""
    path = tmp_path / "registry.yaml"
    path.write_text(data, encoding="utf-8")
    specs = load_registry(str(path))
    with pytest.raises(AssertionError):
        validate_registry(specs)


def test_registry_invalid_clock_raises(tmp_path):
    data = """
- name: op1
  clock: weekly
  level: 0
  channels: [dX]
"""
    path = tmp_path / "registry.yaml"
    path.write_text(data, encoding="utf-8")
    specs = load_registry(str(path))
    with pytest.raises(AssertionError):
        validate_registry(specs)


def test_registry_valid_passes(tmp_path):
    data = """
- name: op1
  clock: fast
  level: 0
  channels: [dX]
- name: op2
  clock: medium
  level: 1
  channels: [dE]
"""
    path = tmp_path / "registry.yaml"
    path.write_text(data, encoding="utf-8")
    specs = load_registry(str(path))
    validate_registry(specs)
