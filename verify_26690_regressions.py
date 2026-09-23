#!/usr/bin/env python3
from pathlib import Path
import re, sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26690_regressions.py BASE CANDIDATE')
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
so=(c/'app/src/main/jniLibs/arm64-v8a/libunspektrawesome_vulkan.so').read_bytes()
# 26690 device-runtime crash: exact JNI_OnLoad class/method/descriptor must exist in source.
assert b'com/unspektrawesome/diagnostics/InternalLogRecorder' in so
assert b'recordNative' in so and b'(ILjava/lang/String;Ljava/lang/String;)V' in so
assert 'package com.unspektrawesome.diagnostics;' in log
assert re.search(r'public\s+static\s+void\s+recordNative\s*\(\s*int\s+priority\s*,\s*String\s+tag\s*,\s*String\s+message\s*\)',log)
assert log.count('@Keep')>=2
# 26690 containment: dormant Spektra must not load native Vulkan during ordinary Iris startup/bind.
ctor=mode[mode.index('public SpektraModeController('):mode.index('public synchronized void bindPreviewSurface')]
bind=mode[mode.index('public synchronized void bindPreviewSurface'):mode.index('private synchronized RawVulkanPreviewController ensureControllerForActivation')]
ensure=mode[mode.index('private synchronized RawVulkanPreviewController ensureControllerForActivation'):mode.index('private void failActivation')]
assert 'new RawVulkanPreviewController' not in ctor
assert 'new RawVulkanPreviewController' not in bind
assert mode.count('new RawVulkanPreviewController')==1 and ensure.count('new RawVulkanPreviewController')==1
assert 'if (controller != null) previewView.bind(controller, owner);' in bind
assert mode.count('ensureControllerForActivation()')>=3
# 26689 R1 compiler failure permanent regression.
plan_error_block='''}.getOrElse { error ->
            stopActiveLocked()
            publishLocked(
                RawPreviewPhase.ERROR,
                "RAW preview selection failed: ${error.message ?: error.javaClass.simpleName}",
            )
            return
        }'''
assert plan_error_block in ctrl, '26689 compiler regression: publishLocked call missing'
# 26688 Surface lifecycle regression.
prep=frag[frag.index('onSpektraPreviewPreparing()'):frag.index('onSpektraPreviewReady()')]
assert 'setSpektraPreviewVisible(true)' in prep and 'setSpektraPreviewVisible(false)' not in prep
assert 'surfaceCreated' in view and 'attachSurface(holder.surface)' in view and 'surfaceDestroyed' in view and 'detachSurface(holder.surface)' in view
# 26687 warmup and owner-isolation regressions.
assert '.warmUp(' not in ctrl and '.warmUp(' not in mode
for x in ('SpektraCameraOwner','SpektraRawCpuOwner','SpektraRawVulkanOwner','SpektraRawDevelop'):
 assert x not in mode and x not in ctrl, f'old owner reachable: {x}'
# Successful 26689 hosted transaction remains unchanged.
assert 'acquireLatestImage()' in sess
assert 'captureStill' in sess and 'resumePreview' in sess
assert ctrl.count('owner.session.captureStill(')==1
assert 'resumePreviewAfterStillLocked' in ctrl
assert 'nativeCaptureRcd' in vr and 'false,\n            true,\n            true,\n            0,' in vr
assert 'pollExposureMeter' in ctrl and 'SpektraExposureController' in ctrl
assert 'DEFAULT_JPEG_QUALITY = 100' in jpeg
assert 'RawPreviewQuality.LOW' in prefs and 'RawPreviewQuality.MEDIUM.name' not in prefs
# No DNG/public-output side effect and no generated-source contamination.
for rel in ('app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt','app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraModeController.java'):
 s=text(rel); assert 'DngCreator' not in s and 'image/x-adobe-dng' not in s
assert not any(str(p.relative_to(c)).startswith('app/build/') or str(p.relative_to(c)).startswith('app/.cxx/') for p in c.rglob('*') if p.is_file())
print('PASS 26690 permanent regressions: exact JNI_OnLoad contract, lazy native startup containment, 26689 compiler, 26688 Surface, 26687 ownership/warmup')
