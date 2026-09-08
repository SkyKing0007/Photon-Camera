#!/usr/bin/env python3
from pathlib import Path
import hashlib, math, sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26613_v1.py BASE CANDIDATE')
B=Path(sys.argv[1]); C=Path(sys.argv[2])
ALLOW=[x.strip() for x in (Path(__file__).parent/'V1_26613_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip()]
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'app').rglob('*')) if p.is_file()}
b,c=H(B),H(C)
assert len(b)==1708 and len(c)==1708, (len(b),len(c))
changed=sorted(k for k in set(b)|set(c) if b.get(k)!=c.get(k))
assert changed==sorted(ALLOW), f'scope mismatch {changed}'
assert (B/'app/version.properties').read_text().find('VERSION_BUILD=26612')>=0
v=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726613' in v and 'VERSION_BUILD=26613' in v
core='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
assert b[core]==c[core], '26611 core Sabre/SHORT shader changed'
# No 26612 moving presentation authority survives in active publication owners.
pubs=[
'app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl','app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl','app/src/main/cpp/motionv2_jpeg444_jni.cpp','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java','app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java']
for rel in pubs:
    s=(C/rel).read_text()
    assert 'iris26612Map' not in s and 'iris26612Tone' not in s, rel
# Fixed-domain mapping fixtures.
def f(x):
    k=.80
    if x<=k:return x
    e=x-k; r=1-k; return k+r*e/(e+r)
for x in [0,.1,.4,.6,.79,.8]: assert f(x)==x
xs=[i/1000 for i in range(0,20001)]
ys=[f(x) for x in xs]
assert all(math.isfinite(y) for y in ys)
assert all(ys[i+1]>=ys[i] for i in range(len(ys)-1))
assert abs((f(.800001)-f(.8))/1e-6-1)<2e-5
for rel in ['app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl','app/src/main/cpp/motionv2_jpeg444_jni.cpp']:
    s=(C/rel).read_text(); assert '0.80' in s and ('IRIS_26613' in s or 'iris26613' in s), rel
# Clean HDR master is direct UHDR authority.
g=(C/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()
assert 'IRIS_26613_CLEAN_HDR_MASTER_GAIN_AUTHORITY' in g and 'float hdr=hdrBase;' in g
cpp=(C/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
assert 'hdrY=hdrBase' in cpp.replace(' ','') or 'float hdrY = hdrBase;' in cpp
# Exact Sabre support is transported read-only into post-VGN cleanup.
st=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
pp=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt').read_text()
for token in ['sabreRSupport26613','sabreSupportR = sabreRSupport26613','sabreSupportGb = resolveAccumulatedWeightsGb26604','IRIS_26613_SABRE_RGB_SUPPORT_PROVENANCE','changesTemporalWeights=false changesResolve=false changesVgn=false']:
    assert token in st, token
for token in ['uSabreWeightR','uSabreWeightsGb','uSabreSupportValid','sabreSupportEvidence','physicalFalseColorScore','legacyFalseColorScore','realColorConfidence']:
    assert token in pp, token
assert 'return copiedRWeight' in st
# DNG invariance explicit.
dng=['app/src/main/cpp/deps/tiny_dng_writer.h','app/src/main/cpp/dngCreator.cpp','app/src/main/cpp/dngCreator.h','app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java','app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java','app/src/main/java/com/particlesdevs/photoncamera/processing/IrisSabreSuperResDngWriter.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2DngColorShadow.java']
for rel in dng: assert b[rel]==c[rel]
print('PASS 26613 semantic validation: authority/scope/fixed-domain/clean-HDR/Sabre-support/DNG')
