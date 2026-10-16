#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
B,C=map(Path,sys.argv[1:3])
CHANGED={'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java','app/version.properties'}
def H(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def U(r): return {str(p.relative_to(r)).replace('\\','/'):H(p) for p in (r/'app').rglob('*') if p.is_file()}
b,c=U(B),U(C); assert set(b)==set(c) and len(b)==1786,(len(b),len(c)); delta={p for p in b if b[p]!=c[p]}; assert delta==CHANGED,(delta-CHANGED,CHANGED-delta)
v=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726843' in v and 'VERSION_BUILD=26843' in v and 'VERSION_MINOR=9726440' in v
# Successful 26842 IQ, color, clipped-color rolloff, mottling, UHDR, DNG, native, SR and high-zoom remain byte-identical.
for rel in [
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/assets/shaders/motionv2/shadow_cleanup.glsl',
'app/src/main/assets/shaders/motionv2/color_transform.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java']:
    assert H(B/rel)==H(C/rel),rel
cap=(C/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
bcap=(B/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
cap1=re.sub(r'\s+',' ',cap)
# Preserve successful target magnitude, deadband, one-shot HAL ownership and corrected-NORMAL shutter safety.
for marker in [
'IRIS_26841_SINGLE_TARGET_HAL_HDR_PREVIEW',
'MOTION_26841_PREVIEW_RETARGET_DEADBAND_EV = 0.30f',
'oneRequestUpdate=true iterative=false staircase=false',
'IRIS_26841_ABSOLUTE_RECIPE_ENERGY_AT_SHUTTER',
'IRIS_26713_HAL_ZSL_EVIDENCE_EXCLUDED_FROM_CORRECTED_NORMAL']:
    assert marker in cap,marker
for const in [
'MOTION_26710_REFERENCE_HEADROOM_TARGET = 0.72f',
'MOTION_26710_HDR_MIN_PROTECTION_EV = 0.35f',
'MOTION_26710_CLIP_MIN_PROTECTION_EV = 0.70f',
'MOTION_26709_MAX_RELATIVE_EV = 1.50f',
'MOTION_26710_DECISION_DEADBAND_EV = 0.08f',
'MOTION_26714_NEW_SCENE_METER_DELAY_NS = 120_000_000L']:
    assert const in cap and const in bcap,const
# 26843 is timing-only: fresh evidence may arm the existing observer early for stronger protection only.
for marker in [
'IRIS_26843_FAST_PROTECTIVE_HDR_ARM',
'iris26843ProvenProtectionEv >= iris26843HeldProtectionEv + MOTION_26841_PREVIEW_RETARGET_DEADBAND_EV',
'bypassStableFrames=true reuseFreshProofMeter=true targetMathChanged=false',
'darkenOnly=true brightenStillStablePath=true',
'zslRefillParallel=true postShutterCorrectedNormalPreserved=true',
'if (motion26712NavigationConfirmed() && !mMotion26843FastProtectObservation)']:
    assert marker in (cap1 if marker.startswith('iris26843ProvenProtectionEv') else cap),marker
# Fast path must only arm observation state; it must not directly mutate Camera2 exposure/ISO/compensation.
fast=cap[cap.index('/* IRIS_26843_FAST_PROTECTIVE_HDR_ARM',cap.index('private void updateMotion26680StablePreviewAuthority')):cap.index('if (shakiness > MOTION_26714_STATIONARY_SHAKINESS_THRESHOLD)',cap.index('private void updateMotion26680StablePreviewAuthority'))]
for forbidden in ['CONTROL_AE_EXPOSURE_COMPENSATION,','SENSOR_EXPOSURE_TIME,','SENSOR_SENSITIVITY,','rebuildPreviewBuilder()']:
    assert forbidden not in fast,forbidden
assert 'mMotion26713ObservationPending = true;' in fast
assert 'mMotion26714ObservationStartSensorTimestampNs = 0L;' in fast
assert 'mMotion26708PublishedTimestampNs = 0L;' in cap[cap.index('private void clearMotion26708HighlightClassifier'):cap.index('private void accumulateMotion26708HighlightPhase')]
# Old reactive staircase writers remain dormant.
for dormant in ['/* updateMotionV2ExposureAuthority(result); intentionally dormant */','/* updateMotion26368AdaptiveAeBias(result); intentionally dormant */','/* updateMotion26662GoogleReferenceExposureAuthority(result); intentionally dormant */']:
    assert dormant in cap,dormant
print('PASS 26843 semantic validation: exact 2-path scope; successful 26842 IQ/shader/color/mottling/DNG/UHDR/native/high-zoom/SR frozen; exact 26713/26841 protection math and amount preserved; fresh RAW evidence only fast-arms stronger darkening; brightening stays conservative; no direct fast-path Camera2 mutation; ZSL/post-shutter corrected-NORMAL safety preserved')
