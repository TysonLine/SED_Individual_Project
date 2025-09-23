"""
Numeric summarization utilities.

This module computes small, human-readable summary tables for selected columns.
Design choices:
- Coerce mixed/dirty columns to numeric with `errors="coerce"` so non-numeric
  entries become NaN (and are ignored in stats).
- Use population standard deviation (ddof=0) for a simple, stable figure.
- Return a compact DataFrame you can print OR save as CSV.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Dict
import pandas as pd


class Summarizer:
    """Compute numeric summaries and save CSVs."""

    @staticmethod
    def table(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
        """
        Build a summary table for the given columns.

        For each column present in `df`, values are coerced to numeric; non-parsable
        entries become NaN and are excluded. Empty results are skipped.

        Parameters
        ----------
        df : pd.DataFrame
            Source data frame.
        cols : List[str]
            Exact column names to summarize.

        Returns
        -------
        pd.DataFrame
            A frame with rows like:
                column | count | mean | std | min | max
            Empty if no selected column yields numeric data.
        """
        rows: List[Dict] = []
        for col in cols:
            if col not in df.columns:
                continue
            s = pd.to_numeric(df[col], errors="coerce").dropna()
            if s.empty:
                continue
            rows.append({
                "column": col,
                "count": int(s.shape[0]),
                "mean": float(s.mean()),
                "std": float(s.std(ddof=0)),  # population stdev for stability
                "min": float(s.min()),
                "max": float(s.max()),
            })
        return pd.DataFrame(rows)

    @staticmethod
    def save_csv(df: pd.DataFrame, path: Path) -> None:
        """
        Save a DataFrame (e.g., the summary table) to CSV without the index.

        Parameters
        ----------
        df : pd.DataFrame
            Data to write.
        path : Path
            Destination file path (directories should already exist).
        """
        df.to_csv(path, index=False)
