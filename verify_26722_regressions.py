#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26722_regressions.py BASE26721 CAND26722')
b,c=map(Path,sys.argv[1:]); pkg=Path(__file__).resolve().parent
def H(r): return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
def txt(r,p): return (r/p).read_text()
def section(s,start,end):
 i=s.index(start); j=s.index(end,i+len(start)); return s[i:j]
B,C=H(b),H(c); assert len(B)==len(C)==1823
expected=set((pkg/'26722_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()); assert expected=={
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/version.properties'}
assert {k for k in B|C if B.get(k)!=C.get(k)}==expected
v=txt(c,'app/version.properties'); assert 'VERSION_NAME=0.9726722' in v and 'VERSION_BUILD=26722' in v
# Successful 26721 architecture outside the narrow high-zoom chroma ownership boundary is frozen.
for rel in [
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java',
'app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt',
'app/src/main/java/com/hinnka/mycamera/processor/RawStackFrameCompat.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
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
# 26720 banding, high-zoom activation/geometry/fallback, explicit SR separation and final handoff remain unchanged.
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
# Successful 26721 RGB32F transport is preserved exactly; only chroma ownership changes.
base_stack=txt(b,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
for start,end in [
('    /* IRIS_26721_HIGH_ZOOM_RGB32F_TRANSFER_OWNER','    private fun writeTrue2xGpuRgbTile('),
('    private fun validateHighZoomRgb32f26721(','    private fun writeTrue2xGpuRgbTile('),
('    private fun reconstructHighZoomRgb26720(','    private fun runHighZoomDetailGpu26718(')]:
 # reconstruct includes only telemetry-neutral producer logic in 26722; it must remain byte-identical.
 if start.startswith('    private fun reconstructHighZoomRgb26720'):
  assert section(base_stack,start,end)==section(stack,start,end),start
 else:
  assert section(base_stack,start,end)==section(stack,start,end),start
assert 'private const val HIGH_ZOOM_RGB32F_BYTES_PER_PIXEL = 3 * Float.SIZE_BYTES' in stack
assert 'IRIS_26721_HIGH_ZOOM_RGB32F_TRANSFER_OWNER' in stack
ct=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java')
for t in ['IRIS_26721_HIGH_ZOOM_RGB32F_TEXTURE_TRANSFER','3L*Float.BYTES','GLFormat.DataType.FLOAT_32,3','transfer=RGB32F bytesPerChannel=4 float16Transfer=false']:
 assert t in ct,t
# 26722: high-zoom direct-CFA chroma authority is removed, but direct-CFA luma/detail remains.
sh=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
prop=section(sh,'    /* IRIS_26722_HIGH_ZOOM_NATIVE_SABRE_VGN_CHROMA_AUTHORITY','    /* IRIS_26719_HIGH_ZOOM_LAZY_ISOLATION')
for t in ['val highZoomRgbProtect26720: String by lazy {','true2xGuideRender26568','direct CFA may select the correct material side through luminance','never contributes independent R/G/B chroma','Real color already present in the native']:
 assert t in prop,t
for t in ['directChromaConfidence','vec3 directChroma =','chromaDelta','protectedChroma','maxChromaDelta']:
 assert t not in prop,t
# The reused 26568 shader must retain its material-aware native chroma protections and direct-CFA luma owner.
guide=section(sh,'    val true2xGuideRender26568 = """','    /* IRIS_26720_HIGH_ZOOM_DIRECT_CFA_RGB_OWNER')
for t in ['IRIS_26579_TRUE2X_TOPOLOGY_CHROMA_UPSAMPLE','IRIS_26580_TRUE2X_SAME_MATERIAL_CHROMA_OWNERSHIP','IRIS_26581_DECISIVE_CROSS_EDGE_CHROMA_VETO','localChromaOccupancy','localColorProtection','anchorChroma','selectedChroma','float directDetail','float factor = guideY > 1.0e-5 ? clamp(targetY / guideY, 0.68, 1.47) : 1.0','oRenderRgb = vec4(max(guideRgb * factor, vec3(0.0))']:
 assert t in guide,t
assert sh.count('val highZoomRgbProtect26720: String by lazy {')==1
assert stack.count('GlesMgcRawSabreShaders.highZoomRgbProtect26720')==1
runhz=section(stack,'    private fun runHighZoomRgbGpu26720(','    private fun reconstructHighZoomRgb26720(')
for t in ['GlesMgcRawSabreShaders.highZoomRgbProtect26720','bindTexture(program,"uDirectRgb",0,resolved)','bindTexture(program,"uNativeVgnGuide",2,nativeVgnGuideTexture)','writeHighZoomRgb32fTile26721(']:
 assert t in runhz,t
# Telemetry must prove the new owner contract without claiming direct high-res color.
for t in ['strongDetailPct=${hz.fullColorPct}','lumaDetailOwner=DIRECT_CFA_TEMPORAL nativeSabreVgnChromaOwner=true directChromaOwner=false','sameMaterialTopology=true realGuideColorPreserved=true']:
 assert t in stack,t
assert 'rgbOwner=DIRECT_CFA_WITH_NATIVE_SABRE_VGN_LOCAL_FALLBACK' not in runhz
# Explicit SR/true-2x and <20x remain independent.
assert 'enableHighZoomDetail && !enableSabreSuperRes' in stack
contracts=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt')
assert 'IRIS_26721_HIGH_ZOOM_RGB32F_TRANSPORT_CONTRACT' in contracts
# Native/vendor/DNG remain invariant.
def loadm(n):
 d={}
 for l in (pkg/n).read_text().splitlines():
  if l.strip(): h,p=l.split(None,1); d[p.strip()]=h
 return d
for stem,count in [('NATIVE_FULL',820),('VENDOR_PROTECTED',1),('DNG',6)]:
 x=loadm(f'26722_{stem}_BASE.sha256'); y=loadm(f'26722_{stem}_CANDIDATE.sha256'); assert len(x)==len(y)==count and x==y
print('PASS 26722 regressions/ownership: exact successful 26721 base; RGB32F transport, Wronski/Sabre, banding, SHORT/highlight, tone/color/UHDR/DNG and <20x/explicit-SR isolation preserved; >=20x direct CFA is luma/detail-only while material-aware native Sabre/VGN chroma preserves real color and forbids independent direct-CFA chroma bleed')
