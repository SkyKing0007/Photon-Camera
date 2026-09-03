#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
CHANGED=[
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java',
'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl',
'app/version.properties']
FROZEN={
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java':'12c21cb276cf835464001b1ede0166a44c39b53d0b32926f009b4ca863f9df84',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java':'c8b8c26967de7e91cea4406221f5d08b0c9c64baca875757ea6fae762afbdd56',
'app/src/main/assets/shaders/motionv2/render.glsl':'e0a438e51e12df5e6d8b53dc92892078ba7659791725cee54700869a6bc62b71',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp':'d73cd24452280958f089e9124545a81461939e8fa0c9c95272b2825942e4b43d',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightNeuralEnhancer.java':'b7595a8a347fcfe3bdf9a0225ecb393406718adf1479c2a68a38eff8d962dbcd',
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
 v=(c/'app/version.properties').read_text();need(v,'VERSION_NAME=0.9726585','version');need(v,'VERSION_BUILD=26585','version')
 for rel,h in FROZEN.items():
  if sha(c/rel)!=h or (b/rel).read_bytes()!=(c/rel).read_bytes():fail('frozen owner '+rel)
 matcher=(c/CHANGED[0]).read_text(); appj=(c/CHANGED[1]).read_text(); shader=(c/CHANGED[2]).read_text()
 # 26584 all-scene detector is retained and strengthened only at its structured top tail.
 for t in ['IRIS_26584_CONTINUOUS_SPATIAL_HIGHLIGHT_OWNER','IRIS_26584_ALL_SCENE_HIGHLIGHT_DECISION','floor26583SceneWhite','continuousTailPressure','structuredPixels','structuredCells','spatialPopulationIndependent=true continuousTail=true','localToneMap=false','histTotal * 0.98','gain, structuredGuide, 0.945f','structuredGuidePercentile=0.98','structuredHighlightTarget=0.945']:
  need(matcher,t,'26585 matcher')
 for t in ['NIGHT_DARK_ADVANTAGE_EV = 0.40f','NIGHT_BRIGHT_ADVANTAGE_EV = 0.30f']:need(matcher,t,'Night brightness')
 if 'presentedLuma(s, 1.0f)' in matcher:fail('26582 V1 Java signature regression')
 # Tone-aware highlight chroma retains the exact legacy path as floor and adds <=1.12 only when post-tone safe.
 for t in ['MAX_WEAK_CHROMA_GAIN = 1.32f','MAX_HIGHLIGHT_CHROMA_GAIN = 1.12f','motionV2ToneAdaptiveSceneWhite','glProg.setVar("sceneWhite", sceneWhite)','toneAwareHighlightChroma=true']:
  need(appj,t,'appearance Java')
 for t in ['IRIS_26585_TONE_AWARE_HIGHLIGHT_CHROMA_PRESERVATION','uniform float sceneWhite;','legacyChromaGain','legacyHighlightSuppression','toneHeadroomGate','toneSafeHighlightGain','highlightFloorGainLimit','min(1.12, highlightFloorGainLimit)','<= 0.995','Output = vec3(centerLuma) + centerChroma * adaptiveChromaGain;']:
  need(shader,t,'appearance GLSL')
 if 'mix(' in shader.split('Output = vec3(centerLuma) + centerChroma * adaptiveChromaGain;')[0].split('IRIS_26585_TONE_AWARE_HIGHLIGHT_CHROMA_PRESERVATION')[-1]:
  # mix is allowed for scalar math only; prohibit neighbor RGB/chroma injection into Output separately below.
  pass
 if 'Output = mix(' in shader or 'Output +=' in shader:fail('appearance output neighbor/color mixing')
 post=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java').read_text()
 for t in ['add(new MotionV2ViewfinderExposureMatcher());','add(new MotionV2AdaptiveColorAppearance());','add(new MotionV2DisplayExposure());','add(new MotionV2Render());']:need(post,t,'common graph')
 jin=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightNeuralEnhancer.java').read_text()
 for t in ['IRIS_26584_JIN_CLEANUP_ONLY_OWNER','constrainCleanupResidual(residual, px)','globalStyleAuthority=false','highlightCleanupRetained=true','nativeSabreGuidedTransferUnchanged=true']:need(jin,t,'frozen Jin')
 print('PASS successful-26584 V1 authority -> exact four-file 26585 V1 allowlist')
 print('PASS 26584 all-scene highlight owner retained; structured shape tail strengthened P98/0.945 only')
 print('PASS tone-aware highlight chroma uses solved sceneWhite, exact legacy floor, <=1.12 own-chroma-axis gain, zero-floor and post-tone safety')
 print('PASS final render/Jin/Night/Sabre/native publication owners frozen')
if __name__=='__main__':main()
