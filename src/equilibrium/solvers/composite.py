"""Composite solver that tries multiple strategies in sequence."""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from equilibrium.models.base import EquationSystem, NDArrayFloat, Params
from equilibrium.solvers.base import (
    SolveResult,
    SolverFailure,
    SolverStrategy,
    build_solve_result,
)
from equilibrium.utils.validation import to_float_array


class CompositeSolver:
    """Try multiple solver strategies until one succeeds."""

    def __init__(self, strategies: list[SolverStrategy]) -> None:
        if not strategies:
            raise ValueError("CompositeSolver requires at least one strategy")
        self.strategies = strategies
        self.name = "composite"

    def solve(
        self,
        system: EquationSystem,
        params: Params,
        initial_guess: NDArrayFloat | None = None,
        *,
        options: dict[str, object] | None = None,
    ) -> SolveResult:
        """Run configured strategies in order until one returns a valid result."""
        failures: list[SolverFailure] = []

        for strategy in self.strategies:
            try:
                result = strategy.solve(
                    system,
                    params,
                    initial_guess=initial_guess,
                    options=options,
                )
            except Exception as exc:
                failures.append(SolverFailure(method=strategy.name, message=str(exc)))
                continue

            combined_failures = tuple([*failures, *result.failures])
            result = replace(result, failures=combined_failures)
            if result.success and result.constraints_ok:
                return result

            failures.append(
                SolverFailure(
                    method=result.method,
                    message=result.message,
                    residual_norm=result.residual_norm,
                )
            )

        fallback_x = self._fallback_vector(system, initial_guess)
        return build_solve_result(
            system,
            params,
            fallback_x,
            success=False,
            method=self.name,
            residual_norm=float("inf"),
            message="All solver strategies failed",
            failures=tuple(failures),
        )

    def _fallback_vector(
        self,
        system: EquationSystem,
        initial_guess: NDArrayFloat | None,
    ) -> NDArrayFloat:
        if initial_guess is None:
            return np.zeros(system.n_vars, dtype=float)
        return system.validate_x(to_float_array(initial_guess))
