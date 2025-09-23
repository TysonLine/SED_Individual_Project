"""
Lightweight data processing utilities.

This module keeps the core "data shaping" steps small and explicit:
- numeric coercion for selected columns,
- optional handling of string "Trace" values (e.g., precipitation),
- inclusive date-range filtering on a detected datetime column,
- optional time resampling with common aggregations.

All heavier logic (I/O, plotting, summarizing) lives elsewhere so each piece
is easy to read, test, and swap out later if needed.
"""

from __future__ import annotations

from typing import Iterable, Optional
import pandas as pd


class DataProcessor:
    """Lightweight cleaning, filtering, and (optional) resampling."""

    @staticmethod
    def to_numeric(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
        """
        Coerce specific columns to numeric dtype.

        Any value that cannot be parsed becomes NaN (errors='coerce'), which prevents
        crashes during plotting/aggregation and lets downstream code drop/ignore NaNs.

        Parameters
        ----------
        df : pd.DataFrame
            Input data.
        columns : Iterable[str]
            Exact column names to coerce (no-op for names not present).

        Returns
        -------
        pd.DataFrame
            The same DataFrame object with selected columns converted in place.
        """
        for col in columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df

    @staticmethod
    def handle_trace_values(
        df: pd.DataFrame,
        columns: Iterable[str],
        trace_token: str = "Trace",
        replacement: float = 0.0,
    ) -> pd.DataFrame:
        """
        Treat a string token (default: 'Trace') as a numeric replacement (default: 0.0).

        This is handy for precipitation fields where very small amounts are recorded
        as 'Trace' rather than a number. We only modify the columns you specify.

        Parameters
        ----------
        df : pd.DataFrame
            Input data.
        columns : Iterable[str]
            Columns to scan for the trace token.
        trace_token : str
            Case-insensitive token to match.
        replacement : float
            Value to substitute for the token (e.g., 0.0).

        Returns
        -------
        pd.DataFrame
            The same DataFrame with replacements applied in place.
        """
        for col in columns:
            if col in df.columns:
                s = df[col].astype(str).str.strip()
                mask = s.str.lower() == str(trace_token).lower()
                if mask.any():
                    df.loc[mask, col] = replacement
        return df

    @staticmethod
    def filter_date_range(
        df: pd.DataFrame,
        datetime_col: str,
        start: Optional[str],
        end: Optional[str],
    ) -> pd.DataFrame:
        """
        Keep only rows within an inclusive datetime range.

        If start or end is None, that bound is not applied. Invalid bounds are coerced
        with pandas.to_datetime(..., errors='coerce').

        Parameters
        ----------
        df : pd.DataFrame
            Input data with a parsed datetime column.
        datetime_col : str
            Name of the datetime column (must already be dtype datetime64).
        start : Optional[str]
            Lower bound (inclusive), e.g., '2025-01-01'.
        end : Optional[str]
            Upper bound (inclusive), e.g., '2025-01-31'.

        Returns
        -------
        pd.DataFrame
            Filtered view (new DataFrame object).
        """
        if datetime_col not in df.columns:
            return df
        if start:
            df = df[df[datetime_col] >= pd.to_datetime(start, errors="coerce")]
        if end:
            df = df[df[datetime_col] <= pd.to_datetime(end, errors="coerce")]
        return df

    @staticmethod
    def resample(
        df: pd.DataFrame,
        datetime_col: str,
        freq: Optional[str],
        agg: str,
        cols: list[str],
    ) -> Optional[pd.DataFrame]:
        """
        Downsample/aggregate time series by a given frequency.

        Examples
        --------
        freq='D'  → daily
        freq='W'  → weekly
        freq='M'  → month-end

        Aggregations supported: 'mean', 'sum', 'min', 'max', 'median'.

        Parameters
        ----------
        df : pd.DataFrame
            Input data with a parsed datetime column.
        datetime_col : str
            Name of the datetime column.
        freq : Optional[str]
            Pandas resample frequency string. If falsy, returns None (caller can skip resampling).
        agg : str
            One of 'mean', 'sum', 'min', 'max', 'median'.
        cols : list[str]
            Value columns to include in the resampled output.

        Returns
        -------
        Optional[pd.DataFrame]
            Resampled frame with the datetime index reset to a column, or None if freq is falsy
            or inputs are not suitable (missing columns, etc.).
        """
        # Validate inputs: need a frequency, a valid datetime column, and present value columns.
        if not freq or datetime_col not in df.columns or not set(cols).issubset(df.columns):
            return None

        # Set the time index just for resampling, then pick the requested columns.
        g = df.set_index(datetime_col)[cols].resample(freq)

        # Choose aggregation
        if   agg == "mean":   out = g.mean()
        elif agg == "sum":    out = g.sum()
        elif agg == "min":    out = g.min()
        elif agg == "max":    out = g.max()
        elif agg == "median": out = g.median()
        else:
            raise SystemExit(f"Unsupported agg: {agg}. Choose from mean,sum,min,max,median.")

        # Drop rows that are entirely NaN after aggregation and restore a regular column for time.
        return out.dropna(how="all").reset_index()
