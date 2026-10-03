#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit("usage: verify_26756_plan_b_bounds.py BASE CANDIDATE")
base,c=map(Path,sys.argv[1:]); rel="app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt"
assert hashlib.sha256((base/rel).read_bytes()).digest()==hashlib.sha256((c/rel).read_bytes()).digest()
kt=(c/rel).read_text(); assert "PLAN_B_MAX_MEMORY_BYTES_26753 = 32L * 1024L * 1024L" in kt and "intArrayOf(512, 384, 256, 192, 128)" in kt and "PLAN_B_STAGE_MAX_MS_26753 = 20_000L" in kt and "PLAN_B_TILE_MAX_MS_26753 = 4_000L" in kt
zoom=(c/"app/src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java").read_text(); assert "LOCAL_MAX_ZOOM = 30.0f" in zoom and "anchor * LOCAL_MAX_ZOOM" in zoom
print("PASS 26756 bounds inheritance: successful 26755 32MiB/core<=512/20s+4s/local-30x mechanics byte-preserved")
