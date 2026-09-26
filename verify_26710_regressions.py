#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26710_regressions.py BASE26709 CAND')
b,c=map(Path,sys.argv[1:]);pkg=Path(__file__).resolve().parent
def H(r):return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
def txt(r,p):return (r/p).read_text()
B,C=H(b),H(c);assert len(B)==len(C)==1823
expected=set((pkg/'26710_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines());assert expected=={
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java','app/version.properties'}
assert {k for k in B|C if B.get(k)!=C.get(k)}==expected
v=txt(c,'app/version.properties');assert 'VERSION_NAME=0.9726710' in v and 'VERSION_BUILD=26710' in v
cap=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
# Older automatic exposure writers remain dormant; exactly one active preview/exposure owner.
for t in ['/* updateMotionV2ExposureAuthority(result); intentionally dormant */','/* updateMotion26368AdaptiveAeBias(result); intentionally dormant */','/* updateMotion26662GoogleReferenceExposureAuthority(result); intentionally dormant */']:assert t in cap,t
assert cap.count('updateMotion26680StablePreviewAuthority(result);')==1
owner=cap[cap.index('/* IRIS_26710_ONE_SHOT_HAL_REFERENCE_OWNER',cap.index('private void resetMotion26680StablePreviewAuthority')):cap.index('/*\n     * IRIS_26662_GOOGLE_HDR_REFERENCE_EXPOSURE_OWNER')]
# One HAL observation -> one negative-only decision -> direct manual target. No feedback/convergence search survives.
for t in ['IRIS_26710_HAL_OBSERVATION_BASELINE','IRIS_26710_ONE_SHOT_REFERENCE_COMMIT','IRIS_26710_REFERENCE_LOCKED','mMotion26710DecisionIssued = true;','mMotion26710ManualReferenceActive = true;','CaptureRequest.CONTROL_AE_MODE_OFF','CaptureRequest.SENSOR_EXPOSURE_TIME, targetExposureNs','CaptureRequest.SENSOR_SENSITIVITY, targetIso','intermediateTargetsForbidden=true','postAdjustmentRawCannotRewriteExposure=true']:assert t in owner,t
for t in ['IRIS_26709_ADAPTIVE_REFERENCE_TARGET','signedBidirectional=true','float desiredOffsetEv = currentOffsetEv;','correctionEv =','MOTION_26709_MAX_SOLVE_STEP_EV','MOTION_26709_CLIPPED_PROBE_MIN_EV','MOTION_26709_CLIPPED_PROBE_MAX_EV']:assert t not in owner,t
# Target decision is committed before the manual repeating write, and once issued the branch returns before meter/solver code.
idx_dec=owner.index('mMotion26710DecisionIssued = true;');idx_off=owner.index('CaptureRequest.CONTROL_AE_MODE_OFF',idx_dec);assert idx_dec < idx_off
issued=owner[owner.index('if (mMotion26710DecisionIssued)'):owner.index('if (mMotion26708PublishedTimestampNs <= 0L')]
assert 'return;' in issued and 'CONTROL_AE_EXPOSURE_COMPENSATION' not in issued and 'SENSOR_EXPOSURE_TIME' not in issued and 'SENSOR_SENSITIVITY' not in issued
# NORMAL is negative-only relative to HAL; unavailable manual mode locks HAL rather than starting a compensation search.
for t in ['requestedProtectionEv = Math.max(0.0f','Math.min(MOTION_26709_MAX_RELATIVE_EV, requestedProtectionEv)','fallback=LOCK_HAL_BASELINE zeroPumpInvariant=true','IRIS_26710_TARGET_CLAMPED_TO_HAL zeroPumpInvariant=true']:assert t in owner,t
# Subject/content motion cannot unlock. Only inherited sustained physical-camera reframe may release the epoch.
for t in ['mMotion26680ReframeMotionFrames >= MOTION_26680_REFRAME_CONFIRM_FRAMES','subjectMotionCannotUnlock=true tvContentCannotUnlock=true','luminanceChangeCannotUnlock=true physicalCameraReframeOnly=true','CaptureRequest.CONTROL_AE_MODE_ON','IRIS_26710_REFERENCE_EPOCH_RELEASE']:assert t in owner,t
# One complete baseline RAW meter is matched to immutable HAL energy before decision; baseline shadow stats freeze there.
for t in ['mMotion26708PublishedGeneration != mIris26548CameraHealthGeneration','meterEvMismatch > 0.08','mMotion26710HalBaselineFloorFraction = mMotion26709PublishedFloorFraction','mMotion26710HalBaselineShadowFraction = mMotion26709PublishedShadowFraction','mMotion26710HalBaselineMeanSignal = mMotion26709PublishedMeanSignal']:assert t in owner,t
# 26703-style proven highlight math is retained as one-shot evidence, not an iterative owner.
for t in ['MOTION_26710_REFERENCE_HEADROOM_TARGET = 0.72f','MOTION_26710_HDR_MIN_PROTECTION_EV = 0.35f','MOTION_26710_CLIP_MIN_PROTECTION_EV = 0.70f','MOTION_26478_HIGHLIGHT_FRACTION_TRIGGER']:assert t in cap,t
# SHORT remains retired. Exact Motion frame budget stays NORMAL + at most one isolated LONG.
assert 'final boolean iris26593ShortSubmitted = false;' in cap
capture=cap[cap.index('/* IRIS_26710_ONE_SHOT_REFERENCE_PLUS_HAL_LONG_CAPTURE_PLAN'):cap.index('final int iris26593NormalAtPress')]
assert 'applyMotion26486ExplicitShortCaptureIfNeeded(' not in capture
assert 'final int iris26593AuxCount = iris26505LongRequested ? 1 : 0;' in capture
assert 'final int iris26593NormalTarget = iris26593TotalTarget - iris26593AuxCount;' in capture
# LONG is independent of underexposed NORMAL: target EV is defined over untouched HAL baseline, and motion cannot attenuate its SNR target.
longblock=cap[cap.index('/* IRIS_26710_HAL_BASELINED_LONG_EXPOSURE_OWNER',cap.index('applyMotion26505ExplicitLongCaptureIfUseful')):cap.index('long maxLongExp',cap.index('/* IRIS_26710_HAL_BASELINED_LONG_EXPOSURE_OWNER',cap.index('applyMotion26505ExplicitLongCaptureIfUseful')))] if False else None
ls=cap.index('/* IRIS_26710_HAL_BASELINED_LONG_EXPOSURE_OWNER',cap.index('applyMotion26505ExplicitLongCaptureIfUseful'))
le=cap.index('long maxLongExp',ls)
longblock=cap[ls:le]
for t in ['mMotion26710HalBaselineFloorFraction','mMotion26710HalBaselineShadowFraction','mMotion26710HalBaselineMeanSignal','MOTION_26710_LONG_MIN_OVER_HAL_EV','MOTION_26710_LONG_MAX_OVER_HAL_EV','double targetEnergy = halBaselineEnergySecIso * Math.pow(2.0, longOverHalEv);','Math.log(targetEnergy / ticket.baselineEnergy)','motionOpportunityObserverOnly']:assert t in cap,t
assert '* rawNeed * (0.45 + 0.55 * shutterOpportunity)' not in longblock
assert 'MOTION_26709_LONG_MIN_EV' not in cap and 'MOTION_26709_LONG_MAX_EV' not in cap
assert 'MOTION_26658_LONG_MAX_EXPOSURE_NS = 66_666_667L' in cap and 'CONTROL_AE_MODE_OFF' in cap
# Quick shutter still waits only for final physical reference generation; exact post-shutter top-up remains.
for t in ['IRIS_26709_ADAPTIVE_REFERENCE_SHUTTER_GENERATION_GUARD','!mMotion26709HalBaselineReady || !mMotion26709ReferenceSettled','Motion26598NormalTopUpTicket','MOTION_26486_EXPOSURE_HALF_WINDOW_EV = 0.05']:assert t in cap,t
# Preserve successful 26709 frame-exact preview/downstream normalization and protected IQ owners byte-identically.
protected=[
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java',
'app/src/main/assets/shaders/preview/main_fs.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp']
for rel in protected:assert (b/rel).read_bytes()==(c/rel).read_bytes(),rel
main=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java');assert 'IRIS_26709_SIGNED_FRAME_EXACT_PREVIEW_PRESENTATION' in main
bridge=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt');assert 'IRIS_26709_ADAPTIVE_NORMAL_REFERENCE_HANDOFF' in bridge
matcher=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java');assert 'IRIS_26709_CANONICAL_REFERENCE_PRESENTATION_SOLVE' in matcher
stack=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt');assert 'IRIS_26707_MOVING_CONTENT_LOW_CONFIDENCE_TAIL_REJECT' in stack
# Permanent 26709 Actions Javac failure remains blocked.
assert 'IRIS_26709_R1_JAVAC_EFFECTIVELY_FINAL_LONG_EV' in cap and 'final double adaptiveLongEvFinal = adaptiveLongEv;' in cap
callback=cap[cap.index('mCaptureSession.capture(b.build(), new CameraCaptureSession.CaptureCallback()'):cap.index('}, mBackgroundHandler);',cap.index('mCaptureSession.capture(b.build(), new CameraCaptureSession.CaptureCallback()'))]
assert '+ " targetDeltaEv=" + adaptiveLongEvFinal' in callback
print('PASS 26710 regressions: one HAL observation / one direct manual NORMAL target / immutable until physical reframe; no RAW feedback pump; NORMAL+HAL-baselined LONG; 26709 viewfinder/downstream/Sabre/render/UHDR and Javac regression protected')
