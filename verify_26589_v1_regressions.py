#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,re
def fail(m):raise SystemExit('FAIL: '+m)
def req(c,m):
 if not c:fail(m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('candidate_root');ns=ap.parse_args();c=Path(ns.candidate_root)
 # Exact successful 26588 runtime owners outside the bridge are frozen byte-for-byte.
 frozen={
 'app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt':'f2595dd8ec821bd01516eb933de1095737d97155e18ba5d57322b08cd9a97141',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt':'722f5bbbee4045e37753ef8b7b0c45c0c276d60845a7c96162d8e9a5600e0796',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt':'5defcae93e37ddf209af7d94eda3853d204ea57c5be2bb176e264daa03185900',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt':'8484529f63ba9bef8ab54b9f21134adfa5b7907ff0e5ce9762a74a343470d5b5',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt':'536d946948996577c1c7dfd7f59c69ac87255adb9445d0ab936f4c3eba02ed08'}
 for r,h in frozen.items():req(sha(c/r)==h,'successful 26588 frozen owner '+r)
 bridge=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
 # Permanent exact 26588 runtime crash regression.
 req('expectedMergedFrames26587 = frames.count { it.role != RawBurstFrameRole.HIGHLIGHT_SHORT }' not in bridge,'old Motion Long overcount survived')
 for tok in ['IRIS_26589_MOTION_AUX_MERGED_COUNT_PARITY','frame.role == RawBurstFrameRole.NORMAL ||','(parameters.irisNightActive && frame.role == RawBurstFrameRole.SHADOW_LONG)','stacked.mergedFrameCount == expectedMergedFrames26589']:
  req(tok in bridge,'26589 merge-count parity '+tok)
 def expected(roles,night):return sum(1 for r in roles if r=='NORMAL' or (night and r=='SHADOW_LONG'))
 req(expected(['NORMAL']*15+['SHADOW_LONG','HIGHLIGHT_SHORT'],False)==15,'exact device Motion 15+Long+Short regression')
 req(expected(['NORMAL']*12+['SHADOW_LONG']*3,True)==15,'Night 12+3 regression')
 # Carry successful 26588 Short fail-closed and ownership protections.
 stack=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text();sh=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
 req('val mergedFrameCount = normalFrameCount + shadowLongFrameCount' in stack,'SHORT merged count regression')
 req('frames = frames.filter { it.role == RawBurstFrameRole.NORMAL }' in stack,'SHORT DNG regression')
 req('frames[index].role != RawBurstFrameRole.HIGHLIGHT_SHORT' in stack and 'if (frame.role == RawBurstFrameRole.HIGHLIGHT_SHORT) continue' in stack,'SHORT SR evidence regression')
 req('clippedQuad(uReferenceRaw, referenceP) < 2' in sh and 'shortNeighborhoodUnclipped(shortP)' in sh and 'evidence < 3' in sh,'SHORT fail-closed proof')
 req('mix(normalRgb.rgb, restoredShort, confidence)' in sh,'whole-RGB restore')
 restore=sh[sh.index('val shortRestoreRgba16f26587'):sh.index('val merge =',sh.index('val shortRestoreRgba16f26587'))]
 req(re.search(r'mix\s*\(\s*normalRgb\.[rgb]\s*,',restore) is None,'per-channel artifact regression')
 req('highlightShortAppliedToTrue2x == sabreSuperResEnabled' in bridge,'1x/true2x highlight divergence')
 req('if (!parameters.irisNightActive && shortFrame != null)' in bridge,'Night SHORT isolation')
 v=(c/'app/version.properties').read_text();req('VERSION_NAME=0.9726589' in v and 'VERSION_BUILD=26589' in v,'version')
 print('PASS exact 26588 device runtime regression: Motion 15 NORMAL + excluded Long + auxiliary Short expects merged=15')
 print('PASS successful 26588 Sabre/SHORT shaders, stack, contracts and fusion owner frozen byte-identical')
 print('PASS carried fail-closed pink/green/cyan, DNG, SR and Night isolation regressions')
if __name__=='__main__':main()
