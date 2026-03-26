import numpy as np
import pytest

from pathlib import Path

from equilibrium.app import (
    build_two_period_solver,
    run_two_period_analysis,
    run_two_period_benchmark,
)
from equilibrium.models import TwoPeriodModel, default_two_period_benchmark
from equilibrium.solvers import CompositeSolver, ScipyRootSolver


def test_default_two_period_benchmark_path_reaches_target() -> None:
    benchmark = default_two_period_benchmark()
    path = benchmark.continuation_path()

    assert path[0]["rho"] == pytest.approx(0.0)
    assert path[-1] == benchmark.params
    assert len(path) == 5


def test_two_period_benchmark_is_stable_across_multiple_initial_guesses() -> None:
    benchmark = default_two_period_benchmark()
    system = TwoPeriodModel()
    solver = CompositeSolver(
        [
            ScipyRootSolver(method="hybr", require_constraints=True),
            ScipyRootSolver(method="lm", require_constraints=True),
        ]
    )
    starts = [
        benchmark.initial_guess,
        np.array(
            [0.6, 0.7, -0.2, 0.15, 0.1, 0.2, 0.08, -0.1, 0.2, 0.2, -0.05], dtype=float
        ),
        np.array(
            [0.3, 0.5, -0.4, 0.1, 0.2, 0.25, 0.1, -0.2, 0.18, 0.22, -0.1], dtype=float
        ),
    ]

    for start in starts:
        result = solver.solve(system, benchmark.params, initial_guess=start)
        assert benchmark.acceptance.accepts(result) is True
        assert np.allclose(result.x, benchmark.expected_solution, atol=1e-6)


def test_two_period_benchmark_continuation_solver_reaches_expected_solution() -> None:
    benchmark = default_two_period_benchmark()
    solver = build_two_period_solver()
    system = TwoPeriodModel()

    result = solver.solve(
        system,
        benchmark.params,
        initial_guess=benchmark.initial_guess,
    )

    assert benchmark.acceptance.accepts(result) is True
    assert np.allclose(result.x, benchmark.expected_solution, atol=1e-6)


def test_run_two_period_benchmark_returns_accepted_result() -> None:
    benchmark = default_two_period_benchmark()
    result = run_two_period_benchmark()

    assert benchmark.acceptance.accepts(result) is True


def test_run_two_period_analysis_persists_expected_outputs(tmp_path: Path) -> None:
    outputs = run_two_period_analysis(tmp_path)

    assert set(outputs) == {"heatmap_png", "summary_json", "sweep_json"}
    assert all(path.exists() for path in outputs.values())
