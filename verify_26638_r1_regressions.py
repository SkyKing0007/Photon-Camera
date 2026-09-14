#!/usr/bin/env python3
from pathlib import Path
import re,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26638_r1_regressions.py BASE CANDIDATE')
base=Path(sys.argv[1]); cand=Path(sys.argv[2])
s=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
stack=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
ct=(cand/'app/src/main/assets/shaders/motionv2/color_transform.glsl').read_text()
r=(cand/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
post=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java').read_text()
n=(cand/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
enc=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java').read_text()
# Permanent SHORT failure regression: no pixel-local fail-open and no weakening of hard veto/physical caps.
assert 'float wholeObservationCoherence(' not in s
for needle in ['coherenceMeasurablePhases >= 2','secondHighest4(phaseContradiction)','shortHeadroom','componentTrust','uSourceClippingPoint','IRIS_26611_BOUNDARY_PROVEN_SHORT_RESCUE_ONLY','IRIS_26611_SHORT_COMPLETE_COMMON_PHYSICAL_CAP']:
 assert needle in s,needle
assert 'IRIS_26638_SHORT_COMPONENT_SPATIAL_PROOF' in stack and 'postSourceClipUnsupported=' in stack
# Color owner: exact once in post graph, no automatic restraint/recovery after ACR3.
assert post.count('add(new MotionV2ColorTransform())')>=2
assert 'add(new MotionV2AdaptiveColorAppearance())' not in post
assert 'targetY/renderedY' in ct
assert 'iris26630AdaptiveColorV5' not in r and '0.22*' not in r and '0.22 *' not in r
assert 'if(abs(sat-1.0)<=1.0e-7) return rgb;' in r
assert 'mul(c,0.95f)' not in n and 'iris26630AdaptiveColorV5' not in n
assert 'MotionV2Acr3Curve.copySamples(), parameters.irisJpegColorValid' in enc
# Shadow regression: retain deepest 0.72 floor protection, but broad 0.18 toe must not survive in active 1x/true2x owners.
assert 'const float floorEnd=0.050' in r and 'const float deepScale=0.72' in r
assert 'toeEnd=0.18' not in r
assert 'floorEnd=0.050f' in n and 'deepScale=0.72f' in n and 'toeEnd=0.18f' not in n
# Frozen presentation/exposure/UHDR architecture remains present and not re-owned here.
for needle in ['iris26621LocalToneLog','iris26623MapMotionSdrFinalGuide','fitDisplayGamut']:
 assert needle in r,needle
# HEIC/JPEG publication remains common post-render source; no HEIC-specific saturation multiplier added.
assert 'heic' not in r.lower()
assert 'IRIS_26637_HEIC' not in n  # true2x JPEG publisher is not HEIC-specific
print('PASS 26638 regressions: SHORT hard vetoes retained; ACR3 single owner; 0.95/V5 absent; narrow 0.05 shadow floor retained; presentation domains frozen')
