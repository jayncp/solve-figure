"""
最小示例 — 用 DemoEquilibriumModel 跑一次 1D sweep 并画图
==========================================================

运行: uv run python examples/demo_sweep.py
输出: output/demo_equilibrium_sweep.png
"""

from pathlib import Path

import numpy as np

from equilibrium.models import DemoEquilibriumModel
from equilibrium.plotting import FigurePlotter, sweep_1d
from equilibrium.solvers import CompositeSolver, ScipyRootSolver

system = DemoEquilibriumModel()
solver = CompositeSolver(
    [
        ScipyRootSolver(method="hybr", require_constraints=True),
        ScipyRootSolver(method="lm", require_constraints=True),
    ]
)

result = sweep_1d(
    system,
    solver,
    base_params={"curvature": 1.0, "slope": 0.75},
    sweep_param="curvature",
    sweep_values=np.linspace(0.25, 4.0, 8),
    metric_names=["x", "y", "total"],
    initial_guess=np.array([1.0, 0.75], dtype=float),
    mode="path",
)

plotter = FigurePlotter()
figure = plotter.plot_1d(
    result,
    metrics=["x", "y", "total"],
    title="Demo Equilibrium Sweep",
    xlabel="curvature",
)
output_path = plotter.save(figure, Path("output/demo_equilibrium_sweep.png"))
print(f"Saved: {output_path}")
