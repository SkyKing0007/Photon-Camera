#!/usr/bin/env python3
"""Exact real successful 26879 -> 26880 changed runtime source and original 1.2.5 ABI.
This is an applicable source regression, not a substitute for compilers or a device.
"""
from pathlib import Path
import sys,hashlib
B=Path(sys.argv[1]);C=Path(sys.argv[2]);A=C/'app'
prefix='app/src/main/java/com/unspektrawesome/'
preview=(C/(prefix+'preview/RawVulkanPreviewController.kt')).read_text()
renderer=(C/(prefix+'vulkan/VulkanRenderer.kt')).read_text()
mode=(C/'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraModeController.java').read_text()
assert 'renderer.renderOriginal125(' in preview and 'renderer.render(' not in preview
assert 'original125Uploads().copy(' in preview and 'upload?.close()' in preview
assert 'original125Cadence.reset()' in preview and 'class Original125Cadence' in preview
assert 'renderer.captureRcd(' in preview and 'jpegWriter.write(' in preview
assert 'RawPreviewQuality.FULL' in mode and 'android.os.Process.is64Bit()' in mode
assert 'fun render(' not in renderer and renderer.count('private external fun nativeRender(')==1
assert 'nativeRawUploads(current)' in renderer and 'nativeWarmUp(current, preview, step, part)' in renderer
assert 'nativeWarmupStepCount(preview)' in renderer
assert 'originalTimeNs = frame.metadata.sensorTimestampNs' in preview
assert 'originalBoundedCount = receipt.count' in preview
assert 'previewSpektraParameters(state.state)' in preview
# Actual Surface presentation, NOT successful nativeRender submission or Camera2 STREAMING.
assert 'renderer.presentedFrames125()' in preview
assert 'nativePresented > presentedFramesBaseline125' in preview
assert 'if (!firstFramePresented && confirmedPresentation)' in preview
assert 'firstFramePresented = true' in preview
assert 'RAW stream active; waiting for a Vulkan-presented frame' in preview
assert 'fun presentedFrames125(): Long' in renderer
assert 'nativePresentedFrames(current)' in renderer
assert 'SpektraFilmParams.exact125Default()' in (C/(prefix+'spektra/SpektraState.kt')).read_text()
# Both SR ON/OFF shaders remain active. ON must never gate continuous
# interpolation with the hard current CFA-cell min that made 2x2 neon blocks.
shader=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26858BNoiseHighlight.kt').read_text()
assert 'val bHighlightRecover = ' in shader and 'val bNativeSensorSmoothWhite26866 = ' in shader
assert 'float cross=mix(mix(independentlyClipped(q),' in shader
assert 'vec3 phaseColorClipAt(ivec2 cell)' in shader
assert 'vec3 colorClip=mix(' in shader
assert 'float inwardCross=min(colorClip.g,max(colorClip.r,colorClip.b));' in shader
assert 'float opticalSupport=min(clippedCoverage,max(inwardCross,greenOnly));' in shader
assert 'float inwardCross=min(centerCross,bilinearCross);' not in shader
assert 'oRgb=vec4(mix(original.rgb,vec3(neutral),fade),original.a);' in shader
# A GL publication log cannot claim a native burst fit succeeded: Wronski
# fallback explicitly allows a missing fit and skips the optional wavelet.
stacker=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
assert 'burstNoiseFitted=unreportedAtGlPublication' in stacker
assert 'burstNoiseFitted=true' not in stacker
assert hashlib.sha256((A/'src/main/jniLibs/arm64-v8a/libunspektrawesome_vulkan.so').read_bytes()).hexdigest()=='e07838d8aa06c08038189454160293a37446a44fac998186755e93fde6e59fd1'
assert (B/'app/src/main/jniLibs/arm64-v8a/libunspektrawesome_vulkan.so').read_bytes()!= (A/'src/main/jniLibs/arm64-v8a/libunspektrawesome_vulkan.so').read_bytes()
print('PASS 26880 B and exact 1.2.5 original Camera2/Vulkan/RAW/JPEG source ownership')
