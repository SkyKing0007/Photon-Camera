#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26658_regressions.py BASE CANDIDATE')
base,cand=map(lambda x:Path(x).resolve(),sys.argv[1:3])
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
# Permanent generated-source exclusions: these directories are absent from compiled-candidate authority.
for root in (base,cand):
 assert not (root/'app/build').exists(), 'FAIL app/build contaminated authority'
 assert not (root/'app/.cxx').exists(), 'FAIL app/.cxx contaminated authority'
# 26653 rendering/color/edge protections must remain byte-identical.
protected=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2PhotonHighlightCompression.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/assets/shaders/motionv2/color_transform.glsl',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl']
for r in protected:
 assert sha(base/r)==sha(cand/r), 'FAIL 26653 protected regression '+r
bridge=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
stack=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
cap=(cand/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
# No old Motion LONG exclusion, no active post-shutter repair, no LONG leakage to SR/DNG.
assert 'CAPTURED_BUT_EXCLUDED_FROM_NORMAL_MOTION_SABRE' not in bridge
assert 'iris26593ShortSubmitted = false' in cap and 'iris26480ShortHighlightRequested = false' in cap
assert 'if (enableSabreSuperRes && frame.role == RawBurstFrameRole.NORMAL)' in stack
assert 'normalDngCoverage = if (' in stack and 'shadowLongFrameCount > 0 || highlightShortFrameCount > 0' in stack
assert 'sourceClipGuard = frame.role == RawBurstFrameRole.SHADOW_LONG' in stack
assert 'productionAccumulatorUnmodifiedByProof=true' in stack
# Night branching remains present; 26658 does not globally convert Night reference semantics.
assert 'if (parameters.irisNightActive)' in bridge and 'COMMON_SABRE_NIGHT_SHADOW_EVIDENCE' in bridge
print('PASS 26658 regressions: 26653 RGB/color/tone/edge owners byte-identical; Night branch retained; LONG excluded from DNG/SR; source clipping + proof retained')
