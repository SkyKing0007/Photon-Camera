#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,re
def fail(m):raise SystemExit('FAIL: '+m)
def req(c,m):
 if not c:fail(m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('candidate_root');ns=ap.parse_args();c=Path(ns.candidate_root)
 # Carry exact successful 26586 meter/final-highlight split.
 m=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java').read_text()
 for tok in ['ToneDecision tone = iris26586ViewfinderMeterToneDecision(gain);','ToneDecision iris26586MeterTone = iris26586ViewfinderMeterToneDecision(1.0f);','presentedLuma(s, 1.0f, iris26586MeterTone.adaptiveSceneWhite)','finalHighlightAuthority ? 256 : 64','finalHighlightAuthority ? 0.98f : 0.90f','finalHighlightAuthority ? 0.945f : 0.965f','return iris26586ToneDecision(gain, false);','return iris26586ToneDecision(gain, true);']:
  req(tok in m,'carried 26586 authority '+tok)
 req(m.count('iris26586ViewfinderMeterToneDecision(')==3,'26586 meter topology')
 # Carry prior pink/cyan/green safety owners byte-for-byte using exact successful hashes.
 frozen={
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java':'6bc93e7d5a79a2e5184fb5e293f623cbbd5397662c60cc04f1a601de755a23c4',
 'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl':'fcf89ce6a70a3c8b43c795c01a8490a770635cebb21ac17b031dbe0e6680a07b',
 'app/src/main/assets/shaders/motionv2/render.glsl':'e0a438e51e12df5e6d8b53dc92892078ba7659791725cee54700869a6bc62b71',
 'app/src/main/cpp/motionv2_jpeg444_jni.cpp':'d73cd24452280958f089e9124545a81461939e8fa0c9c95272b2825942e4b43d',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightNeuralEnhancer.java':'b7595a8a347fcfe3bdf9a0225ecb393406718adf1479c2a68a38eff8d962dbcd',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java':'d5de1abf9bb42b92715fc1ec028d89d1408ecf6c4853cc95afbffc6bfe766b1e'}
 for r,h in frozen.items():req(sha(c/r)==h,'carried frozen owner '+r)
 stack=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
 sh=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
 bridge=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
 # Exact historic failures now permanent regressions.
 req('val mergedFrameCount = normalFrameCount + shadowLongFrameCount' in stack,'SHORT merged count regression')
 req('frames = frames.filter { it.role == RawBurstFrameRole.NORMAL }' in stack,'SHORT DNG-noise regression')
 req('frames[index].role != RawBurstFrameRole.HIGHLIGHT_SHORT' in stack and 'if (frame.role == RawBurstFrameRole.HIGHLIGHT_SHORT) continue' in stack,'SHORT SR evidence regression')
 req('clippedQuad(uReferenceRaw, referenceP) < 2' in sh,'multi-CFA clip proof missing')
 req('shortNeighborhoodUnclipped(shortP)' in sh,'SHORT unclipped-neighborhood proof missing')
 req('evidence < 3' in sh,'radiometric neighborhood evidence missing')
 req('mix(normalRgb.rgb, restoredShort, confidence)' in sh,'whole-RGB restore missing')
 restore=sh[sh.index('val shortRestoreRgba16f26587'):sh.index('val merge =',sh.index('val shortRestoreRgba16f26587'))]
 req(re.search(r'mix\s*\(\s*normalRgb\.[rgb]\s*,',restore) is None,'per-channel artifact regression')
 req('highlightShortAppliedToTrue2x == sabreSuperResEnabled' in bridge,'1x/true2x highlight divergence regression')
 req('if (!parameters.irisNightActive && shortFrame != null)' in bridge,'Night SHORT isolation regression')
 req('VERSION_NAME=0.9726587' in (c/'app/version.properties').read_text() and 'VERSION_BUILD=26587' in (c/'app/version.properties').read_text(),'version')
 print('PASS carried successful-26586 viewfinder/final-highlight authority and adaptive-color/render/Jin/Night owners')
 print('PASS permanent 26587 regressions: no SHORT merged/DNG/SR evidence leak; multi-CFA+unclipped+radiometric fail-closed mask')
 print('PASS permanent pink/green/cyan defense: scalar whole-RGB restore only; no per-channel substitution')
 print('PASS permanent true2x parity + Night isolation regressions')
if __name__=='__main__':main()
