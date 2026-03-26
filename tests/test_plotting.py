from pathlib import Path
from typing import cast

import numpy as np
import pytest

from equilibrium.models import DemoEquilibriumModel
from equilibrium.models.base import EquationSystem, NDArrayFloat, Params
from equilibrium.plotting import FigurePlotter, ParameterSweep
from equilibrium.solvers import ScipyRootSolver, SolveResult, build_solve_result


def test_sweep_1d_returns_metric_series_and_success_mask() -> None:
    system = DemoEquilibriumModel()
    solver = ScipyRootSolver(require_constraints=True)
    sweep = ParameterSweep()

    result = sweep.sweep_1d(
        system,
        solver,
        base_params={"curvature": 1.0, "slope": 0.5},
        sweep_param="curvature",
        sweep_values=np.array([0.25, 1.0, 4.0], dtype=float),
        metric_names=["x", "total"],
        initial_guess=np.array([1.0, 0.5], dtype=float),
        mode="path",
    )

    assert len(result.points) == 3
    assert result.mode == "path"
    assert np.all(result.success_mask() == np.array([1.0, 1.0, 1.0]))
    assert np.all(result.constraints_mask() == np.array([1.0, 1.0, 1.0]))
    assert np.allclose(
        result.metric_series("x"), np.array([0.5, 1.0, 2.0], dtype=float)
    )
    assert result.failure_points() == ()


def test_plotter_saves_figure(tmp_path: Path) -> None:
    system = DemoEquilibriumModel()
    solver = ScipyRootSolver(require_constraints=True)
    sweep = ParameterSweep()
    plotter = FigurePlotter()

    result = sweep.sweep_1d(
        system,
        solver,
        base_params={"curvature": 1.0, "slope": 0.5},
        sweep_param="curvature",
        sweep_values=np.array([0.25, 1.0], dtype=float),
        metric_names=["x", "y"],
        initial_guess=np.array([1.0, 0.5], dtype=float),
        mode="path",
    )
    figure = plotter.plot_1d(result, metrics=["x", "y"], title="test")
    path = plotter.save(figure, tmp_path / "figure.png")

    assert path.exists()


class TrackingSystem(EquationSystem):
    @property
    def variable_names(self) -> tuple[str, ...]:
        return ("x",)

    @property
    def param_names(self) -> tuple[str, ...]:
        return ("target",)

    def equations(self, x: NDArrayFloat, params: Params) -> NDArrayFloat:
        return np.array([x[0] - params["target"]], dtype=float)


class TrackingSolver:
    name = "tracking"

    def __init__(self) -> None:
        self.guesses: list[float | None] = []

    def solve(
        self,
        system: EquationSystem,
        params: Params,
        initial_guess: NDArrayFloat | None = None,
        *,
        options: dict[str, object] | None = None,
    ) -> SolveResult:
        self.guesses.append(None if initial_guess is None else float(initial_guess[0]))
        target = float(params["target"])
        return build_solve_result(
            system,
            params,
            np.array([target], dtype=float),
            success=True,
            method=self.name,
            residual_norm=0.0,
            message="ok",
        )


class ConditionalFailSolver:
    name = "conditional-fail"

    def solve(
        self,
        system: EquationSystem,
        params: Params,
        initial_guess: NDArrayFloat | None = None,
        *,
        options: dict[str, object] | None = None,
    ) -> SolveResult:
        target = float(params["target"])
        success = target != 2.0
        x_value = 1.0 if not success else target
        return build_solve_result(
            system,
            params,
            np.array([x_value], dtype=float),
            success=success,
            method=self.name,
            residual_norm=0.0 if success else 1.0,
            message="ok" if success else "failed at target=2",
        )


def test_sweep_1d_independent_mode_reuses_base_guess_each_time() -> None:
    system = TrackingSystem()
    solver = TrackingSolver()
    sweep = ParameterSweep()

    result = sweep.sweep_1d(
        system,
        solver,
        base_params={"target": 0.0},
        sweep_param="target",
        sweep_values=np.array([1.0, 2.0, 3.0], dtype=float),
        metric_names=[],
        initial_guess=np.array([9.0], dtype=float),
        mode="independent",
    )

    assert result.mode == "independent"
    assert solver.guesses == [9.0, 9.0, 9.0]
    guesses = [cast(np.ndarray, point.initial_guess)[0] for point in result.points]
    assert guesses == pytest.approx([9.0, 9.0, 9.0])


def test_sweep_1d_path_mode_uses_previous_success_as_next_guess() -> None:
    system = TrackingSystem()
    solver = TrackingSolver()
    sweep = ParameterSweep()

    result = sweep.sweep_1d(
        system,
        solver,
        base_params={"target": 0.0},
        sweep_param="target",
        sweep_values=np.array([1.0, 2.0, 3.0], dtype=float),
        metric_names=[],
        initial_guess=np.array([9.0], dtype=float),
        mode="path",
    )

    assert result.mode == "path"
    assert solver.guesses == [9.0, 1.0, 2.0]
    guesses = [cast(np.ndarray, point.initial_guess)[0] for point in result.points]
    assert guesses == pytest.approx([9.0, 1.0, 2.0])


def test_sweep_1d_records_failure_points() -> None:
    system = TrackingSystem()
    solver = ConditionalFailSolver()
    sweep = ParameterSweep()

    result = sweep.sweep_1d(
        system,
        solver,
        base_params={"target": 0.0},
        sweep_param="target",
        sweep_values=np.array([1.0, 2.0, 3.0], dtype=float),
        metric_names=[],
        initial_guess=np.array([1.0], dtype=float),
        mode="path",
    )

    failures = result.failure_points()

    assert np.all(result.success_mask() == np.array([1.0, 0.0, 1.0]))
    assert len(failures) == 1
    assert failures[0].index == 1
    assert failures[0].sweep_value == pytest.approx(2.0)
    assert failures[0].message == "failed at target=2"
