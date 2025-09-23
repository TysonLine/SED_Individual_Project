"""
Command-line interface (CLI) for EnvCanViz.

This module centralizes *all* flag definitions so:
- help text is consistent in one place,
- tests can import/parse args without running the program,
- __main__.py focuses on orchestration (not CLI wiring).

Typical runs:
    # Inspect columns and a few sample rows (no outputs produced)
    python -m envcanviz --input path/to/eccc.csv --inspect

    # Make figures & summary (value column names must match your CSV headers)
    python -m envcanviz --input path/to/eccc.csv \
        --value-cols "Temperature (°C)" "Wind Speed (km/h)" \
        --timeseries --hist --summary
"""

from __future__ import annotations
import argparse


def parse_args(argv=None):
    """
    Build and parse all CLI options.

    Returns
    -------
    argparse.Namespace
        Parsed arguments consumed by envcanviz.__main__.main().
    """
    p = argparse.ArgumentParser(description="EnvCanViz — visualize Environment Canada CSV data.")

    # --------------------------
    # Core inputs
    # --------------------------
    p.add_argument("--input", required=True, help="Path to downloaded CSV from Environment Canada")
    p.add_argument("--encoding", default=None, help="Optional CSV encoding (e.g., latin1)")
    p.add_argument("--datetime-col", default=None, help="Name of datetime column (auto-detect if omitted)")
    p.add_argument(
        "--value-cols",
        nargs="+",
        help="One or more numeric columns to visualize (exact names). "
             "Required for --timeseries/--hist/--summary."
    )
    p.add_argument(
        "--numeric-cols",
        nargs="*",
        default=None,
        help="Columns to coerce to numeric (defaults to --value-cols if omitted)."
    )
    p.add_argument("--start", default=None, help="Filter start date (YYYY-MM-DD)")
    p.add_argument("--end",   default=None, help="Filter end date (YYYY-MM-DD)")

    # --------------------------
    # Actions (what to produce)
    # --------------------------
    # NOTE: --inspect is the only action that does not require --value-cols.
    p.add_argument("--inspect", action="store_true", help="Print columns + sample rows, then exit")
    p.add_argument("--timeseries", action="store_true", help="Generate time-series plots for value-cols")
    p.add_argument("--hist", action="store_true", help="Generate histograms for value-cols")
    p.add_argument("--summary", action="store_true", help="Print and save a numeric summary for value-cols")
    p.add_argument("--export-clean", action="store_true", help="Export cleaned or resampled data to CSV")

    # --------------------------
    # Cleaning / output options
    # --------------------------
    p.add_argument(
        "--trace-as-zero",
        action="store_true",
        help="Treat string 'Trace' values as 0.0 in numeric-cols (useful for precipitation)."
    )
    p.add_argument("--outdir", default="figures", help="Directory for PNG/CSV outputs (default: figures)")

    # --------------------------
    # Optional time resampling
    # --------------------------
    p.add_argument("--resample", default=None, help="Frequency for resample (e.g., D, W, M). Omit to skip.")
    p.add_argument("--agg", default="mean", help="Aggregation for resample: mean,sum,min,max,median (default: mean)")
    p.add_argument("--bins", type=int, default=0, help="Histogram bin count (0 = auto based on data size)")

    return p.parse_args(argv)
