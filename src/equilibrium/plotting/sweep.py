"""Parameter sweep helpers."""

from __future__ import annotations

from dataclasses import dataclass
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

SweepMode: TypeAlias = Literal["independent", "path"]


@dataclass(slots=True)
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


class ParameterSweep:
    """Run parameter sweeps over a model and solver."""

    def sweep_1d(
        self,
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
    ) -> SweepResult1D:
        """Evaluate the system along a 1D path of parameter values."""
        system.validate_params(base_params)
        if sweep_param not in base_params:
            raise KeyError(f"Unknown sweep parameter '{sweep_param}'")

        values = to_float_array(sweep_values)
        current_guess = (
            None
            if initial_guess is None
            else system.validate_x(to_float_array(initial_guess))
        )
        points: list[SweepPoint] = []

        for index, value in enumerate(values):
            params = dict(base_params)
            params[sweep_param] = float(value)
            guess = self._guess_for_mode(mode, current_guess, initial_guess, system)

            try:
                result = solver.solve(
                    system,
                    params,
                    initial_guess=guess,
                    options=options,
                )
            except Exception as exc:
                fallback_x = (
                    np.zeros(system.n_vars, dtype=float) if guess is None else guess
                )
                result = build_solve_result(
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

            points.append(
                SweepPoint(
                    index=index,
                    sweep_value=float(value),
                    params=params,
                    initial_guess=None if guess is None else guess.copy(),
                    result=result,
                )
            )

            if mode == "path" and result.success:
                current_guess = result.x

        return SweepResult1D(
            mode=mode,
            sweep_param=sweep_param,
            sweep_values=values,
            metric_names=tuple(metric_names),
            points=tuple(points),
        )

    def _guess_for_mode(
        self,
        mode: SweepMode,
        current_guess: NDArrayFloat | None,
        initial_guess: NDArrayFloat | None,
        system: EquationSystem,
    ) -> NDArrayFloat | None:
        if mode == "independent":
            if initial_guess is None:
                return None
            return system.validate_x(to_float_array(initial_guess))
        if mode == "path":
            return current_guess
        raise ValueError(f"Unknown sweep mode '{mode}'")
