import numpy as np
import pytest

from equilibrium.models import EquationSystem, NDArrayFloat, Params
from equilibrium.solvers import (
    CompositeSolver,
    ScipyRootSolver,
    SolveResult,
    build_solve_result,
)


class LinearSystem(EquationSystem):
    @property
    def variable_names(self) -> tuple[str, ...]:
        return ("x", "y")

    @property
    def param_names(self) -> tuple[str, ...]:
        return ("x_star", "y_star")

    def equations(self, x: NDArrayFloat, params: Params) -> NDArrayFloat:
        return np.array(
            [x[0] - params["x_star"], x[1] - params["y_star"]],
            dtype=float,
        )

    def constraints(
        self,
        x: NDArrayFloat,
        params: Params,
        intermediates: dict[str, float] | None = None,
    ) -> dict[str, float]:
        return {"x_positive": float(x[0])}

    def metrics(
        self,
        x: NDArrayFloat,
        params: Params,
        intermediates: dict[str, float] | None = None,
    ) -> dict[str, float]:
        return {"sum": float(x.sum())}


class AlwaysFailSolver:
    name = "always-fail"

    def solve(
        self,
        system: EquationSystem,
        params: Params,
        initial_guess: NDArrayFloat | None = None,
        *,
        options: dict[str, object] | None = None,
    ) -> SolveResult:
        x = (
            np.zeros(system.n_vars, dtype=float)
            if initial_guess is None
            else initial_guess
        )
        return build_solve_result(
            system,
            params,
            x,
            success=False,
            method=self.name,
            residual_norm=1.0,
            message="forced failure",
        )


def test_scipy_root_solver_finds_linear_solution() -> None:
    solver = ScipyRootSolver()
    system = LinearSystem()

    result = solver.solve(
        system,
        {"x_star": 1.5, "y_star": -2.0},
        initial_guess=np.array([0.0, 0.0], dtype=float),
    )

    assert result.success is True
    assert result.constraints_ok is True
    assert result.variables["x"] == pytest.approx(1.5)
    assert result.variables["y"] == pytest.approx(-2.0)
    assert result.metrics["sum"] == pytest.approx(-0.5)


def test_scipy_root_solver_can_enforce_constraints() -> None:
    solver = ScipyRootSolver(require_constraints=True)
    system = LinearSystem()

    result = solver.solve(
        system,
        {"x_star": -1.0, "y_star": 2.0},
        initial_guess=np.array([0.2, 0.2], dtype=float),
    )

    assert result.success is False
    assert result.constraints_ok is False


def test_composite_solver_falls_back_to_next_strategy() -> None:
    solver = CompositeSolver([AlwaysFailSolver(), ScipyRootSolver()])
    system = LinearSystem()

    result = solver.solve(
        system,
        {"x_star": 2.0, "y_star": 3.0},
        initial_guess=np.array([0.0, 0.0], dtype=float),
    )

    assert result.success is True
    assert result.variables["x"] == pytest.approx(2.0)
    assert result.variables["y"] == pytest.approx(3.0)
    assert len(result.failures) == 1
    assert result.failures[0].method == "always-fail"
