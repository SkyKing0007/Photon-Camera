#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26675.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def read(rel): return (cand/rel).read_text()
def sha(root,rel): return hashlib.sha256((root/rel).read_bytes()).hexdigest()
def same(rel): assert sha(base,rel)==sha(cand,rel), f'protected 26674 byte drift: {rel}'
# Version/build.
v=read('app/version.properties'); assert 'VERSION_NAME=0.9726675' in v and 'VERSION_BUILD=26675' in v
# Capture authority is a hardlock: preview presentation may never alter these successful-26674 owners.
acq=[
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java']
for rel in acq: same(rel)
cc=read(acq[0])
for t in ['updateMotion26662GoogleReferenceExposureAuthority(result)','IRIS_26662_GOOGLE_REFERENCE_AE',
'MOTION_26661_REFERENCE_HEADROOM_TARGET = 0.72f','MOTION_26661_MAX_PROTECTION_EV = 1.50f',
'MOTION_26662_AE_BASELINE_CONFIRM_FRAMES = 6','heldStructureCannotOwnMagnitude=true',
'IRIS_26670_ISOLATED_POST_SHUTTER_HDR_TRANSACTION','IRIS_26670_ISOLATED_HDR_CAPTURE_PLAN',
'MOTION_26505_LONG_TARGET_EV = 2.5','getMotion26663ReferencePreviewProtectionEv']:
 assert t in cc,t
render=read(acq[3]); matcher=read(acq[4]); mr=read(acq[5])
for t in ['IRIS_26662_CANONICAL_HDR_REFERENCE_NORMALIZATION','beforeLocalTone=true beforeSdrTone=true beforeUhdrGainMap=true','unclippedFloatCarrier=true longGlobalBrightnessAuthority=false']: assert t in render,t
for t in ['IRIS_26662_CANONICAL_REFERENCE_PRESENTATION_SOLVE','candidateMeterCanonicalized=true','protectionResidualEvAdded=false','MOTION_FIXED_MATCH_STRENGTH_PERCENT = 65']: assert t in matcher,t
for t in ['IRIS_26667_FRAME_EXACT_PREVIEW_PRESENTATION','mIris26663LastConfirmedProtectionEv','getMotion26663ReferencePreviewProtectionEv']: assert t in mr,t
# Preview is now display-only virtual-unprotected presentation. It must not preserve the protected highlight reveal.
ps=read('app/src/main/assets/shaders/preview/main_fs.glsl')
for t in ['uniform float iris26662ReferencePreviewGain','IRIS_26675_CAPTURE_DECOUPLED_PREVIEW_CLIP_OWNER','iris26675VirtualUnprotectedGain','linearRgb *= iris26675VirtualUnprotectedGain']:
 assert t in ps,t
assert 'mappedGuide = iris26662Gain * guide' not in ps
# The bridge may only forward already-frozen selected-reference protection EV downstream.
bridge=read('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
for t in ['IRIS_26674_PROTECTED_NORMAL_REFERENCE_HANDOFF','reference.motionV2ReferenceProtectionEv.coerceIn(0.0f, 1.50f)',
'shortFrame?.let { orderedPhysical += it to RawBurstFrameRole.HIGHLIGHT_SHORT }','longGlobalBrightnessAuthority=false',
'IRIS_26675_PROTECTED_NORMAL_SHORT_ADMISSION_CONTEXT','parameters.motionV2ReferenceProtectionEv.coerceIn(0.0f, 1.50f)']:
 assert t in bridge,t
# Protected-NORMAL-aware SHORT admission: protected NORMAL cannot grant inferred-only SHORT authority;
# physical NORMAL source loss remains valid, and unprotected NORMAL leaves inference enabled.
sh=read('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
for t in ['uniform float uReferenceProtectionEv','IRIS_26675_PROTECTED_NORMAL_SHORT_ADMISSION',
'float protectedNormalActive = step(0.25, uReferenceProtectionEv);',
'inferredRadiometricLoss *= (1.0 - protectedNormalActive);',
'float measuredNormalLoss = max(physicalNormalLoss, inferredRadiometricLoss);']:
 assert t in sh,t
stack=read('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
for t in ['IRIS_26675_PROTECTED_NORMAL_SHORT_ADMISSION_CONTEXT','uniform1f(program, "uReferenceProtectionEv", referenceProtectionEv.coerceIn(0f, 1.5f))','IRIS_26675_PROTECTED_NORMAL_SHORT_ADMISSION']:
 assert t in stack,t
for rel in ['app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt']:
 txt=read(rel); assert 'IRIS_26675_PROTECTED_NORMAL_SHORT_ADMISSION_CONTEXT' in txt and 'referenceProtectionEv' in txt
# Manual geometry: structural parent remains unmoved; actual visible top drawables own midpoint.
frag=read('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java')
ui=read('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java')
assert 'IRIS_26672_MANUAL_ROW_MIDPOINT' not in frag+ui
assert 'IRIS_26674_SINGLE_MANUAL_GEOMETRY_OWNER' not in frag
for t in ['IRIS_26675_VISIBLE_MANUAL_ICON_GEOMETRY_OWNER','iris26675VisibleTopDrawableCenterY','getCompoundDrawablesRelative()',
'button.getPaddingTop() + 0.5f * drawableHeight','visibleIconCenterBeforeY','focus.setTranslationY(fixedTranslationY)',
'shutter.setTranslationY(fixedTranslationY)','iso.setTranslationY(fixedTranslationY)','ev.setTranslationY(fixedTranslationY)',
'buttons.setTranslationY(0.0f)','IRIS_26675_MANUAL_VISIBILITY_INVARIANCE']:
 assert t in frag,t
assert 'buttons.setTranslationY(fixedTranslationY)' not in frag
assert 'rowLp.topMargin' not in frag+ui and 'manualMode.setTranslationY' not in frag+ui
# Critical publication/tone owners are exact 26674 bytes.
for rel in [
'app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl',
'app/src/main/cpp/iris_heic_jni.cpp','app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java']:
 same(rel)
print('PASS 26675 semantic validation: successful-26674 capture authority byte-hardlocked; preview display decoupled only; protected-NORMAL SHORT requires measured loss; visible manual icons own midpoint')
