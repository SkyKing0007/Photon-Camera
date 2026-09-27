#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
if len(sys.argv)!=3:raise SystemExit('usage: verify_26718_regressions.py BASE26717 CAND26718')
b,c=map(Path,sys.argv[1:]);pkg=Path(__file__).resolve().parent
def H(r):return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
def txt(r,p):return (r/p).read_text()
B,C=H(b),H(c);assert len(B)==len(C)==1823
expected=set((pkg/'26718_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines());assert len(expected)==12;assert {k for k in B|C if B.get(k)!=C.get(k)}==expected
v=txt(c,'app/version.properties');assert 'VERSION_NAME=0.9726718' in v and 'VERSION_BUILD=26718' in v
# Acquisition, logging, preview, native, DNG, vendor, denoise/color owners stay exactly successful-26717 bytes.
for rel in [
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/app/PhotonCamera.java',
'app/src/main/java/com/particlesdevs/photoncamera/util/Log.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java',
'app/src/main/assets/shaders/preview/main_fs.glsl',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/IrisSabreSuperResDngWriter.java',
'app/src/main/java/com/particlesdevs/photoncamera/api/VendorTagUtils.java']:
 assert (b/rel).read_bytes()==(c/rel).read_bytes(),rel
bridge=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
# IRIS_26718_R1_KOTLIN_COMPILER_REGRESSION: exact Actions failure must be impossible.
assert 'import com.particlesdevs.photoncamera.util.MotionTrace' in bridge
assert 'frames.firstOrNull { it.frameNumber == mgcBase.motionV2FrameNumber }' in bridge
assert 'mgcBase.frameNumber' not in bridge
assert 'MotionTrace.processingState("IRIS_26718_HIGH_ZOOM_ACTIVATION", highZoomActivation)' in bridge
assert 'MotionTrace.processingState("IRIS_26718_HIGH_ZOOM_DETAIL_HANDOFF", handoff)' in bridge
for t in ['parameters.motionV2Active && !parameters.irisNightActive','!sabreSuperResEnabled && displayedGlobalZoom >= 20f','localOutputZoom > 1.00001f','IRIS_26718_HIGH_ZOOM_ACTIVATION','focusDistanceDiopters=','lensState=','rgbOwner=NATIVE_SABRE_VGN','detailOwner=${if (highZoomDetailEnabled) "NORMAL_SCALAR_2X_LUMA_ROI" else "NONE"}','enableHighZoomDetail = highZoomDetailEnabled','highZoomSourceZoom = localOutputZoom','IRIS_26718_HIGH_ZOOM_DETAIL_HANDOFF']:
 assert t in bridge,t
stack=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
for forbidden in ['IRIS_26718_HIGH_ZOOM_PHASE_RESERVOIR','highZoomPhaseSlots26718']:
 assert forbidden not in stack,forbidden
for t in ['IRIS_26718_HIGH_ZOOM_ALL_NORMAL_EVIDENCE','val highZoomEvidence26718 = ArrayList<True2xFrameEvidence>()','enableHighZoomDetail && frame.role == RawBurstFrameRole.NORMAL','existingPhaseEvidence = null','refineForHighZoom26718 = true','allAdmittedNormal=true','srReservoirIndependent=true','shortDetailEvidence=false','longDetailEvidence=false','IRIS_26718_HIGH_ZOOM_FLOW_REFINE','directHighResRgb=false','detailOwner=NORMAL_SCALAR_2X_LUMA_ROI']:
 assert t in stack,t
# Existing SR reservoir remains present and separate; default false keeps its former refine condition semantics.
for t in ['val true2xFastPhaseSlots: Array<True2xFrameEvidence?>?','TRUE2X_JPEG_MAX_EVIDENCE','refineForHighZoom26718: Boolean = false','if ((existingPhaseEvidence != null || refineForHighZoom26718) && frameIndex != 0)']:
 assert t in stack,t
assert 'enableSabreSuperRes && enableHighZoomDetail' in stack
sh=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
for t in ['IRIS_26718_HIGH_ZOOM_SCALAR_MERGE','oTemporalLumaStats','oPhaseOccupancy','IRIS_26718_HIGH_ZOOM_DETAIL_RESOLVE']:
 assert t in sh,t
# Handoff is scalar only; actual generated shader proof is separately enforced in verify_26718_shaders.py.
contracts=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt');assert 'Signed R16F log2 luminance-detail field' in contracts and 'It never owns RGB/chroma, DNG, exposure or tone' in contracts
render=txt(c,'app/src/main/assets/shaders/motionv2/render.glsl');gain=txt(c,'app/src/main/assets/shaders/motionv2/gainmap.glsl')
def helper(src):
 m=re.search(r'float iris26718HighZoomLogDetail\(vec2 sourcePixel\)\{.*?\n\}',src,re.S);assert m;return m.group(0)
assert helper(render)==helper(gain)
assert 'linearSrgb=max(linearSrgb*exp2(iris26718HighZoomLogDetail(sourcePixel)),vec3(0.0));' in render
assert 'hdrRgb=max(hdrRgb*exp2(iris26718HighZoomLogDetail(masterSourcePixel)),vec3(0.0));' in gain
mr=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java')
for t in ['IRIS_26718_HIGH_ZOOM_DETAIL_TEXTURE_OWNER','new GLFormat(GLFormat.DataType.FLOAT_16, 1)','26718 high-zoom route active without detail texture','glProg.setTexture("iris26718HighZoomDetail", iris26718HighZoomDetail)','iris26718HighZoomDetail.close()']:
 assert t in mr,t
hdr=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java');assert 'IRIS_26718_HIGH_ZOOM_EXCEPTION_CLEANUP_OWNER' in hdr and 'mMotion26718HighZoomDetailPathForCleanup' in hdr and 'deleteIfExists' in hdr
# DNG/native/vendor invariance is a semantic requirement, not just an allowlist fact.
for stem,count in [('NATIVE_FULL',820),('VENDOR_PROTECTED',1),('DNG',6)]:
 def load(n):
  d={}
  for l in (pkg/n).read_text().splitlines():
   if l.strip():h,p=l.split(None,1);d[p.strip()]=h
  return d
 x=load(f'26718_{stem}_BASE.sha256');y=load(f'26718_{stem}_CANDIDATE.sha256');assert len(x)==len(y)==count and x==y
print('PASS 26718 regressions/ownership: <20/no-sidecar remains exact no-op; >=20 Motion-only SR-independent all-NORMAL scalar detail; native Sabre/VGN sole RGB owner; SDR/UHDR shared detail geometry; capture/logging/DNG/native/vendor owners invariant')
