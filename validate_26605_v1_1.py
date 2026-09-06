#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
PKG=Path(__file__).resolve().parent
CHANGED=[x for x in (PKG/'V1_1_26605_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
def fail(m):raise SystemExit('FAIL: '+m)
def H(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def allh(r):return {str(p.relative_to(r)):H(p) for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
def need(s,t,l):
 if t not in s:fail(l+' missing '+t)
def forbid(s,t,l):
 if t in s:fail(l+' stale '+t)
def section(s,a,b):
 i=s.find(a);j=s.find(b,i)
 if i<0 or j<0:fail('section '+a)
 return s[i:j]
def main():
 if len(sys.argv)!=3:fail('usage base candidate')
 b,c=map(Path,sys.argv[1:]);bh,ch=allh(b),allh(c);diff=sorted(k for k in bh if bh[k]!=ch.get(k))
 if diff!=sorted(CHANGED):fail('runtime diff allowlist '+repr(diff))
 if set(bh)!=set(ch) or len(bh)!=1708:fail('full app universe changed')
 v=(c/'app/version.properties').read_text();need(v,'VERSION_NAME=0.9726605','version');need(v,'VERSION_BUILD=26605','version')
 untouched=['app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java','app/src/main/assets/shaders/motionv2/display_exposure.glsl','app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl','app/src/main/assets/shaders/motionv2/iris_tone_controls.glsl','app/src/main/cpp/motionv2_jpeg444_jni.cpp','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java']
 for r in untouched:
  if (b/r).read_bytes()!=(c/r).read_bytes():fail('successful-26604 untouched owner changed '+r)
 sh=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
 rej=section(sh,'    val rejection = """','    """.trimIndent()')
 need(rej,'float localFlowVariation = flow.z;','normalized flow.z owner')
 need(rej,'smoothstep(0.50,2.00,max(flow.w,0.0))','RAW-pixel confidence flow.w')
 forbid(rej,'smoothstep(0.50,2.00,localFlowVariation)','wrong flow component')
 need(sh,'oFlow = vec4(uvFlow, localFlowVariation, localFlowVariationRawPixels);','flow converter domains')
 uint16=section(sh,'    val outputTransformUint16 = """','    """.trimIndent()')
 flt=section(sh,'    val outputTransformFloat = """','    """.trimIndent()')
 need(uint16,'clamp(transformOutput(p), 0.0, 1.0)','normalized VGN proxy clamp');forbid(flt,'clamp(transformOutput(p)','physical HDR float clamp')
 for t in ['IRIS_26605_EXTENDED_HDR_POST_VGN_RESTORE','vec3 normalizedProxy = clamp(physical, 0.0, 1.0);','vec3 restored = physical + (vgn - normalizedProxy);']:need(sh,t,'post-VGN HDR restore')
 st=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text();active=section(st,'private fun processSabreFrames','private data class SabreNormalDngSupportStats')
 for t in ['private val preserveExtendedHdrThroughVgn: Boolean = false','preserveExtendedHdrThroughVgn','sabreOutputTransformFloatProgram','sabreExtendedHdrRestoreProgram','FLOAT_HDR_HANDOFF_PRE_VGN','POST_VGN_HDR_MASTER','IRIS_26605_SHORT_FLOW_W_STATS','component=flow.w domain=RAW_PIXELS','activeConfidenceConsumer=true','val nativeHdrAuthority26601 = exportedTexture','reconstructTrue2x(']:need(st,t,'stacker HDR/flow ownership')
 need(active,'if (enableSabreSuperRes && frame.role == RawBurstFrameRole.NORMAL)','SR detail NORMAL-only')
 need(active,'if (normalDngAccumulator != 0 && frame.role == RawBurstFrameRole.NORMAL)','DNG NORMAL-only')
 proc=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt').read_text()
 need(proc,'preserveExtendedHdrThroughVgn = !allowShadowLong &&','normal Motion only HDR preservation');need(proc,'exportGpuLinearRgbSource && gpuLinearRgbStorage == GpuLinearRgbStorage.RGBA16F','RGBA16F gate')
 br=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
 if 'MotionTrace.processingState(' in br:fail("exact failed-26605 Kotlin unresolved MotionTrace call survived")
 need(br,'PLog.i("MotionTrace", "PIPELINE_STATE stage=IRIS_26605_AUX_PHYSICAL_METADATA details=$details")','26605 V1.1 proven MotionTrace PLog telemetry')
 for t in ['allowSabreShadowLong = parameters.irisNightActive','CAPTURED_BUT_EXCLUDED_FROM_NORMAL_MOTION_SABRE','COMMON_SABRE_NIGHT_SHADOW_EVIDENCE','IRIS_26605_AUX_PHYSICAL_METADATA']:need(br,t,'LONG/aux ownership')
 # Normal Motion merged count remains NORMAL + Night-only shadow LONG; captured normal LONG is not silently counted.
 need(br,'parameters.irisNightActive','Night LONG gating')
 # No stale bodyGain authority anywhere in runtime source.
 for p in (c/'app/src/main').rglob('*'):
  if p.is_file():
   try:s=p.read_text()
   except UnicodeDecodeError:continue
   if 'bodyGainUnity' in s:fail('stale bodyGainUnity '+str(p.relative_to(c)))
 for r in ['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java','app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java']:
  s=(c/r).read_text();need(s,'HDR_MASTER' if r.endswith('MotionV2Render.java') else ('POST_VGN_EXTENDED_LINEAR' if not r.endswith('MotionV2UltraHdr.java') else 'HEALTHY_HDR_MASTER_VS_SDR'),'healthy HDR ownership telemetry')
 print('PASS exact 9-file runtime scope from successful-26604 authority; version 0.9726605/26605; untouched tone/capture/DNG/SR publication owners invariant')
 print('PASS physical HDR float carrier survives pre-VGN; normalized uint16 VGN proxy clamp retained; one post-VGN extended-linear master restored; Night isolated')
 print('PASS active raw-pixel SHORT gate consumes flow.w while normalized flow.z remains; normal Motion LONG truthfully excluded; SR guide uses corrected master and SR detail/DNG stay NORMAL-only')
 print('PASS stale bodyGainUnity telemetry absent from app/src/main')
if __name__=='__main__':main()
