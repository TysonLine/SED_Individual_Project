"""
Plotting utilities (matplotlib).

This module focuses only on rendering:
- timeseries(): one line plot per selected value column vs. a datetime column
- histograms(): one histogram per selected value column

Design notes:
- We keep layout simple and readable (no global styles).
- Filenames are derived from column names via slugify().
- Binning auto-selection uses √N with sane bounds for readability.
"""

from __future__ import annotations

from pathlib import Path
from typing import List
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from .utils import slugify


class Visualizer:
    """Matplotlib-based plotting for time-series and histograms."""

    @staticmethod
    def timeseries(
        df: pd.DataFrame,
        datetime_col: str,
        value_cols: list[str],
        outdir: Path,
        suffix: str = "",
    ) -> List[str]:
        """
        Render one time-series PNG per value column.

        Parameters
        ----------
        df : pd.DataFrame
            Input data; must contain `datetime_col` and each of `value_cols`.
        datetime_col : str
            Column name to use on the X axis (already parsed as datetime).
        value_cols : list[str]
            Column names to plot on the Y axis (one figure per column).
        outdir : Path
            Output directory to write PNG files.
        suffix : str
            Optional suffix (e.g., '_D_mean') appended to filenames and titles.

        Returns
        -------
        List[str]
            Paths of the PNG files created (empty list if nothing was plotted).
        """
        paths: List[str] = []
        for col in value_cols:
            if col not in df.columns:
                continue  # skip silently if a requested column is missing

            # Create a simple line chart with time on X and the selected column on Y.
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(df[datetime_col], df[col])
            ax.set_title(f"{col} over time{suffix}")
            ax.set_xlabel(datetime_col)
            ax.set_ylabel(col)
            fig.autofmt_xdate()  # rotate/format x labels for readability
            fig.tight_layout()

            # Save figure using a safe filename derived from the column name.
            out = outdir / f"{slugify(col)}{suffix}.png"
            fig.savefig(out, dpi=150)
            plt.close(fig)
            paths.append(str(out))
        return paths

    @staticmethod
    def histograms(
        df: pd.DataFrame,
        value_cols: list[str],
        outdir: Path,
        bins: int = 0,
        suffix: str = "",
    ) -> List[str]:
        """
        Render one histogram PNG per value column.

        Parameters
        ----------
        df : pd.DataFrame
            Input data containing the requested columns.
        value_cols : list[str]
            Column names to histogram (each coerced to numeric).
        outdir : Path
            Output directory to write PNG files.
        bins : int
            Number of bins; if 0, choose automatically using sqrt(N) clamped to [10, 50].
        suffix : str
            Optional suffix (e.g., '_D_mean') appended to filenames and titles.

        Returns
        -------
        List[str]
            Paths of the PNG files created (empty list if nothing was plotted).
        """
        paths: List[str] = []
        for col in value_cols:
            if col not in df.columns:
                continue  # skip columns that do not exist

            # Coerce to numeric; drop non-numeric entries for a clean histogram.
            series = pd.to_numeric(df[col], errors="coerce").dropna()
            if series.empty:
                continue  # nothing to plot

            # Choose bin count: sqrt(N) is a decent general-purpose rule; clamp to avoid extremes.
            auto_bins = max(10, min(50, int(np.sqrt(len(series))))) if bins == 0 else bins

            fig, ax = plt.subplots(figsize=(6, 4))
            ax.hist(series, bins=auto_bins)
            ax.set_title(f"{col} histogram{suffix}")
            ax.set_xlabel(col)
            ax.set_ylabel("Count")
            fig.tight_layout()

            out = outdir / f"{slugify(col)}_hist{suffix}.png"
            fig.savefig(out, dpi=150)
            plt.close(fig)
            paths.append(str(out))
        return paths
