#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26622_r1_regressions.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2])
rel='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
b=(B/rel).read_text(); c=(C/rel).read_text()
# Exact device failure from 26621: guide[last].mSize is used by telemetry after guide[] entries were closed and nulled.
old='''                    + " coarsest=" + guide[IRIS_26621_LAPLACIAN_LEVELS - 1].mSize.x
                        + "x" + guide[IRIS_26621_LAPLACIAN_LEVELS - 1].mSize.y'''
assert old in b,'26621 device crash condition not reproduced in authority'
brelease=b.index('guide[level] = null;'); blog=b.index('Log.i(Name, "IRIS_26621_NEW_SIMPLIFIED_LOCAL_LAPLACIAN"')
assert brelease < blog and b.index(old) > brelease,'26621 post-release dereference ordering not reproduced'
# Candidate must snapshot diagnostic dimensions while guide is alive, then never dereference guide after release.
assert 'IRIS_26622_LOCAL_LAPLACIAN_TELEMETRY_LIFETIME' in c
cw=c.index('final int coarsestWidth = guide[IRIS_26621_LAPLACIAN_LEVELS - 1].mSize.x;')
ch=c.index('final int coarsestHeight = guide[IRIS_26621_LAPLACIAN_LEVELS - 1].mSize.y;')
release=c.index('guide[level] = null;'); log=c.index('Log.i(Name, "IRIS_26621_NEW_SIMPLIFIED_LOCAL_LAPLACIAN"')
assert cw < release and ch < release < log
assert 'guide[IRIS_26621_LAPLACIAN_LEVELS - 1].mSize' not in c[release:],'post-release guide texture dereference survived'
assert '+ " coarsest=" + coarsestWidth' in c and '+ "x" + coarsestHeight' in c
# Do not "fix" the crash by bypassing or disabling the presentation architecture.
assert c.count('iris26621BuildLocalLaplacianTone(extendedLinearHdr)')==1
assert 'absoluteFullResolutionToneMap=true' in c
assert 'correctionMap=false' in c
assert 'detailAlpha=1.0' in c
assert 'keepFinal = true;' in c and 'return finalTone;' in c
for forbidden in [
    'catch (NullPointerException',
    'localToneEnabled=false',
    'iris26621BuildLocalLaplacianTone(extendedLinearHdr) == null',
]:
    assert forbidden not in c,forbidden
# All new global-tone and shader math remains outside the 26622 runtime delta.
for path in [
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_accumulate_26621.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_downsample_26621.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_reconstruct_26621.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
]:
    assert (B/path).read_bytes()==(C/path).read_bytes(),f'26621 presentation math unexpectedly changed: {path}'
print('PASS 26622 regressions: exact 26621 device NPE reproduced; coarsest telemetry dimensions snapshotted before guide release; no post-release GLTexture dereference; tone/Local-Laplacian math unchanged')
