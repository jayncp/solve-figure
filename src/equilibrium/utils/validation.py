"""Validation helpers shared across the framework."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np

from equilibrium.models.base import NDArrayFloat


def to_float_array(values: Sequence[float] | NDArrayFloat) -> NDArrayFloat:
    """Convert a 1D input sequence to a float array."""
    array = np.asarray(values, dtype=float)
    if array.ndim != 1:
        raise ValueError(f"Expected a 1D vector, got ndim={array.ndim}")
    return array


def ensure_finite(name: str, values: NDArrayFloat) -> None:
    """Raise ValueError when a vector contains NaN or inf."""
    if not np.isfinite(values).all():
        raise ValueError(f"{name} contains non-finite values")


def constraints_ok(constraints: Mapping[str, float]) -> bool:
    """Return True when all named constraints are strictly positive."""
    return all(value > 0 for value in constraints.values())
