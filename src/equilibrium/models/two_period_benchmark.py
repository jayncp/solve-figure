"""Benchmark configuration for the two-period model."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from equilibrium.models.base import NDArrayFloat, Params
from equilibrium.solvers.base import SolveAcceptance


@dataclass(frozen=True, slots=True)
class TwoPeriodBenchmark:
    """Stable benchmark configuration for the two-period model."""

    name: str
    params: Params
    initial_guess: NDArrayFloat
    expected_solution: NDArrayFloat
    acceptance: SolveAcceptance

    def continuation_path(self, *, steps: int = 5) -> tuple[Params, ...]:
        """Build a simple rho-continuation path ending at the benchmark params."""
        if steps < 2:
            raise ValueError("steps must be at least 2")
        rho_values = np.linspace(0.0, self.params["rho"], steps)
        path = []
        for rho in rho_values:
            step = dict(self.params)
            step["rho"] = float(rho)
            path.append(step)
        return tuple(path)


def default_two_period_benchmark() -> TwoPeriodBenchmark:
    """Return the default benchmark used for Step 7 validation."""
    return TwoPeriodBenchmark(
        name="two_period_rho_path",
        params={
            "J_I": 2.0,
            "J_U": 3.0,
            "sigma_v2": 1.5,
            "sigma_u2": 0.8,
            "sigma_epsilon2": 0.4,
            "sigma_eta2": 0.6,
            "rho": 0.3,
        },
        initial_guess=np.array(
            [0.8, 0.9, 0.1, 0.4, 0.05, 0.35, 0.02, 0.03, 0.25, 0.2, 0.04],
            dtype=float,
        ),
        expected_solution=np.array(
            [
                0.25347207,
                0.59568708,
                -0.44998400,
                0.11056912,
                0.19471181,
                0.24415610,
                0.11233787,
                -0.19956548,
                0.19325677,
                0.21745350,
                -0.11354437,
            ],
            dtype=float,
        ),
        acceptance=SolveAcceptance(
            residual_tol=1e-8,
            require_success=True,
            require_constraints=True,
        ),
    )
