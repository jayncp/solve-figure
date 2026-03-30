"""LYC-0327: 生成 5 张利润对比图。"""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt

import numpy as np

from two_period import TwoPeriodModel
from equilibrium.solvers.composite import CompositeSolver
from equilibrium.solvers.scipy_root import ScipyRootSolver

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


def make_solver() -> CompositeSolver:
    return CompositeSolver(
        [
            ScipyRootSolver(method="hybr", require_constraints=True),
            ScipyRootSolver(method="lm", require_constraints=True),
            ScipyRootSolver(method="hybr", require_constraints=False),
            ScipyRootSolver(method="lm", require_constraints=False),
        ]
    )


def _solve_one_direction(
    sweep_param: str,
    sweep_values: np.ndarray,
    extra_param: str | None = None,
    extra_fn: Callable[[float], float] | None = None,
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
                out.append(
                    (result.residual_norm, dict(result.metrics), result.x.copy())
                )
                current_guess = result.x
                success_count += 1
            else:
                out.append((float("inf"), None, None))
        except Exception:
            out.append((float("inf"), None, None))

        if (i + 1) % 10 == 0 or i == len(sweep_values) - 1:
            print(f"  {label}[{i + 1}/{len(sweep_values)}] success: {success_count}")

    return out


def solve_sweep(
    sweep_param: str,
    sweep_values: np.ndarray,
    extra_param: str | None = None,
    extra_fn: Callable[[float], float] | None = None,
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
        y = np.array(results[m])
        ax.plot(x_values, y, marker=".", markersize=3, label=LABELS[m])
        # Mark max (red) and min (blue) for non-NaN values
        valid = np.isfinite(y)
        if valid.any():
            idx_max = np.nanargmax(y)
            idx_min = np.nanargmin(y)
            ax.plot(
                x_values[idx_max], y[idx_max], ".", color="red", markersize=4, zorder=5
            )
            ax.plot(
                x_values[idx_min], y[idx_min], ".", color="blue", markersize=4, zorder=5
            )
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel("Expected Profit", fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.legend(fontsize=8, framealpha=0.5, loc="best")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    path = OUTPUT_DIR / filename
    fig.savefig(path, dpi=200)
    plt.close(fig)
    print(f"  Saved: {path}")


GROUP_SMALL = (
    "profit_informed_mm",
    "profit_uninformed_mm",
    "profit_mm_diff",
)  # MM group (small values, bottom)
GROUP_LARGE = ("profit_insider", "Gamma")  # Insider/Noise group (large values, top)


def _group_range(
    results: dict[str, list[float]], keys: tuple[str, ...], expand: float = 0.10
) -> tuple[float, float]:
    """Return (lo, hi) across all keys, expanded by *expand* fraction on each side."""
    vals = np.concatenate([np.array(results[k]) for k in keys])
    vals = vals[np.isfinite(vals)]
    lo, hi = float(vals.min()), float(vals.max())
    margin = (hi - lo) * expand if hi != lo else abs(lo) * expand or 0.1
    return lo - margin, hi + margin


def plot_profit_curves_rescaled(
    x_values: np.ndarray,
    results: dict[str, list[float]],
    xlabel: str,
    title: str,
    filename: str,
) -> None:
    """Single y-axis with piecewise-linear scaling.

    The MM group (small) occupies the bottom half of the visual space and
    the Insider/Gamma group (large) occupies the top half, with a break
    mark in between.  Tick labels show true values; grid uses dashed lines.
    """
    lo_s, hi_s = _group_range(results, GROUP_SMALL)  # small range (bottom)
    lo_l, hi_l = _group_range(results, GROUP_LARGE)  # large range (top)

    # Each group maps to half the visual height.
    # visual coordinate: small group -> [0, 0.48], gap -> 0.48‥0.52, large group -> [0.52, 1]
    V_S_LO, V_S_HI = 0.0, 0.48
    V_L_LO, V_L_HI = 0.52, 1.0

    def to_visual(y: np.ndarray, group: str) -> np.ndarray:
        """Map original y -> visual coordinate based on group membership."""
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
        y_raw = np.array(results[m])
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

    # ── break mark (diagonal lines at the boundary) ──
    brk_y = (V_S_HI + V_L_LO) / 2
    d = 0.008
    for xf in (0.0, 1.0):  # on both spines
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

    # ── non-uniform y-axis ticks ──
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
    """Merge range-interior integers into *values*.

    Returns (merged_sorted, is_integer_mask).  The mask marks which entries
    are integers (suitable for filtering after solving).
    """
    lo, hi = int(np.ceil(values.min())), int(np.floor(values.max()))
    integers = set(range(lo, hi + 1))
    merged = sorted(set(values.tolist()) | {float(i) for i in integers})
    arr = np.array(merged)
    mask = np.array([x == int(x) and int(x) in integers for x in merged])
    return arr, mask


def _filter_by_mask(
    x_all: np.ndarray,
    res_all: dict[str, list[float]],
    mask: np.ndarray,
) -> tuple[np.ndarray, dict[str, list[float]]]:
    """Keep only the points where *mask* is True."""
    return x_all[mask], {
        m: [v for v, keep in zip(res_all[m], mask) if keep] for m in res_all
    }


def run_single_figure_J(value_values: np.ndarray) -> None:
    total_j = int(np.round(value_values.max()))
    dense_vals, int_mask = _insert_integers(value_values)
    x_all, res_all = solve_sweep(
        "J_I",
        dense_vals,
        extra_param="J_U",
        extra_fn=lambda j: total_j - j,
        bidirectional=True,
    )
    x, res = _filter_by_mask(x_all, res_all, int_mask)
    plot_profit_curves_rescaled(
        x,
        res,
        "J_I",
        f"Profits vs J_I (J_I + J_U = {total_j})",
        "fig1_J_I_sweep.png",
    )


def run_single_figure_other(value_param: str, value_values: np.ndarray) -> None:
    x, res = solve_sweep(value_param, value_values, bidirectional=True)
    plot_profit_curves_rescaled(
        x, res, value_param, f"Profits vs {value_param}", f"fig_{value_param}_sweep.png"
    )


if __name__ == "__main__":
    run_single_figure_J(np.linspace(1, 30, 50))
    run_single_figure_other("sigma_epsilon2", np.linspace(0.1, 30, 100))
