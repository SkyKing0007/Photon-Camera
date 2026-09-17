#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys,textwrap
if len(sys.argv)!=3: raise SystemExit('usage: validate_26653.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'app').rglob('*')) if p.is_file()}
def txt(root,r): return (root/r).read_text()
def embedded(src):
 out={}
 for m in re.finditer(r'\bval\s+([A-Za-z_]\w*)\s*=\s*"""(.*?)"""\.trimIndent\(\)',src,re.S): out[m.group(1)]=textwrap.dedent(m.group(2)).strip('\n')
 return out
bh,ch=H(base),H(cand); assert len(bh)==len(ch)==1721
changed={r for r in set(bh)|set(ch) if bh.get(r)!=ch.get(r)}
expected={
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2PhotonHighlightCompression.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/assets/shaders/motionv2/color_transform.glsl',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl','app/version.properties'}
assert changed==expected,changed^expected
v=txt(cand,'app/version.properties'); assert 'VERSION_NAME=0.9726653' in v and 'VERSION_BUILD=26653' in v
# Only the intended fusion body changes inside the 51-body Sabre carrier.
bs=embedded(txt(base,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'))
cs=embedded(txt(cand,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'))
assert set(bs)==set(cs) and len(bs)==len(cs)==51
assert {n for n in bs if bs[n]!=cs[n]}=={'universalNormalMasterShortFusion26651'}
f=cs['universalNormalMasterShortFusion26651']
for t in ['IRIS_26653_FULL_RES_FINE_STRUCTURE_SHORT_RADIANCE_GUARD','float normalFineStructureProtection()','texelFetch(uNormalMean, lP, 0)','texelFetch(uNormalMean, rP, 0)','texelFetch(uNormalMean, dP, 0)','texelFetch(uNormalMean, uP, 0)','float lap =','float ridgeX =','float ridgeY =','smoothstep(0.035, 0.120','float physicalNormalLoss = clamp(1.0 - normalSourceConfidence','float fineStructurePhysicalSupport = smoothstep(0.20, 0.70, physicalNormalLoss);','float inferredRadiometricLoss = effectiveRadiometricLoss *','mix(1.0, fineStructurePhysicalSupport, fineStructure);','float measuredNormalLoss = max(physicalNormalLoss, inferredRadiometricLoss);','float targetY = mix(normalY, shortY, radianceAuthority);','IRIS_26652_TRUSTED_SHORT_CHROMA_CONSENSUS']:
 assert t in f,t
# 26652 trusted chroma and 26651 NORMAL-master contracts survive.
for t in ['edgeCorrespondence(referenceUv, sampleUv)','minimum3(measuredNormalPhysicalLoss)','localNormalChromaConsensus(','float trustedColorConfidence = colorEligibility * consensusConfidence;','float validityRoom = max(0.970 - normalSourceConfidence, 0.0);']:
 assert t in f,t
for bad in ['mix(normalMean.rgb, shortRgb, authority)','if (leaf','if (foliage','if (lamp','if (hair','if (fabric']:
 assert bad.lower() not in f.lower(),bad
# Highlight Compression becomes analysis only; KNEE_REF remains exact.
hc=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2PhotonHighlightCompression.java')
for t in ['private static final float KNEE_REF = 0.10f;','IRIS_26653_ANALYSIS_ONLY_NO_PRECOLOR_PIXEL_OWNER','owner=analysisOnlyFinalToneConsumer','toggleApplication=finalExtendedLinearToneOnly','brightnessMatcherCompensation=false']:
 assert t in hc,t
for bad in ['motionV2PhotonCurveOff','motionV2PhotonCurveOn','GLTexture','WorkingTexture = basePipeline','glProg.draw']:
 assert bad not in hc,bad
assert 'WorkingTexture = previousNode.WorkingTexture;' in hc
# Color transform receives fused carrier unchanged by highlight toggle.
ct=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java')
cg=txt(cand,'app/src/main/assets/shaders/motionv2/color_transform.glsl')
for t in ['IRIS_26653_NO_PRECOLOR_HIGHLIGHT_TONE','photonToggleDifferentialPreColor=false']: assert t in ct,t
for bad in ['PhotonCurveOff','PhotonCurveOn','USE_PHOTON_HIGHLIGHT_COMPRESSION']: assert bad not in ct and bad not in cg,bad
assert 'IRIS_26653_HIGHLIGHT_TONE_DEFERRED_TO_FINAL_RENDER' in cg
# Viewfinder matcher is byte-identical and remains on 26652/OFF mapping so ON cannot be compensated.
matcher='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java'
assert bh[matcher]==ch[matcher]
mt=txt(cand,matcher); assert 'iris26623MapMotionSdrFinalGuide' in mt and 'iris26653MapMotionSdrFinalGuide' not in mt
# One final post-brightness tone contract is consumed by render, Local Laplacian global seed and UHDR gainmap.
r=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java')
assert 'public static final float IRIS_26623_UPPER_TONE_START = 0.65f;' in r
for t in ['IRIS_26653_SINGLE_FINAL_HIGHLIGHT_TONE_REFERENCE','static float iris26653MapMotionSdrFinalGuide','if (!highlightCompressionEnabled || x <= IRIS_26623_UPPER_TONE_START) return off;','final float whiteSpan = Math.max(1.0f','iris26653SetFinalToneUniforms()','owner=MotionV2RenderAfterBrightnessSolve','matcherUses26652OffMap=true','lowerToneExactThrough=" + IRIS_26623_UPPER_TONE_START','localLaplacianSharedMap=true','gainMapSharedMap=true','preColorDifferential=false']:
 assert t in r,t
for path,marker,fn in [
('app/src/main/assets/shaders/motionv2/render.glsl','IRIS_26653_SINGLE_FINAL_HIGHLIGHT_TONE','iris26653MapMotionSdrFinalGuide'),
('app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl','IRIS_26653_SINGLE_FINAL_HIGHLIGHT_TONE','iris26653MapMotionSdrFinalGuide'),
('app/src/main/assets/shaders/motionv2/gainmap.glsl','IRIS_26653_UHDR_SHARED_FINAL_SDR_TONE','iris26653MapMotionSdrGuide')]:
 s=txt(cand,path)
 for t in [marker,'uniform int iris26653HighlightCompressionEnabled;','uniform float iris26653HighlightKnee;','uniform float iris26653AdaptiveWhitePoint;',fn,'x<=0.65','mix(0.915,0.890,pressure)','mix(0.090,0.055,pressure)','sqrt(max(iris26653AdaptiveWhitePoint,1.0))']: assert t in s,(path,t)
# render and Local-Laplacian global guide use literally identical final function bodies.
def fun(src,name):
 m=re.search(r'float\s+'+re.escape(name)+r'\s*\([^)]*\)\s*\{',src); assert m
 i=m.start(); j=m.end(); d=1
 while d:
  d += (src[j]=='{')-(src[j]=='}'); j+=1
 return src[i:j]
rg=txt(cand,'app/src/main/assets/shaders/motionv2/render.glsl'); lg=txt(cand,'app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl')
assert fun(rg,'iris26653MapMotionSdrFinalGuide')==fun(lg,'iris26653MapMotionSdrFinalGuide')
# Local remap remains protected; final global authority changed, not detail reconstruction mechanics.
ll='app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl'; assert bh[ll]==ch[ll]
# Protected capture/DNG/HEIC/Night/SR roots remain unchanged.
for p in ['app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHeicUltraHdrEncoder.java','app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHardwareHevcEncoder.java','app/src/main/cpp/iris_heic_jni.cpp','app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java','app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java']:
 assert bh[p]==ch[p],p
print('PASS 26653 semantic/ownership validation: 10-path/0-addition scope; full-res fine-structure SHORT guard; pre-color HC removed; matcher frozen; one post-brightness final SDR tone shared by render/Local-Laplacian/UHDR; KNEE_REF 0.10')
