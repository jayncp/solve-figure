"""Wrapper around scipy.optimize.root."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
from scipy import optimize

from equilibrium.models.base import EquationSystem, NDArrayFloat, Params
from equilibrium.solvers.base import SolveResult, build_solve_result
from equilibrium.utils.validation import to_float_array


class ScipyRootSolver:
    """Solve nonlinear systems with scipy.optimize.root."""

    def __init__(
        self, method: str = "hybr", *, require_constraints: bool = False
    ) -> None:
        self.method = method
        self.require_constraints = require_constraints
        self.name = f"scipy.root[{method}]"

    def solve(
        self,
        system: EquationSystem,
        params: Params,
        initial_guess: NDArrayFloat | None = None,
        *,
        options: dict[str, object] | None = None,
    ) -> SolveResult:
        """Solve the system from an initial guess using scipy.optimize.root."""
        system.validate_params(params)

        guess = self._normalize_initial_guess(system, initial_guess)
        root_options = dict(options or {})
        use_jacobian = bool(root_options.pop("use_jacobian", False))

        raw = optimize.root(
            lambda vector: system.equations(to_float_array(vector), params),
            guess,
            method=self.method,
            jac=(lambda v: system.jacobian(to_float_array(v), params))
            if use_jacobian
            else None,
            options=root_options,
        )

        residual_norm = float(np.linalg.norm(raw.fun))
        result = build_solve_result(
            system,
            params,
            raw.x,
            success=bool(raw.success),
            method=self.name,
            residual_norm=residual_norm,
            message=str(raw.message),
            nfev=getattr(raw, "nfev", None),
            njev=getattr(raw, "njev", None),
        )

        if self.require_constraints and result.success and not result.constraints_ok:
            return replace(
                result,
                success=False,
                message=f"{result.message}; constraints not satisfied",
            )

        return result

    def _normalize_initial_guess(
        self,
        system: EquationSystem,
        initial_guess: NDArrayFloat | None,
    ) -> NDArrayFloat:
        if initial_guess is None:
            return np.zeros(system.n_vars, dtype=float)
        guess = to_float_array(initial_guess)
        return system.validate_x(guess)
