#!/usr/bin/env python3
"""Write and print a focused trace of the retained Soul-0 center-stall case."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from software.research.soul0.stall_trace import main


if __name__ == "__main__":
    raise SystemExit(main())
