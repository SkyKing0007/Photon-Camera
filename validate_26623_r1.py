#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26623_r1.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2])
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'app').rglob('*')) if p.is_file()}
bh,ch=H(B),H(C); assert len(bh)==1713 and len(ch)==1713,(len(bh),len(ch))
changed=sorted(p for p in set(bh)|set(ch) if bh.get(p)!=ch.get(p))
expected=sorted([
'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/version.properties'])
assert changed==expected,(changed,expected)
ver=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726623' in ver and 'VERSION_BUILD=26623' in ver
# Presentation ownership: one adaptive upper-tone map, same four statistics, no new exposure owner.
render=(C/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
global_log=(C/'app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl').read_text()
adaptive=(C/'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl').read_text()
for s,name in [(render,'render'),(global_log,'global_log'),(adaptive,'adaptive_color')]:
    for tok in ['IRIS_26623_SCENE_ADAPTIVE_UPPER_TONE','iris26623HighlightPressure','iris26623MapMotionSdrFinalGuide',
                'iris26623ToneBroadNearFraction','iris26623ToneHardFraction','iris26623ToneBaseSceneWhite','iris26623ToneAdaptiveSceneWhite',
                'const float upperStart=0.65','mix(0.925,0.885,pressure)','mix(0.270,0.200,pressure)']:
        assert tok in s,(name,tok)
    assert 'sceneRecognition' not in s
# Old 26621 map may remain as legacy reference only; active Motion calls must target 26623.
assert 'return iris26623MapMotionSdrFinalGuide(sourceGuide);' in render
assert 'float globalMapped=iris26623MapMotionSdrFinalGuide(sourceGuide);' in render
assert 'float mapped=iris26623MapMotionSdrFinalGuide' in global_log
assert 'float mappedFinal=iris26623MapMotionSdrFinalGuide(sourceGuide);' in adaptive
# Java owns uniforms/telemetry only; motionV2DisplayGain remains sole brightness request.
j=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
for tok in ['IRIS_26623_UPPER_TONE_START = 0.65f','IRIS_26623_SPARSE_WHITE_ANCHOR = 0.925f','IRIS_26623_BROAD_WHITE_ANCHOR = 0.885f',
            'IRIS_26623_SPARSE_WHITE_SLOPE = 0.270f','IRIS_26623_BROAD_WHITE_SLOPE = 0.200f','iris26623SetAdaptiveUpperToneUniforms()',
            'IRIS_26623_ADAPTIVE_UPPER_TONE_SDR_UHDR_SR_PARITY=true']:
    assert tok in j,tok
assert j.count('iris26623SetAdaptiveUpperToneUniforms();')==2
# Local Laplacian algorithm and true2x/UHDR publication remain byte-identical to successful 26622 except global-log seed.
for path in [
'app/src/main/assets/shaders/motionv2/local_laplacian_downsample_26621.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_accumulate_26621.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_reconstruct_26621.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java']:
    assert (B/path).read_bytes()==(C/path).read_bytes(),f'protected presentation/runtime owner changed: {path}'
# SHORT change is telemetry only and preserves GPU loss-mask release ordering/timing.
k=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
for tok in ['IRIS_26623_SHORT_BROAD_LOSS_SUPPORT_TELEMETRY','readOnly=true outputUnchanged=true','retainBytes = true','centerPlus4CardinalNormalLoss','postSourceClipTargetAccumulator']:
    assert tok in k,tok
release=k.index('shortLossCandidateWeight26607, "26607 SHORT loss-candidate proof"')
frame_release=k.index('releaseOwnedTexture(frameWeight, "26607 ordinary SHORT post-dilation weight")')
rescue=k.index('logSabreShortBroadLossSupport26623(')
assert release < frame_release < rescue,'SHORT GPU release order changed'
# No telemetry may alter core SHORT weights/masks/resolve functions.
for token in ['renderSabreShortRescueWeight26607(','renderSabreUnifiedBracketCoverage26604(','shortHeadroomOwner=SAME_AS_COMMON_RBF_FINAL_0P75_PERCENT']:
    assert token in k,token
print('PASS 26623 semantic/ownership/domain: exact 7-path delta; adaptive upper tone only above source guide 0.65; Local-Laplacian/true2x/UHDR/reconstruction protected; SHORT change read-only telemetry with original GPU release ordering')
