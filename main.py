#!/usr/bin/env python3
"""Copy the rendered front page to the grader's output directory.

Standard library only: nothing is installed before this runs.
"""
import os
import shutil
from pathlib import Path


def main():
    here = Path(__file__).resolve().parent
    out = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "out"))
    out.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(here / "entry.png", out / "entry.png")


if __name__ == "__main__":
    main()
