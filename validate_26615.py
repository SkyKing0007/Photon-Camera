#!/usr/bin/env python3
from pathlib import Path
import re,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26615.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2])
def t(rel): return (C/rel).read_text()
def must(rel,*ss):
    s=t(rel)
    for x in ss:
        if x not in s: raise SystemExit(f'{rel}: missing {x}')
    return s
def forbid(rel,*ss):
    s=t(rel)
    for x in ss:
        if x in s: raise SystemExit(f'{rel}: forbidden {x}')
# Version is coupled to build.
v=t('app/version.properties')
for x in ['VERSION_NAME=0.9726615','VERSION_BUILD=26615']:
    if x not in v: raise SystemExit('version mismatch '+x)
# One spatial owner: low-frequency base + scalar RGB residual preservation. Exact shader text is embedded in the already-modified Java owner so successful 26614 same-universe patch mechanics remain unchanged.
d=must('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java','IRIS_26615_IRIS_OWNED_SPATIAL_APPEARANCE_OWNER','IRIS_26615_SPATIAL_BASE_SHORT_EDGE = 96','IRIS_26615_SPATIAL_BASE_SHADER','IRIS_26615_SPATIAL_APPLY_SHADER','glProg.useProgram(IRIS_26615_SPATIAL_BASE_SHADER)','glProg.useProgram(IRIS_26615_SPATIAL_APPLY_SHADER)','for(int j=-4;j<=4;j++)','for(int i=-4;i<=4;i++)','brightnessTargetGain','Output=vec4(rgb*gain,physicalGuide)','return target/(1.0+(target-1.0)*b)','motionV2SpatialAppearanceBaseGrid = grid','glDeleteFramebuffers','fullResolutionScratchAdded=false','return;')
if d.index('if (basePipeline.mParameters.motionV2Active)') > d.index('/* Exact successful Night behavior'): raise SystemExit('Motion owner must precede inherited Night path')
# Manual controls cannot replay automatic brightness; alpha provenance survives them.
forbid('app/src/main/assets/shaders/motionv2/iris_tone_controls.glsl','brightnessTargetGain')
must('app/src/main/assets/shaders/motionv2/iris_tone_controls.glsl','Output = vec4(max(rgb, vec3(0.0)), source.a);')
forbid('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisMotionToneControls.java','setVar("brightnessTargetGain"')
# Final Motion render is projection-only; Night uniforms remain allowed.
r=must('app/src/main/assets/shaders/motionv2/render.glsl','IRIS_26615','iris26615ProjectCanonicalSdrGuide','0.95')
if 'uniform float displayGain;' in r: raise SystemExit('Motion render global displayGain survived')
rj=must('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','IRIS_26615_SINGLE_SPATIAL_APPEARANCE_OWNER','iris26615SpatialAppearanceGain','iris26615ProjectCanonicalSdrGuide','iris26615RenderBrightnessAuthority=false')
if 'glProg.setVar("displayGain"' in rj: raise SystemExit('render writes duplicate displayGain')
# UHDR body must use immutable pre-spatial physical alpha only.
g=must('app/src/main/assets/shaders/motionv2/gainmap.glsl','hdrSample.a','motionHdrHandoff')
if 'uniform float displayGain;' in g: raise SystemExit('gainmap duplicate displayGain')
must('app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java','motionV2SpatialAppearanceBaseGrid','writeTrue2xNative','IRIS_26615_TRUE2X_SHARED_SPATIAL_APPEARANCE=true')
must('app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java','motionV2SpatialAppearanceBaseGrid','motionV2SpatialAppearanceBaseWidth','motionV2SpatialAppearanceBaseHeight')
# Viewfinder solver predicts the same owner instead of old global pixel multiplier.
vm=must('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java','iris26615BuildCandidateSpatialBase','iris26615SpatialBaseForSample','iris26615SpatialAppearanceGain','iris26615ProjectCanonicalSdrGuide','meterToneAuthority=IRIS_26615_SPATIAL_APPEARANCE_PREDICTOR')
# True2x CPU/GPU share the exact 1x base and physical-headroom provenance.
cpp=must('app/src/main/cpp/motionv2_jpeg444_jni.cpp','iris26615SpatialBaseAt','iris26615SpatialGain','uSpatialBase','uSpatialBaseSize','physicalGuide','GL_RGBA32F','GL_NEAREST','IRIS_26615_TRUE2X_SHARED_SPATIAL_BASE_GPU')
if cpp.count('return target/(1.f+(target-1.f)*b);')<1 or 'float b=clampf(std::max(base,0.f),0.f,1.f);' not in cpp: raise SystemExit('CPU spatial equation missing')
if cpp.count('return target/(1.0+(target-1.0)*b);')<1 or 'float b=clamp(max(base,0.0),0.0,1.0);' not in cpp: raise SystemExit('GPU spatial equation missing')
# No Photon APK processing reuse in changed implementation.
for rel in [x for x in (Path(__file__).resolve().parent/'R1_26615_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]:
    s=t(rel)
    for bad in ['AutoExposureCurveNew','ModernInitial','LocalLaplacian']:
        if bad in s: raise SystemExit(f'{rel}: forbidden Photon implementation token {bad}')
print('PASS 26615 semantic ownership: one Iris spatial appearance owner; solver/render/UHDR/true2x parity; manual and HDR provenance separation')
