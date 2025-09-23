"""
Small utility helpers for EnvCanViz.

- slugify: make safe filenames from free-form text (e.g., column names).
- ensure_outdir: create an output directory if it doesn't exist yet.
- inspect_frame: pretty-print columns (with dtypes) and a small sample of rows.
"""

from __future__ import annotations

import re
from pathlib import Path
import pandas as pd


def slugify(value: str) -> str:
    """
    Convert arbitrary text into a filesystem-friendly slug.

    Steps:
    - Collapse whitespace to single hyphens.
    - Remove any character that is not alnum, dot, underscore, or hyphen.
    - Fallback to 'figure' if the result would be empty.

    Examples
    --------
    "Temperature (°C)" -> "Temperature-C"
    "Total Precip (mm)" -> "Total-Precip-mm"
    """
    # Replace runs of whitespace with a single hyphen
    value = re.sub(r"\s+", "-", value.strip())
    # Strip characters that are likely to be unsafe in filenames
    value = re.sub(r"[^A-Za-z0-9._-]", "", value)
    return value or "figure"


def ensure_outdir(path: str | Path) -> Path:
    """
    Ensure that the output directory exists (create parents as needed).

    Parameters
    ----------
    path : str | Path
        Directory path to create if missing.

    Returns
    -------
    Path
        The Path object for the created/existing directory.
    """
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def inspect_frame(df: pd.DataFrame, n: int = 5) -> str:
    """
    Return a human-readable report of DataFrame columns and a sample of rows.

    Includes:
    - column names with their pandas dtypes, and
    - the first `n` rows rendered as a fixed-width table (without the index).

    Useful for `--inspect` so users can copy exact header names for --value-cols.
    """
    lines = []
    lines.append("Columns:")
    for c in df.columns:
        lines.append(f"  - {c} ({df[c].dtype})")
    lines.append("")
    lines.append(f"First {n} rows:")
    try:
        # Neat aligned preview; some exotic dtypes can raise, so keep a fallback.
        lines.append(df.head(n).to_string(index=False))
    except Exception:
        lines.append(str(df.head(n)))
    return "\n".join(lines)
