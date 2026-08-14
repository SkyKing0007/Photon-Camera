#!/usr/bin/env python3
"""Single 26480 transform entry point.

The precursor expresses the first mechanically validated 26479->26480 anchors.
The V2 post-transform immediately replaces every rejected V1 behavior before
candidate compilation or live-source application. They execute in isolated
Python globals; no V1 candidate is ever built or copied to live app source.
"""
from pathlib import Path
import runpy
import sys

here = Path(__file__).resolve().parent
root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
for script in [
    here / "transform_26480_precursor_v1.py",
    here / "transform_26480_bjzhou_integrated_v2_post.py",
]:
    old = sys.argv[:]
    try:
        sys.argv = [str(script), str(root)]
        runpy.run_path(str(script), run_name="__main__")
    finally:
        sys.argv = old
print("26480 integrated V2 single-entry transform PASS")
