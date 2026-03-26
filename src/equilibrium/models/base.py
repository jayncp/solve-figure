"""Base abstractions for equilibrium systems."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

Params: TypeAlias = dict[str, float]
ConstraintMap: TypeAlias = dict[str, float]
MetricMap: TypeAlias = dict[str, float]
IntermediateMap: TypeAlias = dict[str, float]
NDArrayFloat: TypeAlias = NDArray[np.float64]


class EquationSystem(ABC):
    """Stateless interface for a nonlinear equation system."""

    @property
    @abstractmethod
    def variable_names(self) -> tuple[str, ...]:
        """Ordered variable names corresponding to a solution vector."""

    @property
    @abstractmethod
    def param_names(self) -> tuple[str, ...]:
        """Required parameter names for this system."""

    @abstractmethod
    def equations(self, x: NDArrayFloat, params: Params) -> NDArrayFloat:
        """Return the residual vector F(x)."""

    def intermediates(self, x: NDArrayFloat, params: Params) -> IntermediateMap:
        """Compute shared intermediate values."""
        return {}

    def constraints(
        self,
        x: NDArrayFloat,
        params: Params,
        intermediates: IntermediateMap | None = None,
    ) -> ConstraintMap:
        """Return named inequality constraints; values greater than zero satisfy them."""
        if intermediates is None:
            intermediates = self.intermediates(x, params)
        return {}

    def metrics(
        self,
        x: NDArrayFloat,
        params: Params,
        intermediates: IntermediateMap | None = None,
    ) -> MetricMap:
        """Return named post-solve metrics."""
        if intermediates is None:
            intermediates = self.intermediates(x, params)
        return {}

    def jacobian(self, x: NDArrayFloat, params: Params) -> NDArrayFloat | None:
        """Return an analytical Jacobian if available."""
        return None

    @property
    def n_vars(self) -> int:
        """Number of unknowns in the system."""
        return len(self.variable_names)

    def validate_params(self, params: Mapping[str, float]) -> None:
        """Raise ValueError when required params are missing or unexpected params are provided."""
        expected = set(self.param_names)
        got = set(params.keys())
        missing = tuple(sorted(expected - got))
        extra = tuple(sorted(got - expected))
        if missing or extra:
            raise ValueError(f"Param mismatch: missing={missing}, extra={extra}")

    def validate_x(self, x: NDArrayFloat) -> NDArrayFloat:
        """Return a normalized 1D vector with the correct system size."""
        array = np.asarray(x, dtype=float)
        if array.ndim != 1:
            raise ValueError(f"Expected a 1D vector, got ndim={array.ndim}")
        if array.shape[0] != self.n_vars:
            raise ValueError(
                f"Expected vector length {self.n_vars}, got {array.shape[0]}"
            )
        return array

    def variable_dict(self, x: NDArrayFloat) -> dict[str, float]:
        """Map variable names to values from a solution vector."""
        array = self.validate_x(x)
        return dict(zip(self.variable_names, array.tolist(), strict=True))
