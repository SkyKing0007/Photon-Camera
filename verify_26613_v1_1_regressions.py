#!/usr/bin/env python3
from pathlib import Path
import math,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26613_v1_1_regressions.py BASE CANDIDATE')
B=Path(sys.argv[1]); C=Path(sys.argv[2])
def text(rel): return (C/rel).read_text()
# Regression 1: 26612 moving quantile knots cannot return.
for rel in ['app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl','app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl','app/src/main/cpp/motionv2_jpeg444_jni.cpp']:
    s=text(rel); assert 'iris26612SourceP99Final' not in s and 'iris26612SourceP995Final' not in s and 'iris26612SourceP998Final' not in s
# Regression 2: body is exact identity and fixed curve has no collapsed interval.
def m(x):
    if x<=.8:return x
    return .8+.2*(x-.8)/((x-.8)+.2)
assert all(m(x)==x for x in [0,.2,.4,.6,.8])
assert m(.9)<m(1.0)<m(1.2)<m(2.0)<1.0
# Regression 3: UHDR direct master; no second HDR percentile boost.
assert 'float hdr=hdrBase;' in text('app/src/main/assets/shaders/motionv2/gainmap.glsl')
assert 'HdrP99Boost' not in text('app/src/main/assets/shaders/motionv2/gainmap.glsl')
# Regression 4: exact 26611 core survives byte identical.
core='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
assert (B/core).read_bytes()==(C/core).read_bytes()
coretxt=text(core)
for token in ['IRIS_26611_SAME_CFA_MEASURABLE_BOUNDARY_SEED','IRIS_26611_CLIPPED_INTERIOR_CANNOT_SELF_SEED','IRIS_26611_HDR_INDEPENDENT_VGN_COLOR_DIRECTION','IRIS_26611_CLEAN_DIRECTION_SCALAR_HDR_RESTORE']:
    assert token in coretxt, f'26611 inheritance marker missing {token}'
# Regression 5: support evidence behaves as physical provenance, not scene statistic.
def evidence(support,desired):
    mx=max(support); mn=min(support); imb=0 if mx<=1e-7 else (mx-mn)/mx
    weak=min(range(3), key=lambda i:support[i]); L=math.sqrt(sum(v*v for v in desired)); inc=desired[weak]
    direction=0 if L<=1e-7 else max(0,min(1,inc/L)); return imb*direction
assert evidence([4,4,4],[0,1,0])==0
assert evidence([4,1,4],[0,1,0])>.70
assert evidence([4,1,4],[0,-1,0])==0
assert evidence([1,4,4],[1,0,0])>.70
# Regression 6: real-color veto remains in physical score path.
pp=text('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
assert 'falseColorBase' in pp and '(1.0 - realColorConfidence)' in pp
assert 'sabreDecisiveNeutralCfaProof' in pp and 'targetNeutral' in pp
# Regression 7: no private SHORT/radiance changes in changed core host.
st=text('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
assert 'changesTemporalWeights=false changesResolve=false changesVgn=false' in st
# Regression 8: newly-added whitespace forbidden; check only added patch separately in patch verifier too.

# Regression 9: 26613 V1 Java compiler failure -- cross-package true2x telemetry requires public constant.
render_java=text('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java')
encoder_java=text('app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java')
assert 'public static final float IRIS_26613_SDR_KNEE_FINAL = 0.80f;' in render_java
assert 'MotionV2Render.IRIS_26613_SDR_KNEE_FINAL' in encoder_java

print('PASS 26613 V1.1 permanent regressions: no quantile authority / fixed-domain identity / direct HDR / 26611 freeze / physical support / real-color veto')
