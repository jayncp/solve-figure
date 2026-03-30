"""Solver wrapper with multi-stage initial guess fallback."""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from equilibrium.models.base import EquationSystem, NDArrayFloat, Params
from equilibrium.solvers.base import SolveResult, SolverFailure, SolverStrategy


class RobustGuessSolver:
    """Wrap a solver with user -> noisy -> random initial guess fallback.

    On each solve call the wrapper tries up to three stages:
    1. The caller-provided initial guess (if any).
    2. Perturbed copies of that guess (element-wise relative noise).
    3. Fully random guesses drawn from a uniform distribution.

    The first result satisfying ``success and constraints_ok`` is returned
    immediately.  If every attempt fails the result with the smallest
    *residual_norm* among constraint-satisfying solutions is preferred;
    otherwise the overall smallest residual is returned.
    """

    def __init__(
        self,
        inner: SolverStrategy,
        *,
        noise_scale: float = 0.1,
        noise_attempts: int = 3,
        random_attempts: int = 2,
        random_scale: float = 1.0,
        rng_seed: int | None = None,
    ) -> None:
        self.inner = inner
        self.noise_scale = noise_scale
        self.noise_attempts = noise_attempts
        self.random_attempts = random_attempts
        self.random_scale = random_scale
        self.rng = np.random.default_rng(rng_seed)
        self.name = f"robust[{inner.name}]"

    def solve(
        self,
        system: EquationSystem,
        params: Params,
        initial_guess: NDArrayFloat | None = None,
        *,
        options: dict[str, object] | None = None,
    ) -> SolveResult:
        failures: list[SolverFailure] = []
        best: SolveResult | None = None
        best_constrained: SolveResult | None = None

        def _update_best(result: SolveResult) -> None:
            nonlocal best, best_constrained
            if best is None or result.residual_norm < best.residual_norm:
                best = result
            if result.constraints_ok and (
                best_constrained is None
                or result.residual_norm < best_constrained.residual_norm
            ):
                best_constrained = result

        def _try(guess: NDArrayFloat | None, label: str) -> SolveResult | None:
            try:
                result = self.inner.solve(
                    system, params, initial_guess=guess, options=options
                )
            except Exception as exc:
                failures.append(
                    SolverFailure(method=f"{self.name}/{label}", message=str(exc))
                )
                return None

            if result.success and result.constraints_ok:
                return replace(result, failures=(*failures, *result.failures))

            _update_best(result)
            failures.append(
                SolverFailure(
                    method=f"{self.name}/{label}",
                    message=result.message,
                    residual_norm=result.residual_norm,
                )
            )
            return None

        # Stage 1: user-provided guess
        ok = _try(initial_guess, "user")
        if ok is not None:
            return ok

        # Stage 2: noisy perturbations of the user guess
        if initial_guess is not None:
            base = np.asarray(initial_guess, dtype=float)
            for i in range(self.noise_attempts):
                noise = self.rng.normal(0, self.noise_scale, size=base.shape) * (
                    np.abs(base) + 1e-8
                )
                ok = _try(base + noise, f"noise-{i}")
                if ok is not None:
                    return ok

        # Stage 3: random guesses
        n = system.n_vars
        for i in range(self.random_attempts):
            rand_guess = self.rng.uniform(-self.random_scale, self.random_scale, size=n)
            ok = _try(rand_guess, f"random-{i}")
            if ok is not None:
                return ok

        # All failed – prefer best constrained result, then overall best
        fallback = best_constrained if best_constrained is not None else best
        assert fallback is not None
        return replace(fallback, failures=tuple(failures))
