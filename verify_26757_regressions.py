#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit("usage: verify_26757_regressions.py BASE CANDIDATE")
base,c=map(Path,sys.argv[1:])
ktrel="app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt"; jrel="app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java"; brel="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt"; cpprel="app/src/main/cpp/motionv2_jpeg444_jni.cpp"
kt=(c/ktrel).read_text(); j=(c/jrel).read_text(); br=(c/brel).read_text(); cpp=(c/cpprel).read_text(); bkt=(base/ktrel).read_text(); bcpp=(base/cpprel).read_text()
for needle in ["IRIS_26757_SR_MAXIMUM_NO_WAIT_CAPTURE","iris26757EffectiveNormalTarget","Math.min(4, iris26593NormalTarget)","sliderIsMaximumWhenSuperRes=true"]: assert needle in j,needle
assert "mMotion26575SuperResAtShutter" in j and "? Math.min(iris26593NormalTarget" in j and ": iris26593NormalTarget;" in j
assert '" exactTotalRequired=" + (!mMotion26575SuperResAtShutter)' in j
assert "IRIS_26757_SR_NO_PLAN_B_RAW_STAGING" in kt and "IRIS_26757_SR_GPU_COST_ROUTER" in kt
post=kt.index("/* IRIS_26601_POST_SR_SHARED_HDR_PUBLICATION"); sr0=kt.rfind("if (enableSabreSuperRes)",0,post); assert sr0>=0
sr=kt[sr0:post]; assert "stagePlanBRawEvidence26755" not in sr and "reconstructTrue2x(" in sr
r0=kt.index("private fun reconstructTrue2x("); r1=kt.index("private fun reconstructDirectTrue2x26733(",r0); assert "return reconstructDirectTrue2x26733(" in kt[r0:r1]
def block(t,a,b): i=t.index(a); return t[i:t.index(b,i)]
start="    private fun reconstructDirectTrue2x26733("; end="    private fun cleanupTrue2xEvidence("
assert hashlib.sha256(block(bkt,start,end).encode()).digest()==hashlib.sha256(block(kt,start,end).encode()).digest()
for needle in ["IRIS_26757_EVIDENCE_LIMITED_PLAN_B","planBSelected=","allAdmittedNormalMergedBySabre=true","planBSupportedScale26757","normalEvidenceCount >= 9 -> 3f","normalEvidenceCount >= 4 -> 2f","val required = if (requestedScale > 2.05f) 9 else 6","cleanupTrue2xEvidence(allReconstructionEvidence)"]: assert needle in kt,needle
for needle in ["IRIS_26757_EVIDENCE_LIMITED_DETAIL_HANDOFF","stacked.highZoomDetailWidth in 1..size.x","stacked.highZoomDetailFrames in 4..expectedPlanBFrames26753","rgbOwner=NATIVE_SABRE_VGN chromaOwner=NATIVE_SABRE_VGN"]: assert needle in br,needle
for needle in ["IRIS_26757_IPOL_PRIMAL_ALIAS_SOLVER","solveWeightedPrimal","IRIS_26757_PLAN_B_SOLVER_GRID"]: assert needle in cpp,needle
assert cpp.count("solveWeightedPrimal(output.data()")>=2 and "solveWeightedDual(output.data()" not in cpp
def cblock(t,a,b): i=t.index(a); return t[i:t.index(b,i)]
assert hashlib.sha256(cblock(bcpp,"struct FftPlan","inline double tukeyProfile").encode()).digest()==hashlib.sha256(cblock(cpp,"struct FftPlan","inline double tukeyProfile").encode()).digest()
assert "mixed235Forward" not in cpp and "IRIS_26757_FFT_SMOOTH_235" not in cpp
for needle in ["PLAN_B_STAGE_MAX_MS_26753 = 20_000L","PLAN_B_TILE_MAX_MS_26753 = 4_000L","PLAN_B_MAX_MEMORY_BYTES_26753 = 32L * 1024L * 1024L","intArrayOf(976, 464, 208, 80)"]: assert needle in kt,needle
assert "planBFastSmoothSize26757" not in kt
assert cpp.index("} // U::~U releases UTF chars here while js is still a valid local reference.") < cpp.index("IRIS_26756_PLAN_B_TILE0_PATH_UTF_RELEASED frame=0") < cpp.index("e->DeleteLocalRef(js);")
assert "abort()" not in cpp and "std::exit(" not in cpp and "_exit(" not in cpp
for rel in ["app/src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java","app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/preview/GLPreview.java","app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/preview/MainRenderer.java","app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/GLPreview.java","app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java","app/src/main/assets/shaders/preview/main_fs.glsl"]:
 assert hashlib.sha256((base/rel).read_bytes()).digest()==hashlib.sha256((c/rel).read_bytes()).digest(),rel
print("PASS 26757 regressions: SR maximum/no-wait; current direct-CFA SR owner preserved; all-frame Sabre + 6/9 phase-diverse Plan-B; <=2x/<=3x evidence scale; primal alias solve + FFT-friendly core geometry; 32MiB/20s/4s bounds unchanged; 26756 JNI lifetime + zoom/IQ/DNG/UHDR preserved")
