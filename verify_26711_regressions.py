#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26711_regressions.py BASE26710 CAND')
b,c=map(Path,sys.argv[1:]);pkg=Path(__file__).resolve().parent
def H(r):return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
def txt(r,p):return (r/p).read_text()
B,C=H(b),H(c);assert len(B)==len(C)==1823
expected=set((pkg/'26711_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines());assert expected=={
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java',
'app/version.properties'}
assert {k for k in B|C if B.get(k)!=C.get(k)}==expected
v=txt(c,'app/version.properties');assert 'VERSION_NAME=0.9726711' in v and 'VERSION_BUILD=26711' in v
cap=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
main=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java')
# Existing dormant exposure owners remain dormant; 26680/26710 lineage remains sole callback owner.
for t in ['/* updateMotionV2ExposureAuthority(result); intentionally dormant */','/* updateMotion26368AdaptiveAeBias(result); intentionally dormant */','/* updateMotion26662GoogleReferenceExposureAuthority(result); intentionally dormant */']:assert t in cap,t
assert cap.count('updateMotion26680StablePreviewAuthority(result);')==1
# 26711 hard owner: one decision, no feedback solver, continuous immutable lock.
for t in ['IRIS_26711_IMMUTABLE_REFERENCE_LIFECYCLE_OWNER','IRIS_26711_ONE_SHOT_REFERENCE_COMMIT','IRIS_26711_REFERENCE_LOCKED','IRIS_26711_LOCK_REASSERT','exposureRecompute=false sameFrozenTarget=true','IRIS_26711_LEGACY_3A_TAKEOVER_GUARD','IRIS_26711_LEGACY_3A_TAKEOVER_BLOCKED']: assert t in cap,t
for t in ['IRIS_26709_ADAPTIVE_REFERENCE_TARGET','signedBidirectional=true','float desiredOffsetEv = currentOffsetEv;','MOTION_26709_MAX_SOLVE_STEP_EV','MOTION_26709_CLIPPED_PROBE_MIN_EV','MOTION_26709_CLIPPED_PROBE_MAX_EV']: assert t not in cap,t
# 26710 bug regression: never declare lock merely because observe-frame timeout elapsed.
issued=cap[cap.index('if (mMotion26710DecisionIssued)'):cap.index('if (mMotion26708PublishedTimestampNs <= 0L')]
assert 'mismatchEv <= MOTION_26710_TARGET_OBSERVED_TOLERANCE_EV' in issued
assert 'MOTION_26710_TARGET_OBSERVE_MAX_FRAMES' in issued and 'motion26711ReassertLockedManualReference' in issued
assert '|| mMotion26710TargetObserveFrames >= MOTION_26710_TARGET_OBSERVE_MAX_FRAMES' not in issued
# Hand shake / jerk is not a reframe. Release requires net pose settled away from lock or whole-frame structural replacement.
for t in ['MOTION_26711_REFRAME_ANGLE_DEG = 7.0f','MOTION_26711_REFRAME_SETTLED_SHAKINESS = 48','MOTION_26711_REFRAME_SETTLED_FRAMES = 6','motion26711PoseReframeConfirmed','returning hand jerk','NET_POSE_CHANGE','WHOLE_FRAME_REPLACEMENT','handShakeCannotUnlock=true returningHandJerkCannotUnlock=true']: assert t in cap,t
owner=cap[cap.index('/* IRIS_26710_ONE_SHOT_HAL_REFERENCE_OWNER',cap.index('private void resetMotion26680StablePreviewAuthority')):cap.index('/*\n     * IRIS_26662_GOOGLE_HDR_REFERENCE_EXPOSURE_OWNER')]
assert 'mMotion26680ReframeMotionFrames >= MOTION_26680_REFRAME_CONFIRM_FRAMES' not in owner
# Whole-frame replacement is spatial and exposure-normalized: 12/16 tiles, persistent; local TV/person/flicker cannot vote alone.
for t in ['IRIS_26711_WHOLE_FRAME_SCENE_SIGNATURE','MOTION_26711_SCENE_TILES = 16','MOTION_26711_SCENE_CHANGED_TILES = 12','MOTION_26711_SCENE_CHANGE_CONFIRM_FRAMES = 18','motion26711WholeFrameSceneReplacementConfirmed','rawBrightnessCannotUnlock=true']:assert t in cap,t
# Physical target is policed continuously after lock; same target is reasserted if request/result drifts.
for t in ['motion26711LockedManualRequestMatchesBuilder','MOTION_26711_LOCK_REASSERT_FRAMES = 2','RESULT_DRIFT','BUILDER_OWNER_LOST','IRIS_26711_LOCK_REASSERT_CONFIRMED']: assert t in cap,t
reassert=cap[cap.index('private void motion26711ReassertLockedManualReference'):cap.index('public boolean shouldHoldMotion26711PreviewExposureTransition')]
for t in ['mMotion26710TargetExposureNs','mMotion26710TargetIso','CONTROL_AE_MODE_OFF']: assert t in reassert,t
for t in ['mMotion26709PublishedP995','requestedProtectionEv','targetScale','mMotion26710HalBaselineHighlightFraction']: assert t not in reassert,t
# Viewfinder hides HAL<->manual/reassert/post-capture physical transition by retaining last stable OES texture.
for t in ['IRIS_26711_HIDDEN_PHYSICAL_EXPOSURE_TRANSITION','shouldHoldMotion26711PreviewExposureTransition','iris26711HoldExposureTransition','mUpdateST && !iris26711HoldExposureTransition']: assert t in main,t
assert 'IRIS_26709_SIGNED_FRAME_EXACT_PREVIEW_PRESENTATION' in main
# Post-shutter owner ends at immutable physical-batch boundary, before processing executor starts; HAL is restored at 0 EV while processing continues.
for t in ['IRIS_26711_CAPTURE_EXPOSURE_OWNER_ENDS_AT_PHYSICAL_BATCH','IRIS_26711_PHYSICAL_CAPTURE_COMPLETE_HAL_RELEASE','IRIS_26711_POST_CAPTURE_HAL_RESTORED','CaptureRequest.CONTROL_AE_EXPOSURE_COMPENSATION, 0','processingIndependent=true','immutableBatchAlreadyFrozen=true']: assert t in cap,t
batch=cap[cap.index('clearMotion26593CapturePlan(iris26593Plan, "immutable_batch_handoff")'):cap.index('processExecutor.execute(() -> {',cap.index('clearMotion26593CapturePlan(iris26593Plan, "immutable_batch_handoff")'))]
assert 'motion26711ReleaseToHalAfterPhysicalCapture();' in batch
# HAL anti-banding behavior is preserved where physically possible: reduce ISO first while keeping HAL shutter; shorten shutter only after ISO floor.
for t in ['IRIS_26711_HAL_ANTIBANDING_SHUTTER_PRESERVATION','mMotion26709HalBaselineExposureNs','targetIso = (int)Math.round(targetEnergy / Math.max(1.0, targetExposureNs))','targetIso = sensitivityRange.getLower();','halShutterPreservedForAntibanding=']: assert t in cap,t
# One-shot negative-only NORMAL and HAL-baselined LONG remain unchanged in role. SHORT stays retired.
for t in ['requestedProtectionEv = Math.max(0.0f','Math.min(MOTION_26709_MAX_RELATIVE_EV, requestedProtectionEv)','fallback=LOCK_HAL_BASELINE zeroPumpInvariant=true','IRIS_26710_TARGET_CLAMPED_TO_HAL zeroPumpInvariant=true']: assert t in cap,t
assert 'final boolean iris26593ShortSubmitted = false;' in cap
for t in ['IRIS_26710_HAL_BASELINED_LONG_EXPOSURE_OWNER','MOTION_26710_LONG_MIN_OVER_HAL_EV','MOTION_26710_LONG_MAX_OVER_HAL_EV','double targetEnergy = halBaselineEnergySecIso * Math.pow(2.0, longOverHalEv);','motionOpportunityObserverOnly','MOTION_26658_LONG_MAX_EXPOSURE_NS = 66_666_667L']: assert t in cap,t
# Exact top-up + 14 NORMAL / at most one LONG budget semantics remain.
for t in ['IRIS_26709_ADAPTIVE_REFERENCE_SHUTTER_GENERATION_GUARD','Motion26598NormalTopUpTicket','MOTION_26486_EXPOSURE_HALF_WINDOW_EV = 0.05','final int iris26593AuxCount = iris26505LongRequested ? 1 : 0;','final int iris26593NormalTarget = iris26593TotalTarget - iris26593AuxCount;']: assert t in cap,t
# Protected IQ/native/DNG/shader owners remain byte-identical to successful 26710; only renderer among prior IQ list may change for presentation holding.
protected=[
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
bridge=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt');assert 'IRIS_26709_ADAPTIVE_NORMAL_REFERENCE_HANDOFF' in bridge
matcher=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java');assert 'IRIS_26709_CANONICAL_REFERENCE_PRESENTATION_SOLVE' in matcher
stack=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt');assert 'IRIS_26707_MOVING_CONTENT_LOW_CONFIDENCE_TAIL_REJECT' in stack
# Permanent 26709 Javac closure-capture failure remains fixed.
assert 'IRIS_26709_R1_JAVAC_EFFECTIVELY_FINAL_LONG_EV' in cap and 'final double adaptiveLongEvFinal = adaptiveLongEv;' in cap
callback=cap[cap.index('mCaptureSession.capture(b.build(), new CameraCaptureSession.CaptureCallback()'):cap.index('}, mBackgroundHandler);',cap.index('mCaptureSession.capture(b.build(), new CameraCaptureSession.CaptureCallback()'))]
assert '+ " targetDeltaEv=" + adaptiveLongEvFinal' in callback
print('PASS 26711 regressions: one-shot exposure immutable across shake/jerk/subjects; net-pose or whole-frame release only; continuous lock reassert; hidden transition; HAL 0 EV restored at physical-batch completion; HAL-baselined LONG and protected IQ preserved')
