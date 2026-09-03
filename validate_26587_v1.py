#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
CHANGED=[
'app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/version.properties']
def fail(x):raise SystemExit('FAIL: '+x)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def amap(r):return {p.relative_to(r).as_posix():sha(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
def need(s,t,l):
 if t not in s:fail(l+' missing '+t)
def ordered(s,toks,label):
 pos=[];cur=0
 for t in toks:
  i=s.find(t,cur)
  if i<0:fail(label+' order token '+t)
  pos.append(i);cur=i+1
 if pos!=sorted(pos):fail(label+' ordering')
def main():
 if len(sys.argv)!=3:fail('usage base candidate')
 b,c=map(Path,sys.argv[1:]);a,d=amap(b),amap(c)
 if len(a)!=1708 or len(d)!=1708:fail(f'universe {len(a)}/{len(d)}')
 diff=sorted(k for k in set(a)|set(d) if a.get(k)!=d.get(k))
 if diff!=sorted(CHANGED):fail('allowlist '+repr(diff))
 v=(c/'app/version.properties').read_text();need(v,'VERSION_NAME=0.9726587','version');need(v,'VERSION_BUILD=26587','version')
 # Everything outside exact six-file scope must remain byte-identical to successful 26586 authority.
 for r,h in a.items():
  if r not in CHANGED and d.get(r)!=h:fail('protected owner '+r)
 contracts=(c/CHANGED[0]).read_text();proc=(c/CHANGED[1]).read_text();stack=(c/CHANGED[2]).read_text();sh=(c/CHANGED[3]).read_text();bridge=(c/CHANGED[4]).read_text()
 for t in ['highlightShortAdmitted','highlightShortRestoreMaskGenerated','highlightShortAppliedToTrue2x','highlightShortExposureRatio']:
  need(contracts,t,'result telemetry')
 for t in ['highlightShortIndices.size <= 1','exposure < baseExposure','addAll(highlightShortIndices)','srEvidence=NORMAL_ONLY','shortContribution=NORMAL_ACCUMULATOR_EXCLUDED']:
  need(proc,t,'Sabre admission')
 schedule=proc[proc.index('val admittedIndices = buildList {'):proc.index('val admittedSet = admittedIndices.toSet()')]
 ordered(schedule,['add(baseIndex)','frames[index].role == RawBurstFrameRole.NORMAL','frame.role == RawBurstFrameRole.SHADOW_LONG','addAll(highlightShortIndices)'],'SHORT last scheduling')
 for t in [
  'val mergedFrameCount = normalFrameCount + shadowLongFrameCount',
  'if (frame.role == RawBurstFrameRole.HIGHLIGHT_SHORT) {',
  'highlightShortTexture26587 = resolveSabreShortNativeExposure26587(',
  'highlightShortMask26587 = createTexture(',
  'renderSabreShortRestoreMask26587(',
  '} else {',
  'frames = frames.filter { it.role == RawBurstFrameRole.NORMAL }',
  'nativeHighlightAuthority26587',
  'reconstructTrue2x(',
  'reconstructionEvidence, nativeHighlightAuthority26587, exportNormalStackedDng',
  'IRIS_26587_POST_SR_RGBA16F_SHORT_PUBLICATION',
  'mergedFrameCount = mergedFrameCount',
 ]:need(stack,t,'Sabre runtime')
 # SHORT branch must close before NORMAL/LONG coverage/merge branch begins.
 short=stack.index('if (frame.role == RawBurstFrameRole.HIGHLIGHT_SHORT) {',stack.index('renderDilation(reverseWeight, frameWeight)'))
 normal_else=stack.index('} else {',short)
 for forbidden in ['renderSabreCoverage(','renderSabreShadowLongCoverage(','renderSabreMerge(','renderSabreNormalDngMerge(']:
  if forbidden in stack[short:normal_else]:fail('SHORT accumulator leak '+forbidden)
 # Normal DNG support/noise frame count must not use scheduled total.
 dng0=stack.index('IRIS_26587_MOTION_DNG_NORMAL_ONLY_SUPPORT')
 dng1=stack.index('PLog.i(',dng0)
 block=stack[dng0:dng1]
 need(block,'frameCount = normalFrameCount','DNG NORMAL support')
 need(block,'frames = frames.filter { it.role == RawBurstFrameRole.NORMAL }','DNG NORMAL noise')
 if 'frameCount = frames.size' in block:fail('SHORT leaked into DNG support count')
 # True-2x evidence must explicitly reject HIGHLIGHT_SHORT everywhere it derives temporal evidence.
 need(stack,'frames[index].role != RawBurstFrameRole.HIGHLIGHT_SHORT','SR evidence role exclusion')
 need(stack,'if (frame.role == RawBurstFrameRole.HIGHLIGHT_SHORT) continue','temporal SR short skip')
 # Shared guide is created before true2x and published as same native output only after true2x completes.
 ordered(stack,['val nativeHighlightAuthority26587 = if (highlightShortAdmitted26587)','if (enableSabreSuperRes) {','reconstructTrue2x(','IRIS_26587_POST_SR_RGBA16F_SHORT_PUBLICATION','exportedTexture = nativeHighlightAuthority26587'],'shared 1x/true2x authority')
 # Whole RGB restore shader: one scalar confidence, one vec3 mix; no channel-specific replacement outputs.
 for t in ['layout(location = 0) out float oMask;','clippedQuad(uReferenceRaw, referenceP) < 2','shortNeighborhoodUnclipped(shortP)','evidence < 3','uConsistencyThreshold','flow.z > uFlowVariationThreshold','unblocker > uUnblockerThreshold','vec3 restoredShort = texture(uShortRgb, uv).rgb * uExposureRatio;','float confidence = clamp(texture(uMask, uv).r','mix(normalRgb.rgb, restoredShort, confidence)']:
  need(sh,t,'26587 shader')
 restore=sh[sh.index('val shortRestoreRgba16f26587'):sh.index('val merge =',sh.index('val shortRestoreRgba16f26587'))]
 import re
 if re.search(r'mix\s*\(\s*normalRgb\.[rgb]\s*,',restore):fail('per-channel SHORT substitution')
 for t in ['expectedMergedFrames26587 = frames.count { it.role != RawBurstFrameRole.HIGHLIGHT_SHORT }','stacked.highlightShortAppliedToTrue2x == sabreSuperResEnabled','dngShortExcluded=true','srShortEvidenceExcluded=true']:
  need(bridge,t,'bridge proof')
 # Night owners are outside changed scope and must remain byte identical (covered above); ensure bridge forbids auxiliary in Night.
 need(bridge,'if (!parameters.irisNightActive && shortFrame != null)','Motion-only SHORT gate')
 print('PASS exact successful-26586 authority -> six-file 26587 V1 allowlist')
 print('PASS SHORT scheduled last, aligned/reconstructed separately, NORMAL accumulator/mergedFrameCount/DNG/SR evidence excluded')
 print('PASS one fail-closed scalar mask controls whole-RGB RGBA16F restore; no per-channel substitution')
 print('PASS restored native Sabre/VGN RGB is shared 1x + true-2x post-reconstruction guide authority')
 print('PASS all 1702 non-allowlisted app files byte-identical to successful 26586')
if __name__=='__main__':main()
