#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26723_regressions.py BASE26722 CAND26723')
b,c=map(Path,sys.argv[1:]); pkg=Path(__file__).resolve().parent
def H(r): return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
def txt(r,p): return (r/p).read_text()
def section(s,start,end):
 i=s.index(start); j=s.index(end,i+len(start)); return s[i:j]
B,C=H(b),H(c); assert len(B)==len(C)==1823
expected=set((pkg/'26723_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()); assert expected=={
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/version.properties'}
assert {k for k in B|C if B.get(k)!=C.get(k)}==expected
v=txt(c,'app/version.properties'); assert 'VERSION_NAME=0.9726723' in v and 'VERSION_BUILD=26723' in v
# Freeze successful 26722 architecture outside the two intended owners.
for rel in [
'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java',
'app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt',
'app/src/main/java/com/hinnka/mycamera/processor/RawStackFrameCompat.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Denoise.java',
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
# Flicker capture ownership: observer-only RAW/preview is preserved; 26723 only changes selected-burst confidence attachment.
cap=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
for t in ['IRIS_26680_FLICKER_OBSERVER_ONLY_PREVIEW','IRIS_26680_FLICKER_OBSERVER_ONLY_CAPTURE','IRIS_26720_CAPTURE_ROW_FLICKER_EVIDENCE','IRIS_26723_INTELLIGENT_FLICKER_BATCH_GATE','MOTION_26723_FLICKER_MIN_SELECTED_ACTIVE_FRAMES = 2','MOTION_26723_FLICKER_MIN_PHASE_TRANSITIONS = 2','mMotion26723FlickerBatchState = "ACTIVE"','evidence[4] > 0.0f','frame.motionV2RowFlickerStrength = appliedStrength','retroactiveFullStrength=false','rawRewritten=false confidenceOnly=true','shortLongUntouched=true highlightRecoveryUntouched=true dngUntouched=true']:
 assert t in cap,t
attach=section(cap,'    private int motion26720AttachNormalRowFlickerEvidence(','    /* IRIS_26720_LEAST_FLICKERED_STRUCTURAL_REFERENCE')
assert 'frame.motionV2RowFlickerStrength = 1.0f;' not in attach
assert 'candidateByHarmonic' in attach and 'activeByHarmonic' in attach and 'maxTransitions' in attach
assert 'MOTION_26723_FLICKER_MIN_SELECTED_CANDIDATES' in attach
# Capture/exposure/SHORT-LONG ownership outside the narrow attach/reference boundary is not rewritten.
bcap=txt(b,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
for marker in ['IRIS_26608_UNIVERSAL_HDR_DYNAMIC_RANGE_TRIGGER','IRIS_26678_RAW_ROW_FLICKER_OBSERVER','IRIS_26680_FLICKER_OBSERVER_ONLY_PREVIEW','IRIS_26680_FLICKER_OBSERVER_ONLY_CAPTURE']:
 assert marker in bcap and marker in cap
# Successful 26721 RGB32F transport remains exactly present.
stack=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
for t in ['IRIS_26721_HIGH_ZOOM_RGB32F_TRANSFER_OWNER','private const val HIGH_ZOOM_RGB32F_BYTES_PER_PIXEL = 3 * Float.SIZE_BYTES','transfer=RGB32F bytesPerChannel=4 float16Transfer=false','IRIS_26721_HIGH_ZOOM_RGB32F_CARRIER']:
 assert t in stack,t
# 26723 high-zoom refinement is isolated: original 26574 shader remains and high-zoom gets a dedicated owner.
sh=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
for t in ['IRIS_26723_HIGH_ZOOM_FLOW_PROXY_REFINEMENT','val highZoomFlowRefine26723: String by lazy {','const ivec2 d[9]','conditioning>0.008&&improvement>0.055&&uniqueness>0.025&&variationRaw<2.0','IRIS_26723_HIGH_ZOOM_PROVEN_MICROCONTRAST']:
 assert t in sh,t
for t in ['highZoomFlowRefineProgram26723','highZoomRefine26723 = refineForHighZoom26718','IRIS_26723_HIGH_ZOOM_SUBPIXEL_DIVERSITY','proxyWindow=3x3','originalRawReconstructionUntouched=true','spatialLumaDenoiseAdded=false']:
 assert t in stack,t
# Explicit Super Res refinement source string remains byte-identical between successful 26722 and 26723.
def triple(k,name):
 m=re.search(r'val\s+'+re.escape(name)+r'\s*=\s*"""\n(.*?)\n\s*"""\.trimIndent\(\)',k,re.S); assert m,name
 return m.group(1)
bsh=txt(b,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
assert triple(bsh,'true2xFlowRefine26574')==triple(sh,'true2xFlowRefine26574')
# 26722 native-Sabre/VGN chroma topology is preserved; 26723 changes only supported luminance residual gain.
guide=triple(sh,'true2xGuideRender26568'); bguide=triple(bsh,'true2xGuideRender26568'); assert guide==bguide
for t in ['IRIS_26579_TRUE2X_TOPOLOGY_CHROMA_UPSAMPLE','IRIS_26580_TRUE2X_SAME_MATERIAL_CHROMA_OWNERSHIP','IRIS_26581_DECISIVE_CROSS_EDGE_CHROMA_VETO','localChromaOccupancy','localColorProtection','anchorChroma','selectedChroma']:
 assert t in guide,t
prop=section(sh,'    /* IRIS_26722_HIGH_ZOOM_NATIVE_SABRE_VGN_CHROMA_AUTHORITY','    /* IRIS_26719_HIGH_ZOOM_LAZY_ISOLATION')
for t in ['true2xGuideRender26568','IRIS_26723_HIGH_ZOOM_PROVEN_MICROCONTRAST','provenMicrocontrastGain = 1.0 + 0.10']:
 assert t in prop,t
for t in ['directChromaConfidence','vec3 directChroma =','chromaDelta','protectedChroma','maxChromaDelta']:
 assert t not in prop,t
# Existing high-zoom direct CFA RGB merge/flicker shader transform remains byte-semantic; 26723 capture gate supplies safer metadata.
for t in ['val highZoomRgbMerge26720: String by lazy {','iris26720HighZoomRowReliability','return mix(1.0, 0.08','uObservationConfidence']:
 assert t in sh,t
# Automatic luma denoise remains zero; no high-zoom spatial denoiser or sharpening owner is added.
bridge=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
assert 'val automaticLumaScale26639 = 0.0f' in bridge
assert (b/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_bytes()==(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_bytes()
# <20x and explicit SR route isolation remains inherited.
assert 'enableHighZoomDetail && !enableSabreSuperRes' in stack
# Permanent 26720 compiler regressions remain guarded.
assert 'val failure = checkNotNull(rgbAttempt.exceptionOrNull())' in stack
assert 'reason=${failure?.message}", failure)' not in stack
color=txt(c,'app/src/main/assets/shaders/motionv2/color_transform.glsl'); macro_define='#define USE_IRIS_26720_HIGH_ZOOM_RGB 0'; macro_use='#if USE_IRIS_26720_HIGH_ZOOM_RGB == 1'; assert color.count(macro_define)==1 and color.count(macro_use)==2 and color.index(macro_define)<color.index(macro_use)
# Native/vendor/DNG remain invariant.
def loadm(n):
 d={}
 for l in (pkg/n).read_text().splitlines():
  if l.strip(): h,p=l.split(None,1); d[p.strip()]=h
 return d
for stem,count in [('NATIVE_FULL',820),('VENDOR_PROTECTED',1),('DNG',6)]:
 x=loadm(f'26723_{stem}_BASE.sha256'); y=loadm(f'26723_{stem}_CANDIDATE.sha256'); assert len(x)==len(y)==count and x==y
print('PASS 26723 regressions/ownership: exact successful 26722 base; flicker correction is selected-burst ACTIVE-only with measured strength/no retroactive full-strength promotion; >=20x refinement is isolated 3x3 proxy over untouched RAW; 26722 native-Sabre/VGN chroma, RGB32F, exposure/LONG/SHORT/tone/UHDR/DNG, <20x and explicit SR are preserved')
