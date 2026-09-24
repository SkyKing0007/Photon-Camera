#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3:raise SystemExit('usage: validate_26696r1.py BASE26695 CANDIDATE')
b=Path(sys.argv[1]);c=Path(sys.argv[2]);pkg=Path(__file__).resolve().parent
def t(r):return (c/r).read_text()
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def H(root):return {str(p.relative_to(root)):h(p) for p in root.rglob('*') if p.is_file()}
B=H(b/'app');C=H(c/'app');changed=sorted('app/'+x for x in set(B)|set(C) if B.get(x)!=C.get(x));exp=sorted(x.strip() for x in (pkg/'26696R1_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip());added=[x.strip() for x in (pkg/'26696R1_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x.strip()]
assert changed==exp and len(B)==1822 and len(C)==1823 and len(changed)==9 and len(added)==1
assert added==['app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraPipelineWarmup.java'] and not (b/added[0]).exists() and (c/added[0]).is_file()
raw=t('app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt'); sess=t('app/src/main/java/com/unspektrawesome/camera/session/Camera2RawSession.java'); mode=t('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraModeController.java'); ae=t('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraExposureController.java'); warm=t('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraPipelineWarmup.java'); app=t('app/src/main/java/com/particlesdevs/photoncamera/app/PhotonCamera.java'); cap=t('app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java'); ui=t('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java'); vr=t('app/src/main/java/com/unspektrawesome/vulkan/VulkanRenderer.kt')
# Exact 1.1.2 meter transport semantics recovered from APK.
for x in ['EXPOSURE_METER_GENERATION_OFFSET = 0','EXPOSURE_METER_POLL_MS = 4L','MAX_PENDING_EXPOSURE_METERS = 8','LinkedHashMap<Long, PendingExposureMeter>','renderer.pollExposureMeter(exposureMeterBuffer)','consumeExposureMeterCarrierLocked(owner, "render")','scheduleExposureMeterPollLocked()','putLong(EXPOSURE_METER_GENERATION_OFFSET, generation)','putLong(VulkanRenderer.EXPOSURE_METER_SEQUENCE_OFFSET, 0L)','putDouble(VulkanRenderer.EXPOSURE_METER_VALUE_OFFSET, Double.NaN)','pending.actualIso','pending.actualExposureNs','IRIS_26696_UNSPEKTRA_AE'] : assert x in raw,x
assert raw.index('consumeExposureMeterCarrierLocked(owner, "render")') < raw.index('scheduleExposureMeterPollLocked()')
assert 'if (meterGeneration > 0L) pendingExposureMeters.remove(meterGeneration)' in raw
for x in ['EXPOSURE_METER_METHOD_CENTER_WEIGHTED = 0','EXPOSURE_METER_DEFAULT_CENTER = 0.5f','EXPOSURE_METER_SEQUENCE_OFFSET = 24','EXPOSURE_METER_VALUE_OFFSET = 32']: assert x in vr,x
# Solver is actual-frame authoritative, retains 1.1.2 default lens AE limits and lock/balance behavior.
for x in ['IRIS_26696_UNSPEKTRA_AE_ACTUAL_FRAME_AUTHORITY','IRIS_26696_UNSPEKTRA_AE_LENS_LIMITS','DEFAULT_AE_SLOWEST_EXPOSURE_NS = 33_333_333L','setAeBalanceEv','case ISO_PRIORITY:','case SHUTTER_PRIORITY:','case MANUAL:','hardwareExposureMaxNs','TARGET_LINEAR = 0.18','MAX_STEP_EV = 0.20']: assert x in ae,x
assert 'int actualIso, long actualExposureNs' in ae and 'currentIso = clampInt(actualIso' in ae and 'currentExposureNs = clampLong(actualExposureNs' in ae
assert 'IRIS_26696R1_DORMANT_CALLER_SOURCE_COMPATIBILITY' in ae
assert ae.count('public synchronized Solution update(long nowNs, double centerWeightedLinearMeter)') == 1
dorm=t('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraCameraOwner.java')
assert dorm.count('exposureController.update(System.nanoTime(), meter)') == 1
assert 'pending.actualIso' in raw and 'pending.actualExposureNs' in raw
assert 'this.mode == Mode.MANUAL' in ae and 'hardwareIsoMin' in ae and 'hardwareIsoMax' in ae
# 1.1.2-style asynchronous preview/export startup warmup: never gates camera entry/handoff.
for x in ['IRIS_26696_STANDALONE_ASYNC_WARMUP_OWNER','newFixedThreadPool(2','runTrack(app, true, "preview")','runTrack(app, false, "export")','for (int step = 0; step <= 9; step++)','renderer.warmUp(preview, step)']: assert x in warm,x
assert 'SpektraPipelineWarmup.start(this);' in app
for bad in ['CountDownLatch','await(','Thread.sleep(','join(']: assert bad not in warm,bad
assert 'ensureCaptureWarmupLocked' not in raw and 'IRIS_26695_STANDALONE_CAPTURE_PIPELINE_WARMUP_OWNER' not in raw
# Existing Iris processing-ring authority, no parallel animation owner.
assert 'IRIS_26696_SPEKTRA_PROCESSING_UI_AUTHORITY' in mode
st=mode[mode.index('private void bridgeProcessingStarted'):mode.index('private void bridgeCaptureSucceeded')]; assert st.index('CaptureController.isProcessing = true;') < st.index('events.onProcessingStarted("Spektra")')
assert mode.count('CaptureController.isProcessing = false;')>=3
# Async CameraDevice release; destination mode commit after actual onClosed, never a blocking wait.
for x in ['IRIS_26696_CAMERA_DEVICE_RELEASE_CALLBACK_OWNER','public void onClosed(CameraDevice device)','closeWhenCameraReleased','finishCameraDeviceRelease']: assert x in sess,x
for bad in ['CountDownLatch','closeAndAwaitCameraRelease','cameraDeviceClosedLatch','.await(']: assert bad not in sess,bad
assert 'fun retireForModeHandoff(onReleased: Runnable)' in raw and 'current.session.closeWhenCameraReleased' in raw
assert 'exitForModeHandoff(() ->' in cap and 'retireModeForTransition(previousMode, cameraMode,' in ui and 'commitAndRestartMode(previousMode, cameraMode)' in ui
assert 'retireForModeHandoff(2500L)' not in mode
# Proven 26694 behavior retained.
assert 'ALBUM_NAME = "Camera"' in t('app/src/main/java/com/unspektrawesome/capture/JpegMediaStoreWriter.kt')
for r in ['app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java','app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java','app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/SpektraLiveHistogramView.java','app/src/main/res/layout/camera_fragment.xml','app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraCameraOwner.java']:
 assert (b/r).read_bytes()==(c/r).read_bytes(),r
assert 'VERSION_NAME=0.9726696' in t('app/version.properties') and 'VERSION_BUILD=26696' in t('app/version.properties')
print('PASS 26696 R1 semantic/ownership validation: 1.1.2 generation+poll AE; actual-frame solver; async preview/export warmup; Iris processing ring; async CameraDevice release')
