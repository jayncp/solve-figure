"""Parameter sweep helpers."""

from __future__ import annotations

import warnings
from collections.abc import Callable
from dataclasses import dataclass, replace
import json
from pathlib import Path
from typing import Literal, TypeAlias

import numpy as np

from equilibrium.models.base import EquationSystem, NDArrayFloat, Params
from equilibrium.solvers.base import (
    SolveResult,
    SolverFailure,
    SolverStrategy,
    build_solve_result,
)
from equilibrium.utils.validation import to_float_array

SweepMode: TypeAlias = Literal["independent", "path", "adaptive"]


@dataclass(slots=True, frozen=True)
class SweepPoint:
    """One point in a parameter sweep."""

    index: int
    sweep_value: float
    params: Params
    initial_guess: NDArrayFloat | None
    result: SolveResult


@dataclass(slots=True)
class SweepFailurePoint:
    """Failure summary for one sweep point."""

    index: int
    sweep_value: float
    method: str
    message: str
    residual_norm: float


@dataclass(slots=True)
class SweepResult1D:
    """Results from a one-dimensional sweep."""

    mode: SweepMode
    sweep_param: str
    sweep_values: NDArrayFloat
    metric_names: tuple[str, ...]
    points: tuple[SweepPoint, ...]

    def metric_series(self, metric_name: str) -> NDArrayFloat:
        """Return a metric series aligned with sweep_values, filling failures with NaN."""
        if metric_name not in self.metric_names:
            raise KeyError(f"Unknown metric '{metric_name}'")
        values = [
            point.result.metrics.get(metric_name, float("nan"))
            if point.result.success
            else float("nan")
            for point in self.points
        ]
        return np.asarray(values, dtype=float)

    def constraints_mask(self) -> NDArrayFloat:
        """Return a float mask with 1.0 when constraints are satisfied and 0.0 otherwise."""
        values = [1.0 if point.result.constraints_ok else 0.0 for point in self.points]
        return np.asarray(values, dtype=float)

    def success_mask(self) -> NDArrayFloat:
        """Return a float mask with 1.0 for successful points and 0.0 otherwise."""
        values = [1.0 if point.result.success else 0.0 for point in self.points]
        return np.asarray(values, dtype=float)

    def failure_points(self) -> tuple[SweepFailurePoint, ...]:
        """Return a compact list of failed points for diagnostics."""
        failures = [
            SweepFailurePoint(
                index=point.index,
                sweep_value=point.sweep_value,
                method=point.result.method,
                message=point.result.message,
                residual_norm=point.result.residual_norm,
            )
            for point in self.points
            if not point.result.success
        ]
        return tuple(failures)

    def to_dict(self) -> dict[str, object]:
        """Serialize the sweep result into a JSON-friendly structure."""
        return {
            "kind": "sweep_1d",
            "mode": self.mode,
            "sweep_param": self.sweep_param,
            "sweep_values": self.sweep_values.tolist(),
            "metric_names": list(self.metric_names),
            "points": [
                {
                    "index": point.index,
                    "sweep_value": point.sweep_value,
                    "params": point.params,
                    "initial_guess": None
                    if point.initial_guess is None
                    else point.initial_guess.tolist(),
                    "success": point.result.success,
                    "constraints_ok": point.result.constraints_ok,
                    "residual_norm": point.result.residual_norm,
                    "method": point.result.method,
                    "message": point.result.message,
                    "metrics": point.result.metrics,
                    "constraints": point.result.constraints,
                }
                for point in self.points
            ],
        }


@dataclass(slots=True)
class SweepPoint2D:
    """One point in a two-dimensional parameter sweep."""

    row_index: int
    col_index: int
    sweep_value_1: float
    sweep_value_2: float
    params: Params
    initial_guess: NDArrayFloat | None
    result: SolveResult


@dataclass(slots=True)
class SweepFailurePoint2D:
    """Failure summary for one point in a 2D sweep."""

    row_index: int
    col_index: int
    sweep_value_1: float
    sweep_value_2: float
    method: str
    message: str
    residual_norm: float


@dataclass(slots=True)
class SweepResult2D:
    """Results from a two-dimensional sweep."""

    mode: SweepMode
    sweep_param_1: str
    sweep_values_1: NDArrayFloat
    sweep_param_2: str
    sweep_values_2: NDArrayFloat
    metric_names: tuple[str, ...]
    points: tuple[SweepPoint2D, ...]

    def metric_grid(self, metric_name: str) -> NDArrayFloat:
        """Return a metric grid shaped as (len(sweep_values_1), len(sweep_values_2))."""
        if metric_name not in self.metric_names:
            raise KeyError(f"Unknown metric '{metric_name}'")
        grid = np.full(
            (len(self.sweep_values_1), len(self.sweep_values_2)), np.nan, dtype=float
        )
        for point in self.points:
            if point.result.success:
                grid[point.row_index, point.col_index] = point.result.metrics.get(
                    metric_name, float("nan")
                )
        return grid

    def success_mask(self) -> NDArrayFloat:
        """Return a 2D float mask with 1.0 for successful points and 0.0 otherwise."""
        grid = np.zeros(
            (len(self.sweep_values_1), len(self.sweep_values_2)), dtype=float
        )
        for point in self.points:
            grid[point.row_index, point.col_index] = (
                1.0 if point.result.success else 0.0
            )
        return grid

    def constraints_mask(self) -> NDArrayFloat:
        """Return a 2D float mask with 1.0 when constraints are satisfied."""
        grid = np.zeros(
            (len(self.sweep_values_1), len(self.sweep_values_2)), dtype=float
        )
        for point in self.points:
            grid[point.row_index, point.col_index] = (
                1.0 if point.result.constraints_ok else 0.0
            )
        return grid

    def failure_points(self) -> tuple[SweepFailurePoint2D, ...]:
        """Return a compact list of failed points for diagnostics."""
        failures = [
            SweepFailurePoint2D(
                row_index=point.row_index,
                col_index=point.col_index,
                sweep_value_1=point.sweep_value_1,
                sweep_value_2=point.sweep_value_2,
                method=point.result.method,
                message=point.result.message,
                residual_norm=point.result.residual_norm,
            )
            for point in self.points
            if not point.result.success
        ]
        return tuple(failures)

    def to_dict(self) -> dict[str, object]:
        """Serialize the 2D sweep result into a JSON-friendly structure."""
        return {
            "kind": "sweep_2d",
            "mode": self.mode,
            "sweep_param_1": self.sweep_param_1,
            "sweep_values_1": self.sweep_values_1.tolist(),
            "sweep_param_2": self.sweep_param_2,
            "sweep_values_2": self.sweep_values_2.tolist(),
            "metric_names": list(self.metric_names),
            "points": [
                {
                    "row_index": point.row_index,
                    "col_index": point.col_index,
                    "sweep_value_1": point.sweep_value_1,
                    "sweep_value_2": point.sweep_value_2,
                    "params": point.params,
                    "initial_guess": None
                    if point.initial_guess is None
                    else point.initial_guess.tolist(),
                    "success": point.result.success,
                    "constraints_ok": point.result.constraints_ok,
                    "residual_norm": point.result.residual_norm,
                    "method": point.result.method,
                    "message": point.result.message,
                    "metrics": point.result.metrics,
                    "constraints": point.result.constraints,
                }
                for point in self.points
            ],
        }


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _make_params(
    base_params: Params,
    sweep_param: str,
    value: float,
    param_modifier: Callable[[Params, float], Params] | None,
) -> Params:
    params = dict(base_params)
    params[sweep_param] = value
    if param_modifier is not None:
        params = param_modifier(params, value)
    return params


def _solve_one(
    system: EquationSystem,
    solver: SolverStrategy,
    params: Params,
    guess: NDArrayFloat | None,
    options: dict[str, object] | None,
) -> SolveResult:
    try:
        return solver.solve(system, params, initial_guess=guess, options=options)
    except Exception as exc:
        fallback_x = np.zeros(system.n_vars, dtype=float) if guess is None else guess
        return build_solve_result(
            system,
            params,
            fallback_x,
            success=False,
            method=getattr(solver, "name", type(solver).__name__),
            residual_norm=float("inf"),
            message=str(exc),
            failures=(
                SolverFailure(
                    method=getattr(solver, "name", type(solver).__name__),
                    message=str(exc),
                ),
            ),
        )


def _sweep_path(
    system: EquationSystem,
    solver: SolverStrategy,
    base_params: Params,
    sweep_param: str,
    values: NDArrayFloat,
    start_guess: NDArrayFloat | None,
    options: dict[str, object] | None,
    param_modifier: Callable[[Params, float], Params] | None,
    *,
    progress_interval: int = 0,
) -> list[SweepPoint]:
    """Sweep along *values* in path mode (warm-start), returning ordered SweepPoints."""
    current_guess = (
        None
        if start_guess is None
        else system.validate_x(to_float_array(start_guess))
    )
    points: list[SweepPoint] = []

    for i, value in enumerate(values):
        fval = float(value)
        params = _make_params(base_params, sweep_param, fval, param_modifier)
        result = _solve_one(system, solver, params, current_guess, options)

        points.append(
            SweepPoint(
                index=i,
                sweep_value=fval,
                params=params,
                initial_guess=None if current_guess is None else current_guess.copy(),
                result=result,
            )
        )

        if result.success:
            current_guess = result.x

        if progress_interval > 0 and (
            (i + 1) % progress_interval == 0 or i == len(values) - 1
        ):
            n_ok = sum(1 for p in points if p.result.success)
            print(f"  [{i + 1}/{len(values)}] success: {n_ok}")

    return points


def _sweep_independent(
    system: EquationSystem,
    solver: SolverStrategy,
    base_params: Params,
    sweep_param: str,
    values: NDArrayFloat,
    initial_guess: NDArrayFloat | None,
    options: dict[str, object] | None,
    param_modifier: Callable[[Params, float], Params] | None,
) -> list[SweepPoint]:
    """Sweep along *values* solving each point from the same initial guess."""
    base_guess = (
        None
        if initial_guess is None
        else system.validate_x(to_float_array(initial_guess))
    )
    points: list[SweepPoint] = []

    for i, value in enumerate(values):
        fval = float(value)
        params = _make_params(base_params, sweep_param, fval, param_modifier)
        result = _solve_one(system, solver, params, base_guess, options)

        points.append(
            SweepPoint(
                index=i,
                sweep_value=fval,
                params=params,
                initial_guess=None if base_guess is None else base_guess.copy(),
                result=result,
            )
        )

    return points


def _probe_direction(
    system: EquationSystem,
    solver: SolverStrategy,
    base_params: Params,
    sweep_param: str,
    probe_values: NDArrayFloat,
    initial_guess: NDArrayFloat | None,
    options: dict[str, object] | None,
    param_modifier: Callable[[Params, float], Params] | None,
) -> tuple[int, int, NDArrayFloat | None]:
    """Solve a short probe sequence and return (successes, total, last_ok_x)."""
    current_guess = (
        None
        if initial_guess is None
        else system.validate_x(to_float_array(initial_guess))
    )
    successes = 0
    last_ok_x: NDArrayFloat | None = None

    for value in probe_values:
        params = _make_params(base_params, sweep_param, float(value), param_modifier)
        try:
            result = solver.solve(
                system,
                params,
                initial_guess=current_guess,
                options=options,
            )
            if result.success and result.constraints_ok:
                successes += 1
                current_guess = result.x
                last_ok_x = result.x.copy()
        except Exception:
            pass

    return successes, len(probe_values), last_ok_x


# ---------------------------------------------------------------------------
# Public API — 1D sweep
# ---------------------------------------------------------------------------


def sweep_1d(
    system: EquationSystem,
    solver: SolverStrategy,
    base_params: Params,
    sweep_param: str,
    sweep_values: NDArrayFloat,
    metric_names: list[str],
    *,
    initial_guess: NDArrayFloat | None = None,
    options: dict[str, object] | None = None,
    mode: SweepMode = "path",
    param_modifier: Callable[[Params, float], Params] | None = None,
    probe_size: int = 10,
) -> SweepResult1D:
    """Evaluate the system along a 1D path of parameter values.

    When *mode* is ``"adaptive"``, the first *probe_size* points from both
    ends are solved to determine the sweep direction with the higher
    success rate, then the full sweep proceeds from that end using
    warm-start (``"path"`` mode).
    """
    system.validate_params(base_params)
    if sweep_param not in base_params:
        raise KeyError(f"Unknown sweep parameter '{sweep_param}'")

    values = to_float_array(sweep_values)

    if mode == "adaptive":
        return _sweep_1d_adaptive(
            system,
            solver,
            base_params,
            sweep_param,
            values,
            metric_names,
            initial_guess=initial_guess,
            options=options,
            param_modifier=param_modifier,
            probe_size=probe_size,
        )

    if mode == "path":
        points = _sweep_path(
            system, solver, base_params, sweep_param, values,
            initial_guess, options, param_modifier,
        )
    elif mode == "independent":
        points = _sweep_independent(
            system, solver, base_params, sweep_param, values,
            initial_guess, options, param_modifier,
        )
    else:
        raise ValueError(f"Unknown sweep mode '{mode}'")

    return SweepResult1D(
        mode=mode,
        sweep_param=sweep_param,
        sweep_values=values,
        metric_names=tuple(metric_names),
        points=tuple(points),
    )


def _sweep_1d_adaptive(
    system: EquationSystem,
    solver: SolverStrategy,
    base_params: Params,
    sweep_param: str,
    values: NDArrayFloat,
    metric_names: list[str],
    *,
    initial_guess: NDArrayFloat | None,
    options: dict[str, object] | None,
    param_modifier: Callable[[Params, float], Params] | None,
    probe_size: int,
) -> SweepResult1D:
    n = min(probe_size, len(values))

    left_ok, left_total, left_x = _probe_direction(
        system, solver, base_params, sweep_param,
        values[:n], initial_guess, options, param_modifier,
    )
    right_ok, right_total, right_x = _probe_direction(
        system, solver, base_params, sweep_param,
        values[-n:][::-1], initial_guess, options, param_modifier,
    )

    if left_ok == 0 and right_ok == 0:
        warnings.warn(
            f"Adaptive probe: both sides 0/{left_total} success — "
            "check param_modifier, initial_guess, or parameter range",
            stacklevel=3,
        )

    sweep_from_right = right_ok > left_ok or (right_ok == left_ok and right_ok > 0)
    direction = "right" if sweep_from_right else "left"
    print(
        f"  Adaptive probe: left {left_ok}/{left_total}, "
        f"right {right_ok}/{right_total} -> sweep from {direction}"
    )

    if sweep_from_right:
        ordered_values = values[::-1]
        warm_guess = right_x
    else:
        ordered_values = values
        warm_guess = left_x

    start_guess = warm_guess if warm_guess is not None else initial_guess

    raw_points = _sweep_path(
        system, solver, base_params, sweep_param, ordered_values,
        start_guess, options, param_modifier, progress_interval=20,
    )

    # Re-order to match original sweep_values and assign correct indices
    if sweep_from_right:
        raw_points = [
            replace(pt, index=len(raw_points) - 1 - pt.index)
            for pt in reversed(raw_points)
        ]

    return SweepResult1D(
        mode="adaptive",
        sweep_param=sweep_param,
        sweep_values=values,
        metric_names=tuple(metric_names),
        points=tuple(raw_points),
    )


# ---------------------------------------------------------------------------
# Public API — 2D sweep
# ---------------------------------------------------------------------------


def sweep_2d(
    system: EquationSystem,
    solver: SolverStrategy,
    base_params: Params,
    sweep_param_1: str,
    sweep_values_1: NDArrayFloat,
    sweep_param_2: str,
    sweep_values_2: NDArrayFloat,
    metric_names: list[str],
    *,
    initial_guess: NDArrayFloat | None = None,
    options: dict[str, object] | None = None,
    mode: SweepMode = "path",
) -> SweepResult2D:
    """Evaluate the system over a 2D parameter grid."""
    system.validate_params(base_params)
    if sweep_param_1 not in base_params:
        raise KeyError(f"Unknown sweep parameter '{sweep_param_1}'")
    if sweep_param_2 not in base_params:
        raise KeyError(f"Unknown sweep parameter '{sweep_param_2}'")

    values_1 = to_float_array(sweep_values_1)
    values_2 = to_float_array(sweep_values_2)
    base_guess = (
        None
        if initial_guess is None
        else system.validate_x(to_float_array(initial_guess))
    )
    is_path = mode == "path"
    points: list[SweepPoint2D] = []
    row_start_guess = base_guess

    for row_index, value_1 in enumerate(values_1):
        current_guess = row_start_guess if is_path else base_guess
        row_last_success: NDArrayFloat | None = None

        for col_index, value_2 in enumerate(values_2):
            params = dict(base_params)
            params[sweep_param_1] = float(value_1)
            params[sweep_param_2] = float(value_2)
            guess = current_guess if is_path else base_guess
            result = _solve_one(system, solver, params, guess, options)

            points.append(
                SweepPoint2D(
                    row_index=row_index,
                    col_index=col_index,
                    sweep_value_1=float(value_1),
                    sweep_value_2=float(value_2),
                    params=params,
                    initial_guess=None if guess is None else guess.copy(),
                    result=result,
                )
            )

            if is_path and result.success:
                current_guess = result.x
                row_last_success = result.x

        if is_path and row_last_success is not None:
            row_start_guess = row_last_success

    return SweepResult2D(
        mode=mode,
        sweep_param_1=sweep_param_1,
        sweep_values_1=values_1,
        sweep_param_2=sweep_param_2,
        sweep_values_2=values_2,
        metric_names=tuple(metric_names),
        points=tuple(points),
    )


# ---------------------------------------------------------------------------
# Public API — persistence
# ---------------------------------------------------------------------------


def save_json(
    result: SweepResult1D | SweepResult2D,
    path: str | Path,
) -> Path:
    """Persist a sweep result as JSON."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(result.to_dict(), handle, indent=2, ensure_ascii=True)
    return target
