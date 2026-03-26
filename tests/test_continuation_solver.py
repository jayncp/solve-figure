import numpy as np
import pytest

from equilibrium.models import EquationSystem, NDArrayFloat, Params
from equilibrium.solvers import (
    ContinuationSolver,
    ScipyRootSolver,
    SolveAcceptance,
    build_solve_result,
)


class LinearPathSystem(EquationSystem):
    @property
    def variable_names(self) -> tuple[str, ...]:
        return ("x",)

    @property
    def param_names(self) -> tuple[str, ...]:
        return ("target",)

    def equations(self, x: NDArrayFloat, params: Params) -> NDArrayFloat:
        return np.array([x[0] - params["target"]], dtype=float)

    def constraints(
        self,
        x: NDArrayFloat,
        params: Params,
        intermediates: dict[str, float] | None = None,
    ) -> dict[str, float]:
        return {"x_positive": float(x[0])}


def test_solve_acceptance_applies_residual_and_constraints() -> None:
    acceptance = SolveAcceptance(residual_tol=1e-6)
    system = LinearPathSystem()
    good = build_solve_result(
        system,
        {"target": 1.0},
        np.array([1.0], dtype=float),
        success=True,
        method="mock",
        residual_norm=1e-8,
        message="ok",
    )
    failed = build_solve_result(
        system,
        {"target": 1.0},
        np.array([1.0], dtype=float),
        success=False,
        method="mock",
        residual_norm=1e-8,
        message="failed",
    )
    bad_constraint = build_solve_result(
        system,
        {"target": -1.0},
        np.array([-1.0], dtype=float),
        success=True,
        method="mock",
        residual_norm=1e-8,
        message="ok",
    )
    high_residual = build_solve_result(
        system,
        {"target": 1.0},
        np.array([1.0], dtype=float),
        success=True,
        method="mock",
        residual_norm=1e-3,
        message="ok",
    )

    assert acceptance.accepts(good) is True
    assert acceptance.accepts(failed) is False
    assert acceptance.accepts(bad_constraint) is False
    assert acceptance.accepts(high_residual) is False


def test_continuation_solver_follows_path_and_solves_target() -> None:
    system = LinearPathSystem()
    step_solver = ScipyRootSolver(require_constraints=True)
    solver = ContinuationSolver(
        step_solver,
        path_builder=lambda params: (
            {"target": 0.5},
            {"target": 1.0},
            dict(params),
        ),
    )

    result = solver.solve(
        system,
        {"target": 2.0},
        initial_guess=np.array([0.0], dtype=float),
    )

    assert result.success is True
    assert result.constraints_ok is True
    assert result.variables["x"] == pytest.approx(2.0)
    assert result.residual_norm <= 1e-8


def test_continuation_solver_rejects_step_that_fails_acceptance() -> None:
    system = LinearPathSystem()
    step_solver = ScipyRootSolver(require_constraints=False)
    solver = ContinuationSolver(
        step_solver,
        acceptance=SolveAcceptance(require_constraints=True),
        path_builder=lambda params: (
            {"target": 1.0},
            dict(params),
        ),
    )

    result = solver.solve(
        system,
        {"target": -1.0},
        initial_guess=np.array([1.0], dtype=float),
    )

    assert result.success is False
    assert result.message.startswith("Continuation rejected step")
    assert result.failures
