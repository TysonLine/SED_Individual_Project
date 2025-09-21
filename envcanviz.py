#!/usr/bin/env python3
"""
EnvCanViz — minimal starter (read CSV + get column data)

Usage:
  # See available columns
  python envcanviz.py --input path/to/eccc.csv

  # Print the first N values from a specific column
  python envcanviz.py --input path/to/eccc.csv --column "Temperature" --n 5
"""

import argparse
import csv
from pathlib import Path
from typing import List, Dict


def read_csv_file(path: str) -> List[Dict[str, str]]:
    """Read a CSV file (UTF-8) and return a list of rows as dicts."""
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def get_column(rows: List[Dict[str, str]], column: str) -> List[str]:
    """Extract a column (as strings) from the loaded rows."""
    if not rows:
        return []
    if column not in rows[0]:
        available = ", ".join(rows[0].keys())
        raise KeyError(f'Column "{column}" not found. Available columns: {available}')
    return [r.get(column, "") for r in rows]


def main() -> None:
    p = argparse.ArgumentParser(description="Read an Environment Canada CSV and get data from it.")
    p.add_argument("--input", required=True, help="Path to CSV downloaded from Environment Canada")
    p.add_argument("--column", help="Column name to extract")
    p.add_argument("--n", type=int, default=5, help="Show first N values when --column is provided (default: 5)")
    args = p.parse_args()

    csv_path = Path(args.input)
    if not csv_path.exists():
        raise SystemExit(f"Input CSV not found: {csv_path}")

    rows = read_csv_file(str(csv_path))

    if not rows:
        print("File loaded, but it has no data rows.")
        return

    if args.column:
        try:
            values = get_column(rows, args.column)
        except KeyError as e:
            raise SystemExit(str(e))
        print(f'First {min(args.n, len(values))} value(s) from "{args.column}":')
        for v in values[: args.n]:
            print(v)
    else:
        # No column requested: just show the headers so the user can decide later.
        headers = list(rows[0].keys())
        print("CSV loaded.")
        print("Available columns:")
        for h in headers:
            print(f" - {h}")


if __name__ == "__main__":
    main()
