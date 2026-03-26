import numpy as np
import pytest

from equilibrium.models import EquationSystem, NDArrayFloat, Params


class MockSystem(EquationSystem):
    @property
    def variable_names(self) -> tuple[str, ...]:
        return ("x", "y")

    @property
    def param_names(self) -> tuple[str, ...]:
        return ("scale", "target")

    def equations(self, x: NDArrayFloat, params: Params) -> NDArrayFloat:
        return np.array([x[0] - params["target"], x[1] - params["scale"]], dtype=float)

    def intermediates(self, x: NDArrayFloat, params: Params) -> dict[str, float]:
        total = float(x.sum())
        return {"total": total, "scaled_total": total * params["scale"]}

    def constraints(
        self,
        x: NDArrayFloat,
        params: Params,
        intermediates: dict[str, float] | None = None,
    ) -> dict[str, float]:
        if intermediates is None:
            intermediates = self.intermediates(x, params)
        return {"positive_total": intermediates["total"]}

    def metrics(
        self,
        x: NDArrayFloat,
        params: Params,
        intermediates: dict[str, float] | None = None,
    ) -> dict[str, float]:
        if intermediates is None:
            intermediates = self.intermediates(x, params)
        return {"scaled_total": intermediates["scaled_total"]}


def test_validate_params_accepts_exact_match() -> None:
    system = MockSystem()
    system.validate_params({"scale": 2.0, "target": 1.0})


def test_validate_params_rejects_missing_or_extra_keys() -> None:
    system = MockSystem()

    with pytest.raises(ValueError, match="missing"):
        system.validate_params({"scale": 2.0})

    with pytest.raises(ValueError, match="extra"):
        system.validate_params({"scale": 2.0, "target": 1.0, "extra": 3.0})


def test_variable_dict_uses_declared_order() -> None:
    system = MockSystem()

    assert system.n_vars == 2
    assert system.variable_dict(np.array([1.5, -2.0], dtype=float)) == {
        "x": 1.5,
        "y": -2.0,
    }


def test_validate_x_rejects_wrong_length() -> None:
    system = MockSystem()

    with pytest.raises(ValueError, match="Expected vector length 2"):
        system.validate_x(np.array([1.0], dtype=float))
