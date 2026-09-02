#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
CHANGED=[
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
'app/version.properties']
FROZEN=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp']
GPU_SHA='d73cd24452280958f089e9124545a81461939e8fa0c9c95272b2825942e4b43d'
RENDER_SHADER_SHA='e0a438e51e12df5e6d8b53dc92892078ba7659791725cee54700869a6bc62b71'
def fail(m):raise SystemExit('FAIL: '+m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def amap(root):return {p.relative_to(root).as_posix():sha(p) for p in sorted((root/'app').rglob('*')) if p.is_file()}
def need(s,t,label):
 if t not in s: fail(label+' missing '+t)
def main():
 if len(sys.argv)!=3:fail('usage base candidate')
 base,cand=map(Path,sys.argv[1:]);a,b=amap(base),amap(cand)
 if len(a)!=1708 or len(b)!=1708:fail(f'universe {len(a)}/{len(b)}')
 diff=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k))
 if diff!=sorted(CHANGED):fail('changed allowlist '+repr(diff))
 v=(cand/'app/version.properties').read_text();need(v,'VERSION_NAME=0.9726582','version');need(v,'VERSION_BUILD=26582','version')
 for rel in FROZEN:
  if (base/rel).read_bytes()!=(cand/rel).read_bytes():fail('frozen owner changed '+rel)
 if sha(cand/'app/src/main/cpp/motionv2_jpeg444_jni.cpp')!=GPU_SHA:fail('GPU C++ SHA')
 if sha(cand/'app/src/main/assets/shaders/motionv2/render.glsl')!=RENDER_SHADER_SHA:fail('render GLSL SHA')
 r=(cand/CHANGED[0]).read_text();m=(cand/CHANGED[1]).read_text();p=(cand/CHANGED[2]).read_text()
 for t in ['IRIS_26582_SHARED_GLOBAL_TONE_MODEL','IRIS_26582_HIGHLIGHT_TARGET = 0.97f','IRIS_26582_CLIP_FRACTION_START = 0.002f','IRIS_26582_CLIP_FRACTION_FULL = 0.025f','IRIS_26582_MAX_ADAPTIVE_SCENE_WHITE = 12.0f','iris26582AdaptiveSceneWhite','IRIS_26582_SCENE_ADAPTIVE_GLOBAL_TONE=true']:
  need(r,t,'render tone owner')
 for t in ['IRIS_26582_SCENE_ADAPTIVE_TONE_DECISION','IRIS_26582_SOLVER_RENDER_TONE_PARITY','motionV2ToneP95Guide','motionV2ToneP99Guide','motionV2TonePredictedClipFraction','presentedLuma(sample, gain, tone.adaptiveSceneWhite)','presentedLuma(s, 1.0f, iris26582MeterTone.adaptiveSceneWhite)','MotionV2Render.iris26582MapHeadroom','uniformRgbScalar=true chromaOwnerUnchanged=true']:
  need(m,t,'matcher tone owner')
 for t in ['IRIS_26582_SCENE_ADAPTIVE_GLOBAL_TONE_STATE','motionV2ToneP95Guide','motionV2ToneP99Guide','motionV2ToneAdaptiveSceneWhite','motionV2ToneAdaptiveStrength']:
  need(p,t,'tone state owner')
 # Exact 26582 V1 compiler failure must never recur.
 if 'presentedLuma(s, 1.0f)' in m:fail('26582 V1 two-argument presentedLuma compiler regression survived')
 if m.count('presentedLuma(') != 3:fail('unexpected presentedLuma declaration/call-site count')
 # Stale 26581 solver-only white convergence must be retired; final render never used it.
 for bad in ['neutralMix = smoothstep(0.82f, 1.0f, pos)','mix(r / outPeak, 1.0f, t)','mix(g / outPeak, 1.0f, t)','mix(b / outPeak, 1.0f, t)']:
  if bad in m:fail('stale solver tone behavior survived '+bad)
 post=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java').read_text()
 for t in ['add(new MotionV2ViewfinderExposureMatcher());','add(new MotionV2AdaptiveColorAppearance());','add(new MotionV2DisplayExposure());','add(new MotionV2Render());','autoExposure=false','exposureFusion=false','captureSharpening=false']:
  need(post,t,'active post graph')
 # No chroma/CFA/SR/HDR/DNG/capture owner in runtime delta.
 forbidden=[x for x in diff if any(k in x for k in ['GlesIris26529SpatialRgbChromaPostprocessor','GlesMgcRawSabreShaders','Dng','ImageSaver','CaptureController','MotionV2Merger','PhotonMotionMgc1271Bridge','motionv2_jpeg444_jni.cpp','gainmap.glsl','render.glsl'])]
 if forbidden:fail('forbidden owner delta '+repr(forbidden))
 print('PASS exact successful-26581 1708-file authority -> four-file 26582 allowlist')
 print('PASS 26582 single global tone authority: existing low-res matcher probe -> adaptive sceneWhite -> existing scalar render shoulder')
 print('PASS solver/render tone parity: stale neutral/overflow-to-white approximation retired')
 print('PASS 26581 VGN/SR gap-edge owners, render/gainmap GLSL, GPU publication, DNG/capture owners frozen')
if __name__=='__main__':main()
