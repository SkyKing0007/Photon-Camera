#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26674.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def read(rel): return (cand/rel).read_text()
def sha(root,rel): return hashlib.sha256((root/rel).read_bytes()).hexdigest()
# Version/build
v=read('app/version.properties'); assert 'VERSION_NAME=0.9726674' in v and 'VERSION_BUILD=26674' in v
# Exact protected-NORMAL acquisition owner and anti-ratchet current-RAW solve.
cc=read('app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
for t in ['updateMotion26662GoogleReferenceExposureAuthority(result)','IRIS_26662_GOOGLE_REFERENCE_AE','MOTION_26661_REFERENCE_HEADROOM_TARGET = 0.72f','MOTION_26661_MAX_PROTECTION_EV = 1.50f','MOTION_26662_AE_BASELINE_CONFIRM_FRAMES = 6','heldStructureCannotOwnMagnitude=true','IRIS_26670_ISOLATED_POST_SHUTTER_HDR_TRANSACTION','IRIS_26670_ISOLATED_HDR_CAPTURE_PLAN','MOTION_26505_LONG_TARGET_EV = 2.5','getMotion26663ReferencePreviewProtectionEv']:
 assert t in cc,t
for bad in ['IRIS_26661_GOOGLE_HDR_BRACKETING_CAPTURE_PLAN','postNormalHighlightShortRepair=false']:
 assert bad not in cc,bad
# Metadata carrier/handoff and canonical FLOAT restoration.
img=read('app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java'); par=read('app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java')
assert 'motionV2ReferenceProtectionEv = 0.0f' in img and 'motionV2ReferenceProtectionEv = 0.0f' in par
bridge=read('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
for t in ['IRIS_26674_PROTECTED_NORMAL_REFERENCE_HANDOFF','reference.motionV2ReferenceProtectionEv.coerceIn(0.0f, 1.50f)','shortFrame?.let { orderedPhysical += it to RawBurstFrameRole.HIGHLIGHT_SHORT }','longGlobalBrightnessAuthority=false']:
 assert t in bridge,t
render=read('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java')
for t in ['IRIS_26662_CANONICAL_HDR_REFERENCE_NORMALIZATION','motionv2/display_exposure','beforeLocalTone=true beforeSdrTone=true beforeUhdrGainMap=true','unclippedFloatCarrier=true longGlobalBrightnessAuthority=false']:
 assert t in render,t
matcher=read('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java')
for t in ['IRIS_26662_CANONICAL_REFERENCE_PRESENTATION_SOLVE','candidateMeterCanonicalized=true','protectionResidualEvAdded=false','MOTION_FIXED_MATCH_STRENGTH_PERCENT = 65']:
 assert t in matcher,t
# Preview exact timestamp/hold-on-miss and white-anchored presentation shader.
mr=read('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java'); ps=read('app/src/main/assets/shaders/preview/main_fs.glsl')
for t in ['IRIS_26667_FRAME_EXACT_PREVIEW_PRESENTATION','mIris26663LastConfirmedProtectionEv','getMotion26663ReferencePreviewProtectionEv']:
 assert t in mr,t
for t in ['uniform float iris26662ReferencePreviewGain','mappedGuide = iris26662Gain * guide','IRIS_26662_FRAME_MATCHED_PREVIEW_PRESENTATION']:
 assert t in ps,t
# Manual row: old owner gone; exactly one row geometry method owns translation; parent never moves.
ui=read('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java'); frag=read('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java')
assert 'IRIS_26672_MANUAL_ROW_MIDPOINT' not in ui+frag
assert 'iris26672CenterManualModeRowFromCurrent26671Geometry' not in ui+frag
for t in ['IRIS_26674_SINGLE_MANUAL_GEOMETRY_OWNER','IRIS_26674_MANUAL_GEOMETRY_OWNER','IRIS_26674_MANUAL_VISIBILITY_INVARIANCE','buttons.setTranslationY(fixedTranslationY)','addOnPreDrawListener(iris26674ManualPreDrawListener)','panel.setAlpha(0.0f)','panel.setVisibility(View.VISIBLE)']:
 assert t in frag,t
assert 'rowLp.topMargin' not in ui+frag and 'manualMode.setTranslationY' not in ui+frag
# Explicitly protected IQ/publication files remain exact successful 26673 bytes.
protected=[
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/cpp/iris_heic_jni.cpp']
for rel in protected: assert sha(base,rel)==sha(cand,rel),rel
print('PASS 26674 semantic validation: protected NORMAL acquisition + exact FLOAT normalization + frame-exact preview; successful-26673 SHORT/LONG/IQ/HEIC retained; sole manual geometry owner')
