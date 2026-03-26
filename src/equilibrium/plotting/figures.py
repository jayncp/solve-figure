"""Matplotlib helpers for result visualization."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from matplotlib import pyplot as plt
from matplotlib.figure import Figure

from equilibrium.plotting.sweep import SweepResult1D


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
