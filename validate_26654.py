#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26654.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'app').rglob('*')) if p.is_file()}
def txt(root,r): return (root/r).read_text()
def fun(src,name):
 m=re.search(r'float\s+'+re.escape(name)+r'\s*\([^)]*\)\s*\{',src); assert m,name
 i=m.start(); j=m.end(); d=1
 while d:
  d += (src[j]=='{')-(src[j]=='}'); j+=1
 return src[i:j]
bh,ch=H(base),H(cand); assert len(bh)==len(ch)==1721
changed={r for r in set(bh)|set(ch) if bh.get(r)!=ch.get(r)}
expected={
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2PhotonHighlightCompression.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl','app/version.properties'}
assert changed==expected,changed^expected
v=txt(cand,'app/version.properties'); assert 'VERSION_NAME=0.9726654' in v and 'VERSION_BUILD=26654' in v
# 26653 SHORT fusion and brightness solver remain exact compiled authority.
for p in ['app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
          'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java']:
 assert bh[p]==ch[p],p
matcher=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java')
assert 'iris26623MapMotionSdrFinalGuide' in matcher and 'iris26654MapMotionSdrFinalGuide' not in matcher
# Photon analyzer is knee/pressure evidence only; old adaptive white may be logged but has no tone authority.
hc=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2PhotonHighlightCompression.java')
for t in ['private static final float KNEE_REF = 0.10f;','IRIS_26654_ANALYSIS_ONLY_NO_TONE_WHITE_AUTHORITY','owner=analysisOnlyKneeConsumer','adaptiveWhiteOutputAuthority=false irisSceneWhiteTailAuthority=true','preColorPixelModification=false','brightnessMatcherCompensation=false']:
 assert t in hc,t
for bad in ['motionV2PhotonCurveOff','motionV2PhotonCurveOn','GLTexture','glProg.draw']:
 assert bad not in hc,bad
assert 'WorkingTexture = previousNode.WorkingTexture;' in hc
# Final Java tone: no Photon white argument, Iris scene-white ratio owns >1 tail.
r=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java')
for t in ['IRIS_26654_SINGLE_FINAL_HIGHLIGHT_TONE_REFERENCE','static float iris26654MapMotionSdrFinalGuide','IRIS_26654_IRIS_SCENE_WHITE_TAIL_AUTHORITY','safeAdaptiveWhite / safeBaseWhite','iris26654SetFinalToneUniforms()','glProg.setVar("iris26654HighlightCompressionEnabled"','glProg.setVar("iris26654HighlightKnee"','photonAdaptiveWhiteTelemetryOnly=','localLaplacianAbsoluteToneOwner=false localLaplacianBoundedZeroDcDetailOnly=true','gainMapSharedFinalToneAndResidualContract=true','irisSceneWhiteTailAuthority=true']:
 assert t in r,t
assert 'glProg.setVar("iris26653AdaptiveWhitePoint"' not in r
assert 'iris26650HighlightCompressionEnabled' not in r
# Local Laplacian no longer knows HC toggle; inherited legacy local result is only a candidate.
ll=txt(cand,'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl')
for t in ['IRIS_26654_LOCAL_LAPLACIAN_NO_HIGHLIGHT_TOGGLE_AUTHORITY','IRIS_26654_LOCAL_DETAIL_CANDIDATE_ONLY','IRIS_26645_LEGACY_LOCAL_CANDIDATE_HEADROOM','IRIS_26646_LEGACY_LOCAL_CANDIDATE_RADIANCE','float baseOut=legacyBaseOut;','float residualWeight=legacyResidualWeight;']:
 assert t in ll,t
assert 'iris26650HighlightCompressionEnabled' not in ll
# Three final tone consumers use scene-white tail; render/gainmap enforce same bounded zero-DC residual contract.
rg=txt(cand,'app/src/main/assets/shaders/motionv2/render.glsl')
lg=txt(cand,'app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl')
gm=txt(cand,'app/src/main/assets/shaders/motionv2/gainmap.glsl')
for path,s,fn in [
('render',rg,'iris26654MapMotionSdrFinalGuide'),('local-global',lg,'iris26654MapMotionSdrFinalGuide'),('gainmap',gm,'iris26654MapMotionSdrGuide')]:
 for t in ['uniform int iris26654HighlightCompressionEnabled;','uniform float iris26654HighlightKnee;','adaptiveWhite/baseWhite','clamp(adaptiveWhite/baseWhite,1.0,3.0)',fn]: assert t in s,(path,t)
 assert 'iris26653AdaptiveWhitePoint' not in s,path
assert fun(rg,'iris26654MapMotionSdrFinalGuide')==fun(lg,'iris26654MapMotionSdrFinalGuide')
for t in ['IRIS_26654_BOUNDED_ZERO_DC_LOCAL_DETAIL','iris26654BoundedLocalDetail','const float radius=8.0','float zeroDc=(localMapped-globalMapped)-dc;','float maxAbs=mix(0.018,0.045,upper);','smoothstep(0.65,0.72,sourceGuide)','iris26654HighlightCompressionEnabled!=0 && sourceGuide>0.65']:
 assert t in rg,t
for t in ['iris26654GainLocalDeltaAt','const float radius=8.0','float zeroDc=(localMapped-globalMapped)-dc;','float maxAbs=mix(0.018,0.045,upper);','iris26640Smoothstep(0.65,0.72,sourceGuide)','iris26654HighlightCompressionEnabled==0 || sourceGuide<=0.65']:
 assert t in gm,t
# Shared constants must match exactly between SDR and UHDR residual contract.
for token in ['0.010,0.050','0.018,0.045','radius=8.0','0.65,0.72']:
 assert token in rg and token in gm,token
# Protected capture/DNG/HEIC/Night/SR/color owners stay byte-identical.
for p in ['app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHeicUltraHdrEncoder.java','app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHardwareHevcEncoder.java','app/src/main/cpp/iris_heic_jni.cpp','app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java','app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java','app/src/main/assets/shaders/motionv2/color_transform.glsl']:
 assert bh[p]==ch[p],p
print('PASS 26654 semantic/ownership validation: 8-path/0-addition scope; 26653 SHORT+matcher frozen; stale Local-Laplacian HC authority removed; Iris scene-white owns >1 tail; HC-ON absolute tone is global with bounded zero-DC source-structure detail; UHDR parity retained; KNEE_REF 0.10')
