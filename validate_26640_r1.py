#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26640_r1.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3]); root=Path(__file__).resolve().parent
changed=[x for x in (root/'R1_26640_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def tree(r): return {str(p.relative_to(r)):sha(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
b,c=tree(base),tree(cand)
assert len(b)==len(c)==1717 and set(b)==set(c)
actual=sorted(k for k in b if b[k]!=c[k]); assert actual==sorted(changed),(actual,changed)
assert len(actual)==5
sabre=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
gain=(cand/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()
render=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
ultra=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java').read_text()
ver=(cand/'app/version.properties').read_text()
# SHORT: component membership is no longer local merge authority.
assert sabre.count('IRIS_26640_LOCAL_SHORT_PROPAGATION_SUPPORT')==1
assert sabre.count('IRIS_26640_LOCAL_GEOMETRY_SAFE_COMPONENT_PROPAGATION')==1
for x in ['anchorQuadEvidence >= 2','anchorPhaseEvidence >= 4','coherenceMeasurablePhases >= 2',
          'float propagationCeiling = min(componentConfidence, localPropagationSupport);',
          'float localPropagationCeiling = clamp(anchor.z, 0.0, 1.0);']:
 assert x in sabre,x
for n in range(4):
 assert f'min(trustAt(n{n}), compatibleFlow(p, n{n}))))' in sabre,n
# Preserve stronger stationary boundary seed and legacy dormant marker; no global SHORT disable.
assert 'anchorQuadEvidence >= 4 && anchorPhaseEvidence >= 8' in sabre
assert 'selectedGeometryProof > 0.0' in sabre
assert sabre.count('IRIS_26606_SHORT_BOUNDARY_BOTTLENECK_PROPAGATION')==1
# UHDR: matched scalar linear intents, Android 1/64 offsets, no fixed brightness eligibility/dilation.
for stale in ['IRIS_26639_SELECTIVE_RECOVERABLE_HEADROOM_UHDR','const float hdrEntry=0.65','const float hdrFullEntry=0.85','iris26639MotionGainCapacity']:
 assert stale not in gain+render,stale
for x in ['IRIS_26640_MATCHED_SDR_HDR_INTENT_QUOTIENT','const float UHDR_OFFSET = 0.015625;',
          'ratio=clamp((hdrIntentY+UHDR_OFFSET)/(sdr+UHDR_OFFSET),1.0,safeMax);']:
 assert x in gain,x
assert 'motionHdrPointwiseThreshold=false' in render
assert 'motionHdrEligibilityDilation=false' in render
assert 'IRIS_26640_MEASURED_GAINMAP_CAPACITY' in render
assert 'actualPeakContentRatio' in render
assert 'Math.max(1.001f, Math.min(8.0f, maxRatio))' in ultra
# Version convention inherited unchanged except name/build.
assert 'VERSION_MINOR=9726440' in ver and 'VERSION_NAME=0.9726640' in ver and 'VERSION_BUILD=26640' in ver
print('PASS 26640 semantics: local SHORT propagation support + matched SDR/HDR scalar luminance quotient + exact 5-file scope')
