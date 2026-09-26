#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
if len(sys.argv)!=3:raise SystemExit('usage: verify_26709_regressions.py BASE26708 CAND')
b,c=map(Path,sys.argv[1:])
def H(r):return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
def txt(r,p):return (r/p).read_text()
B,C=H(b),H(c);assert len(B)==len(C)==1823
expected=set(Path(__file__).with_name('26709_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines());assert len(expected)==6;assert {k for k in B|C if B.get(k)!=C.get(k)}==expected
v=txt(c,'app/version.properties');assert 'VERSION_NAME=0.9726709' in v and 'VERSION_BUILD=26709' in v
cap=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
# exactly one active exposure authority; all older raw-reactive writers remain dormant.
for t in ['/* updateMotionV2ExposureAuthority(result); intentionally dormant */','/* updateMotion26368AdaptiveAeBias(result); intentionally dormant */','/* updateMotion26662GoogleReferenceExposureAuthority(result); intentionally dormant */']:assert t in cap,t
assert cap.count('updateMotion26680StablePreviewAuthority(result);')==1
# signed adaptive immutable-HAL reference solver + anti-pump continuity.
for t in ['IRIS_26709_ADAPTIVE_EQUAL_EXPOSURE_REFERENCE_OWNER','MOTION_26709_REFERENCE_SIGNAL_TARGET = 0.92f','MOTION_26709_CLIP_SIGNAL = 0.985f','MOTION_26709_MAX_RELATIVE_EV = 1.50f','previousAdjustedExposureNeverRebased=true','float desiredOffsetEv = currentOffsetEv;','IRIS_26709_REFERENCE_RELEASE_CONFIRMED','IRIS_26709_REFERENCE_SETTLED','IRIS_26709_USER_EV_REBASE']:assert t in cap,t
# physical reframe still uses inherited gyro confirmation; subject/content cannot unlock.
assert 'mMotion26680ReframeMotionFrames >= MOTION_26680_REFRAME_CONFIRM_FRAMES' in cap
assert 'subjectMotionCannotUnlock=true viewfinder26708Behavior=true' in cap
# old fixed SHORT rescue retired; frame budget is NORMAL + at most one LONG.
assert 'final boolean iris26593ShortSubmitted = false;' in cap
capture_block=cap[cap.index('/* IRIS_26709_ADAPTIVE_REFERENCE_PLUS_LONG_CAPTURE_PLAN'):cap.index('final int iris26593NormalAtPress')]
assert 'applyMotion26486ExplicitShortCaptureIfNeeded(' not in capture_block
assert 'final int iris26593AuxCount = iris26505LongRequested ? 1 : 0;' in capture_block
assert 'final int iris26593NormalTarget = iris26593TotalTarget - iris26593AuxCount;' in capture_block
# quick shutter keeps existing exact-exposure post-shutter top-up; no stale-generation hard failure.
assert 'IRIS_26709_CAPTURE_GENERATION_GUARD' in cap and 'fallback=currentPhysicalEpoch topUpStillExact=true' in cap
for t in ['MOTION_26486_EXPOSURE_HALF_WINDOW_EV = 0.05','Motion26598NormalTopUpTicket','SENSOR_EXPOSURE_TIME','SENSOR_SENSITIVITY']:assert t in cap
# adaptive LONG replaces fixed +2.5 owner, retains isolated RAW-only manual capture and 1/15 ceiling.
for t in ['IRIS_26709_ADAPTIVE_LONG_BRACKET_OWNER','MOTION_26709_LONG_MIN_EV = 0.50','MOTION_26709_LONG_MAX_EV = 2.50','referenceRole=ADAPTIVE_EQUAL_EXPOSURE_NORMAL','CONTROL_AE_MODE_OFF','MOTION_26658_LONG_MAX_EXPOSURE_NS = 66_666_667L']:assert t in cap,t
assert 'MOTION_26505_LONG_TARGET_EV' not in cap and 'MOTION_26505_LONG_TARGET_MULTIPLIER' not in cap
# NORMAL carries measured positive underexposure only; actual Camera2 exposure/ISO remains authority.
assert 'IRIS_26709_ADAPTIVE_NORMAL_REFERENCE_PROTECTION' in cap
assert 'mMotion26709FrozenCaptureProtectionEv' in cap
# signed frame-exact preview presentation owner, including hidden brighter-than-HAL reference.
main=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java');sh=txt(c,'app/src/main/assets/shaders/preview/main_fs.glsl')
for t in ['IRIS_26709_SIGNED_FRAME_EXACT_PREVIEW_PRESENTATION','getMotion26663ReferencePreviewProtectionEv','Math.max(-1.50f, Math.min(1.50f, exactEv))']:assert t in main,t
for t in ['IRIS_26709_SIGNED_FRAME_EXACT_PREVIEW_PRESENTATION','clamp(iris26662ReferencePreviewGain, 0.3535534, 2.8284271)','abs(iris26662Gain - 1.0) > 0.0001']:assert t in sh,t
# Proven positive protected-reference downstream restoration restored without changing render owner.
bridge=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt');matcher=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java')
for t in ['IRIS_26709_ADAPTIVE_NORMAL_REFERENCE_HANDOFF','reference.motionV2ReferenceProtectionEv.coerceIn(0.0f, 1.50f)']:assert t in bridge,t
for t in ['IRIS_26709_CANONICAL_REFERENCE_PRESENTATION_SOLVE','Math.pow(2.0, referenceProtectionEv)','bodyEligible.add(sample)','globalGainShortVote=false']:assert t in matcher,t
# Critical untouched owners remain byte-identical to exact 26708 compiled authority.
protected=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp']
for rel in protected:assert (b/rel).read_bytes()==(c/rel).read_bytes(),rel
stack=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt');assert 'IRIS_26707_MOVING_CONTENT_LOW_CONFIDENCE_TAIL_REJECT' in stack
print('PASS 26709 regressions: 26708 viewfinder ownership preserved; one signed adaptive NORMAL owner; no cumulative rebase/pump; SHORT retired; NORMAL+adaptive LONG budget; exact top-up retained; downstream reference normalization restored; Sabre/render/UHDR/chroma/moving-tail protected')
# Permanent exact 26709 Actions failure regression (run 36244684183):
# Java anonymous CaptureCallback must never capture the multiply-assigned adaptiveLongEv local.
assert 'IRIS_26709_R1_JAVAC_EFFECTIVELY_FINAL_LONG_EV' in cap
assert 'final double adaptiveLongEvFinal = adaptiveLongEv;' in cap
callback=cap[cap.index('mCaptureSession.capture(b.build(), new CameraCaptureSession.CaptureCallback()'):cap.index('}, mBackgroundHandler);',cap.index('mCaptureSession.capture(b.build(), new CameraCaptureSession.CaptureCallback()'))]
assert '+ " targetDeltaEv=" + adaptiveLongEvFinal' in callback
assert '+ " targetDeltaEv=" + adaptiveLongEv\n' not in callback
print('PASS 26709 R1 regression: Actions run 36244684183 Javac inner-class effectively-final failure permanently blocked')
