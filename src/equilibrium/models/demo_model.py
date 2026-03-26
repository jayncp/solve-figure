"""Simple demo system used to validate the framework pipeline."""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np

from equilibrium.models.base import EquationSystem, NDArrayFloat, Params


class DemoEquilibriumModel(EquationSystem):
    """Two-variable system with one economically meaningful constraint."""

    @property
    def variable_names(self) -> tuple[str, ...]:
        return ("x", "y")

    @property
    def param_names(self) -> tuple[str, ...]:
        return ("curvature", "slope")

    def equations(self, x: NDArrayFloat, params: Params) -> NDArrayFloat:
        vector = self.validate_x(x)
        return np.array(
            [
                vector[0] ** 2 - params["curvature"],
                vector[1] - params["slope"] * vector[0],
            ],
            dtype=float,
        )

    def intermediates(self, x: NDArrayFloat, params: Params) -> dict[str, float]:
        vector = self.validate_x(x)
        x_value = float(vector[0])
        y_value = float(vector[1])
        return {
            "x_squared": x_value**2,
            "total": x_value + y_value,
            "product": x_value * y_value,
        }

    def constraints(
        self,
        x: NDArrayFloat,
        params: Params,
        intermediates: dict[str, float] | None = None,
    ) -> dict[str, float]:
        vector = self.validate_x(x)
        return {
            "x_positive": float(vector[0]),
            "y_non_negative": float(vector[1]),
        }

    def metrics(
        self,
        x: NDArrayFloat,
        params: Params,
        intermediates: dict[str, float] | None = None,
    ) -> dict[str, float]:
        if intermediates is None:
            intermediates = self.intermediates(x, params)
        vector = self.validate_x(x)
        return {
            "x": float(vector[0]),
            "y": float(vector[1]),
            "total": intermediates["total"],
            "product": intermediates["product"],
        }

    def validate_params(self, params: Mapping[str, float]) -> None:
        super().validate_params(params)
        if params["curvature"] <= 0:
            raise ValueError("curvature must be positive")
        if params["slope"] < 0:
            raise ValueError("slope must be non-negative")
