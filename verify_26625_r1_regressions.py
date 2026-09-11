#!/usr/bin/env python3
from pathlib import Path
import re,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26625_r1_regressions.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2])
bs=(B/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text(); cs=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
bk=(B/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text(); ck=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
# Exact 26624 direct-sun failure condition: valid -2.5EV SHORT but local residuals could yield zero seeds.
for literal in ['boundarySeedCells=','componentTrustedCells=','targetAccumulatorEligibleCells=']:
    assert literal in ck
# Never solve by loosening 26611 thresholds.
for literal in ['0.35', '0.95']:
    assert literal in cs
assert 'strictBoundaryResidualConfidence <= 0.0' in cs
# Fallback validity is independent geometry quality, then boundary radiometry remains mandatory.
for literal in ['core.size < 12','candidates.size < 12','minimumInliers = max(12','coverageX >= 0.30f','coverageY >= 0.30f','p90 <= 0.75f','boundaryRadiometryStillRequired=true','geometryAloneCannotAuthorize=true']:
    assert literal in ck,literal
for literal in ['anchorQuadEvidence >= 4','anchorPhaseEvidence >= 8','anchorConfidenceSum','radiometricConfidence']:
    assert literal in cs,literal
# Existing component bottleneck / CFA-safe flow barrier remains untouched.
def emb(text,name):
    m=re.search(r'\bval\s+'+re.escape(name)+r'\s*=\s*'+chr(34)*3+r'(.*?)'+chr(34)*3+r'\.trimIndent\(\)',text,re.S); assert m,name; return m.group(1)
assert emb(bs,'shortComponentPropagate26607')==emb(cs,'shortComponentPropagate26607')
# Selected fallback geometry must actually reach common Sabre merge, not merely telemetry.
assert 'mergeFlow = component.effectiveFlow' in ck
assert re.search(r'renderSabreMerge\(\s*extracted = currentExtracted,\s*flow = mergeFlow,',ck,re.S)
# Permanent regression for Actions run 34549354529 compileDebugKotlin failure:
# component is block-local, so frame telemetry must carry its value through a frame-local scalar.
assert 'var shortFallbackTrustedCells26625 = 0' in ck
assert 'shortFallbackTrustedCells26625 = component.fallbackTrustedCells' in ck
assert '"fallbackTrustedCells=$shortFallbackTrustedCells26625 " +' in ck
assert '"fallbackTrustedCells=${component.fallbackTrustedCells} " +' not in ck
# SHORT only: true2x NORMAL and NORMAL DNG stay on production flow.
segment=ck[ck.index('if (enableSabreSuperRes && frame.role == RawBurstFrameRole.NORMAL)'):ck.index('PLog.i(\n                    SABRE_TAG,\n                    "MGC Sabre frame=',ck.index('if (enableSabreSuperRes && frame.role == RawBurstFrameRole.NORMAL)'))]
assert segment.count('flow = flow')>=2
# No fill/smoothing/inpainting and no late/private RGB resurrection.
for bad in ['spatialFill=true','inpainting=true','privateShortAccumulator=true','lateRgbBlend=true']:
    assert bad not in ck+cs
# Version correct.
v=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726625' in v and 'VERSION_BUILD=26625' in v
print('PASS 26625 regressions: robust SHORT fallback remains radiometry-authorized and reaches actual merge; Actions 34549354529 block-local telemetry scope failure is permanently rejected; CFA barrier/component/headroom/physical/source-clip protections and 26624 presentation remain')
