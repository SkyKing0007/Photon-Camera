#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3:raise SystemExit('usage: validate_26695.py BASE CANDIDATE')
b=Path(sys.argv[1]);c=Path(sys.argv[2]);pkg=Path(__file__).resolve().parent
def t(r):return (c/r).read_text()
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def H(root):return {str(p.relative_to(root)):h(p) for p in root.rglob('*') if p.is_file()}
B=H(b/'app');C=H(c/'app');changed=sorted('app/'+x for x in set(B)|set(C) if B.get(x)!=C.get(x));exp=sorted(x.strip() for x in (pkg/'26695_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip());assert changed==exp and len(B)==len(C)==1822 and len(changed)==4
raw=t('app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt');sess=t('app/src/main/java/com/unspektrawesome/camera/session/Camera2RawSession.java');mode=t('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraModeController.java');vr=t('app/src/main/java/com/unspektrawesome/vulkan/VulkanRenderer.kt')
assert 'IRIS_26695_RENDER_DELIVERED_AE_METER_OWNER' in raw and 'if (!renderer.pollExposureMeter(exposureMeterBuffer)) return' not in raw
meter=raw[raw.index('private fun updateExposureFromNativeMeter'):raw.index('private fun recordRawImportCapability')];assert 'pollExposureMeter' not in meter and 'getLong(VulkanRenderer.EXPOSURE_METER_SEQUENCE_OFFSET)' in meter and 'getDouble(VulkanRenderer.EXPOSURE_METER_VALUE_OFFSET)' in meter
for x in ['EXPOSURE_METER_METHOD_CENTER_WEIGHTED = 0','EXPOSURE_METER_DEFAULT_CENTER = 0.5f','EXPOSURE_METER_SEQUENCE_OFFSET = 24','EXPOSURE_METER_VALUE_OFFSET = 32']:assert x in vr
assert (b/'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraExposureController.java').read_bytes()==(c/'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraExposureController.java').read_bytes()
assert 'IRIS_26695_STANDALONE_CAPTURE_PIPELINE_WARMUP_OWNER' in raw and 'for (step in 0..9)' in raw and 'renderer.warmUp(false, step)' in raw
reconcile=raw[raw.index('private fun reconcileLocked'):raw.index('private fun startLocked')];assert 'if (!ensureCaptureWarmupLocked()) return' in reconcile
assert 'IRIS_26695_SPEKTRA_PROCESSING_UI_AUTHORITY' in mode
st=mode[mode.index('private void bridgeProcessingStarted'):mode.index('private void bridgeCaptureSucceeded')];assert st.index('CaptureController.isProcessing = true;')<st.index('events.onProcessingStarted("Spektra")');assert mode.count('CaptureController.isProcessing = false;')>=3
assert 'IRIS_26695_CAMERA_DEVICE_RELEASE_AUTHORITY' in sess and 'closeAndAwaitCameraRelease' in sess and 'public void onClosed(CameraDevice device)' in sess and 'cameraDeviceClosedLatch' in sess
assert 'IRIS_26695_SPEKTRA_RELEASE_BARRIER' in raw and 'owner.session.closeAndAwaitCameraRelease(timeoutMs)' in raw and 'retireForModeHandoff(2500L)' in mode
assert 'IRIS_26695_SPEKTRA_SHUTTER_EXPOSURE' in sess
assert 'ALBUM_NAME = "Camera"' in t('app/src/main/java/com/unspektrawesome/capture/JpegMediaStoreWriter.kt')
for r in ['app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java','app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java','app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/SpektraLiveHistogramView.java','app/src/main/res/layout/camera_fragment.xml']:
 assert (b/r).read_bytes()==(c/r).read_bytes(),r
assert 'VERSION_NAME=0.9726695' in t('app/version.properties') and 'VERSION_BUILD=26695' in t('app/version.properties')
print('PASS 26695 semantic/ownership validation: render-delivered AE; cold capture warmup; Photo processing UI; real CameraDevice release barrier')
