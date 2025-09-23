"""
EnvCanViz package initializer.

This file keeps the public API small and documents the package version.
The class names listed in __all__ are defined in the following submodules:
- CSVLoader     → loader.py
- DataProcessor → processor.py
- Visualizer    → visualizer.py
- Summarizer    → summary.py
"""

# Controls what gets imported with:  from envcanviz import *
# (It does NOT import these names; it just declares the public API.)
__all__ = ["CSVLoader", "DataProcessor", "Visualizer", "Summarizer"]

# Package version string. Bump this when you make a notable change/release.
__version__ = "0.2.0"
