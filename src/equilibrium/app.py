"""Application entrypoints."""

from __future__ import annotations

from pathlib import Path
import json

import numpy as np

from equilibrium.models import (
    DemoEquilibriumModel,
    TwoPeriodModel,
    default_two_period_benchmark,
)
from equilibrium.plotting import FigurePlotter, ParameterSweep
from equilibrium.solvers import (
    CompositeSolver,
    ContinuationSolver,
    ScipyRootSolver,
    SolveResult,
)


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
        mode="path",
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


def build_two_period_solver() -> ContinuationSolver:
    """Build the layered solver used for the two-period benchmark."""
    step_solver = CompositeSolver(
        [
            ScipyRootSolver(method="hybr", require_constraints=True),
            ScipyRootSolver(method="lm", require_constraints=True),
        ]
    )
    benchmark = default_two_period_benchmark()
    return ContinuationSolver(
        step_solver,
        acceptance=benchmark.acceptance,
        path_builder=lambda params: benchmark.continuation_path(params),
    )


def run_two_period_benchmark() -> SolveResult:
    """Solve the default two-period benchmark through continuation."""
    benchmark = default_two_period_benchmark()
    system = TwoPeriodModel()
    solver = build_two_period_solver()
    return solver.solve(
        system,
        benchmark.params,
        initial_guess=benchmark.initial_guess,
    )


def run_two_period_analysis(output_dir: str | Path = "output") -> dict[str, Path]:
    """Run a small 2D two-period analysis and persist the results."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    benchmark = default_two_period_benchmark()
    system = TwoPeriodModel()
    solver = build_two_period_solver()
    sweep = ParameterSweep()
    plotter = FigurePlotter()

    rho_values = np.linspace(0.0, benchmark.params["rho"], 5)
    sigma_eta_values = np.linspace(0.45, 0.75, 4)
    result = sweep.sweep_2d(
        system,
        solver,
        base_params=benchmark.params,
        sweep_param_1="rho",
        sweep_values_1=rho_values,
        sweep_param_2="sigma_eta2",
        sweep_values_2=sigma_eta_values,
        metric_names=[
            "profit_insider",
            "profit_informed_mm",
            "profit_uninformed_mm",
        ],
        initial_guess=benchmark.initial_guess,
        mode="path",
    )

    json_path = sweep.save_json(result, output_path / "two_period_sweep_2d.json")
    figure = plotter.plot_2d_heatmap(
        result,
        metric="profit_insider",
        title="Two-Period Model: Insider Profit Heatmap",
        xlabel="sigma_eta2",
        ylabel="rho",
    )
    figure_path = plotter.save(
        figure, output_path / "two_period_profit_insider_heatmap.png"
    )
    summary_path = output_path / "two_period_benchmark_summary.json"
    summary = {
        "benchmark_name": benchmark.name,
        "params": benchmark.params,
        "expected_solution": benchmark.expected_solution.tolist(),
        "success_mask_sum": float(result.success_mask().sum()),
        "failure_count": len(result.failure_points()),
    }
    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=True)

    return {
        "sweep_json": json_path,
        "heatmap_png": figure_path,
        "summary_json": summary_path,
    }


def main() -> None:
    """CLI entrypoint."""
    outputs = run_two_period_analysis()
    print(f"two-period analysis complete: heatmap saved to {outputs['heatmap_png']}")
