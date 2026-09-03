#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib

def fail(m):raise SystemExit('FAIL: '+m)
def req(c,m):
 if not c:fail(m)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('candidate_root');ns=ap.parse_args();c=Path(ns.candidate_root)
 rel='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java'
 m=(c/rel).read_text()
 # Exact 26585 failure regression: final P98/0.945 authority must not own viewfinder/body meter trial evaluation.
 req('ToneDecision tone = iris26586ViewfinderMeterToneDecision(gain);' in m,'exposureError meter authority missing')
 req('ToneDecision iris26586MeterTone = iris26586ViewfinderMeterToneDecision(1.0f);' in m,'fixed meter sample selection authority missing')
 req('presentedLuma(s, 1.0f, iris26586MeterTone.adaptiveSceneWhite)' in m,'fixed meter sample luma authority missing')
 for tok in ['finalHighlightAuthority ? 256 : 64','finalHighlightAuthority ? 0.98f : 0.90f','finalHighlightAuthority ? 0.945f : 0.965f','return iris26586ToneDecision(gain, false);','return iris26586ToneDecision(gain, true);']:
  req(tok in m,'authority split token '+tok)
 req(m.count('iris26586ViewfinderMeterToneDecision(')==3,'unexpected meter authority topology')
 req(m.count('iris26586ToneDecision(gain, false)')==1,'meter branch must have one helper owner')
 req(m.count('iris26586ToneDecision(gain, true)')==1,'final branch must have one helper owner')
 # Final 26585 P98/0.945 highlight authority is computed only after displayGain is solved and frozen.
 solve=m.index('rawSolvedEv = solveBounded(')
 gain=m.index('float gain = (float)Math.pow(2.0, solvedEv);',solve)
 frozen=m.index('basePipeline.mParameters.motionV2DisplayGain = gain;',gain)
 final=m.index('ToneDecision iris26583Tone = iris26583ToneDecision(gain);',frozen)
 req(solve<gain<frozen<final,'final highlight sceneWhite must occur after displayGain freeze')
 # The exact 26585 pink/cyan/green fail-closed owners remain byte-frozen.
 frozen_files={
  'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java':'6bc93e7d5a79a2e5184fb5e293f623cbbd5397662c60cc04f1a601de755a23c4',
  'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl':'fcf89ce6a70a3c8b43c795c01a8490a770635cebb21ac17b031dbe0e6680a07b',
  'app/src/main/assets/shaders/motionv2/render.glsl':'e0a438e51e12df5e6d8b53dc92892078ba7659791725cee54700869a6bc62b71',
  'app/src/main/cpp/motionv2_jpeg444_jni.cpp':'d73cd24452280958f089e9124545a81461939e8fa0c9c95272b2825942e4b43d',
  'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightNeuralEnhancer.java':'b7595a8a347fcfe3bdf9a0225ecb393406718adf1479c2a68a38eff8d962dbcd'}
 for r,h in frozen_files.items():req(hashlib.sha256((c/r).read_bytes()).hexdigest()==h,'frozen regression '+r)
 sh=(c/'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl').read_text()
 aj=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java').read_text()
 for tok in ['IRIS_26585_TONE_AWARE_HIGHLIGHT_CHROMA_PRESERVATION','legacyChromaGain','legacyHighlightSuppression','toneSafeHighlightGain','min(1.12, highlightFloorGainLimit)','Output = vec3(centerLuma) + centerChroma * adaptiveChromaGain;']:req(tok in sh,'carried chroma contract '+tok)
 for tok in ['MAX_HIGHLIGHT_CHROMA_GAIN = 1.12f','motionV2ToneAdaptiveSceneWhite','toneAwareHighlightChroma=true']:req(tok in aj,'carried appearance owner '+tok)
 ver=(c/'app/version.properties').read_text();req('VERSION_NAME=0.9726586' in ver and 'VERSION_BUILD=26586' in ver,'version')
 print('PASS exact 26585 feedback failure removed from trial exposure and fixed meter sample selection')
 print('PASS body/viewfinder authority=26584 P90/0.965; final highlight authority=26585 P98/0.945 only after solved gain')
 print('PASS 26585 tone-aware chroma/pink-cyan-green safety + render/Jin/native owners byte-frozen')
if __name__=='__main__':main()
