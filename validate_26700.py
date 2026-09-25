#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26700.py BASE26699 CANDIDATE')
b=Path(sys.argv[1]);c=Path(sys.argv[2]);pkg=Path(__file__).resolve().parent
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def H(root): return {'app/'+str(p.relative_to(root/'app')):h(p) for p in sorted((root/'app').rglob('*')) if p.is_file()}
def t(rel): return (c/rel).read_text()
B=H(b);C=H(c);exp=[x.strip() for x in (pkg/'26700_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip()]
changed=sorted(k for k in set(B)|set(C) if B.get(k)!=C.get(k))
assert len(B)==len(C)==1823,(len(B),len(C));assert changed==sorted(exp),(changed,exp);assert len(changed)==5
assert not [x for x in (pkg/'26700_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x.strip()]
for name,root in [('26700_BASE_26699_FULL_APP.sha256',b),('26700_EXPECTED_CANDIDATE_FULL_APP.sha256',c)]:
 for line in (pkg/name).read_text().splitlines():
  if line.strip(): hh,rel=line.split(None,1);assert h(root/rel.strip())==hh,(name,rel)
for rel in B:
 if rel not in exp: assert B[rel]==C[rel],rel
SB={k:v for k,v in B.items() if k.startswith('app/src/main/assets/shaders/')};SC={k:v for k,v in C.items() if k.startswith('app/src/main/assets/shaders/')};assert len(SB)==271 and SB==SC
# Capture recovery: successful-26698 RGBA32F bridge restored, 26699 native release retained.
bridge=t('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
assert 'IRIS_26700_MOTION_RGBA32F_CAPTURE_RECOVERY' in bridge
assert 'val output: ByteBuffer = convertHalfRgbaToFloatRgba(denoiseBuffer, size.x, size.y)' in bridge
assert 'IRIS_26699_MOTION_DIRECT_RGBA16F_HANDOFF' not in bridge
assert 'val directHalfMotionCarrier' not in bridge
assert 'MgcFullResolutionDenoise.denoise(' in bridge and 'forceOpaqueHalfAlpha(denoiseBuffer' in bridge
# Critical timeline/EGL barriers remain inherited.
assert 'GLES30.glFinish()\n            gpu.stackCompletionTimeline?.releasePending()' in bridge
assert 'runCatching { GLES30.glFinish() }' in bridge and 'egl?.close()' in bridge
inp=t('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java')
assert 'IRIS_26700_MOTION_RGBA32F_RELEASE_OWNER' in inp
assert 'new GLFormat(GLFormat.DataType.FLOAT_32, 4)' in inp
assert 'Allocator.free(source);' in inp and 'pipeline.motionV2FloatCfa = null;' in inp
assert 'GLES30.GL_HALF_FLOAT' not in inp and 'IRIS_26699_MOTION_DIRECT_RGBA16F_UPLOAD' not in inp
assert 'directFloatBytes' in inp and '* 4L * 4L' in inp
# Exact 26699 runtime failure guard remains strict and now agrees with the restored carrier.
hdr=t('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java')
assert '26534 Motion RGB carrier too small' in hdr
assert (b/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_bytes()==(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_bytes()
# Inherited 26699 performance/UI behavior remains present outside the 5-file delta.
stage=t('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/StageTelemetry.java');run=stage[stage.index('public void Run()'):]
assert 'IRIS_26699_STAGE_TELEMETRY_REDUNDANT_BARRIER_REMOVED' in run and 'glFinish()' not in run
sabre=t('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
for marker in ('IRIS_26699_LONG_PROOF_REDUNDANT_BARRIER_REMOVED','IRIS_26699_FUSION_DECISION_BARRIER_REMOVED','IRIS_26699_FUSION_RADIANCE_BARRIER_REMOVED','IRIS_26699_HDR_PROBE_BARRIER_REMOVED stage=FLOAT_HDR_HANDOFF_PRE_VGN','IRIS_26699_HDR_PROBE_BARRIER_REMOVED stage=POST_VGN_HDR_MASTER'): assert marker in sabre,marker
sw=t('app/src/main/java/com/particlesdevs/photoncamera/control/Swipe.java');assert 'IRIS_26699_VIDEO_BOTTOM_TOUCH_FOCUS_EXCLUSION' in sw
ui=t('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java');assert 'iris26699VideoRecordingTicker' in ui
grid=t('app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/SurfaceViewOverViewfinder.java');assert 'whitePaint.setAlpha(153)' in grid and 'whitePaint.setStrokeWidth(1.0f)' in grid
# Spektra watermark parity reuses Motion's exact final-raster contract.
enc=t('app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java')
raw=t('app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt')
for token in ('IRIS_26700_SPEKTRA_MOTION_WATERMARK_PARITY','width * 0.115f','Math.min(width, height) * 0.025f','>= 0.55f','0.2126f * r + 0.7152f * g + 0.0722f * b','iris_camera_watermark_dark.png','iris_camera_watermark_white.png','Paint.FILTER_BITMAP_FLAG'):
 assert token in enc,token
for token in ('PreferenceKeys.isShowWatermarkOn()','MotionV2Jpeg444Encoder.applyFinalRasterWatermark(image)','val watermarkEnabled: Boolean','IRIS_26700_SPEKTRA_WATERMARK_PARITY'):
 assert token in raw,token
shader=t('app/src/main/assets/shaders/addwatermark_rotate.glsl')
for token in ('* 0.115','* 0.025','>= 0.55','vec3(0.2126, 0.7152, 0.0722)'): assert token in shader,token
# Existing Motion JPEG-R / JPEG444 owner remains intact; helper is additive only.
for token in ('IRIS_26699_JPEGR_STAGE_TIMING','IRIS_26565_DISPLAY_P3_JPEG444','writeNative(bitmap,base.toString()','packageJpegRNative(base.toString(),gain.toString()'):
 assert token in enc,token
ver=t('app/version.properties');assert 'VERSION_NAME=0.9726700' in ver and 'VERSION_BUILD=26700' in ver
print('PASS validate 26700: exact 5-file capture-recovery/Spektra-watermark scope; 1818 protected; proven RGBA32F transport + carrier release + Motion-parity watermark; 271 shaders invariant')
