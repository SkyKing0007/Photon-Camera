#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
CHANGED=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
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
 v=(c/'app/version.properties').read_text();need(v,'VERSION_NAME=0.9726590','version');need(v,'VERSION_BUILD=26590','version')
 for r,h in a.items():
  if r not in CHANGED and d.get(r)!=h:fail('protected owner '+r)
 sh=(c/CHANGED[0]).read_text();stack=(c/CHANGED[1]).read_text()
 for t in [
  'IRIS_26590_NEAR_CLIP_FAIL_CLOSED_SHORT_RESTORE_MASK',
  'uniform float uReferenceNearClipThreshold;',
  'uniform float uShortHeadroomThreshold;',
  'referenceNearClipQuad(referenceP) < 2',
  'shortNeighborhoodHasHeadroom(shortP)',
  'sensorClippedQuad(uReferenceRaw, rp) != 0',
  'sensorClippedQuad(uShortRaw, sp) != 0',
  'shortWeight < uShortWeightThreshold',
  'coverage < uNormalCoverageThreshold',
  'flow.z > uFlowVariationThreshold',
  'unblocker > uUnblockerThreshold',
  'evidence < 3',
  'meanError >= uConsistencyThreshold',
  'vec2 shortUv = clamp(referenceUv + flow.xy',
  'mix(normalRgb.rgb, restoredShort, confidence)',
  'val shortRestoreMaskProbe26590',
 ]:need(sh,t,'26590 short mask')
 for t in [
  'width, height, GLES30.GL_R8, GLES30.GL_NEAREST',
  'uniform1f(program, "uReferenceNearClipThreshold", 0.98f)',
  'uniform1f(program, "uShortHeadroomThreshold", 0.90f)',
  'IRIS_26590_SHORT_MASK_EFFECT',
  'sameSabreFlow=true wholeRgb=true maskFilter=NEAREST',
  'probeSabreShortRestoreMask26590(highlightShortMask26587)',
  'flow = flow,',
  'covariance = currentCovariance,',
  'nativeHighlightAuthority26587',
  'val mergedFrameCount = normalFrameCount + shadowLongFrameCount',
  'frames = frames.filter { it.role == RawBurstFrameRole.NORMAL }',
 ]:need(stack,t,'26590 stack/ownership')
 restore=sh[sh.index('val shortRestoreRgba16f26587'):sh.index('val merge =',sh.index('val shortRestoreRgba16f26587'))]
 if re.search(r'mix\s*\(\s*normalRgb\.[rgb]\s*,',restore):fail('per-channel SHORT replacement')
 # Exact threshold semantics: black-subtracted 0.98, not raw-code 1023-only admission.
 if 'referenceNearClipQuad(referenceP) < 2' not in sh or 'uWhiteLevel - 0.5' not in sh:fail('nearclip/sensorclip split')
 print('PASS exact successful-26589 authority -> three-file 26590 micro allowlist')
 print('PASS near-clip admission matches 0.98 black-subtracted capture concept while sensor-clipped consistency guard remains separate')
 print('PASS same Sabre flow/covariance/rejection geometry; nearest native mask; scalar whole-RGB fail-closed NORMAL fallback')
 print('PASS all 1705 non-allowlisted app files byte-identical to successful 26589')
if __name__=='__main__':main()
