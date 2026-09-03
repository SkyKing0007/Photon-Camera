#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
CHANGED=[
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightNeuralEnhancer.java',
'app/version.properties']
FROZEN={
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java':'12c21cb276cf835464001b1ede0166a44c39b53d0b32926f009b4ca863f9df84',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java':'c8b8c26967de7e91cea4406221f5d08b0c9c64baca875757ea6fae762afbdd56',
'app/src/main/assets/shaders/motionv2/render.glsl':'e0a438e51e12df5e6d8b53dc92892078ba7659791725cee54700869a6bc62b71',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp':'d73cd24452280958f089e9124545a81461939e8fa0c9c95272b2825942e4b43d',
'app/src/main/assets/models/iris_night_jin_lol_512.onnx':'bb7f911afd1ac209a27f20b97d6f2d532bb1ffa1231374755859139cb4e30ff7',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java':'d5de1abf9bb42b92715fc1ec028d89d1408ecf6c4853cc95afbffc6bfe766b1e'}
def fail(x):raise SystemExit('FAIL: '+x)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def amap(r):return {p.relative_to(r).as_posix():sha(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
def need(s,t,l):
 if t not in s:fail(l+' missing '+t)
def main():
 if len(sys.argv)!=3:fail('usage base candidate')
 b,c=map(Path,sys.argv[1:]);a,d=amap(b),amap(c)
 if len(a)!=1708 or len(d)!=1708:fail(f'universe {len(a)}/{len(d)}')
 diff=sorted(k for k in set(a)|set(d) if a.get(k)!=d.get(k))
 if diff!=sorted(CHANGED):fail('allowlist '+repr(diff))
 v=(c/'app/version.properties').read_text();need(v,'VERSION_NAME=0.9726584','version');need(v,'VERSION_BUILD=26584','version')
 for rel,h in FROZEN.items():
  if sha(c/rel)!=h or (b/rel).read_bytes()!=(c/rel).read_bytes():fail('frozen owner '+rel)
 # Successful 26583 projected broad+compact tone remains the mandatory floor; 26584 may only add continuous/spatial headroom above it.
 render=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
 matcher=(c/CHANGED[0]).read_text()
 state=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java').read_text()
 for t in ['IRIS_26583_PROJECTED_BROAD_AND_COMPACT_HIGHLIGHT_TAIL','IRIS_26583_BROAD_HIGHLIGHT_TARGET = 0.955f','IRIS_26583_COMPACT_HIGHLIGHT_TARGET = 0.965f']:need(render,t,'26583 tone')
 for t in ['IRIS_26583_PROJECTED_HIGHLIGHT_TAIL_DECISION','projectedBroadNearCeilingFraction','projectedBroadTailStrength','uniformRgbScalar=true chromaOwnerUnchanged=true','IRIS_26584_CONTINUOUS_SPATIAL_HIGHLIGHT_OWNER','IRIS_26584_ALL_SCENE_HIGHLIGHT_DECISION','continuousTailPressure','continuousTailStrength','structuredPixels','structuredCells','structuredGuide','structuredStrength','floor26583SceneWhite','spatialPopulationIndependent=true continuousTail=true','localToneMap=false']:need(matcher,t,'26584 matcher')
 for t in ['IRIS_26583_PROJECTED_COMPACT_HIGHLIGHT_TAIL_STATE','motionV2ToneProjectedBroadNearCeilingFraction','motionV2ToneCompactTailStrength']:need(state,t,'26583 state')
 for t in ['NIGHT_DARK_ADVANTAGE_EV = 0.40f','NIGHT_BRIGHT_ADVANTAGE_EV = 0.30f']:need(matcher,t,'Night brightness')
 if 'presentedLuma(s, 1.0f)' in matcher:fail('26582 V1 Java signature regression')
 jin=(c/CHANGED[1]).read_text()
 for t in ['IRIS_26584_JIN_CLEANUP_ONLY_OWNER','IRIS_26584_JIN_CLEANUP_ONLY_RESIDUAL','IRIS_26584_JIN_CLEANUP_CONTRACT','constrainCleanupResidual(residual, px)','globalStyleAuthority=false','broadExposureAuthority=false','broadColorAuthority=false','highlightCleanupRetained=true','neutralShadowChromaCleanupRetained=true','nativeSabreGuidedTransferUnchanged=true','applyReferenceResidualNative(base, residual, px, N, N, baseDisplayP3)']:need(jin,t,'Jin cleanup')
 post=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java').read_text()
 for t in ['add(new MotionV2ViewfinderExposureMatcher());','add(new MotionV2AdaptiveColorAppearance());','add(new MotionV2DisplayExposure());','add(new MotionV2Render());']:need(post,t,'common graph')
 print('PASS successful-26583 V2 authority -> exact three-file 26584 V1 allowlist')
 print('PASS successful 26583 projected broad+compact tone retained as floor; continuous/spatial all-scene highlight owner only adds headroom')
 print('PASS Jin retained as constrained cleanup residual; ONNX/Night owner/native transfer/GPU publication frozen')
if __name__=='__main__':main()
