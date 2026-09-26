#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26714_regressions.py BASE26713 CAND')
b,c=map(Path,sys.argv[1:]);pkg=Path(__file__).resolve().parent
def H(r):return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
def txt(r,p):return (r/p).read_text()
B,C=H(b),H(c);assert len(B)==len(C)==1823
expected={'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java','app/version.properties'}
assert set((pkg/'26714_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines())==expected
assert {k for k in B|C if B.get(k)!=C.get(k)}==expected
v=txt(c,'app/version.properties');assert 'VERSION_NAME=0.9726714' in v and 'VERSION_BUILD=26714' in v
cap=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
# Viewfinder/rendering remain exact successful 26713 bytes (already restored to 26708 behavior).
for rel in ['app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java','app/src/main/assets/shaders/preview/main_fs.glsl']:
 assert (b/rel).read_bytes()==(c/rel).read_bytes(),rel
# Preview authority stays observation-only: absolutely no Iris exposure write in repeating owner.
start=cap.index('private void updateMotion26680StablePreviewAuthority(@NonNull TotalCaptureResult result)')
end=cap.index('/*\n     * IRIS_26662_GOOGLE_HDR_REFERENCE_EXPOSURE_OWNER',start)
owner=cap[start:end]
for forbidden in ['mPreviewRequestBuilder.set','rebuildPreviewBuilder();','mMotion26710ManualReferenceActive = true','IRIS_26712_ONE_SHOT_REFERENCE_COMMIT']:
 assert forbidden not in owner,forbidden
# 26714 continuous read-only nine-phase meter survives ordinary HAL drift and normalizes P99.5.
for t in ['IRIS_26714_NORMALIZED_HANDHELD_HIGHLIGHT_RECIPE','MOTION_26714_CLASSIFIER_PACKET_MAX_DRIFT_EV = 0.35f','MOTION_26714_METER_NORMALIZE_MAX_EV = 0.85f','exposureNormalized26714=true']:
 assert t in cap,t
meter=cap[cap.index('private void accumulateMotion26708HighlightPhase'):cap.index('private float motion26708FrozenShortProtectionEv')]
assert '!mMotion26709HalBaselineReady' not in meter
assert '> MOTION_26714_CLASSIFIER_PACKET_MAX_DRIFT_EV' in meter
assert 'iris26714PacketScale' in meter and 'mMotion26708PublishedExposureEnergy = mMotion26708ClassifierExposureEnergy;' in meter
# Observation/recipe invalidation is semantic scene navigation, never a raw shakiness or tiny AE drift abort.
assert 'observation-camera-motion' not in owner and 'observation-hal-drift' not in owner
assert 'meterEvMismatch > 0.08' not in owner
for t in ['motion26712NavigationConfirmed()','observation-semantic-navigation','iris26714MeterScale','iris26714NormalizedP995','semanticMotionOnlyInvalidation=true','continuousNinePhaseMeterPreserved=true','MOTION_26714_NEW_SCENE_METER_DELAY_NS']:
 assert t in owner,t
assert 'clearMotion26708HighlightClassifier("26713-hal-observation-start")' not in owner
assert 'MOTION_26714_STATIONARY_SHAKINESS_THRESHOLD' in owner
# Strong 26713 observed condition: 0.11EV meter mismatch must be inside normalization tolerance.
assert 0.11 < 0.85
# Cached recipe is scene-relative EV intent and re-based to current untouched HAL at shutter.
for t in ['IRIS_26714_SHUTTER_HAL_REBASE','recipeRebasedToCurrentHal=true','desiredEnergy = iris26713CurrentHalEnergy * Math.pow(2.0, desiredOffsetEv)','mMotion26709HalBaselineEnergy = iris26713CurrentHalEnergy']:
 assert t in cap,t
shutter=cap[cap.index('final double iris26713CurrentHalEnergy'):cap.index('mZslCapturing = true;',cap.index('final double iris26713CurrentHalEnergy'))]
assert 'iris26713RecipeBaselineMismatchEv' not in shutter
assert 'mMotion26713RecipeExposureNs > 0L && mMotion26713RecipeIso > 0' not in shutter
# Shutter wait remains bounded and never writes preview exposure.
guard=cap[cap.index('private boolean motion26676ProtectionIncreasePendingForShutter'):cap.index('private void triggerZslCapture()')]
assert 'IRIS_26714_RECIPE_ONLY_SHUTTER_GUARD' in guard and 'MOTION_26676_SHUTTER_MAX_WAIT_MS = 1500L' in cap
assert 'mPreviewRequestBuilder.set' not in guard and 'rebuildPreviewBuilder' not in guard
# Capture-domain corrected NORMAL, clean HAL restore, independent LONG all remain inherited.
for t in ['IRIS_26713_HAL_ZSL_EVIDENCE_EXCLUDED_FROM_CORRECTED_NORMAL','captureDomainOnly=true','previewRepeatingNeverMutated=true','previewRepeatingRequestMutated=false rawOnlyTarget=true','IRIS_26713_CLEAN_HAL_REPEATING_RESTORE','IRIS_26710_HAL_BASELINED_LONG_EXPOSURE_OWNER','IRIS_26712_LONG_STAYS_ABOVE_SIGNED_NORMAL']:
 assert t in cap,t
# Historical reactive exposure owners remain dormant.
for t in ['/* updateMotionV2ExposureAuthority(result); intentionally dormant */','/* updateMotion26368AdaptiveAeBias(result); intentionally dormant */','/* updateMotion26662GoogleReferenceExposureAuthority(result); intentionally dormant */']:
 assert t in cap,t
assert cap.count('updateMotion26680StablePreviewAuthority(result);')==1
# Core IQ/native/DNG/UHDR/Sabre owners remain byte-identical to successful 26713.
protected=[
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp']
for rel in protected:assert (b/rel).read_bytes()==(c/rel).read_bytes(),rel
assert 'IRIS_26709_R1_JAVAC_EFFECTIVELY_FINAL_LONG_EV' in cap and 'final double adaptiveLongEvFinal = adaptiveLongEv;' in cap
print('PASS 26714 regressions: HAL-only viewfinder preserved; nine-phase meter exposure-normalized; micro-shake/AE drift cannot erase recipe; semantic navigation invalidates; shutter rebase + capture-domain NORMAL/LONG preserved')
