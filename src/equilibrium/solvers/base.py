"""Shared solver result structures."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from equilibrium.models.base import (
    ConstraintMap,
    EquationSystem,
    IntermediateMap,
    MetricMap,
    NDArrayFloat,
    Params,
)
from equilibrium.utils.validation import constraints_ok, ensure_finite, to_float_array


class SolverStrategy(Protocol):
    """Protocol implemented by all solver strategies."""

    name: str

    def solve(
        self,
        system: EquationSystem,
        params: Params,
        initial_guess: NDArrayFloat | None = None,
        *,
        options: dict[str, object] | None = None,
    ) -> SolveResult: ...


@dataclass(frozen=True, slots=True)
class SolveAcceptance:
    """Acceptance criteria applied after a solver returns."""

    residual_tol: float = 1e-8
    require_success: bool = True
    require_constraints: bool = True

    def accepts(self, result: "SolveResult") -> bool:
        """Return True when a result satisfies all configured acceptance checks."""
        if self.require_success and not result.success:
            return False
        if self.require_constraints and not result.constraints_ok:
            return False
        return result.residual_norm <= self.residual_tol


@dataclass(slots=True)
class SolverFailure:
    """Structured description of a failed solver attempt."""

    method: str
    message: str
    residual_norm: float | None = None


@dataclass(slots=True)
class SolveResult:
    """Normalized solve output returned by solver implementations."""

    success: bool
    method: str
    x: NDArrayFloat
    residual_norm: float
    variables: dict[str, float]
    constraints: ConstraintMap
    constraints_ok: bool
    intermediates: IntermediateMap
    metrics: MetricMap
    message: str
    nfev: int | None = None
    njev: int | None = None
    failures: tuple[SolverFailure, ...] = ()


def build_solve_result(
    system: EquationSystem,
    params: Params,
    x: NDArrayFloat,
    *,
    success: bool,
    method: str,
    residual_norm: float,
    message: str,
    nfev: int | None = None,
    njev: int | None = None,
    failures: tuple[SolverFailure, ...] = (),
) -> SolveResult:
    """Construct a SolveResult from a system and a solution vector."""
    system.validate_params(params)
    array = to_float_array(x)
    array = system.validate_x(array)
    ensure_finite("solution vector", array)

    intermediates = system.intermediates(array, params)
    constraints = system.constraints(array, params, intermediates=intermediates)
    metrics = system.metrics(array, params, intermediates=intermediates)

    return SolveResult(
        success=success,
        method=method,
        x=array,
        residual_norm=residual_norm,
        variables=system.variable_dict(array),
        constraints=constraints,
        constraints_ok=constraints_ok(constraints),
        intermediates=intermediates,
        metrics=metrics,
        message=message,
        nfev=nfev,
        njev=njev,
        failures=failures,
    )
