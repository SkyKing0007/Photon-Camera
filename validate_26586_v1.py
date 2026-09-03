#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
CHANGED=[
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/version.properties']
FROZEN={
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java':'6bc93e7d5a79a2e5184fb5e293f623cbbd5397662c60cc04f1a601de755a23c4',
'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl':'fcf89ce6a70a3c8b43c795c01a8490a770635cebb21ac17b031dbe0e6680a07b',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java':'12c21cb276cf835464001b1ede0166a44c39b53d0b32926f009b4ca863f9df84',
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
 v=(c/'app/version.properties').read_text();need(v,'VERSION_NAME=0.9726586','version');need(v,'VERSION_BUILD=26586','version')
 for rel,h in FROZEN.items():
  if sha(c/rel)!=h or (b/rel).read_bytes()!=(c/rel).read_bytes():fail('frozen owner '+rel)
 m=(c/CHANGED[0]).read_text()
 for t in [
  'IRIS_26586_VIEWFINDER_TONE_AUTHORITY_SPLIT',
  'ToneDecision iris26586MeterTone = iris26586ViewfinderMeterToneDecision(1.0f);',
  'ToneDecision tone = iris26586ViewfinderMeterToneDecision(gain);',
  'return iris26586ToneDecision(gain, true);',
  'return iris26586ToneDecision(gain, false);',
  'final int structuredHistogramBins = finalHighlightAuthority ? 256 : 64;',
  'final float structuredPercentile = finalHighlightAuthority ? 0.98f : 0.90f;',
  'final float structuredHighlightTarget = finalHighlightAuthority ? 0.945f : 0.965f;',
  'ToneDecision iris26583Tone = iris26583ToneDecision(gain);',
  'meterToneAuthority=26584 finalHighlightAuthority=26585',
  'IRIS_26584_CONTINUOUS_SPATIAL_HIGHLIGHT_OWNER',
  'IRIS_26585_STRUCTURED_HIGHLIGHT_SHAPE_TAIL',
  'NIGHT_DARK_ADVANTAGE_EV = 0.40f','NIGHT_BRIGHT_ADVANTAGE_EV = 0.30f']:
  need(m,t,'26586 matcher')
 # Fail closed: the exposure solve and fixed candidate meter sample selection must both use meter authority.
 if m.count('iris26586ViewfinderMeterToneDecision(')!=3:fail('meter authority call topology changed')
 if m.count('iris26586ToneDecision(gain, false)')!=1:fail('false/final split topology')
 if m.count('iris26586ToneDecision(gain, true)')!=1:fail('true/final split topology')
 if 'presentedLuma(s, 1.0f, iris26583MeterTone.adaptiveSceneWhite)' in m:fail('26585 final highlight tone still owns meter selection')
 post=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java').read_text()
 for t in ['add(new MotionV2ViewfinderExposureMatcher());','add(new MotionV2AdaptiveColorAppearance());','add(new MotionV2DisplayExposure());','add(new MotionV2Render());']:need(post,t,'common graph')
 print('PASS successful-26585 authority -> exact two-file 26586 V1 allowlist')
 print('PASS viewfinder/body meter authority split uses 26584 P90/0.965 structured baseline in both sample selection and solve')
 print('PASS final highlight authority remains 26585 P98/0.945 after displayGain solve')
 print('PASS 26585 adaptive-color GLSL/Java + render/Jin/Night/native owners byte-frozen')
if __name__=='__main__':main()
