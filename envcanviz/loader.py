"""
CSV loading + datetime detection.

This module is intentionally small and focused:
- Read a CSV downloaded from Environment Canada into a pandas DataFrame.
- Detect which column is the timestamp, parse it to datetime, drop bad rows, and sort.
- Return both the DataFrame and the detected/confirmed datetime column name.

Design goals:
- Be forgiving about column names (heuristic detection).
- Keep side effects minimal (only parse/clean the datetime column here).
- Leave other cleaning steps to DataProcessor.
"""

from __future__ import annotations

from typing import Optional, Tuple
import pandas as pd


class CSVLoader:
    """Load an Environment Canada CSV and detect/parse a datetime column."""

    @staticmethod
    def _score_datetime(series: pd.Series, sample: int = 100) -> float:
        """
        Heuristically score how "datetime-like" a column is.

        We try to parse the first `sample` values and compute the fraction that
        successfully convert to datetime. A score close to 1.0 indicates a strong
        candidate for a timestamp column.

        Parameters
        ----------
        series : pd.Series
            Column to evaluate.
        sample : int
            Number of leading rows to probe (limits cost on big files).

        Returns
        -------
        float
            Fraction in [0, 1] representing parse success rate.
        """
        try:
            parsed = pd.to_datetime(series.head(sample), errors="coerce", infer_datetime_format=True)
            return float(parsed.notna().mean())
        except Exception:
            # If anything goes wrong (e.g., mixed objects that explode parsing),
            # treat as score 0 — not a datetime column.
            return 0.0

    @classmethod
    def detect_datetime_col(cls, df: pd.DataFrame) -> Optional[str]:
        """
        Pick the most likely datetime column using two passes:

        1) Prefer columns whose header contains 'date' or 'time' AND parse successfully
           (score >= 0.8 on the first ~100 rows).
        2) Otherwise, score *all* columns and choose the best one if it also
           clears the 0.8 threshold.

        The 0.8 cutoff is a pragmatic balance: it tolerates some missing/bad values
        but avoids columns that only occasionally look like dates.

        Returns
        -------
        Optional[str]
            The chosen column name, or None if no good candidate is found.
        """
        # Pass 1: name-based candidates
        candidates = [c for c in df.columns if any(k in c.lower() for k in ["date", "time"])]
        for c in candidates:
            if cls._score_datetime(df[c]) >= 0.8:
                return c

        # Pass 2: score everything and take the best if it meets the threshold
        scored = sorted(((c, cls._score_datetime(df[c])) for c in df.columns),
                        key=lambda x: x[1], reverse=True)
        if scored and scored[0][1] >= 0.8:
            return scored[0][0]
        return None

    @classmethod
    def load(
        cls,
        path: str,
        datetime_col: Optional[str] = None,
        encoding: Optional[str] = None,
    ) -> Tuple[pd.DataFrame, Optional[str]]:
        """
        Read the CSV and normalize its time axis.

        Steps:
        - pandas.read_csv with optional `encoding` (e.g., 'latin1' for some files).
        - If `datetime_col` is not provided, detect it with `detect_datetime_col`.
        - If we have a datetime column:
            * Parse to pandas datetime (coerce invalid entries to NaT),
            * Drop rows where datetime is NaT (cannot be placed on a time axis),
            * Sort by time ascending.

        Parameters
        ----------
        path : str
            Filesystem path to the CSV.
        datetime_col : Optional[str]
            Exact name of the datetime column (skip detection if provided).
        encoding : Optional[str]
            Text encoding; None assumes UTF-8 (pandas default).

        Returns
        -------
        (pd.DataFrame, Optional[str])
            The loaded frame and the datetime column name (or None if undetected).
        """
        # Read the file; if a non-UTF-8 file throws a decode error, the caller can retry with --encoding.
        df = pd.read_csv(path, encoding=encoding) if encoding else pd.read_csv(path)

        # Auto-detect datetime column unless the caller specified it explicitly.
        if datetime_col is None:
            datetime_col = cls.detect_datetime_col(df)

        # If a datetime column is known and present, normalize it.
        if datetime_col is not None and datetime_col in df.columns:
            # Convert to pandas datetime; bad parses become NaT
            df[datetime_col] = pd.to_datetime(df[datetime_col], errors="coerce", infer_datetime_format=True)
            # Drop rows without a valid timestamp — downstream steps require a proper time axis
            df = df.dropna(subset=[datetime_col]).copy()
            # Ensure time-ordered data for plotting/resampling
            df = df.sort_values(by=datetime_col)

        return df, datetime_col
