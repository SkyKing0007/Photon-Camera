#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26758_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])

def read(root,rel): return (root/rel).read_text()
def sha(root,rel): return hashlib.sha256((root/rel).read_bytes()).hexdigest()
def same(rel):
    assert sha(base,rel)==sha(cand,rel),f'protected regression changed: {rel}'

stack_rel='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
shader_rel='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
bridge_rel='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'
cap_rel='app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java'
stack=read(cand,stack_rel); shader=read(cand,shader_rel); bridge=read(cand,bridge_rel); cap=read(cand,cap_rel)

# 26758 active routing: Plan B may remain as dead rollback/reference helpers, but there is no active call/backend branch.
assert stack.count('reconstructPlanB26753(')==1,'Plan B reconstruction has an active caller'
assert stack.count('stagePlanBRawEvidence26755(')==1,'Plan B RAW staging has an active caller'
assert 'rawResult.backend=="PLAN_B"' not in stack and 'rawResult.backend == "PLAN_B"' not in stack
assert 'stacked.true2xBackend=="PLAN_B"' not in bridge and 'stacked.true2xBackend == "PLAN_B"' not in bridge
assert 'IPOL_PLAN_B_DIRECT_WLS_OPTIONAL_IRLS' not in bridge,'stale Plan-B detail owner survived bridge'
assert stack.count('reconstructHighZoomDetail26718(')==2,'ordinary zoom direct-CFA detail must have exactly one definition+one active call'
assert stack.count('reconstructHighZoomRgb26720(')==1,'old high-zoom RGB owner became active'

# Universal lens-relative, same-lens route; no device/lens allowlist and no cross-lens detail source.
for token in ['IRIS_26758_UNIVERSAL_CROP_FIRST_DIRECT_CFA_DETAIL','samePhysicalLens=true','cropFirst=true',
              'maxSpatialScale=2.0','allAdmittedNormalMergedBySabre=true','directChromaOwner=false']:
    assert token in stack,token
for token in ['IRIS_26758_UNIVERSAL_LENS_RELATIVE_DIRECT_CFA_SR','localOutputZoom >= 1.10f',
              'physicalCameraId=${referenceStackFrame.physicalCameraId}','directNativePlanB=false',
              'rgbOwner=NATIVE_SABRE_VGN','DIRECT_CFA_TEMPORAL_ADAPTIVE']:
    assert token in bridge,token
assert 'no cross-lens frame mixing is allowed' in bridge
assert 'no cross-lens frame mixing' in stack

# Every admitted NORMAL remains in Sabre; only auxiliary direct-CFA detail is bounded to the existing 8-slot phase basis.
assert 'highZoomEvidence26718 += persistTrue2xEvidence' in stack
assert 'enableHighZoomDetail && frame.role == RawBurstFrameRole.NORMAL' in stack
assert 'TRUE2X_JPEG_MAX_EVIDENCE = 4 * TRUE2X_JPEG_EVIDENCE_PER_PHASE' in stack
assert 'TRUE2X_JPEG_EVIDENCE_PER_PHASE = 2' in stack
assert 'return selected.take(TRUE2X_JPEG_MAX_EVIDENCE)' in stack
assert 'allAdmittedNormalMergedBySabre=true' in stack
assert 'stacked.highZoomDetailFrames in 2..minOf(8, expectedNormalFrames26758)' in bridge

# Super Res remains the established direct-CFA GPU-first/full true-2x path and does not invoke Plan-B staging.
for token in ['IRIS_26758_SR_DIRECT_CFA_ONLY_ROUTER','backend=DIRECT_CFA_GPU_ONLY',
              'return reconstructDirectTrue2x26733(','IRIS_26757_SR_NO_PLAN_B_RAW_STAGING']:
    assert token in stack,token
assert 'stagePlanBRawEvidence26755(images, reconstructionEvidence)' not in stack
assert 'if(stacked.true2xBackend=="GPU")' in bridge
assert 'IRIS_26758_TRUE_DETAIL_RENDER_FUSED' in bridge
assert 'highResLumaOwner=$lumaOwner directChromaOwner=false' in bridge

# The proven 26757 true-2x direct reconstruction method itself is byte-identical; 26758 changes safety shaders/routing around it.
def method(src,name):
    a=src.index('    private fun '+name+'(')
    b=src.find('\n    private fun ',a+20)
    if b<0: b=len(src)
    return src[a:b]
assert method(read(base,stack_rel),'reconstructDirectTrue2x26733') == method(stack,'reconstructDirectTrue2x26733'), 'true2x direct-CFA method body changed'

# Paper-inspired adaptive uncertainty rejection applies to ordinary zoom and Super Res, with explicit old-artifact classes.
for token in ['IRIS_26758_ADAPTIVE_FUSION_REJECTION','rowAlternation','colAlternation','checkerAlternation',
              'aliasGate','highlightGate','confidence=clamp(phaseGate*temporalGate*signalGate*agreementGate*aliasGate*highlightGate']:
    assert token in shader,token
for token in ['IRIS_26758_SR_ADAPTIVE_ALIGNMENT_REJECTION','unsupportedRow','unsupportedCol','unsupportedChecker',
              'float aliasGate=1.0-irisSmooth01','float confidence = clamp(phaseGate * temporalGate * safetyGate * aliasGate']:
    assert token in shader,token
assert 'IRIS_26758_DIRECT_CFA_OBSERVATION_RELIABILITY' in shader
assert 'var source = highZoomRgbMerge26720' in shader,'ordinary scalar detail lost current observation/row-flicker reliability source'
for token in ['uObservationConfidence','uRowFlickerEnabled','uRowFlickerHarmonic','uRowFlickerAB','uRowFlickerStrength']:
    assert token in stack,token

# Highlight ownership/non-regression: direct detail fades out; current shared Sabre/VGN HDR guide remains the owner.
for token in ['val nativeHdrAuthority26601 = exportedTexture','nativeSabreVgnRgbChromaHighlightOwner=true',
              'flatHighlightVeto=true','highlightOwner=NATIVE_SABRE_VGN']:
    assert token in stack+bridge,token
assert 'float highlightGate' in shader
assert 'float boundedDetail=directDetail*shapeScale*confidence;' in shader and 'float logDetail=confidence>0.02 ?' in shader

# Capture behavior is inherited byte-for-byte: Super Res slider is a maximum/no-wait policy, not a latency requirement.
same(cap_rel)
for token in ['IRIS_26757_SR_MAXIMUM_NO_WAIT_CAPTURE','slider is a maximum evidence budget',
              'Math.min(4, iris26593NormalTarget)','iris26757EffectiveNormalTarget']:
    assert token in cap,token

# Protected final publication/preview/zoom owners remain byte-identical to successful 26757.
protected_candidates=[
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.kt',
 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/IrisZoomController.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLPreview.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/MainRenderer.java',
]
for rel in protected_candidates:
    if (base/rel).is_file(): same(rel)
# All asset shaders, DNG/UHDR/native are enforced elsewhere by complete manifests; assert representative final render/gainmap assets are identical when present.
for rel in [
 'app/src/main/assets/shaders/motionv2/render.glsl',
 'app/src/main/assets/shaders/motionv2/gainmap.glsl',
 'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
]:
    if (base/rel).is_file(): same(rel)

# Version exact.
ver=read(cand,'app/version.properties')
assert 'VERSION_NAME=0.9726758' in ver and 'VERSION_BUILD=26758' in ver

print('PASS 26758 regressions: Plan B unreachable; universal same-lens direct-CFA zoom/SR; all NORMAL Sabre base; <=8 auxiliary detail; adaptive alias/zipper/row/col/checker/highlight rejection; Sabre/VGN RGB/chroma/highlight; 26757 SR no-wait capture and protected publication preserved')
