#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26689_regressions.py BASE CANDIDATE')
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
# 26688 failure: Surface must exist before first presented frame; PREPARING must not hide it.
prep=frag[frag.index('onSpektraPreviewPreparing()'):frag.index('onSpektraPreviewReady()')]
assert 'setSpektraPreviewVisible(true)' in prep and 'setSpektraPreviewVisible(false)' not in prep
assert 'surfaceCreated' in view and 'attachSurface(holder.surface)' in view and 'surfaceDestroyed' in view and 'detachSurface(holder.surface)' in view
# 26687 failure: no Iris-created warmup gate may block camera opening.
assert '.warmUp(' not in ctrl and '.warmUp(' not in mode
# Old recreated owners may remain protected bytes but cannot be reachable from sole facade/controller.
for x in ('SpektraCameraOwner','SpektraRawCpuOwner','SpektraRawVulkanOwner','SpektraRawDevelop'):
 assert x not in mode and x not in ctrl, f'old owner reachable: {x}'
# Standalone transaction: newest preview only, exactly one full-res still request, then resume preview.
assert 'acquireLatestImage()' in sess
assert 'captureStill' in sess and 'resumePreview' in sess
assert ctrl.count('owner.session.captureStill(')==1
assert 'resumePreviewAfterStillLocked' in ctrl
# Exact 1.1.2 native/processing behavior.
assert 'nativeCaptureRcd' in vr and 'false,\n            true,\n            true,\n            0,' in vr
assert 'pollExposureMeter' in ctrl and 'SpektraExposureController' in ctrl
assert 'DEFAULT_JPEG_QUALITY = 100' in jpeg
assert 'RawPreviewQuality.LOW' in prefs and 'RawPreviewQuality.MEDIUM.name' not in prefs
# Iris legacy owner isolation stays enforced by unchanged CaptureController guards plus new facade.
cap=text('app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
assert 'spektraModeController' in cap
# No public DNG side effect added by 26689.
for rel in ('app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt','app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraModeController.java'):
 s=text(rel); assert 'DngCreator' not in s and 'image/x-adobe-dng' not in s
# Historical source contamination rules.
assert not any(str(p.relative_to(c)).startswith('app/build/') or str(p.relative_to(c)).startswith('app/.cxx/') for p in c.rglob('*') if p.is_file())
print('PASS 26689 permanent regressions: 26687 warmup, 26688 Surface gate, owner isolation, one-RAW capture, exact 1.1.2 defaults')
