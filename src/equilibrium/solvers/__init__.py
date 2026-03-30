"""Solver result types and shared solver utilities."""

from equilibrium.solvers.base import (
    SolveAcceptance,
    SolveResult,
    SolverFailure,
    SolverStrategy,
    build_solve_result,
)
from equilibrium.solvers.composite import CompositeSolver
from equilibrium.solvers.continuation import ContinuationSolver
from equilibrium.solvers.robust import RobustGuessSolver
from equilibrium.solvers.scipy_root import ScipyRootSolver

__all__ = [
    "CompositeSolver",
    "ContinuationSolver",
    "RobustGuessSolver",
    "ScipyRootSolver",
    "SolveAcceptance",
    "SolveResult",
    "SolverFailure",
    "SolverStrategy",
    "build_solve_result",
]
