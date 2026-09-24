#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3:raise SystemExit('usage: repair_26695_regressions.py BASE CANDIDATE')
b=Path(sys.argv[1]);c=Path(sys.argv[2]);t=lambda r:(c/r).read_text()
assert 'import com.unspektrawesome.camera.RawFormat' in t('app/src/main/java/com/unspektrawesome/preview/RawPreviewPlanSelector.kt')
assert hashlib.sha256((c/'app/src/main/jniLibs/arm64-v8a/libunspektrawesome_vulkan.so').read_bytes()).hexdigest()=='f40b4707ae27e7d181563d99c31370d5a0e39daef1edb6366bba27da7a201dbd'
for r in ['app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java','app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/SpektraLiveHistogramView.java','app/src/main/res/layout/camera_fragment.xml','app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisLiveHistogramView.java','app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraCameraOwner.java']:
 assert (b/r).read_bytes()==(c/r).read_bytes(),r
raw=t('app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt');assert 'if (!renderer.pollExposureMeter(exposureMeterBuffer)) return' not in raw and 'IRIS_26695_RENDER_DELIVERED_AE_METER_OWNER' in raw and 'renderer.warmUp(false, step)' in raw
sess=t('app/src/main/java/com/unspektrawesome/camera/session/Camera2RawSession.java');assert 'closeAndAwaitCameraRelease' in sess and 'public void onClosed(CameraDevice device)' in sess
mode=t('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraModeController.java');assert 'CaptureController.isProcessing = true;' in mode and 'retireForModeHandoff(2500L)' in mode
assert 'ALBUM_NAME = "Camera"' in t('app/src/main/java/com/unspektrawesome/capture/JpegMediaStoreWriter.kt')
print('PASS 26695 permanent regressions: RawFormat; fixed UI/hist/native; no AE double-poll; cold RCD warmup; release barrier; Photo processing UI gate')
