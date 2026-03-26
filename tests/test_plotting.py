from pathlib import Path

import numpy as np

from equilibrium.models import DemoEquilibriumModel
from equilibrium.plotting import FigurePlotter, ParameterSweep
from equilibrium.solvers import ScipyRootSolver


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
    )

    assert len(result.points) == 3
    assert np.all(result.success_mask() == np.array([1.0, 1.0, 1.0]))
    assert np.allclose(
        result.metric_series("x"), np.array([0.5, 1.0, 2.0], dtype=float)
    )


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
    )
    figure = plotter.plot_1d(result, metrics=["x", "y"], title="test")
    path = plotter.save(figure, tmp_path / "figure.png")

    assert path.exists()
