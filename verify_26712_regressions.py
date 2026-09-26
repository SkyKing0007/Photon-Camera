#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26712_regressions.py BASE26711 CAND')
b,c=map(Path,sys.argv[1:]);pkg=Path(__file__).resolve().parent
def H(r):return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
def txt(r,p):return (r/p).read_text()
B,C=H(b),H(c);assert len(B)==len(C)==1823
expected=set((pkg/'26712_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines());assert expected=={
'app/src/main/assets/shaders/preview/main_fs.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/version.properties'}
assert {k for k in B|C if B.get(k)!=C.get(k)}==expected
v=txt(c,'app/version.properties');assert 'VERSION_NAME=0.9726712' in v and 'VERSION_BUILD=26712' in v
cap=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
main=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java')
shader=txt(c,'app/src/main/assets/shaders/preview/main_fs.glsl')
# Dormant historical exposure writers stay dormant; 26680 lineage remains sole callback owner.
for t in ['/* updateMotionV2ExposureAuthority(result); intentionally dormant */','/* updateMotion26368AdaptiveAeBias(result); intentionally dormant */','/* updateMotion26662GoogleReferenceExposureAuthority(result); intentionally dormant */']:assert t in cap,t
assert cap.count('updateMotion26680StablePreviewAuthority(result);')==1
# 26712 is one-shot only: signed baseline vote is allowed, feedback search remains forbidden.
for t in ['IRIS_26712_ONE_SHOT_HAL_REFERENCE_OWNER','IRIS_26712_ONE_SHOT_SIGNED_SCENE_CORRECTION','IRIS_26712_ONE_SHOT_REFERENCE_COMMIT','postAdjustmentRawCannotRewriteExposure=true','signedOneShot=true viewfinderAuthority=HAL_26708']:assert t in cap,t
for t in ['IRIS_26709_ADAPTIVE_REFERENCE_TARGET','float desiredOffsetEv = currentOffsetEv;','MOTION_26709_MAX_SOLVE_STEP_EV','MOTION_26709_CLIPPED_PROBE_MIN_EV','MOTION_26709_CLIPPED_PROBE_MAX_EV']:assert t not in cap,t
# Signed correction is bounded and conservative: highlight pressure darkens; only clearly dark/highlight-safe scene may brighten.
for t in ['MOTION_26712_BRIGHTEN_MAX_EV = 0.75f','MOTION_26712_BRIGHTEN_MIN_EV = 0.18f','mMotion26710HalBaselineHighlightFraction < 0.0015f','mMotion26709PublishedP995 < 0.50f','requestedPhysicalOffsetEv = -requestedProtectionEv','targetEnergy = mMotion26709HalBaselineEnergy\n                    * Math.pow(2.0, requestedPhysicalOffsetEv)']:assert t in cap,t
# Exact manual target remains continuously policed; drift reasserts same target and never recomputes exposure.
for t in ['IRIS_26711_IMMUTABLE_REFERENCE_LIFECYCLE_OWNER','motion26711LockedManualRequestMatchesBuilder','IRIS_26711_LOCK_REASSERT','exposureRecompute=false sameFrozenTarget=true','RESULT_DRIFT','BUILDER_OWNER_LOST','IRIS_26711_LEGACY_3A_TAKEOVER_GUARD','IRIS_26711_LEGACY_3A_TAKEOVER_BLOCKED']:assert t in cap,t
reassert=cap[cap.index('private void motion26711ReassertLockedManualReference'):cap.index('public boolean shouldHoldMotion26711PreviewExposureTransition')]
for t in ['mMotion26710TargetExposureNs','mMotion26710TargetIso','CONTROL_AE_MODE_OFF']:assert t in reassert,t
for t in ['mMotion26709PublishedP995','requestedProtectionEv','targetScale','mMotion26710HalBaselineHighlightFraction']:assert t not in reassert,t
# 26712 reframe semantics: release while navigation is underway using sustained net travel + normalized whole-frame structure.
for t in ['IRIS_26712_SEMANTIC_NAVIGATION_RELEASE','MOTION_26712_NAV_MIN_ANGLE_DEG = 2.75f','MOTION_26712_NAV_STRONG_ANGLE_DEG = 7.0f','MOTION_26712_NAV_RETURN_ANGLE_DEG = 1.25f','MOTION_26712_NAV_CONFIRM_FRAMES = 5','MOTION_26712_NAV_CONFIRM_MS = 150L','MOTION_26712_NAV_STRUCTURAL_TILES = 8','MOTION_26712_WHOLE_FRAME_TILES = 12','MOTION_26712_WHOLE_FRAME_CONFIRM_SAMPLES = 4','motion26712NavigationConfirmed','localSubjectMotionCannotRelease=true','IRIS_26712_HAL_NAVIGATION_RELEASE','waitForNewSceneSettle=false previewHold=false','subjectMotionCannotUnlock=true tvContentCannotUnlock=true']:assert t in cap,t
owner=cap[cap.index('private void updateMotion26680StablePreviewAuthority'):cap.index('/*\n     * IRIS_26662_GOOGLE_HDR_REFERENCE_EXPOSURE_OWNER')]
assert 'motion26712NavigationConfirmed()' in owner
assert 'motion26711PoseReframeConfirmed(shakiness)' not in owner
assert 'motion26711WholeFrameSceneReplacementConfirmed()' not in owner
# Iris machinery must never freeze the visible preview; frame-exact presentation carries the offset instead.
assert 'IRIS_26712_NO_VISIBLE_PREVIEW_FREEZE' in cap
hold=cap[cap.index('public boolean shouldHoldMotion26711PreviewExposureTransition'):cap.index('private void motion26711ReleaseToHalAfterPhysicalCapture')]
assert 'return false;' in hold and 'return isZslMode()' not in hold
assert (b/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java').read_bytes()==(c/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java').read_bytes()
for t in ['IRIS_26711_HIDDEN_PHYSICAL_EXPOSURE_TRANSITION','getMotion26663ReferencePreviewProtectionEv','IRIS_26709_SIGNED_FRAME_EXACT_PREVIEW_PRESENTATION']:assert t in main,t
# Preview shader now fully inverses capture-domain exposure instead of white-anchored highlight-preserving display mapping.
for t in ['IRIS_26712_FULL_INVERSE_HAL_PREVIEW_PRESENTATION','linearRgb = max(linearRgb, vec3(0.0)) * iris26662Gain','viewfinder highlights to clip exactly as the HAL-looking']:assert t in shader,t
pre=shader[:shader.index('/* IRIS_26678_POST_WYSIWYG_ROW_FLICKER_CORRECTION')]
assert 'mappedGuide = iris26662Gain * guide' not in pre
# Post-capture: physical batch completion immediately returns AE ON/0EV with no preview convergence hold; processing still publishes zero offset for HAL frames.
for t in ['IRIS_26712_POST_CAPTURE_HAL_LIVE_IMMEDIATE','IRIS_26712_PHYSICAL_CAPTURE_COMPLETE_HAL_LIVE_IMMEDIATE','waitForAeConvergence=false','previewHold=false','CaptureRequest.CONTROL_AE_EXPOSURE_COMPENSATION, 0','IRIS_26712_PROCESSING_PREVIEW_STAYS_HAL','recordMotion26662PreviewProtection(processingPreviewTs, 0.0f)']:assert t in cap,t
release=cap[cap.index('private void motion26711ReleaseToHalAfterPhysicalCapture'):cap.index('private boolean motion26711HandlePostCaptureHalRestore')]
assert 'mMotion26711PreviewTransitionHold = false;' in release
assert 'mMotion26711PostCaptureHalRestorePending = false;' in release
assert 'mMotion26709HalBaselineReady = false;' in release
assert 'mMotion26709HalBaselineEnergy = Double.NaN;' in release
batch=cap[cap.index('clearMotion26593CapturePlan(iris26593Plan, "immutable_batch_handoff")'):cap.index('processExecutor.execute(() -> {',cap.index('clearMotion26593CapturePlan(iris26593Plan, "immutable_batch_handoff")'))]
assert 'motion26711ReleaseToHalAfterPhysicalCapture();' in batch
# While processing, trailing AE-OFF results do not get falsely labeled HAL zero; first AE-ON results do.
processing=cap[cap.index('IRIS_26712_PROCESSING_PREVIEW_STAYS_HAL'):cap.index('if (!isZslMode() || mZslCapturing',cap.index('IRIS_26712_PROCESSING_PREVIEW_STAYS_HAL'))]
assert 'processingPreviewAeMode != CaptureResult.CONTROL_AE_MODE_OFF' in processing
# LONG stays HAL-baselined and remains above a possible brightened NORMAL.
for t in ['IRIS_26710_HAL_BASELINED_LONG_EXPOSURE_OWNER','IRIS_26712_LONG_STAYS_ABOVE_SIGNED_NORMAL','mMotion26712TargetPhysicalOffsetEv + 0.50','MOTION_26710_LONG_MIN_OVER_HAL_EV','MOTION_26710_LONG_MAX_OVER_HAL_EV','double targetEnergy = halBaselineEnergySecIso * Math.pow(2.0, longOverHalEv);','MOTION_26658_LONG_MAX_EXPOSURE_NS = 66_666_667L']:assert t in cap,t
# Successful 14 NORMAL + max-one LONG budget and exact top-up mechanics preserved; SHORT remains retired.
assert 'final boolean iris26593ShortSubmitted = false;' in cap
for t in ['IRIS_26709_ADAPTIVE_REFERENCE_SHUTTER_GENERATION_GUARD','Motion26598NormalTopUpTicket','MOTION_26486_EXPOSURE_HALF_WINDOW_EV = 0.05','final int iris26593AuxCount = iris26505LongRequested ? 1 : 0;','final int iris26593NormalTarget = iris26593TotalTarget - iris26593AuxCount;']:assert t in cap,t
# Core IQ/native/DNG owners outside capture + preview presentation remain byte-identical to successful 26711.
protected=[
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp']
for rel in protected:assert (b/rel).read_bytes()==(c/rel).read_bytes(),rel
# Permanent 26709 Javac regression remains fixed.
assert 'IRIS_26709_R1_JAVAC_EFFECTIVELY_FINAL_LONG_EV' in cap and 'final double adaptiveLongEvFinal = adaptiveLongEv;' in cap
callback=cap[cap.index('mCaptureSession.capture(b.build(), new CameraCaptureSession.CaptureCallback()'):cap.index('}, mBackgroundHandler);',cap.index('mCaptureSession.capture(b.build(), new CameraCaptureSession.CaptureCallback()'))]
assert '+ " targetDeltaEv=" + adaptiveLongEvFinal' in callback
print('PASS 26712 regressions: 26708-like HAL visible navigation; one hidden signed scene correction; semantic navigation release during movement; no preview freeze; immediate post-capture HAL/0EV; HAL-baselined LONG; protected IQ preserved')
