#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26715_regressions.py BASE26714 CAND')
b,c=map(Path,sys.argv[1:]);pkg=Path(__file__).resolve().parent
def H(r):return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
def txt(r,p):return (r/p).read_text()
B,C=H(b),H(c);assert len(B)==len(C)==1823
expected={
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/util/Log.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/version.properties'}
assert set((pkg/'26715_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines())==expected
assert {k for k in B|C if B.get(k)!=C.get(k)}==expected
v=txt(c,'app/version.properties');assert 'VERSION_NAME=0.9726715' in v and 'VERSION_BUILD=26715' in v
capb=txt(b,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java');cap=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
# Visible viewfinder and shader stay exact successful 26714 bytes.
for rel in ['app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java','app/src/main/assets/shaders/preview/main_fs.glsl']:
 assert (b/rel).read_bytes()==(c/rel).read_bytes(),rel
# 26714 normalized handheld meter and semantic scene invalidation remain active.
for t in ['IRIS_26714_NORMALIZED_HANDHELD_HIGHLIGHT_RECIPE','MOTION_26714_CLASSIFIER_PACKET_MAX_DRIFT_EV = 0.35f','MOTION_26714_METER_NORMALIZE_MAX_EV = 0.85f','exposureNormalized26714=true','motion26712NavigationConfirmed()','observation-semantic-navigation','semanticMotionOnlyInvalidation=true','continuousNinePhaseMeterPreserved=true']:
 assert t in cap,t
# Preview owner remains observation-only and may not write Iris exposure.
start=cap.index('private void updateMotion26680StablePreviewAuthority(@NonNull TotalCaptureResult result)');end=cap.index('/*\n     * IRIS_26662_GOOGLE_HDR_REFERENCE_EXPOSURE_OWNER',start);owner=cap[start:end]
for forbidden in ['mPreviewRequestBuilder.set','rebuildPreviewBuilder();','mMotion26710ManualReferenceActive = true','IRIS_26712_ONE_SHOT_REFERENCE_COMMIT']:
 assert forbidden not in owner,forbidden
# Negative HDR protection branch must be byte-identical to successful 26714.
anchor='                if (desiredOffsetEv < -0.03f) {'; stop='                } else if (desiredOffsetEv > 0.03f) {'
nb=capb[capb.index(anchor):capb.index(stop,capb.index(anchor))];nc=cap[cap.index(anchor):cap.index(stop,cap.index(anchor))];assert nb==nc,'26714 negative protection branch changed'
# SDR/no-highlight/positive intent keeps physical NORMAL at untouched HAL, enabling true ZSL.
pos=cap[cap.index(stop):cap.index('                final double actualRebasedEnergy',cap.index(stop))]
for t in ['IRIS_26715_SDR_ZSL_NORMAL_OWNER','iris26714RebasedTargetExp = iris26593ReferenceExp;','iris26714RebasedTargetIso = iris26593ReferenceIso;','IRIS_26715_SDR_ZSL_ROUTE','highlightProtectionRequired=false']:
 assert t in pos,t
for forbidden in ['desiredEnergy /','Math.ceil(','shutterCeilingNs']:
 assert forbidden not in pos,('positive branch still manufactures manual exposure',forbidden)
for t in ['iris26715NegativeProtectionRequired','iris26715SdrZslEligible','zslDisabledOnlyForNegativeProtection=']:
 assert t in cap,t
# Existing target-match gate still preserves HAL ring only when NORMAL equals HAL and excludes it for protected HDR.
for t in ['freezeMotion26598PreShutterNormals(iris26593NormalReference, iris26593TotalTarget)','final boolean iris26713TargetMatchesHal','IRIS_26713_HAL_ZSL_EVIDENCE_EXCLUDED_FROM_CORRECTED_NORMAL']:
 assert t in cap,t
# If an HAL-equivalent ZSL ring is short, top-up uses capture-local HAL AE lock, never a manual 70ms/high-ISO request.
top=cap[cap.index('private boolean submitMotion26593MissingNormals'):cap.index('private boolean motion26676ProtectionIncreasePendingForShutter')]
for t in ['iris26715HalEquivalentTopUp','IRIS_26715_HAL_EQUIVALENT_ZSL_TOPUP','CaptureRequest.CONTROL_AE_MODE_ON','CaptureRequest.CONTROL_AE_LOCK, true','CAPTURE_LOCAL_AE_LOCK_HAL_EQUIVALENT']:
 assert t in top,t
assert top.index('if (iris26715HalEquivalentTopUp)') < top.index('else if (manual)')
# LONG and 26714 capture-domain HDR owners stay present.
for t in ['IRIS_26710_HAL_BASELINED_LONG_EXPOSURE_OWNER','IRIS_26712_LONG_STAYS_ABOVE_SIGNED_NORMAL','IRIS_26713_CAPTURE_DOMAIN_NORMAL_PLUS_HAL_LONG_PLAN','captureDomainOnly=true','previewRepeatingNeverMutated=true']:
 assert t in cap,t
# New first-shot prewarm is idle-only/best-effort and must never gate shutter or mutate preview.
for t in ['IRIS_26715_IDLE_PIPELINE_PREWARM','THREAD_PRIORITY_BACKGROUND','PhotonMotionMgc1271Bridge.prewarmCapturePrograms()','captureMathChanged=false']:
 assert t in cap,t
pre=cap[cap.index('private void scheduleMotion26715IdlePipelinePrewarm()'):cap.index('public CaptureController(',cap.index('private void scheduleMotion26715IdlePipelinePrewarm()'))]
for forbidden in ['mPreviewRequestBuilder.set','rebuildPreviewBuilder','captureStillPicture()','triggerZslCapture()','mZslCapturing = true']:
 assert forbidden not in pre,forbidden
bridgeb=txt(b,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt');bridge=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
for t in ['IRIS_26715_IDLE_SABRE_PROGRAM_PREWARM','fun prewarmCapturePrograms(): Boolean','EglOwner.create()','prewarmGlesMgcSabreCapturePrograms(4096, 3072, 0)']:
 assert t in bridge,t
# reconstruct body from its declaration onward remains byte-identical (prewarm is additive before it).
rb=bridgeb[bridgeb.index('    @JvmStatic\n    fun reconstruct('):];rc=bridge[bridge.index('    @JvmStatic\n    fun reconstruct('):];assert rb==rc,'reconstruct processing math changed'
stackb=txt(b,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt');stack=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
for t in ['IRIS_26715_IDLE_SABRE_PROGRAM_PREWARM','internal fun prewarmGlesMgcSabreCapturePrograms','prewarmCapturePipeline(frameCount = 15, includeBento = false)']:
 assert t in stack,t
# Existing class itself, including processFrames/prewarmCapturePipeline and all reconstruction equations, is byte-identical.
cb=stackb[stackb.index('internal class GlesMgcRawSpatialStacker('):];cc=stack[stack.index('internal class GlesMgcRawSpatialStacker('):];assert cb==cc,'stacker class/reconstruction math changed'
# Log owner moves only persistent log files; tuning/backup storage owner remains untouched.
log=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/util/Log.java')
for t in ['IRIS_26715_IRIS_OWNED_LOG_DIRECTORY','IRIS_LOG_RELATIVE_PATH = "DCIM/Camera/Iris Camera/Logs"','DocumentFileType.FOLDER','getLogFolderDocumentFile();','cleanupOldLogs();']:
 assert t in log,t
assert 'PHOTON_LOG_SUBFOLDER' not in log
simple='app/src/main/java/com/particlesdevs/photoncamera/util/SimpleStorageHelper.java';assert (b/simple).read_bytes()==(c/simple).read_bytes();assert 'PHOTON_CAMERA_RELATIVE_PATH = "DCIM/PhotonCamera"' in txt(c,simple)
# Historical reactive owners remain dormant and protected IQ/native/DNG/UHDR owners stay byte-identical unless explicitly in allowlist.
for t in ['/* updateMotionV2ExposureAuthority(result); intentionally dormant */','/* updateMotion26368AdaptiveAeBias(result); intentionally dormant */','/* updateMotion26662GoogleReferenceExposureAuthority(result); intentionally dormant */']:
 assert t in cap,t
protected=[
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp']
for rel in protected:assert (b/rel).read_bytes()==(c/rel).read_bytes(),rel
print('PASS 26715 regressions: 26714 HDR/viewfinder/microshake preserved; no-highlight SDR uses HAL ZSL; dark positive manual burst retired; HAL-equivalent top-up safe; Iris-owned Logs; best-effort idle Sabre prewarm additive only')
