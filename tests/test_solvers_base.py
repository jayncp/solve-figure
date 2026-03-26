import numpy as np

from equilibrium.models import EquationSystem, NDArrayFloat, Params
from equilibrium.solvers import SolverFailure, build_solve_result


class MockSystem(EquationSystem):
    @property
    def variable_names(self) -> tuple[str, ...]:
        return ("x", "y")

    @property
    def param_names(self) -> tuple[str, ...]:
        return ("scale",)

    def equations(self, x: NDArrayFloat, params: Params) -> NDArrayFloat:
        return np.array([x[0], x[1] - params["scale"]], dtype=float)

    def intermediates(self, x: NDArrayFloat, params: Params) -> dict[str, float]:
        return {"sum": float(x.sum())}

    def constraints(
        self,
        x: NDArrayFloat,
        params: Params,
        intermediates: dict[str, float] | None = None,
    ) -> dict[str, float]:
        if intermediates is None:
            intermediates = self.intermediates(x, params)
        return {"positive_sum": intermediates["sum"]}

    def metrics(
        self,
        x: NDArrayFloat,
        params: Params,
        intermediates: dict[str, float] | None = None,
    ) -> dict[str, float]:
        if intermediates is None:
            intermediates = self.intermediates(x, params)
        return {"scaled_sum": intermediates["sum"] * params["scale"]}


def test_build_solve_result_populates_all_derived_fields() -> None:
    system = MockSystem()
    result = build_solve_result(
        system,
        {"scale": 2.0},
        np.array([1.0, 2.0], dtype=float),
        success=True,
        method="mock",
        residual_norm=0.0,
        message="ok",
        nfev=3,
        failures=(SolverFailure(method="seed", message="retry"),),
    )

    assert result.success is True
    assert result.variables == {"x": 1.0, "y": 2.0}
    assert result.intermediates == {"sum": 3.0}
    assert result.constraints == {"positive_sum": 3.0}
    assert result.constraints_ok is True
    assert result.metrics == {"scaled_sum": 6.0}
    assert result.nfev == 3
    assert result.failures[0].method == "seed"


def test_build_solve_result_marks_failed_constraints() -> None:
    system = MockSystem()
    result = build_solve_result(
        system,
        {"scale": 1.0},
        np.array([-2.0, 1.0], dtype=float),
        success=False,
        method="mock",
        residual_norm=1.5,
        message="bad constraints",
    )

    assert result.constraints_ok is False
    assert result.constraints["positive_sum"] == -1.0
