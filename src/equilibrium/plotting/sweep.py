"""Parameter sweep helpers."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from equilibrium.models.base import EquationSystem, NDArrayFloat, Params
from equilibrium.solvers.base import (
    SolveResult,
    SolverFailure,
    SolverStrategy,
    build_solve_result,
)
from equilibrium.utils.validation import to_float_array


@dataclass(slots=True)
class SweepPoint:
    """One point in a parameter sweep."""

    sweep_value: float
    params: Params
    result: SolveResult


@dataclass(slots=True)
class SweepResult1D:
    """Results from a one-dimensional sweep."""

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

    def success_mask(self) -> NDArrayFloat:
        """Return a float mask with 1.0 for successful points and 0.0 otherwise."""
        values = [1.0 if point.result.success else 0.0 for point in self.points]
        return np.asarray(values, dtype=float)


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
        reuse_previous_success: bool = True,
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

        for value in values:
            params = dict(base_params)
            params[sweep_param] = float(value)

            try:
                result = solver.solve(
                    system,
                    params,
                    initial_guess=current_guess,
                    options=options,
                )
            except Exception as exc:
                fallback_x = (
                    np.zeros(system.n_vars, dtype=float)
                    if current_guess is None
                    else current_guess
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

            points.append(SweepPoint(float(value), params, result))

            if reuse_previous_success and result.success:
                current_guess = result.x

        return SweepResult1D(
            sweep_param=sweep_param,
            sweep_values=values,
            metric_names=tuple(metric_names),
            points=tuple(points),
        )
