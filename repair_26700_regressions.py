#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3:raise SystemExit('usage: repair_26700_regressions.py BASE26699 CANDIDATE')
b=Path(sys.argv[1]);c=Path(sys.argv[2]);t=lambda r:(c/r).read_text();bt=lambda r:(b/r).read_bytes();ct=lambda r:(c/r).read_bytes()
assert not any((c/'app/build').glob('**/*')) if (c/'app/build').exists() else True
assert not any((c/'app/.cxx').glob('**/*')) if (c/'app/.cxx').exists() else True
# Exact 26699 device runtime failure regression: 4096x3072 direct-half carrier was 100663296,
# while Hdrx required the established RGBA32F carrier >=201326592. Recovery must never emit half.
br=t('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
inp=t('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java')
hdr=t('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java')
assert '100663296' not in br and 'IRIS_26699_MOTION_DIRECT_RGBA16F_HANDOFF' not in br and 'directHalfMotionCarrier' not in br
assert 'convertHalfRgbaToFloatRgba(denoiseBuffer, size.x, size.y)' in br
assert 'GLES30.GL_HALF_FLOAT' not in inp and 'directFloatBytes' in inp and '* 4L * 4L' in inp
assert 'Allocator.free(source);' in inp
assert '26534 Motion RGB carrier too small' in hdr
# The 26699 safe optimizations survive the recovery.
st=t('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/StageTelemetry.java');assert 'IRIS_26699_STAGE_TELEMETRY_REDUNDANT_BARRIER_REMOVED' in st
sa=t('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
for m in ('IRIS_26699_LONG_PROOF_REDUNDANT_BARRIER_REMOVED','IRIS_26699_FUSION_DECISION_BARRIER_REMOVED','IRIS_26699_FUSION_RADIANCE_BARRIER_REMOVED'):assert m in sa,m
# Critical photographic owners not in the explicit 5-file scope remain exact 26699 bytes.
protected=['app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java','app/src/main/java/com/particlesdevs/photoncamera/control/TouchFocus.java','app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraExposureController.java','app/src/main/java/com/unspektrawesome/camera/session/Camera2RawSession.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java','app/src/main/java/com/unspektrawesome/capture/JpegMediaStoreWriter.kt']
for rel in protected:assert bt(rel)==ct(rel),rel
# Spektra watermark is post-render/pre-existing-JPEG-writer only and capture-frozen.
raw=t('app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt');enc=t('app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java')
assert raw.index('renderer.captureRcd(') < raw.index('MotionV2Jpeg444Encoder.applyFinalRasterWatermark(image)') < raw.index('jpegWriter.write(')
assert 'PreferenceKeys.isShowWatermarkOn()' in raw and 'val watermarkEnabled: Boolean' in raw
for tok in ('width * 0.115f','Math.min(width, height) * 0.025f','>= 0.55f','iris_camera_watermark_dark.png','iris_camera_watermark_white.png'):assert tok in enc,tok
# Motion JPEG 4:4:4 path is not replaced or weakened.
for tok in ('IRIS_26565_DISPLAY_P3_JPEG444','writeNative(bitmap,base.toString()','packageJpegRNative(base.toString(),gain.toString()'):assert tok in enc,tok
# All shaders remain exact 26699 bytes.
for pb in (b/'app/src/main/assets/shaders').rglob('*'):
 if pb.is_file(): rel=pb.relative_to(b);assert pb.read_bytes()==(c/rel).read_bytes(),rel
print('PASS 26700 regressions: exact 26699 half-carrier runtime failure prevented; RGBA32F recovery + carrier release retained; Spektra watermark post-render only; inherited UI/performance and Motion JPEG444 preserved')
