"""
⛔ THIS SCRIPT HAS BEEN QUARANTINED ⛔

DO NOT RUN THIS SCRIPT.

Why: rebuild_city_grids.py regenerates grids with flat default values
(1.92 degrees everywhere) and overwrites the real boundary grid with a
synthetic square grid — destroying real committed data.

What to use instead:
  python -m scripts.build_heatmaps nagpur
  python -m scripts.build_heatmaps pune
  python -m scripts.build_heatmaps

The original dangerous script is preserved at:
  scripts/DANGEROUS_DO_NOT_RUN_rebuild_city_grids.py.bak
"""

raise RuntimeError(
    "\n\n"
    "BLOCKED: rebuild_city_grids.py has been quarantined.\n"
    "This script overwrites real data with flat fake defaults.\n\n"
    "Use instead:\n"
    "  python -m scripts.build_heatmaps nagpur\n"
    "  python -m scripts.build_heatmaps pune\n"
)
