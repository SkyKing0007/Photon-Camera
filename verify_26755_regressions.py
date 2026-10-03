#!/usr/bin/env python3
from pathlib import Path
import sys,hashlib,re
if len(sys.argv)!=3: raise SystemExit("usage: verify_26755_regressions.py BASE CANDIDATE")
base,cand=map(Path,sys.argv[1:]); safe=(cand/"app/src/main/java/com/hinnka/mycamera/model/SafeImage.kt").read_text(); kt=(cand/"app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt").read_text()
# Exact RAW staging must finish before any original owner is released.
for s in ["IRIS_26755_PLAN_B_RAW_LIFETIME_OWNER","copyRawBackingTo","Staged RAW bytes=","owned.size == indices.size","images.forEach { it.close() }","diskBackedNormals=${owned.size}"]: assert s in safe+kt,s
stage=kt[kt.index("private fun stagePlanBRawEvidence26755"):kt.index("private fun planBEstimatedTileBytes26753")]
assert stage.index("owned.size == indices.size") < stage.index("images.forEach { it.close() }")
# Real fix path has only the minimal proof telemetry.
for s in ["IRIS_26755_PLAN_B_MEMORY_BEFORE_RAW_RELEASE","IRIS_26755_PLAN_B_MEMORY_AFTER_RAW_RELEASE","IRIS_26755_PLAN_B_TILE0_NATIVE_BEGIN","IRIS_26755_PLAN_B_TILE0_NATIVE_DONE","/proc/self/status","VmRSS:"]: assert s in kt,s
# Java maxHeap is forbidden as Plan-B memory authority; solver own peak fixed at 32 MiB and <=512 core.
region=kt[kt.index("private fun planBMemoryBudgetBytes26753"):kt.index("private fun planBEstimatedTileBytes26753")]; assert "Runtime.getRuntime().maxMemory" not in region; assert "return PLAN_B_MAX_MEMORY_BYTES_26753" in region
assert "PLAN_B_MAX_MEMORY_BYTES_26753 = 32L * 1024L * 1024L" in kt and "PLAN_B_RAW_STAGE_MAX_MS_26755 = 8_000L" in kt
assert "intArrayOf(512, 384, 256, 192, 128)" in kt
# Plan B and Super Res both consume the staged population.
assert kt.count("stagePlanBRawEvidence26755(images, reconstructionEvidence).use") == 2
# Preserve 26754 architecture outside the three-file allowlist.
for rel in [
 "app/src/main/cpp/motionv2_jpeg444_jni.cpp",
 "app/src/main/java/com/hinnka/mycamera/processor/RawStackFrameCompat.kt",
 "app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java",
 "app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java",
 "app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt",
 "app/src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java",
 "app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java",
 "app/src/main/assets/shaders/preview/main_fs.glsl",
]: assert hashlib.sha256((base/rel).read_bytes()).digest()==hashlib.sha256((cand/rel).read_bytes()).digest(),rel
for s in ["referencePhysicalCameraId","lensStateIdentityOwner=false","PLAN_B_IRLS_MAX_UPDATES_26753 = 5","PLAN_B_STAGE_MAX_MS_26753 = 20_000L","PLAN_B_TILE_MAX_MS_26753 = 4_000L","ipolSpectralEnhancement=true","fixedFrameCount=true","directNativeGrid=true","secondScaler=false"]: assert s in kt,s
zoom=(cand/"app/src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java").read_text(); assert "LOCAL_MAX_ZOOM = 30.0f" in zoom and "anchor * LOCAL_MAX_ZOOM" in zoom and "localZoom / hardwareZoom" in zoom
bs={p.relative_to(base/"app").as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (base/"app/src/main/assets/shaders").rglob("*") if p.is_file()}; cs={p.relative_to(cand/"app").as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (cand/"app/src/main/assets/shaders").rglob("*") if p.is_file()}; assert bs==cs and len(bs)==271
print("PASS 26755 regressions: complete RAW staging-before-release; RSS/tile proof markers; 32MiB/512 bounded solver; both Plan-B routes staged; 26754 physical owner/IPOL/zoom/IQ/DNG/UHDR preserved")
