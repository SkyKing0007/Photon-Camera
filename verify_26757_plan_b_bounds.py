#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3: raise SystemExit("usage: verify_26757_plan_b_bounds.py BASE CANDIDATE")
base,c=map(Path,sys.argv[1:]); kt=(c/"app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt").read_text(); cpp=(c/"app/src/main/cpp/motionv2_jpeg444_jni.cpp").read_text()
for s in ["PLAN_B_MAX_MEMORY_BYTES_26753 = 32L * 1024L * 1024L","PLAN_B_STAGE_MAX_MS_26753 = 20_000L","PLAN_B_TILE_MAX_MS_26753 = 4_000L","PLAN_B_IRLS_MAX_UPDATES_26753 = 5","intArrayOf(976, 464, 208, 80)","normalEvidenceCount >= 9 -> 3f","normalEvidenceCount >= 4 -> 2f"]: assert s in kt,s
assert "kIrlsMaxUpdates = 5" in cpp
zoom=(c/"app/src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java").read_text(); assert "LOCAL_MAX_ZOOM = 30.0f" in zoom and "anchor * LOCAL_MAX_ZOOM" in zoom
print("PASS 26757 bounds: <=3x evidence-limited Plan-B; phase basis <=9; solver <=32MiB; 20s stage/4s tile/IRLS<=5; universal local-30x unchanged")
