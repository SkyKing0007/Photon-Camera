#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26667.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def text(root,r): return (root/r).read_text()
def sha(root,r): return hashlib.sha256((root/r).read_bytes()).hexdigest()
changed=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java',
'app/version.properties']
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'app').rglob('*')) if p.is_file()}
a,b=H(base),H(cand); assert len(a)==len(b)==1721
actual=sorted(r for r in a if a[r]!=b[r]); assert actual==sorted(changed),(actual,changed)
ver=text(cand,'app/version.properties'); assert 'VERSION_NAME=0.9726667' in ver and 'VERSION_BUILD=26667' in ver
main=text(cand,changed[2]); stack=text(cand,changed[1]); sabre=text(cand,changed[0])
assert 'IRIS_26667_FRAME_EXACT_PREVIEW_PRESENTATION' in main
assert 'mIris26663PresentedProtectionEv' not in main
assert 'getMotion26663ReferencePreviewProtectionEv' in main
assert 'iris26667PreviewGain' in main
assert 'IRIS_26667_LOCAL_CONFIDENCE_LONG_EVIDENCE_REQUEST' in stack
assert 'longEvidencePolicy26667=LOCAL_CONFIDENCE_GATE' in stack
assert 'longConfidenceStart26667=0.60 longConfidenceFull26667=0.90' in stack
assert 'longFinalWeightCap26667=1.25' in stack
for t in ['IRIS_26667_LOCAL_CONFIDENCE_LONG_EVIDENCE','smoothstep(0.60, 0.90, iris26667BaseWeight)','min(iris26667BaseWeight * iris26667AppliedBoost, 1.25)']:
    assert t in sabre,t
# Exact successful 26666 acquisition/rendering owners are protected, not reinterpreted.
protected=[
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/assets/shaders/preview/main_fs.glsl',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java']
for r in protected: assert sha(base,r)==sha(cand,r),r
cap=text(cand,protected[0]); matcher=text(cand,protected[5])
for t in ['IRIS_26661_GOOGLE_HDR_BRACKETING_CAPTURE_OWNER','iris26593ShortBudgetAllows = false','IRIS_26666_ADAPTIVE_SHADOW_LONG_PHOTON_EVIDENCE','postNormalHighlightShortRepair=false']:
    assert t in cap,t
assert 'MOTION_FIXED_MATCH_STRENGTH_PERCENT = 65.0f' in matcher
assert 'effectiveSupport' not in main+stack+sabre
print('PASS 26667 semantic/ownership: exact 26666 Google HDR acquisition/highlight renderer frozen; NORMAL temporal owner retained; preview extra slew removed; deep LONG extra authority local-confidence-gated and capped; effectiveSupport not used as frame-count authority')
