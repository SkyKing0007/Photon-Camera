#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
if len(sys.argv)!=3: raise SystemExit('usage: validate_26621_r1.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2])
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'app').rglob('*')) if p.is_file()}
bh,ch=H(B),H(C)
assert len(bh)==1711 and len(ch)==1713,(len(bh),len(ch))
changed=sorted(p for p in set(bh)|set(ch) if bh.get(p)!=ch.get(p))
expected=sorted([
'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_accumulate_26621.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_correction_26620.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_downsample_26620.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_downsample_26621.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_reconstruct_26621.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_seed_26620.glsl',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/version.properties'])
assert changed==expected,(changed,expected)
ver=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726621' in ver and 'VERSION_BUILD=26621' in ver
# Unrelated image-formation/routing/gainmap/DNG owners remain byte-identical to successful 26620.
protected=[
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2DngColorShadow.java']
for rel in protected: assert (B/rel).read_bytes()==(C/rel).read_bytes(),f'protected owner changed: {rel}'
# New global tone has one named authority mirrored in every consumer that predicts or renders it.
rj=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
matcher=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java').read_text()
adj=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java').read_text()
render=(C/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
adapt=(C/'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl').read_text()
global_log=(C/'app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl').read_text()
cpp=(C/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
for tok in ['IRIS_26621_NEW_SIMPLIFIED_PRESENTATION_OWNER','IRIS_26621_LAPLACIAN_LEVELS = 7','IRIS_26621_REFERENCE_COUNT = 12',
            'IRIS_26621_DETAIL_SIGMA_EV = 0.35f','IRIS_26621_EDGE_SLOPE = 0.94f','IRIS_26621_SDR_WHITE_ANCHOR = 0.95f',
            'iris26621BuildLocalLaplacianTone(extendedLinearHdr)','absoluteFullResolutionToneMap=true','detailAlpha=1.0']:
    assert tok in rj,tok
assert rj.count('iris26621BuildLocalLaplacianTone(extendedLinearHdr)')==1
assert 'MotionV2Render.iris26621MapMotionSdrFinalGuide(guide, gain)' in matcher
assert 'IRIS_26621_NEW_SIMPLIFIED_TONE_PREDICTOR_PARITY=true' in adj
for text in [render,adapt,global_log,cpp]: assert 'iris26621MapMotionSdrFinalGuide' in text or 'iris26621GlobalTone' in text
# Old active 26620 correction-map owner is removed physically and cannot be referenced.
for oldrel in [
'app/src/main/assets/shaders/motionv2/local_laplacian_seed_26620.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_downsample_26620.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_correction_26620.glsl']:
    assert (B/oldrel).is_file() and not (C/oldrel).exists(),f'stale 26620 shader survived: {oldrel}'
for old in ['local_laplacian_seed_26620','local_laplacian_downsample_26620','local_laplacian_correction_26620']:
    assert old not in rj+render+cpp,f'stale 26620 owner referenced: {old}'
for tok in ['motionV2LocalLaplacianMap','motionV2LocalLaplacianWidth','uLocalLaplacianMap','irisLocalLaplacianEv']:
    assert tok not in rj+render+cpp+(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java').read_text(),tok
# Local-Laplacian path: global mapped log -> matched REDUCE -> reference remap -> weighted Laplacian bands -> matched EXPAND reconstruction.
down=(C/'app/src/main/assets/shaders/motionv2/local_laplacian_downsample_26621.glsl').read_text()
remap=(C/'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl').read_text()
acc=(C/'app/src/main/assets/shaders/motionv2/local_laplacian_accumulate_26621.glsl').read_text()
rec=(C/'app/src/main/assets/shaders/motionv2/local_laplacian_reconstruct_26621.glsl').read_text()
for tok in ['ivec2 center=q*2','sum*(1.0/256.0)','irisKernel5']:
    assert tok in down,tok
for tok in ['a<=sigmaEv ? a : sigmaEv+edgeSlope*(a-sigmaEv)','IRIS_26621_TRUE_LOCAL_LAPLACIAN_REMAP']:
    assert tok in remap,tok
for text in [acc,rec]:
    for tok in ['IRIS_26621_MATCHED_PYRAMID','wm=0.125;wc=0.750;wp=0.125','wm=0.0;wc=0.5;wp=0.5','irisExpand']:
        assert tok in text,tok
for tok in ['weight=max(1.0-abs(localReference-referenceLog)/max(referenceStep,1.0e-6),0.0)','previous=firstReference!=0 ? 0.0']:
    assert tok in acc,tok
# Full-resolution absolute local target and scalar-only final application.
params=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java').read_text()
enc=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java').read_text()
for tok in ['motionV2LocalToneLogMap','motionV2LocalToneLogWidth','motionV2LocalToneLogHeight','motionV2LocalToneLogSourceWidth','motionV2LocalToneLogSourceHeight']:
    assert tok in params and tok in enc,tok
for tok in ['iris26621LocalToneLog','float localStrength=smoothstep(0.030,0.100,globalMapped)','linearSrgb=sourceRgb*(mappedGuide/sourceGuide)','linearSrgb=fitDisplayGamut(linearSrgb)']:
    assert tok in render,tok
assert 'sourcePixel*0.5' not in render,'26620 half-resolution correction geometry survived'
# True2x CPU and GPU consume the same absolute map, with no independent Local-Laplacian solve.
for tok in ['localToneMappedGuide','localToneLogMap','localToneLogW','localToneLogH','IRIS_26621_TRUE2X_SHARED_LOCAL_TONE_MAP',
            'uLocalToneLogMap','uLocalToneLogEnabled','irisLocalToneMappedGuide','IRIS_26621_SINGLE_TONE_OWNER_TRUE2X_GPU']:
    assert tok in cpp,tok
for forbidden in ['uLocalLaplacianMap','irisLocalLaplacianEv','localCorrectionEv']:
    assert forbidden not in cpp,forbidden
# Exact 26620 gainmap remains unchanged; UHDR keeps genuine >1 scene headroom authority.
assert (B/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_bytes()==(C/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_bytes()
# Lifecycle: release guide/bands before optional full-resolution direct readback; clear retained buffer after publication.
for tok in ['IRIS_26621_LOCAL_LAPLACIAN_PEAK_LIFETIME','bands[level] = null','guide[level] = null','finalTone.textureBuffer(scalar, true)']:
    assert tok in rj,tok
assert 'parameters.motionV2LocalToneLogMap = null;' in enc
print('PASS 26621 semantic/ownership/domain: exact 17-path presentation delta; old 26620 correction assets removed; one global tone plus one full-resolution fast Local-Laplacian owner; matcher/adaptive/1x/true2x parity; upstream/UHDR/DNG protected')
