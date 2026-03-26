import numpy as np
import pytest

from equilibrium.models import DemoEquilibriumModel


def test_demo_model_metrics_and_constraints() -> None:
    model = DemoEquilibriumModel()
    x = np.array([2.0, 1.0], dtype=float)
    params = {"curvature": 4.0, "slope": 0.5}

    assert np.allclose(model.equations(x, params), np.array([0.0, 0.0], dtype=float))
    assert model.constraints(x, params) == {"x_positive": 2.0, "y_non_negative": 1.0}
    assert model.metrics(x, params)["total"] == pytest.approx(3.0)


def test_demo_model_rejects_invalid_params() -> None:
    model = DemoEquilibriumModel()

    with pytest.raises(ValueError, match="curvature must be positive"):
        model.validate_params({"curvature": 0.0, "slope": 0.5})

    with pytest.raises(ValueError, match="slope must be non-negative"):
        model.validate_params({"curvature": 1.0, "slope": -0.1})
