"""
EnvCanViz entry point (module executable)

This module glues together:
- argument parsing (cli.parse_args)
- CSV loading + datetime detection (CSVLoader)
- lightweight cleaning / filtering / resampling (DataProcessor)
- visual outputs (Visualizer) and numeric summaries (Summarizer)

Run from the project root (the directory that contains the `envcanviz/` folder):
    python -m envcanviz --input path/to/eccc.csv --inspect
"""

from __future__ import annotations

import sys
from pathlib import Path

from .cli import parse_args
from .loader import CSVLoader
from .processor import DataProcessor
from .visualizer import Visualizer
from .summary import Summarizer
from .utils import ensure_outdir, inspect_frame


def main(argv=None):
    # Parse all CLI flags and create the output directory if needed.
    args = parse_args(argv)
    outdir = ensure_outdir(args.outdir)

    # 1) Load CSV into a DataFrame and detect/parse a datetime column (unless user supplied one).
    df, dtcol = CSVLoader.load(args.input, datetime_col=args.datetime_col, encoding=args.encoding)

    # Guardrails: empty file or no rows → exit early with a clear message.
    if df.empty:
        raise SystemExit("CSV loaded but has no rows.")

    # If we still don't have a valid datetime column, either show an inspect report (if requested)
    # or exit with tips on how to proceed.
    if dtcol is None or dtcol not in df.columns:
        if args.inspect:
            print(inspect_frame(df))
            print("\nNo datetime column detected. Pass --datetime-col \"Exact Column Name\" if needed.")
            return
        msg = [
            "Could not detect a datetime column.",
            "Tips:",
            "  - Run with --inspect to see column names and sample rows.",
            "  - Or pass --datetime-col \"Exact Column Name\" explicitly.",
        ]
        raise SystemExit("\n".join(msg))

    # 2) Inspect-only mode: print columns + sample rows and the detected datetime, then exit cleanly.
    if args.inspect:
        print(inspect_frame(df))
        print(f"\nDetected datetime column: {dtcol}")
        return

    # 3) Decide which columns are numeric and which to visualize.
    #    - value columns are those you want to plot/summarize
    #    - numeric columns are coerced to numbers (defaults to value columns)
    wanted_cols = args.value_cols or []
    numeric_cols = args.numeric_cols if args.numeric_cols else wanted_cols

    # 4) Minimal cleaning: numeric coercion and optional "Trace"→0.0 handling (e.g., for precip).
    df = DataProcessor.to_numeric(df, numeric_cols)
    if args.trace_as_zero:
        df = DataProcessor.handle_trace_values(df, numeric_cols, trace_token="Trace", replacement=0.0)

    # 5) Optional date filtering (inclusive range on the detected datetime column).
    df = DataProcessor.filter_date_range(df, dtcol, args.start, args.end)

    # 6) Optional resampling (e.g., daily/weekly/monthly). If enabled, downstream steps
    #    operate on the resampled DataFrame instead of the raw/cleaned one.
    resampled = DataProcessor.resample(df, dtcol, args.resample, args.agg, wanted_cols) if args.resample else None
    target = resampled if resampled is not None else df
    # Suffix appended to output filenames to indicate resampling choice (e.g., _D_mean).
    suffix = "" if resampled is None else f"_{args.resample}_{args.agg}"

    made_any = False  # track whether we produced any outputs (files or printed summary)

    # 7) Numeric summary (prints to console AND saves summary CSV if there is valid numeric data).
    if args.summary and wanted_cols:
        sdf = Summarizer.table(target, wanted_cols)
        if not sdf.empty:
            print(sdf.to_string(index=False))
            Summarizer.save_csv(sdf, outdir / f"summary{suffix}.csv")
            made_any = True
        else:
            print("No numeric data available for summary (check column names).")

    # 8) Time-series plots (one PNG per value column).
    if args.timeseries and wanted_cols:
        # If we resampled, the first column of `target` is the new datetime index reset to a column,
        # so we use target.columns[0]; otherwise we use the original detected datetime column.
        paths = Visualizer.timeseries(
            target,
            target.columns[0] if resampled is not None else dtcol,
            wanted_cols,
            outdir,
            suffix=suffix,
        )
        if paths:
            print("Saved time-series:")
            for p in paths:
                print(" -", p)
            made_any = True
        else:
            print("No time-series generated (check column names).")

    # 9) Histograms (one PNG per value column) with auto bins when --bins=0.
    if args.hist and wanted_cols:
        paths = Visualizer.histograms(target, wanted_cols, outdir, bins=args.bins, suffix=suffix)
        if paths:
            print("Saved histograms:")
            for p in paths:
                print(" -", p)
            made_any = True
        else:
            print("No histograms generated (check column names).")

    # 10) Optionally export the cleaned (or resampled) DataFrame to CSV for reuse.
    if args.export_clean:
        (target).to_csv(outdir / (f"data_resampled{suffix}.csv" if resampled is not None else "data_clean.csv"),
                        index=False)
        print("Exported cleaned data CSV.")
        made_any = True

    # Friendly reminder when no action flags were provided.
    if not made_any:
        print("Nothing produced. Did you pass any actions? (--timeseries / --hist / --summary / --export-clean)")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Provide a clean exit code on Ctrl+C.
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)
