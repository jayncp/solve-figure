"""Matplotlib helpers for result visualization."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from matplotlib import pyplot as plt
from matplotlib.figure import Figure

from equilibrium.plotting.sweep import SweepResult1D, SweepResult2D


class FigurePlotter:
    """Render sweep outputs as matplotlib figures."""

    def plot_1d(
        self,
        result: SweepResult1D,
        metrics: list[str],
        *,
        title: str | None = None,
        xlabel: str | None = None,
        ylabel: str = "value",
    ) -> Figure:
        """Plot one or more metric series against a sweep parameter."""
        figure, axis = plt.subplots(figsize=(8, 4.5))
        for metric in metrics:
            axis.plot(
                result.sweep_values,
                result.metric_series(metric),
                marker="o",
                label=metric,
            )

        axis.set_xlabel(xlabel or result.sweep_param)
        axis.set_ylabel(ylabel)
        axis.set_title(title or f"{result.sweep_param} sweep")
        axis.grid(True, alpha=0.3)
        axis.legend()
        figure.tight_layout()
        return figure

    def save(self, figure: Figure, path: str | Path) -> Path:
        """Persist a figure to disk and close it afterwards."""
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(target, dpi=150)
        plt.close(figure)
        return target

    def plot_2d_heatmap(
        self,
        result: SweepResult2D,
        metric: str,
        *,
        title: str | None = None,
        xlabel: str | None = None,
        ylabel: str | None = None,
    ) -> Figure:
        """Plot a 2D heatmap for one metric."""
        figure, axis = plt.subplots(figsize=(7.5, 5.5))
        grid = result.metric_grid(metric)
        image = axis.imshow(
            grid,
            origin="lower",
            aspect="auto",
            extent=(
                float(result.sweep_values_2[0]),
                float(result.sweep_values_2[-1]),
                float(result.sweep_values_1[0]),
                float(result.sweep_values_1[-1]),
            ),
        )
        axis.set_xlabel(xlabel or result.sweep_param_2)
        axis.set_ylabel(ylabel or result.sweep_param_1)
        axis.set_title(title or f"{metric} heatmap")
        figure.colorbar(image, ax=axis, label=metric)
        figure.tight_layout()
        return figure
