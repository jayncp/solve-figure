"""Sweep rho across parameter combinations to find non-monotonic MM profits.

Improvements over naive version:
- Tracks solver residual norms; merges forward/reverse by smaller residual.
- Filters non-monotonicity by relative variation threshold (default 2%).
- Applies light Savitzky-Golay smoothing before checking monotonicity,
  so tiny solver jitter doesn't trigger false positives.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt

import numpy as np

from two_period import TwoPeriodModel
from equilibrium.solvers.composite import CompositeSolver
from equilibrium.solvers.scipy_root import ScipyRootSolver

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

INITIAL_GUESS = np.array(
    [0.8, 0.9, 0.1, 0.4, 0.05, 0.35, 0.02, 0.03, 0.25, 0.2, 0.04],
    dtype=float,
)

# Reject solutions whose residual norm exceeds this — they are spurious
# local minima of ||F(x)||² rather than actual roots F(x)=0.
RESIDUAL_ACCEPT = 1e-6

RHO_VALUES = np.linspace(0.01, 0.99, 120)

BASE_PARAMS = {
    "J_I": 10.0,
    "J_U": 10.0,
    "sigma_v2": 1.0,
    "sigma_u2": 1.0,
    "sigma_epsilon2": 1.0,
    "sigma_eta2": 1.0,
}

EXTREME_VALUES = {
    "J_I": (2.0, 50.0),
    "J_U": (2.0, 50.0),
    "sigma_v2": (0.1, 50.0),
    "sigma_u2": (0.1, 50.0),
    "sigma_epsilon2": (0.1, 50.0),
    "sigma_eta2": (0.1, 50.0),
}

# EXTREME_VALUES = {
#     "sigma_epsilon2": (0.1, 25.0),
# }

# Relative variation threshold: (max-min)/mean must exceed this to count.
REL_VAR_THRESHOLD = 0.01  # 2%


def build_combos() -> list[tuple[str, dict[str, float]]]:
    """Base + 12 single-parameter-extreme combos = 13 total."""
    combos: list[tuple[str, dict[str, float]]] = []
    combos.append(("base", dict(BASE_PARAMS)))
    for name, (small, large) in EXTREME_VALUES.items():
        for val in [small, large]:
            p = dict(BASE_PARAMS)
            p[name] = val
            combos.append((f"{name}={val:g}", p))
    return combos


def make_solver() -> CompositeSolver:
    return CompositeSolver(
        [
            ScipyRootSolver(method="hybr", require_constraints=True),
            ScipyRootSolver(method="lm", require_constraints=True),
            ScipyRootSolver(method="hybr", require_constraints=False),
            ScipyRootSolver(method="lm", require_constraints=False),
        ]
    )


@dataclass
class PointResult:
    informed: float
    uninformed: float
    residual: float
    x: np.ndarray | None


def _sweep_one_dir(
    params_base: dict[str, float], rho_arr: np.ndarray
) -> list[PointResult]:
    model = TwoPeriodModel()
    solver = make_solver()
    g = INITIAL_GUESS.copy()
    out: list[PointResult] = []
    for rho in rho_arr:
        p = dict(params_base, rho=float(rho))
        try:
            r = solver.solve(
                model,
                p,
                initial_guess=g,
                options={"use_jacobian": True, "xtol": 1e-15},
            )
            if r.success and r.residual_norm < RESIDUAL_ACCEPT:
                out.append(
                    PointResult(
                        informed=r.metrics.get("profit_informed_mm", float("nan")),
                        uninformed=r.metrics.get("profit_uninformed_mm", float("nan")),
                        residual=r.residual_norm,
                        x=r.x.copy(),
                    )
                )
                g = r.x
            else:
                out.append(PointResult(float("nan"), float("nan"), float("inf"), None))
        except Exception:
            out.append(PointResult(float("nan"), float("nan"), float("inf"), None))
    return out


def solve_rho_sweep(
    params_base: dict[str, float],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return (rho, informed, uninformed, residuals)."""
    fwd = _sweep_one_dir(params_base, RHO_VALUES)
    rev_raw = _sweep_one_dir(params_base, RHO_VALUES[::-1])
    rev = list(reversed(rev_raw))

    informed = np.empty(len(RHO_VALUES))
    uninformed = np.empty(len(RHO_VALUES))
    residuals = np.empty(len(RHO_VALUES))

    for k in range(len(RHO_VALUES)):
        f, r = fwd[k], rev[k]
        f_ok = np.isfinite(f.informed)
        r_ok = np.isfinite(r.informed)
        if f_ok and r_ok:
            pick = f if f.residual <= r.residual else r
        elif r_ok:
            pick = r
        else:
            pick = f
        informed[k] = pick.informed
        uninformed[k] = pick.uninformed
        residuals[k] = pick.residual

    return RHO_VALUES, informed, uninformed, residuals


def _savgol_smooth(y: np.ndarray, window: int = 11, poly: int = 3) -> np.ndarray:
    """Simple Savitzky-Golay smoothing (no scipy dependency, uses polyfit)."""
    valid = np.isfinite(y)
    if valid.sum() < window:
        return y.copy()
    out = y.copy()
    half = window // 2
    np.where(valid)[0]
    yv = y[valid]
    # Smooth only the valid portion
    smoothed = np.empty_like(yv)
    for i in range(len(yv)):
        lo = max(0, i - half)
        hi = min(len(yv), i + half + 1)
        if hi - lo < poly + 1:
            smoothed[i] = yv[i]
            continue
        x_loc = np.arange(hi - lo, dtype=float)
        coeffs = np.polyfit(x_loc, yv[lo:hi], min(poly, hi - lo - 1))
        smoothed[i] = np.polyval(coeffs, float(i - lo))
    out[valid] = smoothed
    return out


def relative_variation(y: np.ndarray) -> float:
    """(max - min) / |mean|, ignoring NaN."""
    v = y[np.isfinite(y)]
    if len(v) == 0:
        return 0.0
    mean = np.abs(np.mean(v))
    if mean < 1e-15:
        return 0.0
    return float((v.max() - v.min()) / mean)


def is_non_monotonic_robust(
    y: np.ndarray, threshold: float = REL_VAR_THRESHOLD
) -> tuple[bool, float]:
    """Check non-monotonicity on smoothed data with relative variation gate.

    Returns (is_non_monotonic, relative_variation_pct).
    """
    rv = relative_variation(y)
    if rv < threshold:
        return False, rv

    ys = _savgol_smooth(y)
    valid = ys[np.isfinite(ys)]
    if len(valid) < 3:
        return False, rv
    diffs = np.diff(valid)
    diffs = diffs[diffs != 0]
    if len(diffs) < 2:
        return False, rv
    signs = np.sign(diffs)
    changes = np.diff(signs)
    return bool(np.any(changes != 0)), rv


def _expand_range(lo: float, hi: float, frac: float = 0.10) -> tuple[float, float]:
    margin = (hi - lo) * frac if hi != lo else abs(lo) * frac or 0.1
    return lo - margin, hi + margin


def plot_case(
    rho: np.ndarray,
    informed: np.ndarray,
    uninformed: np.ndarray,
    residuals: np.ndarray,
    label: str,
    tag: str,
    nm_which: list[str],
) -> Path:
    """Piecewise-linear y-axis: each curve gets half the visual space."""
    yi, yu = informed, uninformed

    # per-curve ranges (ignoring NaN)
    vi = yi[np.isfinite(yi)]
    vu = yu[np.isfinite(yu)]
    lo_i, hi_i = _expand_range(float(vi.min()), float(vi.max()))
    lo_u, hi_u = _expand_range(float(vu.min()), float(vu.max()))

    # visual bands: uninformed [0, 0.48], informed [0.52, 1.0]
    V_U_LO, V_U_HI = 0.0, 0.48
    V_I_LO, V_I_HI = 0.52, 1.0

    def to_vis(y: np.ndarray, lo: float, hi: float, vlo: float, vhi: float) -> np.ndarray:
        frac = (y - lo) / (hi - lo) if hi != lo else np.full_like(y, 0.5)
        return vlo + frac * (vhi - vlo)

    fig, ax = plt.subplots(figsize=(10, 6))

    # Informed (top)
    yv_i = to_vis(yi, lo_i, hi_i, V_I_LO, V_I_HI)
    ax.plot(rho, yv_i, marker=".", markersize=2, label="Informed MM", color="#1f77b4")
    # Uninformed (bottom)
    yv_u = to_vis(yu, lo_u, hi_u, V_U_LO, V_U_HI)
    ax.plot(rho, yv_u, marker=".", markersize=2, label="Uninformed MM", color="#ff7f0e")

    # Mark max/min
    for yraw, yvis in [(yi, yv_i), (yu, yv_u)]:
        valid = np.isfinite(yraw)
        if valid.any():
            idx_max = int(np.nanargmax(yraw))
            idx_min = int(np.nanargmin(yraw))
            ax.plot(rho[idx_max], yvis[idx_max], "o", color="red", markersize=7, zorder=5)
            ax.plot(rho[idx_min], yvis[idx_min], "o", color="blue", markersize=7, zorder=5)

    # Break mark
    brk_y = (V_U_HI + V_I_LO) / 2
    d = 0.008
    for xf in (0.0, 1.0):
        ax.plot([xf - 0.015, xf + 0.015], [brk_y - d, brk_y + d],
                transform=ax.transAxes, color="k", clip_on=False, linewidth=1.2)
        ax.plot([xf - 0.015, xf + 0.015], [brk_y - 2 * d, brk_y],
                transform=ax.transAxes, color="k", clip_on=False, linewidth=1.2)

    # Non-uniform y ticks
    n_ticks = 6
    ticks_u = np.linspace(lo_u, hi_u, n_ticks)
    ticks_i = np.linspace(lo_i, hi_i, n_ticks)
    pos_u = to_vis(ticks_u, lo_u, hi_u, V_U_LO, V_U_HI)
    pos_i = to_vis(ticks_i, lo_i, hi_i, V_I_LO, V_I_HI)

    all_pos = np.concatenate([pos_u, pos_i])
    all_labels = [f"{v:.6f}" for v in ticks_u] + [f"{v:.6f}" for v in ticks_i]
    all_colors = ["#ff7f0e"] * n_ticks + ["#1f77b4"] * n_ticks

    ax.set_yticks(all_pos)
    ax.set_yticklabels(all_labels, fontsize=7)
    for lbl, col in zip(ax.get_yticklabels(), all_colors):
        lbl.set_color(col)

    ax.set_ylim(-0.04, 1.04)
    ax.yaxis.grid(True, linestyle="--", alpha=0.3)
    ax.xaxis.grid(True, linestyle="--", alpha=0.3)

    ax.set_xlabel(r"$\rho$", fontsize=12)
    ax.set_ylabel("Expected Profit", fontsize=12)
    nm_str = ", ".join(nm_which)
    ax.set_title(f"MM Profits vs rho  |  {label}\nnon-monotonic: {nm_str}", fontsize=10)
    ax.legend(fontsize=10, loc="best")
    fig.tight_layout()

    path = OUTPUT_DIR / f"rho_sweep_{tag}.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def main() -> None:
    combos = build_combos()
    total = len(combos)
    print(f"Total combinations: {total}")
    print(f"Relative variation threshold: {REL_VAR_THRESHOLD:.0%}\n")

    cases: list[dict] = []

    for ci, (label, params) in enumerate(combos):
        tag = (
            label.replace("=", "").replace(".", "p").replace(",", "_").replace(" ", "")
        )
        print(f"[{ci + 1}/{total}] {label}")

        rho, informed, uninformed, residuals = solve_rho_sweep(params)
        n_valid = int(np.sum(np.isfinite(informed)))
        max_res = (
            float(np.nanmax(residuals[np.isfinite(residuals)]))
            if n_valid > 0
            else float("inf")
        )

        nm_i, rv_i = is_non_monotonic_robust(informed)
        nm_u, rv_u = is_non_monotonic_robust(uninformed)

        which: list[str] = []
        if nm_i:
            which.append("informed")
        if nm_u:
            which.append("uninformed")

        status = "NON-MONOTONIC" if which else "monotonic/flat"
        print(
            f"    valid={n_valid}  max_residual={max_res:.2e}"
            f"  informed_rv={rv_i:.4%}  uninformed_rv={rv_u:.4%}  → {status}"
        )

        fig_path = None
        if which:
            fig_path = plot_case(
                rho, informed, uninformed, residuals, label, tag, which
            )
            print(f"    ** {status} [{', '.join(which)}]")

        cases.append(
            {
                "label": label,
                "params": dict(params),
                "n_valid": n_valid,
                "max_residual": max_res,
                "nm_informed": nm_i,
                "nm_uninformed": nm_u,
                "rv_informed": rv_i,
                "rv_uninformed": rv_u,
                "which": which,
                "fig": fig_path.name if fig_path else None,
                "informed_range": (
                    float(np.nanmin(informed)),
                    float(np.nanmax(informed)),
                )
                if n_valid
                else None,
                "uninformed_range": (
                    float(np.nanmin(uninformed)),
                    float(np.nanmax(uninformed)),
                )
                if n_valid
                else None,
            }
        )

    nm_cases = [c for c in cases if c["which"]]

    # ── Write report ──
    report_path = OUTPUT_DIR / "non_monotonic_report.md"
    with open(report_path, "w") as f:
        f.write("# Non-monotonic MM Profit Cases (rho sweep)\n\n")
        f.write(f"- Total combinations tested: {total}\n")
        f.write(f"- Relative variation threshold: {REL_VAR_THRESHOLD:.0%}\n")
        f.write(f"- Non-monotonic cases (after filtering): **{len(nm_cases)}**\n\n")

        f.write("## Strategy\n\n")
        f.write("One parameter deviates at a time; others stay at base.  \n")
        f.write(
            "Non-monotonicity is checked on Savitzky-Golay smoothed data, "
            "only when relative variation (max-min)/|mean| exceeds the threshold.\n\n"
        )

        f.write("## Parameter settings\n\n")
        f.write("| Parameter | Base | Small | Large |\n")
        f.write("|-----------|------|-------|-------|\n")
        for name, (small, large) in EXTREME_VALUES.items():
            f.write(f"| {name} | {BASE_PARAMS[name]:g} | {small:g} | {large:g} |\n")
        f.write("\n")

        # Full summary table
        f.write("## Full results\n\n")
        f.write(
            "| Config | Valid | Max Residual | Informed RV | Uninformed RV | Non-monotonic |\n"
        )
        f.write(
            "|--------|-------|-------------|-------------|---------------|---------------|\n"
        )
        for c in cases:
            nm_str = ", ".join(c["which"]) if c["which"] else "-"
            f.write(
                f"| {c['label']} | {c['n_valid']}/{len(RHO_VALUES)} "
                f"| {c['max_residual']:.2e} "
                f"| {c['rv_informed']:.3%} "
                f"| {c['rv_uninformed']:.3%} "
                f"| {nm_str} |\n"
            )
        f.write("\n")

        if not nm_cases:
            f.write("**No genuinely non-monotonic cases found above the threshold.**\n")
        else:
            f.write("## Non-monotonic cases (detail)\n\n")
            for i, case in enumerate(nm_cases, 1):
                f.write(f"### Case {i}: {case['label']}\n\n")
                f.write("| Parameter | Value |\n")
                f.write("|-----------|-------|\n")
                for k, v in case["params"].items():
                    marker = " *" if v != BASE_PARAMS.get(k) else ""
                    f.write(f"| {k} | {v:g}{marker} |\n")
                f.write("\n")
                f.write(f"- Non-monotonic in: **{', '.join(case['which'])}**\n")
                f.write(f"- Valid points: {case['n_valid']}/{len(RHO_VALUES)}\n")
                f.write(f"- Max solver residual: {case['max_residual']:.2e}\n")
                f.write(f"- Informed relative variation: {case['rv_informed']:.3%}\n")
                f.write(
                    f"- Uninformed relative variation: {case['rv_uninformed']:.3%}\n"
                )
                if case["informed_range"]:
                    lo, hi = case["informed_range"]
                    f.write(f"- Informed profit range: [{lo:.6f}, {hi:.6f}]\n")
                if case["uninformed_range"]:
                    lo, hi = case["uninformed_range"]
                    f.write(f"- Uninformed profit range: [{lo:.6f}, {hi:.6f}]\n")
                f.write(f"- Figure: `{case['fig']}`\n\n")

    print(f"\nReport: {report_path}")
    print(f"Genuine non-monotonic: {len(nm_cases)} / {total}")


if __name__ == "__main__":
    main()
