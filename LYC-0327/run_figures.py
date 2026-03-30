"""LYC-0327: 生成 5 张利润对比图。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt

import numpy as np

from two_period import TwoPeriodModel
from equilibrium.plotting import SweepResult1D, sweep_1d
from equilibrium.solvers import CompositeSolver, RobustGuessSolver, ScipyRootSolver

OUTPUT_DIR = Path(__file__).parent / "figures"
OUTPUT_DIR.mkdir(exist_ok=True)

METRICS = (
    "profit_insider",
    "profit_informed_mm",
    "profit_uninformed_mm",
    "Gamma",
    "profit_mm_diff",
)
LABELS = {
    "profit_insider": "Insider",
    "profit_informed_mm": "Informed MM",
    "profit_uninformed_mm": "Uninformed MM",
    "Gamma": r"$\Gamma$ (Noise Trader Loss)",
    "profit_mm_diff": "Informed MM - Uninformed MM",
}

BASE_PARAMS = {
    "J_I": 15.0,
    "J_U": 15.0,
    "sigma_v2": 1.0,
    "sigma_u2": 0.05,
    "sigma_epsilon2": 1.0,
    "sigma_eta2": 1.0,
    "rho": 0.5,
}

INITIAL_GUESS = np.array(
    [0.8, 0.9, 0.1, 0.4, 0.05, 0.35, 0.02, 0.03, 0.25, 0.2, 0.04],
    dtype=float,
)


def make_solver() -> RobustGuessSolver:
    return RobustGuessSolver(
        CompositeSolver(
            [
                ScipyRootSolver(method="hybr", require_constraints=True),
                ScipyRootSolver(method="lm", require_constraints=True),
                ScipyRootSolver(method="hybr", require_constraints=False),
                ScipyRootSolver(method="lm", require_constraints=False),
            ]
        ),
        noise_scale=0.1,
        noise_attempts=3,
        random_attempts=2,
    )


GROUP_SMALL = (
    "profit_informed_mm",
    "profit_uninformed_mm",
    "profit_mm_diff",
)
GROUP_LARGE = ("profit_insider", "Gamma")


def _group_range(
    results: dict[str, np.ndarray], keys: tuple[str, ...], expand: float = 0.10
) -> tuple[float, float]:
    vals = np.concatenate([results[k] for k in keys])
    vals = vals[np.isfinite(vals)]
    lo, hi = float(vals.min()), float(vals.max())
    margin = (hi - lo) * expand if hi != lo else abs(lo) * expand or 0.1
    return lo - margin, hi + margin


def plot_profit_curves_rescaled(
    x_values: np.ndarray,
    results: dict[str, np.ndarray],
    xlabel: str,
    title: str,
    filename: str,
) -> None:
    lo_s, hi_s = _group_range(results, GROUP_SMALL)
    lo_l, hi_l = _group_range(results, GROUP_LARGE)

    V_S_LO, V_S_HI = 0.0, 0.48
    V_L_LO, V_L_HI = 0.52, 1.0

    def to_visual(y: np.ndarray, group: str) -> np.ndarray:
        y = np.asarray(y, dtype=float)
        if group == "small":
            frac = (y - lo_s) / (hi_s - lo_s) if hi_s != lo_s else np.full_like(y, 0.5)
            return V_S_LO + frac * (V_S_HI - V_S_LO)
        else:
            frac = (y - lo_l) / (hi_l - lo_l) if hi_l != lo_l else np.full_like(y, 0.5)
            return V_L_LO + frac * (V_L_HI - V_L_LO)

    fig, ax = plt.subplots(figsize=(10, 6))

    for m in METRICS:
        grp = "small" if m in GROUP_SMALL else "large"
        y_raw = results[m]
        y_vis = to_visual(y_raw, grp)

        ax.plot(x_values, y_vis, marker=".", markersize=3, label=LABELS[m])

        valid = np.isfinite(y_raw)
        if valid.any():
            idx_max = int(np.nanargmax(y_raw))
            idx_min = int(np.nanargmin(y_raw))
            ax.plot(
                x_values[idx_max],
                y_vis[idx_max],
                "o",
                color="red",
                markersize=7,
                zorder=5,
            )
            ax.plot(
                x_values[idx_min],
                y_vis[idx_min],
                "o",
                color="blue",
                markersize=7,
                zorder=5,
            )

    # break mark
    brk_y = (V_S_HI + V_L_LO) / 2
    d = 0.008
    for xf in (0.0, 1.0):
        ax.plot(
            [xf - 0.015, xf + 0.015],
            [brk_y - d, brk_y + d],
            transform=ax.transAxes,
            color="k",
            clip_on=False,
            linewidth=1.2,
        )
        ax.plot(
            [xf - 0.015, xf + 0.015],
            [brk_y - 2 * d, brk_y],
            transform=ax.transAxes,
            color="k",
            clip_on=False,
            linewidth=1.2,
        )

    n_ticks = 6
    ticks_s = np.linspace(lo_s, hi_s, n_ticks)
    ticks_l = np.linspace(lo_l, hi_l, n_ticks)
    pos_s = to_visual(ticks_s, "small")
    pos_l = to_visual(ticks_l, "large")

    all_pos = np.concatenate([pos_s, pos_l])
    all_labels: list[str] = [f"{v:.4f}" for v in ticks_s] + [
        f"{v:.4f}" for v in ticks_l
    ]

    ax.set_yticks(all_pos)
    ax.set_yticklabels(all_labels, fontsize=8)
    ax.set_ylim(-0.04, 1.04)
    ax.yaxis.grid(True, linestyle="--", alpha=0.3)
    ax.xaxis.grid(True, linestyle="--", alpha=0.3)

    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel("Expected Profit", fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.legend(fontsize=8, framealpha=0.5, loc="best")
    fig.tight_layout()

    path = OUTPUT_DIR / filename
    fig.savefig(path, dpi=200)
    plt.close(fig)
    print(f"  Saved: {path}")


def _insert_integers(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    lo, hi = int(np.ceil(values.min())), int(np.floor(values.max()))
    integers = set(range(lo, hi + 1))
    merged = sorted(set(values.tolist()) | {float(i) for i in integers})
    arr = np.array(merged)
    mask = np.array([x == int(x) and int(x) in integers for x in merged])
    return arr, mask


def _extract_metrics(
    result: SweepResult1D,
    mask: np.ndarray | None = None,
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Extract sweep_values and metric arrays, optionally filtered by mask."""
    x = result.sweep_values
    metrics = {m: result.metric_series(m) for m in METRICS}
    if mask is not None:
        x = x[mask]
        metrics = {m: v[mask] for m, v in metrics.items()}
    return x, metrics


def _run_sweep(
    sweep_param: str,
    sweep_values: np.ndarray,
    *,
    param_modifier=None,
) -> SweepResult1D:
    return sweep_1d(
        system=TwoPeriodModel(),
        solver=make_solver(),
        base_params=BASE_PARAMS,
        sweep_param=sweep_param,
        sweep_values=sweep_values,
        metric_names=list(METRICS),
        initial_guess=INITIAL_GUESS,
        mode="adaptive",
        param_modifier=param_modifier,
    )


def run_single_figure_J(value_values: np.ndarray) -> None:
    total_j = int(np.round(value_values.max()))
    dense_vals, int_mask = _insert_integers(value_values)

    result = _run_sweep(
        "J_I",
        dense_vals,
        param_modifier=lambda p, v: {**p, "J_U": total_j - v},
    )
    x, metrics = _extract_metrics(result, int_mask)

    plot_profit_curves_rescaled(
        x,
        metrics,
        "J_I",
        f"Profits vs J_I (J_I + J_U = {total_j})",
        "fig1_J_I_sweep.png",
    )


def run_single_figure_other(value_param: str, value_values: np.ndarray) -> None:
    result = _run_sweep(value_param, value_values)
    x, metrics = _extract_metrics(result)

    plot_profit_curves_rescaled(
        x,
        metrics,
        value_param,
        f"Profits vs {value_param}",
        f"fig_{value_param}_sweep.png",
    )


if __name__ == "__main__":
    run_single_figure_J(np.linspace(1, 30, 50))
    run_single_figure_other("sigma_epsilon2", np.linspace(0.1, 30, 100))
