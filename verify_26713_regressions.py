#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26713_regressions.py BASE26712 CAND')
b,c=map(Path,sys.argv[1:]);pkg=Path(__file__).resolve().parent
def H(r): return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
def txt(r,p): return (r/p).read_text()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
B,C=H(b),H(c); assert len(B)==len(C)==1823
expected=set((pkg/'26713_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()); assert expected=={
'app/src/main/assets/shaders/preview/main_fs.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java',
'app/version.properties'}
assert {k for k in B|C if B.get(k)!=C.get(k)}==expected
v=txt(c,'app/version.properties'); assert 'VERSION_NAME=0.9726713' in v and 'VERSION_BUILD=26713' in v
cap=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
main=c/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java'
shader=c/'app/src/main/assets/shaders/preview/main_fs.glsl'
# Exact 26708 visible viewfinder bytes restored.
assert sha(main)=='388a09ae0966eeae34dde85c068bd537435ac2f3763be9f4cdf10a32cb62bdfa'
assert sha(shader)=='4f61b83efe5b6ebe64bff6dbd165757576b1c9686e7ea78c24fdd66b3dfa724a'
assert 'IRIS_26711_HIDDEN_PHYSICAL_EXPOSURE_TRANSITION' not in main.read_text()
assert 'IRIS_26712_FULL_INVERSE_HAL_PREVIEW_PRESENTATION' not in shader.read_text()
assert 'IRIS_26662_FRAME_MATCHED_PREVIEW_PRESENTATION' in shader.read_text()
# Active preview authority is observation-only.
start=cap.index('private void updateMotion26680StablePreviewAuthority(@NonNull TotalCaptureResult result)')
end=cap.index('IRIS_26662_GOOGLE_HDR_REFERENCE_EXPOSURE_OWNER',start)
owner=cap[start:end]
for forbidden in ['mPreviewRequestBuilder.set','rebuildPreviewBuilder();','mMotion26710ManualReferenceActive = true','IRIS_26712_ONE_SHOT_REFERENCE_COMMIT']:
    assert forbidden not in owner,forbidden
for t in ['IRIS_26713_CAPTURE_RECIPE_OBSERVER','IRIS_26713_HAL_OBSERVATION_START','IRIS_26713_CAPTURE_RECIPE_READY','previewMutation=false repeatingAeMode=HAL_ON','captureDomainOnly=true adjustedRawCannotVoteAgain=true']:
    assert t in owner,t
# Preview exposure handoff is hard unity.
getter=cap[cap.index('public float getMotion26663ReferencePreviewProtectionEv'):cap.index('IRIS_26496_SPATIALLY_PERSISTENT_HIGHLIGHT_TRIGGER')]
assert 'IRIS_26713_PREVIEW_EXPOSURE_ISOLATION' in getter and 'return 0.0f;' in getter and 'Float.NaN' not in getter
# Bounded recipe lifecycle.
for t in ['MOTION_26713_OBSERVATION_TIMEOUT_MS = 1200L','MOTION_26713_OBSERVATION_DRIFT_EV = 0.12f','MOTION_26713_RECIPE_INVALIDATE_EV = 0.22f','IRIS_26713_CAPTURE_RECIPE_INVALIDATED','previewMutation=false halAeContinuous=true']:
    assert t in cap,t
# Invalidation/completion clears all HAL-baseline statistics so LONG cannot consume stale scene evidence.
for method_name,end_marker in [('motion26713CancelRecipe','private boolean motion26713ManualSensorAvailable'),('motion26713ClearRecipeAfterPhysicalBatch','IRIS_26713_CAPTURE_DOMAIN_ONLY_EXPOSURE_OWNER')]:
    s0=cap.index('private void '+method_name); s1=cap.index(end_marker,s0); body=cap[s0:s1]
    for t in ['mMotion26709FrozenCaptureProtectionEv = 0.0f;','mMotion26709HalBaselineEnergy = Double.NaN;','mMotion26709HalBaselineExposureNs = 0L;','mMotion26709HalBaselineIso = 0;','mMotion26709LastConsumedMeterTimestampNs = 0L;','mMotion26710HalBaselineHighlightFraction = Float.NaN;','mMotion26710HalBaselineFloorFraction = Float.NaN;','mMotion26710HalBaselineShadowFraction = Float.NaN;','mMotion26710HalBaselineMeanSignal = Float.NaN;']:
        assert t in body,(method_name,t)
# Shutter waits for recipe only, never a physical protected preview generation.
guard=cap[cap.index('private boolean motion26676ProtectionIncreasePendingForShutter'):cap.index('private boolean motion26676DeferShutterUntilProtectedGeneration')]
assert 'IRIS_26713_RECIPE_ONLY_SHUTTER_GUARD' in guard and '!mMotion26713RecipeReady' in guard
assert '!mMotion26709HalBaselineReady || !mMotion26709ReferenceSettled' not in guard
# Corrected NORMAL exposure only uses RAW-only still-capture path.
for t in ['IRIS_26713_HAL_ZSL_EVIDENCE_EXCLUDED_FROM_CORRECTED_NORMAL','IRIS_26713_CAPTURE_DOMAIN_REFERENCE_PLAN','captureDomainOnly=true','previewRepeatingNeverMutated=true','normalTargetExposureNs','normalTargetIso','motion26713ResultMatchesTarget','previewRepeatingRequestMutated=false rawOnlyTarget=true','captureDomainOnly26713=true']:
    assert t in cap,t
t0=cap.index('private boolean submitMotion26593MissingNormals')
t1=cap.index('IRIS_26670_CAPTURE_TRANSACTION_PREVIEW_RESTORE',t0)
topup=cap[t0:t1]
assert 'CameraDevice.TEMPLATE_STILL_CAPTURE' in topup
assert 'b.addTarget(mImageReaderRaw.getSurface())' in topup
assert 'mPreviewRequestBuilder.set' not in topup and 'rebuildPreviewBuilder' not in topup
# First actual corrected NORMAL becomes downstream metadata/reference authority.
plan=cap[cap.index('private static final class Motion26593CapturePlan'):cap.index('private volatile Motion26593CapturePlan')]
assert 'volatile TotalCaptureResult normalReferenceResult;' in plan
assert 'if (normalReferenceResult == null)' in plan
# Capture-local completion explicitly restores clean HAL preview request.
restore=cap[cap.index('private boolean restoreMotion26670LivePreviewAfterCaptureLocalRequests'):cap.index('IRIS_26593_TOTAL_BATCH_COMPLETION_GATE')]
for t in ['IRIS_26713_CLEAN_HAL_REPEATING_RESTORE','CaptureRequest.CONTROL_AE_MODE_ON','CaptureRequest.CONTROL_AE_EXPOSURE_COMPENSATION, 0','CaptureRequest.SENSOR_EXPOSURE_TIME, null','CaptureRequest.SENSOR_SENSITIVITY, null']:
    assert t in restore,t
# Batch completion clears recipe ownership only; old repeating-release owner is not invoked.
b0=cap.index('clearMotion26593CapturePlan(iris26593Plan, "immutable_batch_handoff")')
b1=cap.index('processExecutor.execute(() -> {',b0)
batch=cap[b0:b1]
assert 'motion26713ClearRecipeAfterPhysicalBatch();' in batch
assert 'motion26711ReleaseToHalAfterPhysicalCapture();' not in batch
# LONG remains HAL-baselined and exact frame budget remains.
for t in ['IRIS_26710_HAL_BASELINED_LONG_EXPOSURE_OWNER','IRIS_26712_LONG_STAYS_ABOVE_SIGNED_NORMAL','mMotion26712TargetPhysicalOffsetEv + 0.50','final boolean iris26593ShortSubmitted = false;','final int iris26593AuxCount = iris26505LongRequested ? 1 : 0;','final int iris26593NormalTarget = iris26593TotalTarget - iris26593AuxCount;']:
    assert t in cap,t
# Historical reactive owners remain dormant.
for t in ['/* updateMotionV2ExposureAuthority(result); intentionally dormant */','/* updateMotion26368AdaptiveAeBias(result); intentionally dormant */','/* updateMotion26662GoogleReferenceExposureAuthority(result); intentionally dormant */']:
    assert t in cap,t
assert cap.count('updateMotion26680StablePreviewAuthority(result);')==1
# Core IQ/native/DNG owners remain byte-identical to successful 26712.
protected=[
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp']
for rel in protected: assert (b/rel).read_bytes()==(c/rel).read_bytes(),rel
# Permanent 26709 Javac failure remains fixed.
assert 'IRIS_26709_R1_JAVAC_EFFECTIVELY_FINAL_LONG_EV' in cap
assert 'final double adaptiveLongEvFinal = adaptiveLongEv;' in cap
print('PASS 26713 regressions: exact 26708 preview; HAL repeating exposure never taken over; bounded recipe; RAW-only corrected NORMAL burst; clean HAL restore; LONG/IQ preserved')
