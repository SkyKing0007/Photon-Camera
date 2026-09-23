#!/usr/bin/env python3
from pathlib import Path
import re,sys
if len(sys.argv)!=3: raise SystemExit('usage: repair_26692_regressions.py BASE CANDIDATE')
base=Path(sys.argv[1]); c=Path(sys.argv[2])
def t(r): return (c/r).read_text()
plan=t('app/src/main/java/com/unspektrawesome/preview/RawPreviewPlanSelector.kt'); policy=t('app/src/main/java/com/unspektrawesome/camera/RawPreviewPolicy.java'); sess=t('app/src/main/java/com/unspektrawesome/camera/session/Camera2RawSession.java'); pack=t('app/src/main/java/com/unspektrawesome/camera/session/PackedRawPlaneBuffer.java'); ctrl=t('app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt'); hist=t('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/SpektraLiveHistogramView.java'); frag=t('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java'); ui=t('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java'); layout=t('app/src/main/res/layout/camera_fragment.xml')
# 26692 R1 Kotlin compiler regression: modified selector must explicitly import RawFormat.
assert plan.count('import com.unspektrawesome.camera.RawFormat')==1
assert 'candidateFormats: Set<RawFormat>' in plan
# 26692 exact runtime failure: RAW_SENSOR must never depend exclusively on Vulkan AHB import.
assert 'HardwareBuffer.USAGE_GPU_SAMPLED_IMAGE' not in sess
assert sess.count('PackedRawPlaneBuffer.prepare(')==2
assert 'case RAW_SENSOR:' in pack and 'width * 2L' in pack
assert 'hardwareBufferImport=false' in sess
# Exact APK route preference: RAW10 -> RAW12 -> RAW_SENSOR, both preview and full-res still.
assert 'rawSensorOutputs' not in plan
assert 'new RawFormat[]{RawFormat.RAW10, RawFormat.RAW12, RawFormat.RAW_SENSOR}' in policy
# 26691 LSC regression remains: preview LSC absent cannot block shutter; still LSC preferred.
assert 'requireNotNull(latestLensShadingMap)' not in ctrl
assert re.search(r'val\s+captureLensShading\s*=\s*stillLensShading\s*\?:\s*request\.lensShadingMap',ctrl)
# 26692 histogram regression: never render native sample pixels as mini viewfinder, never show toggle.
assert 'drawBitmap' not in hist and 'Bitmap.createBitmap' not in hist and 'BINS = 64' in hist
assert 'spektra_histogram_toggle' not in layout and 'spektraHistogramToggle' not in frag
iris='app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/IrisLiveHistogramView.java'; assert (c/iris).read_bytes()==(base/iris).read_bytes()
# Video/RAW Video may differ visually as record controls, never geometrically.
for bad in ('88.0f * density','74.0f * density','-48.0f * density','-30.0f * density'): assert bad not in ui
assert 'R.drawable.video_record_button' in ui
# Exact Unspektra AE owner remains byte-identical; no Android-AE substitution.
ae='app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraExposureController.java'; assert (c/ae).read_bytes()==(base/ae).read_bytes(); assert 'SpektraExposureController' in ctrl and 'pollExposureMeter' in ctrl
# Native 1.1.2 owner remains unchanged and existing startup/compiler regressions remain.
mode=t('app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraModeController.java'); view=t('app/src/main/java/com/unspektrawesome/preview/VulkanRawPreviewView.kt'); vr=t('app/src/main/java/com/unspektrawesome/vulkan/VulkanRenderer.kt'); log=t('app/src/main/java/com/unspektrawesome/diagnostics/InternalLogRecorder.java')
so=(c/'app/src/main/jniLibs/arm64-v8a/libunspektrawesome_vulkan.so').read_bytes(); assert b'com/unspektrawesome/diagnostics/InternalLogRecorder' in so and b'Java_com_unspektrawesome_vulkan_VulkanRenderer_nativeCaptureRcd' in so
assert 'package com.unspektrawesome.diagnostics;' in log
ctor=mode[mode.index('public SpektraModeController('):mode.index('public synchronized void bindPreviewSurface')]; assert 'new RawVulkanPreviewController' not in ctor
assert mode.count('new RawVulkanPreviewController')==1
assert 'surfaceCreated' in view and 'surfaceDestroyed' in view
assert '.warmUp(' not in ctrl and '.warmUp(' not in mode
for old in ('SpektraCameraOwner','SpektraRawCpuOwner','SpektraRawVulkanOwner','SpektraRawDevelop'): assert old not in mode and old not in ctrl
assert 'nativeCaptureRcd' in vr
print('PASS 26692 permanent regressions: RAW carrier/import, route preference, LSC, histogram, Video geometry, Unspektra AE, JNI/startup/Surface ownership')
