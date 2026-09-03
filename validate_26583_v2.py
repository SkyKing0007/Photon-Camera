#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
CHANGED=['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java','app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java','app/version.properties']
FROZEN=['app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl','app/src/main/cpp/motionv2_jpeg444_jni.cpp']
GPU='d73cd24452280958f089e9124545a81461939e8fa0c9c95272b2825942e4b43d'; RSH='e0a438e51e12df5e6d8b53dc92892078ba7659791725cee54700869a6bc62b71'
def fail(x): raise SystemExit('FAIL: '+x)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def amap(r): return {p.relative_to(r).as_posix():sha(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
def need(s,t,l):
 if t not in s: fail(l+' missing '+t)
def main():
 if len(sys.argv)!=3: fail('usage base candidate')
 b,c=map(Path,sys.argv[1:]); a,d=amap(b),amap(c)
 if len(a)!=1708 or len(d)!=1708: fail(f'universe {len(a)}/{len(d)}')
 diff=sorted(k for k in set(a)|set(d) if a.get(k)!=d.get(k))
 if diff!=sorted(CHANGED): fail('allowlist '+repr(diff))
 v=(c/'app/version.properties').read_text(); need(v,'VERSION_NAME=0.9726583','version'); need(v,'VERSION_BUILD=26583','version')
 for rel in FROZEN:
  if (b/rel).read_bytes()!=(c/rel).read_bytes(): fail('frozen changed '+rel)
 if sha(c/'app/src/main/cpp/motionv2_jpeg444_jni.cpp')!=GPU: fail('GPU sha')
 if sha(c/'app/src/main/assets/shaders/motionv2/render.glsl')!=RSH: fail('render shader sha')
 r=(c/CHANGED[0]).read_text(); m=(c/CHANGED[1]).read_text(); p=(c/CHANGED[2]).read_text()
 for t in ['IRIS_26583_PROJECTED_BROAD_AND_COMPACT_HIGHLIGHT_TAIL','IRIS_26583_BROAD_HIGHLIGHT_TARGET = 0.955f','IRIS_26583_PROJECTED_BROAD_NEAR_CEILING = 0.930f','IRIS_26583_COMPACT_HIGHLIGHT_TARGET = 0.965f','iris26583RequiredSceneWhite','IRIS_26582_SCENE_ADAPTIVE_GLOBAL_TONE=true']:
  need(r,t,'render')
 for t in ['IRIS_26583_PROJECTED_HIGHLIGHT_TAIL_DECISION','IRIS_26583_PROJECTED_BROAD_AND_COMPACT_TAIL_OWNER','iris26583CandidateP995Guide','iris26583CandidateP998Guide','projectedBroadNearCeilingFraction','projectedBroadTailStrength','projectedBaselineTone=true maxChannelDetection=true','uniformRgbScalar=true chromaOwnerUnchanged=true','presentedLuma(s, 1.0f, iris26583MeterTone.adaptiveSceneWhite)']:
  need(m,t,'matcher')
 for t in ['IRIS_26583_PROJECTED_COMPACT_HIGHLIGHT_TAIL_STATE','motionV2ToneP995Guide','motionV2ToneP998Guide','motionV2ToneProjectedBroadNearCeilingFraction','motionV2ToneProjectedNearCeilingFraction','motionV2ToneProjectedHardCeilingFraction','motionV2ToneProjectedBroadTailStrength','motionV2ToneCompactTailStrength']:
  need(p,t,'state')
 if 'presentedLuma(s, 1.0f)' in m: fail('26582 V1 Java signature regression')
 if m.count('presentedLuma(')!=3: fail('presentedLuma count')
 post=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java').read_text()
 for t in ['add(new MotionV2ViewfinderExposureMatcher());','add(new MotionV2AdaptiveColorAppearance());','add(new MotionV2DisplayExposure());','add(new MotionV2Render());','autoExposure=false','exposureFusion=false']:
  need(post,t,'active graph')
 print('PASS successful-26582 V2 authority -> exact four-file 26583 V2 allowlist')
 print('PASS projected broad+compact detector feeds existing uniform-RGB global tone only')
 print('PASS 26582 broad result retained as floor; VGN/SR/render GLSL/UHDR/DNG/GPU owners frozen')
if __name__=='__main__': main()
