#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: repair_26694_regressions.py BASE CANDIDATE')
b=Path(sys.argv[1]); c=Path(sys.argv[2]);
def txt(rel): return (c/rel).read_text()
# Permanent 26692 R1 compiler failure.
plan=txt('app/src/main/java/com/unspektrawesome/preview/RawPreviewPlanSelector.kt'); assert 'import com.unspektrawesome.camera.RawFormat' in plan
# Exact native authority and 26693 histogram architecture remain untouched.
so=c/'app/src/main/jniLibs/arm64-v8a/libunspektrawesome_vulkan.so'; assert hashlib.sha256(so.read_bytes()).hexdigest()=='f40b4707ae27e7d181563d99c31370d5a0e39daef1edb6366bba27da7a201dbd'
for rel in ['app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java','app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/SpektraLiveHistogramView.java','app/src/main/res/layout/camera_fragment.xml','app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisLiveHistogramView.java']:
 assert (b/rel).read_bytes()==(c/rel).read_bytes(),rel
hist=txt('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/SpektraLiveHistogramView.java')
for bad in ('HandlerThread','pollOnce()','startPolling()'): assert bad not in hist
ui=txt('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java'); assert 'IRIS_26693_UI_GEOMETRY_INVARIANT' in ui and 'finalOwner=fixedPhotoControlReference' in ui
# Do not revive dormant SpektraCameraOwner or duplicate publisher.
dorm='app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraCameraOwner.java'; assert (b/dorm).read_bytes()==(c/dorm).read_bytes()
assert 'SpektraJpegPublisher' not in txt('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraModeController.java')
# Regression for the exact 26693 device failure: never leave meter carrier at accidental x/y zero.
vr=txt('app/src/main/java/com/unspektrawesome/vulkan/VulkanRenderer.kt'); ctrl=txt('app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt')
assert 'EXPOSURE_METER_DEFAULT_CENTER = 0.5f' in vr and 'configureCenterWeightedExposureMeter(it)' in ctrl
# Capture UI callback failure may never fail camera/session ownership; callbacks are contained.
assert ctrl.count('SPEKTRA_CAPTURE_UI_CALLBACK_FAILED')==4
# Folder/gallery regression.
assert 'ALBUM_NAME = "Camera"' in txt('app/src/main/java/com/unspektrawesome/capture/JpegMediaStoreWriter.kt')
print('PASS 26694 permanent regressions: RawFormat import; 26693 UI/hist/native invariance; centered AE carrier; no dormant/duplicate owner; DCIM/Camera publication')
