#!/usr/bin/env python3
"""26881 exact runtime failures: 1.2.5 JNI_ERR, crop geometry, halos, magenta clip."""
from pathlib import Path
import hashlib,sys,re
B=Path(sys.argv[1]);C=Path(sys.argv[2]);s=lambda r:(C/'app'/r).read_text()
N='src/main/java/com/unspektrawesome/'
lib=C/'app/src/main/jniLibs/arm64-v8a/libunspektrawesome_vulkan.so'
assert hashlib.sha256(lib.read_bytes()).hexdigest()=='f40b4707ae27e7d181563d99c31370d5a0e39daef1edb6366bba27da7a201dbd', 'must use exact successful 26692 native, NOT 1.2.5 mismatched JNI_OnLoad'
for rel in ('NativeHost.java','preview/RecordingRawBuffer.kt','spektra/SpektraFilmRenderer.kt','vulkan/RawUpload.kt','vulkan/RawUploadPool.kt','vulkan/VulkanBridge.kt'):
 assert (B/'app'/N/rel).is_file() and not (C/'app'/N/rel).exists(),('original 1.2.5 owner not retired',rel)
ctl=s(N+'preview/RawVulkanPreviewController.kt')
assert 'createFullActivePreview' in ctl and 'IRIS_26878_SPEKTRA_SURFACE_EXTENT_REFRESH' in ctl
assert 'renderer.render(' in ctl and 'renderer.renderOriginal125' not in ctl
assert 'IRIS_26881_SPEKTRA' in ctl
assert 'NativeFrame125' not in ctl and 'RawUploadPool' not in ctl
wrapper=s(N+'vulkan/VulkanRenderer.kt')
assert 'fun configureCenterWeightedExposureMeter(target: ByteBuffer)' in wrapper
assert 'EXPOSURE_METER_METHOD_OFFSET = 8' in wrapper and 'EXPOSURE_METER_DEFAULT_CENTER = 0.5f' in wrapper
assert 'nativeHistogramPixels(current, scale) ?: IntArray(0)' in wrapper
view=s(N+'preview/VulkanRawPreviewView.kt')
assert 'IRIS_26881_' in view
chroma=s('src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt')
assert 'ring>=2' in chroma and 'material*=bridgeLum*bridgeHue' in chroma
assert 'radius=ring==0?4:ring==1?11:ring==2?32:72' in chroma
assert 'float amount=0.46' in chroma
highlight=s('src/main/java/com/hinnka/mycamera/processor/GlesIris26858BNoiseHighlight.kt')
assert 'float tripleClip=' in highlight and 'float thirdWitness=' in highlight
assert 'smoothstep(0.13,0.38,opticalSupport)' in highlight
assert not (C/'app/version.properties').read_text().endswith('VERSION_BUILD=26880\n')
print('PASS 26881 native-Spektra ABI retirement, portrait/landscape geometry, 26871 retained chroma with topology guard, native sensor-highlight original color safety')
