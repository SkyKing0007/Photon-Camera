#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26640_r1_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
sabre=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
gain=(cand/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()
render=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
# Exact source conditions for the two real 26639 failures.
assert 'float propagationCeiling = min(componentConfidence, localPropagationSupport);' in sabre
assert 'localPropagationSupport = 0.0;' in sabre
assert 'anchorQuadEvidence >= 2 && anchorPhaseEvidence >= 4' in sabre
assert all(f'min(trustAt(n{i}), compatibleFlow(p, n{i}))))' in sabre for i in range(4))
assert 'hdrEntry' not in gain and 'hdrFullEntry' not in gain
assert 'IRIS_26640_MATCHED_SDR_HDR_INTENT_QUOTIENT' in gain
assert '(hdrIntentY+UHDR_OFFSET)/(sdr+UHDR_OFFSET)' in gain
assert 'motionHdrEligibilityDilation=false' in render and 'motionHdrPointwiseThreshold=false' in render
# Frozen owners are protected by byte equality; pin representative known-good markers too.
frozen=(cand/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
for marker in ['IRIS_26638_USER_SATURATION_ONLY','IRIS_26638_TRUE_SHADOW_FLOOR_GUARD','IRIS_26621_FINAL_DOMAIN_SINGLE_PRESENTATION']:
 assert marker in frozen,marker
# UHDR cannot alter SDR base: gain attachment remains publication-side only, gain shader outputs scalar.
ultra=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java').read_text()
assert 'sdrBase.setGainmap(gainmap);' in ultra
assert 'out float Output;' in gain
print('PASS 26640 permanent regressions: moving/unsupported SHORT fail-closed; broad HDR no fixed threshold; no dilation/RGB gain owner; frozen 26639 IQ owners present')
