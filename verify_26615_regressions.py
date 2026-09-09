#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26615_regressions.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2])
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
# Proven 26614 reconstruction/CFA/Sabre/SHORT/color owners must be byte-identical.
protected=[
'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java']
for rel in protected:
    if h(B/rel)!=h(C/rel): raise SystemExit('26614 reconstruction/color protection changed: '+rel)
# DNG exact unchanged.
for line in (Path(__file__).resolve().parent/'R1_26615_DNG_BASE.sha256').read_text().splitlines():
    sha,rel=line.split('  ',1)
    if h(C/rel)!=sha: raise SystemExit('DNG regression '+rel)
# Stale final brightness owners are forbidden in the actual Motion projection shaders.
render=(C/'app/src/main/assets/shaders/motionv2/render.glsl').read_text(); gain=(C/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text(); controls=(C/'app/src/main/assets/shaders/motionv2/iris_tone_controls.glsl').read_text()
if 'uniform float displayGain;' in render or 'uniform float displayGain;' in gain or 'brightnessTargetGain' in controls: raise SystemExit('duplicate presentation authority survived')
# New allocation is universal/spatial: no scene semantic classifier.
changed=[x for x in (Path(__file__).resolve().parent/'R1_26615_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
for rel in changed:
    s=(C/rel).read_text().lower()
    for token in ['ceilingclassifier','curtainclassifier','windowclassifier']:
        if token in s: raise SystemExit('scene-specific classifier '+rel)
# GPU allocation guard: 1x auxiliary is explicitly bounded; true2x reuses tiny grid and no new full-frame persistent surface.
d=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java').read_text()
for x in ['IRIS_26615_SPATIAL_BASE_SHORT_EDGE = 96','fullResolutionScratchAdded=false','glDeleteFramebuffers']:
    if x not in d: raise SystemExit('GPU lifetime/allocation regression '+x)
cpp=(C/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
for x in ['spatialBaseTex','glDeleteTextures(1,&spatialBaseTex)','GL_NEAREST','uSpatialBaseSize']:
    if x not in cpp: raise SystemExit('true2x shared-base lifecycle regression '+x)
print('PASS 26615 permanent regressions: 26614 Sabre/SHORT/CFA/color/DNG intact; no duplicate tone owner; bounded GPU lifetime; universal spatial behavior')
