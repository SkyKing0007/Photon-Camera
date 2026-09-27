#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26721_regressions.py BASE26720R2 CAND26721')
b,c=map(Path,sys.argv[1:]); pkg=Path(__file__).resolve().parent
def H(r): return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
def txt(r,p): return (r/p).read_text()
def section(s,start,end):
 i=s.index(start); j=s.index(end,i+len(start)); return s[i:j]
B,C=H(b),H(c); assert len(B)==len(C)==1823
expected=set((pkg/'26721_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()); assert expected=={
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/version.properties'}
assert {k for k in B|C if B.get(k)!=C.get(k)}==expected
v=txt(c,'app/version.properties'); assert 'VERSION_NAME=0.9726721' in v and 'VERSION_BUILD=26721' in v
# 26720 R2 architecture outside the transport boundary is frozen byte-for-byte.
for rel in [
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/RawStackFrameCompat.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLFormat.java',
'app/src/main/assets/shaders/motionv2/color_transform.glsl',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/IrisSabreSuperResDngWriter.java']:
 assert (b/rel).read_bytes()==(c/rel).read_bytes(),rel
# Preserve 26720 banding, high-zoom activation, geometry, fallback, and final owner unchanged.
cap=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
for t in ['IRIS_26720_CAPTURE_ROW_FLICKER_EVIDENCE','IRIS_26720_LEAST_FLICKERED_STRUCTURAL_REFERENCE','rawRewritten=false confidenceOnly=true','shortLongUntouched=true highlightRecoveryUntouched=true dngUntouched=true']:
 assert t in cap,t
bridge=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
for t in ['!sabreSuperResEnabled && displayedGlobalZoom >= 20f && localOutputZoom > 1.00001f','parameters.motionV2HighZoomRgbPrepared = true','parameters.motionV2ReconstructionZoom = localOutputZoom','parameters.motionV2RenderResidualZoom = 1f','IRIS_26720_HIGH_ZOOM_RGB_FALLBACK_HANDOFF']:
 assert t in bridge,t
# Permanent failed-26720 compiler regressions remain enforced.
stack=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
assert 'val failure = checkNotNull(rgbAttempt.exceptionOrNull())' in stack
assert 'reason=${failure?.message}", failure)' not in stack
color=txt(c,'app/src/main/assets/shaders/motionv2/color_transform.glsl')
macro_define='#define USE_IRIS_26720_HIGH_ZOOM_RGB 0'; macro_use='#if USE_IRIS_26720_HIGH_ZOOM_RGB == 1'
assert color.count(macro_define)==1 and color.count(macro_use)==2 and color.index(macro_define)<color.index(macro_use)
# 26721 black-image regression: only >=20x sidecar transport moves to RGB32F.
assert 'private const val HIGH_ZOOM_RGB32F_BYTES_PER_PIXEL = 3 * Float.SIZE_BYTES' in stack
assert 'IRIS_26721_HIGH_ZOOM_RGB32F_TRANSFER_OWNER' in stack
writer=section(stack,'/* IRIS_26721_HIGH_ZOOM_RGB32F_TRANSFER_OWNER','    private fun writeTrue2xGpuRgbTile(')
for t in ['GLES30.GL_RGBA, GLES30.GL_FLOAT, rgba','4 * Float.SIZE_BYTES','HIGH_ZOOM_RGB32F_BYTES_PER_PIXEL','asFloatBuffer()','require(r.isFinite() && g.isFinite() && b.isFinite())']:
 assert t in writer,t
assert 'GLES30.GL_HALF_FLOAT' not in writer and 'TRUE2X_RGB16F_BYTES_PER_PIXEL' not in writer
runhz=section(stack,'    private fun runHighZoomRgbGpu26720(','    private fun reconstructHighZoomRgb26720(')
assert 'writeHighZoomRgb32fTile26721(' in runhz and 'out.setLength(outputWidth.toLong() * outputHeight * HIGH_ZOOM_RGB32F_BYTES_PER_PIXEL)' in runhz
assert 'writeTrue2xGpuRgbTile(out,render' not in runhz
recon=section(stack,'    private fun reconstructHighZoomRgb26720(','    private fun runHighZoomDetailGpu26718(')
for t in ['.rgb32f','HIGH_ZOOM_RGB32F_BYTES_PER_PIXEL','validateHighZoomRgb32f26721','IRIS_26721_HIGH_ZOOM_RGB32F_CARRIER','float16Transfer=false','scalar26719FallbackOnFailure=true']:
 assert t in recon,t
assert '.rgb16f' not in recon and 'TRUE2X_RGB16F_BYTES_PER_PIXEL' not in recon
validator=section(stack,'    private fun validateHighZoomRgb32f26721(','    private fun writeTrue2xGpuRgbTile(')
for t in ['value.isFinite()','positiveSamples > 0L && maxSignal > 0f','26721 RGB32F carrier has no positive image energy']:
 assert t in validator,t
# Inherited explicit true-2x/SR RGB16F publication remains exact to successful 26720 R2.
base_stack=txt(b,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
for start,end in [
('    private fun writeTrue2xGpuRgbTile(','    private fun streamTrue2xNativeVgnGuideRgb16f('),
('    private fun streamTrue2xNativeVgnGuideRgb16f(','    private fun updateTrue2xPhaseHistogram(')]:
 assert section(base_stack,start,end)==section(stack,start,end),start
assert 'private const val TRUE2X_RGB16F_BYTES_PER_PIXEL = 3 * Short.SIZE_BYTES' in stack
# Loader matches the proven FLOAT32 cross-context contract; packed half bytes are impossible here.
ct=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java')
load=section(ct,'    private GLTexture loadHighZoomRgb26720() {','    @Override\n    public void Run() {')
for t in ['IRIS_26721_HIGH_ZOOM_RGB32F_TEXTURE_TRANSFER','3L*Float.BYTES','GLFormat.DataType.FLOAT_32,3','transfer=RGB32F bytesPerChannel=4 float16Transfer=false']:
 assert t in ct,t
assert 'GLFormat.DataType.FLOAT_16,3' not in load and '*3L*2L' not in load
# Proven primary Motion transport remains RGBA32F / FLOAT32 and is not edited.
cfa=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java')
for t in ['new GLFormat(GLFormat.DataType.FLOAT_32, 4)','transferFormat=rgba32f','bytesPerChannel=4','float16Transfer=false']:
 assert t in cfa,t
glf=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLFormat.java')
assert 'case FLOAT_16:' in glf and 'case FLOAT_32:' in glf and 'return GL_FLOAT;' in glf and 'return GL_RGB32F;' in glf
contracts=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt')
assert 'IRIS_26721_HIGH_ZOOM_RGB32F_TRANSPORT_CONTRACT' in contracts and 'camera-linear RGB32F centered ROI' in contracts
# Native/vendor/DNG remain invariant.
def loadm(n):
 d={}
 for l in (pkg/n).read_text().splitlines():
  if l.strip(): h,p=l.split(None,1); d[p.strip()]=h
 return d
for stem,count in [('NATIVE_FULL',820),('VENDOR_PROTECTED',1),('DNG',6)]:
 x=loadm(f'26721_{stem}_BASE.sha256'); y=loadm(f'26721_{stem}_CANDIDATE.sha256'); assert len(x)==len(y)==count and x==y
print('PASS 26721 regressions/ownership: successful 26720 R2 behavior preserved; >=20x compact carrier alone restored to proven FLOAT32/RGB32F transport with finite/positive-energy gate and 26719 scalar fallback; prior GLSL/Kotlin failures permanently guarded')
