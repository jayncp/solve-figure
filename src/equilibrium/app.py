"""Application entrypoints."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from equilibrium.models import DemoEquilibriumModel
from equilibrium.plotting import FigurePlotter, ParameterSweep
from equilibrium.solvers import CompositeSolver, ScipyRootSolver


def run_demo_pipeline(output_dir: str | Path = "output") -> Path:
    """Run the demo model, sweep one parameter, and save a figure."""
    system = DemoEquilibriumModel()
    solver = CompositeSolver(
        [
            ScipyRootSolver(method="hybr", require_constraints=True),
            ScipyRootSolver(method="lm", require_constraints=True),
        ]
    )
    sweep = ParameterSweep()
    plotter = FigurePlotter()

    result = sweep.sweep_1d(
        system,
        solver,
        base_params={"curvature": 1.0, "slope": 0.75},
        sweep_param="curvature",
        sweep_values=np.linspace(0.25, 4.0, 8),
        metric_names=["x", "y", "total"],
        initial_guess=np.array([1.0, 0.75], dtype=float),
    )
    figure = plotter.plot_1d(
        result,
        metrics=["x", "y", "total"],
        title="Demo Equilibrium Sweep",
        xlabel="curvature",
    )
    return plotter.save(figure, Path(output_dir) / "demo_equilibrium_sweep.png")


def build_status_message(figure_path: str | Path) -> str:
    """Return a short package status summary for the demo pipeline stage."""
    return f"demo pipeline complete: figure saved to {Path(figure_path)}"


def main() -> None:
    """CLI entrypoint."""
    figure_path = run_demo_pipeline()
    print(build_status_message(figure_path))
