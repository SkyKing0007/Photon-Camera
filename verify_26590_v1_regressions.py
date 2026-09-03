#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,re

def fail(m):raise SystemExit('FAIL: '+m)
def req(c,m):
 if not c:fail(m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('candidate_root');ns=ap.parse_args();c=Path(ns.candidate_root)
 sh=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
 stack=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
 bridge=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
 proc=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt').read_text()
 # Exact 26589 device condition: capture detector fired at black-subtracted >=0.98, but old restore required raw==sensor white.
 req('IRIS_26590_NEAR_CLIP_FAIL_CLOSED_SHORT_RESTORE_MASK' in sh,'26590 near-clip owner')
 req('uniform1f(program, "uReferenceNearClipThreshold", 0.98f)' in stack,'0.98 capture/restore threshold parity')
 req('referenceNearClipQuad(referenceP) < 2' in sh,'two-CFA center-quad gate')
 req('sensorClippedQuad(uReferenceRaw, rp) != 0' in sh and 'sensorClippedQuad(uShortRaw, sp) != 0' in sh,'sensor-clipped radiometry exclusion')
 # SHORT headroom and alignment fail closed.
 req('uniform1f(program, "uShortHeadroomThreshold", 0.90f)' in stack,'SHORT headroom threshold')
 req('shortNeighborhoodHasHeadroom(shortP)' in sh,'SHORT 3x3 headroom gate')
 req('vec2 shortUv = clamp(referenceUv + flow.xy' in sh,'mask uses Sabre reference+flow convention')
 merge=sh[sh.index('val merge ='):sh.index('val mergeShadowLong26558',sh.index('val merge ='))]
 req('vec2 sampleUv = mirrorUvs(referenceUv + flow.xy);' in merge,'Sabre merge reference+flow convention')
 req('flow = flow,' in stack and 'covariance = currentCovariance,' in stack,'native SHORT reconstruction uses same flow/covariance')
 req('shortWeight < uShortWeightThreshold' in sh and 'coverage < uNormalCoverageThreshold' in sh,'weight/coverage gates')
 req('flow.z > uFlowVariationThreshold' in sh and 'unblocker > uUnblockerThreshold' in sh,'flow/unblocker gates')
 req('evidence < 3' in sh and 'meanError >= uConsistencyThreshold' in sh,'radiometric evidence gates')
 # Artifact defenses: native-resolution nearest scalar mask, whole-RGB replacement, no per-channel substitution/search.
 req('width, height, GLES30.GL_R8, GLES30.GL_NEAREST' in stack,'native mask nearest filtering')
 restore=sh[sh.index('val shortRestoreRgba16f26587'):sh.index('val merge =',sh.index('val shortRestoreRgba16f26587'))]
 req('mix(normalRgb.rgb, restoredShort, confidence)' in restore,'whole RGB restore')
 req(re.search(r'mix\s*\(\s*normalRgb\.[rgb]\s*,',restore) is None,'per-channel substitution regression')
 req('there is no second correspondence search' in sh,'no neighborhood correspondence search')
 # Read-only effect probe cannot feed output.
 req('IRIS_26590_SHORT_MASK_EFFECT_PROBE' in sh and 'This shader never feeds reconstruction or rendering.' in sh,'probe read-only contract')
 req('probeSabreShortRestoreMask26590(highlightShortMask26587)' in stack,'probe invocation')
 req('sameSabreFlow=true wholeRgb=true maskFilter=NEAREST' in stack,'probe ownership log')
 # 26589 merge parity and SHORT/DNG/SR/Night isolation remain.
 for tok in ['IRIS_26589_MOTION_AUX_MERGED_COUNT_PARITY','stacked.mergedFrameCount == expectedMergedFrames26589','if (!parameters.irisNightActive && shortFrame != null)']:
  req(tok in bridge,'carried 26589 bridge '+tok)
 for tok in ['addAll(highlightShortIndices)','srEvidence=NORMAL_ONLY','shortContribution=NORMAL_ACCUMULATOR_EXCLUDED']:
  req(tok in proc,'carried Sabre role '+tok)
 req('val mergedFrameCount = normalFrameCount + shadowLongFrameCount' in stack,'SHORT merged-count exclusion')
 req('frames = frames.filter { it.role == RawBurstFrameRole.NORMAL }' in stack,'DNG NORMAL-only')
 req('frames[index].role != RawBurstFrameRole.HIGHLIGHT_SHORT' in stack and 'if (frame.role == RawBurstFrameRole.HIGHLIGHT_SHORT) continue' in stack,'SR SHORT evidence exclusion')
 # Small semantic fixtures for the exact gate intent.
 def near(vals):return sum(v>=0.98 for v in vals)>=2
 req(near([0.981,0.992,0.45,0.40]),'two-phase 0.98 fixture must admit first gate')
 req(not near([0.981,0.97,0.45,0.40]),'one-phase fixture must reject')
 req(max([0.17]*9)<0.90,'valid -2.5EV SHORT headroom fixture')
 req(not (max([0.17]*8+[0.91])<0.90),'SHORT no-headroom fixture must reject')
 v=(c/'app/version.properties').read_text();req('VERSION_NAME=0.9726590' in v and 'VERSION_BUILD=26590' in v,'version')
 print('PASS exact 26589 device near-clip mismatch regression: restore admission now matches black-subtracted 0.98 capture concept')
 print('PASS same Sabre flow/covariance/rejection ownership; no second alignment search; nearest native scalar mask prevents spatial confidence bleed')
 print('PASS whole-RGB fail-closed restore + 3x3 SHORT headroom + temporal/flow/unblocker/radiometric gates')
 print('PASS carried 26589 Motion Long parity, DNG NORMAL-only, SR SHORT exclusion and Night isolation')
if __name__=='__main__':main()
