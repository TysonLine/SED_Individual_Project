# EnvCanViz (Minimal M1)

A tiny Python script that reads an **Environment Canada** CSV you downloaded and lets you:
1. See the **available columns**.
2. Print the **first N values** from a chosen column.

> This is the first milestone (M1). Future milestones will add cleaning, plotting, and summaries.

---

## Features (current)
- Read a CSV file (standard library only).
- List headers.
- Extract the first *N* values from a specific column.

_No external dependencies. Uses Python’s built-in `csv` and `argparse`._

---

## Getting Started

### Prerequisites
- Python 3.x installed.

### Run
```bash
# Show available columns
python envcanviz.py --input path/to/eccc.csv

# Print the first 5 values from a specific column
python envcanviz.py --input path/to/eccc.csv --column "Temperature" --n 5
