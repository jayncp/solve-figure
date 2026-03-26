"""Continuation-based solver wrapper."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import replace
from typing import Callable, TypeAlias, cast

import numpy as np

from equilibrium.models.base import EquationSystem, NDArrayFloat, Params
from equilibrium.solvers.base import (
    SolveAcceptance,
    SolveResult,
    SolverFailure,
    SolverStrategy,
    build_solve_result,
)
from equilibrium.utils.validation import to_float_array

PathBuilder: TypeAlias = Callable[[Params], tuple[Params, ...]]


class ContinuationSolver:
    """Solve a target parameter set by stepping through a continuation path."""

    def __init__(
        self,
        step_solver: SolverStrategy,
        *,
        acceptance: SolveAcceptance | None = None,
        path_builder: PathBuilder | None = None,
    ) -> None:
        self.step_solver = step_solver
        self.acceptance = acceptance or SolveAcceptance()
        self.path_builder = path_builder
        self.name = f"continuation[{step_solver.name}]"

    def solve(
        self,
        system: EquationSystem,
        params: Params,
        initial_guess: NDArrayFloat | None = None,
        *,
        options: dict[str, object] | None = None,
    ) -> SolveResult:
        """Solve by applying the wrapped solver across a continuation path."""
        solver_options = dict(options or {})
        path = self._resolve_path(params, solver_options)
        acceptance = self._resolve_acceptance(solver_options)

        current_guess = self._normalize_initial_guess(system, initial_guess)
        last_result: SolveResult | None = None
        failures: list[SolverFailure] = []

        for index, step_params in enumerate(path):
            try:
                result = self.step_solver.solve(
                    system,
                    step_params,
                    initial_guess=current_guess,
                    options=solver_options,
                )
            except Exception as exc:
                failures.append(
                    SolverFailure(
                        method=f"{self.step_solver.name}@step{index}",
                        message=str(exc),
                    )
                )
                return self._build_failure_result(
                    system,
                    params,
                    current_guess,
                    last_result,
                    f"Continuation failed at step {index}: {exc}",
                    tuple(failures),
                )

            if not acceptance.accepts(result):
                failures.append(
                    SolverFailure(
                        method=f"{result.method}@step{index}",
                        message=result.message,
                        residual_norm=result.residual_norm,
                    )
                )
                return self._build_failure_result(
                    system,
                    params,
                    result.x,
                    result,
                    f"Continuation rejected step {index}: {result.message}",
                    tuple(failures),
                    residual_norm=result.residual_norm,
                )

            current_guess = result.x
            last_result = result

        if last_result is None:
            raise ValueError("Continuation path must contain at least one step")

        return replace(
            last_result,
            method=self.name,
            failures=tuple(failures),
        )

    def _resolve_path(
        self,
        params: Params,
        options: dict[str, object],
    ) -> tuple[Params, ...]:
        option_path = options.pop("continuation_path", None)
        if option_path is not None:
            steps = cast(Iterable[Mapping[str, float]], option_path)
            return tuple(dict(step) for step in steps)
        if self.path_builder is None:
            return (dict(params),)
        return tuple(dict(step) for step in self.path_builder(params))

    def _resolve_acceptance(
        self,
        options: dict[str, object],
    ) -> SolveAcceptance:
        acceptance = options.pop("acceptance", None)
        if acceptance is None:
            return self.acceptance
        if not isinstance(acceptance, SolveAcceptance):
            raise TypeError("acceptance must be a SolveAcceptance instance")
        return acceptance

    def _normalize_initial_guess(
        self,
        system: EquationSystem,
        initial_guess: NDArrayFloat | None,
    ) -> NDArrayFloat | None:
        if initial_guess is None:
            return None
        return system.validate_x(to_float_array(initial_guess))

    def _build_failure_result(
        self,
        system: EquationSystem,
        params: Params,
        current_guess: NDArrayFloat | None,
        last_result: SolveResult | None,
        message: str,
        failures: tuple[SolverFailure, ...],
        *,
        residual_norm: float = float("inf"),
    ) -> SolveResult:
        if current_guess is not None:
            try:
                return build_solve_result(
                    system,
                    params,
                    current_guess,
                    success=False,
                    method=self.name,
                    residual_norm=residual_norm,
                    message=message,
                    failures=failures,
                )
            except Exception:
                pass

        if last_result is not None:
            return replace(
                last_result,
                success=False,
                method=self.name,
                residual_norm=residual_norm,
                message=message,
                failures=failures,
            )

        fallback = np.zeros(system.n_vars, dtype=float)
        return build_solve_result(
            system,
            params,
            fallback,
            success=False,
            method=self.name,
            residual_norm=residual_norm,
            message=message,
            failures=failures,
        )
