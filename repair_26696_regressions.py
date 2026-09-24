#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3:raise SystemExit('usage: repair_26696_regressions.py BASE26695 CANDIDATE')
b=Path(sys.argv[1]);c=Path(sys.argv[2]);t=lambda r:(c/r).read_text()
assert 'import com.unspektrawesome.camera.RawFormat' in t('app/src/main/java/com/unspektrawesome/preview/RawPreviewPlanSelector.kt')
assert hashlib.sha256((c/'app/src/main/jniLibs/arm64-v8a/libunspektrawesome_vulkan.so').read_bytes()).hexdigest()=='f40b4707ae27e7d181563d99c31370d5a0e39daef1edb6366bba27da7a201dbd'
for r in ['app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java','app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/SpektraLiveHistogramView.java','app/src/main/res/layout/camera_fragment.xml','app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisLiveHistogramView.java','app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraCameraOwner.java']:
 assert (b/r).read_bytes()==(c/r).read_bytes(),r
raw=t('app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt');sess=t('app/src/main/java/com/unspektrawesome/camera/session/Camera2RawSession.java');mode=t('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraModeController.java');warm=t('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraPipelineWarmup.java')
# Permanent failures from 26694/26695 must not recur.
assert 'renderer.pollExposureMeter(exposureMeterBuffer)' in raw and 'consumeExposureMeterCarrierLocked(owner, "render")' in raw and 'EXPOSURE_METER_POLL_MS = 4L' in raw and 'MAX_PENDING_EXPOSURE_METERS = 8' in raw
assert 'IRIS_26695_RENDER_DELIVERED_AE_METER_OWNER' not in raw and 'ensureCaptureWarmupLocked' not in raw and 'renderer.warmUp(false, step)' not in raw
assert 'closeAndAwaitCameraRelease' not in sess and 'CountDownLatch' not in sess and '.await(' not in sess and 'closeWhenCameraReleased' in sess and 'public void onClosed(CameraDevice device)' in sess
assert 'retireForModeHandoff(2500L)' not in mode and 'CaptureController.isProcessing = true;' in mode
assert 'newFixedThreadPool(2' in warm and 'runTrack(app, true, "preview")' in warm and 'runTrack(app, false, "export")' in warm
assert 'ALBUM_NAME = "Camera"' in t('app/src/main/java/com/unspektrawesome/capture/JpegMediaStoreWriter.kt')
# Generated trees/scaffolding must never contaminate runtime-source scope; unexpected app/src is caught by exact full-app delta validator.
for bad in ['app/build/','app/.cxx/']:
 assert not any(x.startswith(bad) for x in [p.strip() for p in (Path(__file__).resolve().parent/'26696_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()])
print('PASS 26696 permanent regressions: RawFormat/native/fixed UI; 26694 AE one-shot; 26695 render-only AE; blocking warmup; blocking release latch; Photo processing UI; DCIM/Camera')
