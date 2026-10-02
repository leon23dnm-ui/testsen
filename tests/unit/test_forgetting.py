import pytest

from iski.memory.forgetting import forget_decision


@pytest.mark.parametrize(
    ("w", "forget_rho", "imp", "expected"),
    [
        (0.1, 0.0, 0.0, "archive"),  # w<w_min, imp<th_I
        (0.1, 0.9, 0.5, "archive"),  # w<w_min, forget_rho>th_forget
        (0.1, 0.0, 0.9, "keep"),  # w<w_min, но imp высокий и forget_rho низкий
        (0.5, 0.9, 0.0, "keep"),  # w>=w_min
    ],
)
def test_forget_decision_table(w, forget_rho, imp, expected):
    w_min = 0.2
    th_forget = 0.5
    th_I = 0.3
    assert forget_decision(w, forget_rho, imp, w_min, th_forget, th_I) == expected
