#!/usr/bin/env python3
from pathlib import Path
import re, sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26691_regressions.py BASE CANDIDATE')
base=Path(sys.argv[1]); c=Path(sys.argv[2])
def text(rel): return (c/rel).read_text()
mode=text('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraModeController.java')
frag=text('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java')
ctrl=text('app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt')
view=text('app/src/main/java/com/unspektrawesome/preview/VulkanRawPreviewView.kt')
sess=text('app/src/main/java/com/unspektrawesome/camera/session/Camera2RawSession.java')
vr=text('app/src/main/java/com/unspektrawesome/vulkan/VulkanRenderer.kt')
prefs=text('app/src/main/java/com/unspektrawesome/settings/CameraPreferences.kt')
jpeg=text('app/src/main/java/com/unspektrawesome/capture/JpegMediaStoreWriter.kt')
log=text('app/src/main/java/com/unspektrawesome/diagnostics/InternalLogRecorder.java')
hist=text('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/SpektraLiveHistogramView.java')
layout=text('app/src/main/res/layout/camera_fragment.xml')
so=(c/'app/src/main/jniLibs/arm64-v8a/libunspektrawesome_vulkan.so').read_bytes()
# 26691 exact device failure: absence of preview LSC must never reject shutter before Camera2.
assert 'requireNotNull(latestLensShadingMap)' not in ctrl
assert 'latestLensShadingMap,' in ctrl
assert 'val lensShadingMap: LensShadingMapParameters?' in ctrl
assert re.search(r'val\s+captureLensShading\s*=\s*stillLensShading\s*\?:\s*request\.lensShadingMap',ctrl)
assert 'else -> "NONE"' in ctrl
assert 'lensShadingByteBuffer(captureLensShading)' in ctrl
for marker in ('IRIS_26691_SPEKTRA_CAPTURE_ACCEPT','IRIS_26691_SPEKTRA_STILL_RAW','IRIS_26691_SPEKTRA_RCD_OK','IRIS_26691_SPEKTRA_JPEG_SAVED','IRIS_26691_SPEKTRA_CAPTURE_ERROR'):
 assert marker in ctrl, marker
# 26691 histogram: exact native 1.1.2 owner; never route through Iris GLPreview/PixelCopy.
assert b'Java_com_unspektrawesome_vulkan_VulkanRenderer_nativeHistogramPixels' in so
assert b'ViewfinderHistogram' in so
assert 'fun histogramPixels(scale: Float): IntArray' in vr
assert 'renderer.histogramPixels(scale)' in ctrl
assert 'public int[] histogramPixels(float scale)' in mode
assert 'NATIVE_SIDE = 128' in hist and 'NATIVE_PIXELS = NATIVE_SIDE * NATIVE_SIDE' in hist
assert 'active.histogramPixels(1.0f)' in hist
assert 'PixelCopy' not in hist and 'GLPreview' not in hist
assert 'android:id="@+id/spektra_live_histogram"' in layout
assert 'android:id="@+id/spektra_histogram_toggle"' in layout
assert 'ic_spektra_histogram' in layout
assert 'spektraHistogramEnabled = false' in frag
assert 'spektraHistogramEnabled = !spektraHistogramEnabled' in frag
assert 'setSpektraActive(spektraVisible && spektraHistogramEnabled)' in frag
assert 'IRIS_26691_SPEKTRA_HISTOGRAM_TOGGLE_OWNER' in frag
# Existing Iris histogram source is exact authority byte-for-byte and hidden only during Spektra.
iris='app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisLiveHistogramView.java'
assert (c/iris).read_bytes()==(base/iris).read_bytes()
assert 'R.id.iris_live_histogram' in frag and 'spektraVisible ? View.GONE : View.VISIBLE' in frag
# 26690 device-runtime JNI crash and lazy startup containment remain permanent.
assert b'com/unspektrawesome/diagnostics/InternalLogRecorder' in so
assert b'recordNative' in so and b'(ILjava/lang/String;Ljava/lang/String;)V' in so
assert 'package com.unspektrawesome.diagnostics;' in log
assert re.search(r'public\s+static\s+void\s+recordNative\s*\(\s*int\s+priority\s*,\s*String\s+tag\s*,\s*String\s+message\s*\)',log)
ctor=mode[mode.index('public SpektraModeController('):mode.index('public synchronized void bindPreviewSurface')]
bind=mode[mode.index('public synchronized void bindPreviewSurface'):mode.index('private synchronized RawVulkanPreviewController ensureControllerForActivation')]
ensure=mode[mode.index('private synchronized RawVulkanPreviewController ensureControllerForActivation'):mode.index('private void failActivation')]
assert 'new RawVulkanPreviewController' not in ctor and 'new RawVulkanPreviewController' not in bind
assert mode.count('new RawVulkanPreviewController')==1 and ensure.count('new RawVulkanPreviewController')==1
# 26689 R1 compiler failure remains permanent.
plan_error_block="""}.getOrElse { error ->
            stopActiveLocked()
            publishLocked(
                RawPreviewPhase.ERROR,
                \"RAW preview selection failed: ${error.message ?: error.javaClass.simpleName}\",
            )
            return
        }"""
assert plan_error_block in ctrl
# 26688 Surface lifecycle regression.
prep=frag[frag.index('onSpektraPreviewPreparing()'):frag.index('onSpektraPreviewReady()')]
assert 'setSpektraPreviewVisible(true)' in prep and 'setSpektraPreviewVisible(false)' not in prep
assert 'surfaceCreated' in view and 'attachSurface(holder.surface)' in view and 'surfaceDestroyed' in view and 'detachSurface(holder.surface)' in view
# 26687 ownership/warmup and successful hosted transaction.
assert '.warmUp(' not in ctrl and '.warmUp(' not in mode
for x in ('SpektraCameraOwner','SpektraRawCpuOwner','SpektraRawVulkanOwner','SpektraRawDevelop'):
 assert x not in mode and x not in ctrl, f'old owner reachable: {x}'
assert 'acquireLatestImage()' in sess and 'captureStill' in sess and 'resumePreview' in sess
assert ctrl.count('owner.session.captureStill(')==1
assert 'resumePreviewAfterStillLocked' in ctrl
assert 'nativeCaptureRcd' in vr and 'false,\n            true,\n            true,\n            0,' in vr
assert 'pollExposureMeter' in ctrl and 'SpektraExposureController' in ctrl
assert 'DEFAULT_JPEG_QUALITY = 100' in jpeg
assert 'RawPreviewQuality.LOW' in prefs and 'RawPreviewQuality.MEDIUM.name' not in prefs
# No DNG/generated contamination.
for rel in ('app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt','app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraModeController.java'):
 s=text(rel); assert 'DngCreator' not in s and 'image/x-adobe-dng' not in s
assert not any(str(p.relative_to(c)).startswith('app/build/') or str(p.relative_to(c)).startswith('app/.cxx/') for p in c.rglob('*') if p.is_file())
print('PASS 26691 permanent regressions: nullable-LSC shutter, native Spektra histogram isolation, 26690 JNI/startup, 26689 compiler, 26688 Surface, 26687 ownership')
