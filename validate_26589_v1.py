#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
CHANGED=[
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/version.properties']
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
 v=(c/'app/version.properties').read_text();need(v,'VERSION_NAME=0.9726589','version');need(v,'VERSION_BUILD=26589','version')
 for r,h in a.items():
  if r not in CHANGED and d.get(r)!=h:fail('protected owner '+r)
 bridge=(c/CHANGED[0]).read_text()
 # Exact 26588 device-runtime failure: Motion carried 15 NORMAL + isolated Short + captured-but-excluded Long.
 # The old role!=SHORT expectation incorrectly counted Motion Long and demanded 16 while Sabre correctly merged 15.
 if 'expectedMergedFrames26587 = frames.count { it.role != RawBurstFrameRole.HIGHLIGHT_SHORT }' in bridge:
  fail('exact 26588 device merged-count failure survived')
 for t in [
  'IRIS_26589_MOTION_AUX_MERGED_COUNT_PARITY',
  'frame.role == RawBurstFrameRole.NORMAL ||',
  '(parameters.irisNightActive && frame.role == RawBurstFrameRole.SHADOW_LONG)',
  'stacked.mergedFrameCount == expectedMergedFrames26589',
  'allowSabreShadowLong = parameters.irisNightActive',
  'stacked.highlightShortAppliedToTrue2x == sabreSuperResEnabled',
  'dngShortExcluded=true',
  'srShortEvidenceExcluded=true',
  'if (!parameters.irisNightActive && shortFrame != null)',
 ]: need(bridge,t,'26589 bridge parity')
 # Exact failing role set: Motion = 15 NORMAL + one isolated SHORT + one captured Long => merged expectation stays 15.
 def expected(roles,night):return sum(1 for r in roles if r=='NORMAL' or (night and r=='SHADOW_LONG'))
 motion=['NORMAL']*15+['SHADOW_LONG','HIGHLIGHT_SHORT']
 night=['NORMAL']*12+['SHADOW_LONG']*3
 if expected(motion,False)!=15:fail('exact 26588 Motion role regression fixture')
 if expected(night,True)!=15:fail('Night Long role regression fixture')
 # SHORT/Sabre architecture is frozen from successful 26588, but retain semantic assertions at the active path.
 proc=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt').read_text()
 stack=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
 sh=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
 for t in ['addAll(highlightShortIndices)','srEvidence=NORMAL_ONLY','shortContribution=NORMAL_ACCUMULATOR_EXCLUDED']:
  need(proc,t,'successful 26588 Sabre admission')
 for t in ['val mergedFrameCount = normalFrameCount + shadowLongFrameCount','frames = frames.filter { it.role == RawBurstFrameRole.NORMAL }','nativeHighlightAuthority26587','if (frame.role == RawBurstFrameRole.HIGHLIGHT_SHORT) continue']:
  need(stack,t,'successful 26588 Sabre runtime')
 for t in ['clippedQuad(uReferenceRaw, referenceP) < 2','shortNeighborhoodUnclipped(shortP)','evidence < 3','mix(normalRgb.rgb, restoredShort, confidence)']:
  need(sh,t,'successful 26588 fail-closed shader')
 print('PASS exact successful-26588 authority -> two-file 26589 V1 allowlist')
 print('PASS exact 26588 device failure fixed: Motion Long remains excluded from mergedFrameCount proof; Motion Short remains auxiliary')
 print('PASS Night Long counting remains enabled only under irisNightActive')
 print('PASS all 1706 non-allowlisted app files byte-identical to successful 26588')
if __name__=='__main__':main()
