"""Solver result types and shared solver utilities."""

from equilibrium.solvers.base import (
    SolveResult,
    SolverFailure,
    SolverStrategy,
    build_solve_result,
)
from equilibrium.solvers.composite import CompositeSolver
from equilibrium.solvers.scipy_root import ScipyRootSolver

__all__ = [
    "CompositeSolver",
    "ScipyRootSolver",
    "SolveResult",
    "SolverFailure",
    "SolverStrategy",
    "build_solve_result",
]
