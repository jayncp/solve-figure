"""LYC-0327: 生成 5 张利润对比图。"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.figure import Figure

import numpy as np

from equilibrium.models.two_period import TwoPeriodModel
from equilibrium.solvers.composite import CompositeSolver
from equilibrium.solvers.scipy_root import ScipyRootSolver

OUTPUT_DIR = Path(__file__).parent

METRICS = ("profit_informed_mm", "profit_uninformed_mm")
LABELS = {"profit_informed_mm": "Informed MM", "profit_uninformed_mm": "Uninformed MM"}

BASE_PARAMS = {
    "J_I": 15.0,
    "J_U": 15.0,
    "sigma_v2": 1.0,
    "sigma_u2": 1.0,
    "sigma_epsilon2": 1.0,
    "sigma_eta2": 1.0,
    "rho": 0.5,
}

INITIAL_GUESS = np.array(
    [0.8, 0.9, 0.1, 0.4, 0.05, 0.35, 0.02, 0.03, 0.25, 0.2, 0.04],
    dtype=float,
)


def make_solver() -> CompositeSolver:
    return CompositeSolver([
        ScipyRootSolver(method="hybr", require_constraints=True),
        ScipyRootSolver(method="lm", require_constraints=True),
        ScipyRootSolver(method="hybr", require_constraints=False),
        ScipyRootSolver(method="lm", require_constraints=False),
    ])


def _solve_one_direction(
    sweep_param: str,
    sweep_values: np.ndarray,
    extra_param: str | None = None,
    extra_fn: object = None,
    label: str = "",
) -> list[tuple[float, dict[str, float] | None, np.ndarray | None]]:
    """Solve along one direction with warm start.

    Returns list of (residual, metrics_dict_or_None, solution_x_or_None) per point.
    """
    model = TwoPeriodModel()
    solver = make_solver()
    current_guess = INITIAL_GUESS.copy()
    out: list[tuple[float, dict[str, float] | None, np.ndarray | None]] = []
    success_count = 0

    for i, val in enumerate(sweep_values):
        params = dict(BASE_PARAMS)
        params[sweep_param] = float(val)
        if extra_param and extra_fn:
            params[extra_param] = float(extra_fn(val))

        try:
            result = solver.solve(model, params, initial_guess=current_guess)
            if result.success:
                out.append((result.residual_norm, dict(result.metrics), result.x.copy()))
                current_guess = result.x
                success_count += 1
            else:
                out.append((float("inf"), None, None))
        except Exception:
            out.append((float("inf"), None, None))

        if (i + 1) % 10 == 0 or i == len(sweep_values) - 1:
            print(f"  {label}[{i+1}/{len(sweep_values)}] success: {success_count}")

    return out


def solve_sweep(
    sweep_param: str,
    sweep_values: np.ndarray,
    extra_param: str | None = None,
    extra_fn: object = None,
    bidirectional: bool = False,
) -> tuple[np.ndarray, dict[str, list[float]]]:
    """Solve along a parameter path with warm start.

    If bidirectional=True, sweep both forward and reverse, then merge
    taking the result with smaller residual at each point.
    """
    fwd = _solve_one_direction(
        sweep_param, sweep_values, extra_param, extra_fn, label="fwd"
    )

    if bidirectional:
        rev_raw = _solve_one_direction(
            sweep_param, sweep_values[::-1], extra_param, extra_fn, label="rev"
        )
        rev = list(reversed(rev_raw))

        merged: list[tuple[float, dict[str, float] | None, np.ndarray | None]] = []
        for f, r in zip(fwd, rev):
            if f[1] is not None and r[1] is not None:
                merged.append(f if f[0] <= r[0] else r)
            elif f[1] is not None:
                merged.append(f)
            elif r[1] is not None:
                merged.append(r)
            else:
                merged.append(f)
        fwd = merged

        n_success = sum(1 for x in fwd if x[1] is not None)
        print(f"  merged: {n_success}/{len(fwd)} success")

    results: dict[str, list[float]] = {m: [] for m in METRICS}
    for _, metrics, _ in fwd:
        if metrics is not None:
            for m in METRICS:
                results[m].append(metrics.get(m, float("nan")))
        else:
            for m in METRICS:
                results[m].append(float("nan"))

    return sweep_values, results


def plot_profit_curves(
    x_values: np.ndarray,
    results: dict[str, list[float]],
    xlabel: str,
    title: str,
    filename: str,
) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))
    for m in METRICS:
        ax.plot(x_values, results[m], marker=".", markersize=3, label=LABELS[m])
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel("Expected Profit", fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    path = OUTPUT_DIR / filename
    fig.savefig(path, dpi=200)
    plt.close(fig)
    print(f"  Saved: {path}")


def run_all() -> None:
    # ── 图 1: J_I 变化, J_I + J_U = 30 ──
    print("=" * 60)
    print("Fig 1: J_I sweep (J_I + J_U = 30)")
    print("=" * 60)
    j_values = np.arange(1, 30, dtype=float)
    x, res = solve_sweep("J_I", j_values, extra_param="J_U", extra_fn=lambda j: 30 - j, bidirectional=True)
    plot_profit_curves(x, res, "J_I", "Profits vs J_I (J_I + J_U = 30)", "fig1_J_I_sweep.png")

    # ── 图 2: sigma_epsilon2 变化 ──
    print("=" * 60)
    print("Fig 2: sigma_epsilon2 sweep")
    print("=" * 60)
    x, res = solve_sweep("sigma_epsilon2", np.linspace(0.1, 30, 100), bidirectional=True)
    plot_profit_curves(x, res, r"$\sigma_\epsilon^2$", r"Profits vs $\sigma_\epsilon^2$", "fig2_sigma_epsilon2_sweep.png")

    # ── 图 3: sigma_eta2 变化 ──
    print("=" * 60)
    print("Fig 3: sigma_eta2 sweep")
    print("=" * 60)
    x, res = solve_sweep("sigma_eta2", np.linspace(0.1, 30, 100))
    plot_profit_curves(x, res, r"$\sigma_\eta^2$", r"Profits vs $\sigma_\eta^2$", "fig3_sigma_eta2_sweep.png")

    # ── 图 4: sigma_u2 变化 ──
    print("=" * 60)
    print("Fig 4: sigma_u2 sweep")
    print("=" * 60)
    x, res = solve_sweep("sigma_u2", np.linspace(0.1, 30, 100))
    plot_profit_curves(x, res, r"$\sigma_u^2$", r"Profits vs $\sigma_u^2$", "fig4_sigma_u2_sweep.png")

    # ── 图 5: rho 变化 ──
    print("=" * 60)
    print("Fig 5: rho sweep")
    print("=" * 60)
    x, res = solve_sweep("rho", np.linspace(0.01, 0.99, 100))
    plot_profit_curves(x, res, r"$\rho$", r"Profits vs $\rho$", "fig5_rho_sweep.png")

    print("\nAll figures complete.")


if __name__ == "__main__":
    run_all()
