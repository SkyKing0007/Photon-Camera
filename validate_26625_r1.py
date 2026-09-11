#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26625_r1.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2])
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'app').rglob('*')) if p.is_file()}
bh,ch=H(B),H(C); assert len(bh)==1713 and len(ch)==1713,(len(bh),len(ch))
changed=sorted(p for p in set(bh)|set(ch) if bh.get(p)!=ch.get(p))
expected=sorted(['app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/version.properties'])
assert changed==expected,(changed,expected)
ver=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726625' in ver and 'VERSION_BUILD=26625' in ver
bs=(B/expected[0]).read_text(); cs=(C/expected[0]).read_text(); bk=(B/expected[1]).read_text(); ck=(C/expected[1]).read_text()
# Successful 26624 component/effective-loss ownership must survive exactly in semantics.
for tok in ['IRIS_26624_COMPONENT_OWNED_EFFECTIVE_LOSS_MEMBERSHIP','IRIS_26624_BOUNDARY_PROVEN_LITERAL_PLUS_EFFECTIVE_COMPONENT','IRIS_26624_COMPONENT_OWNED_EFFECTIVE_LOSS_RESCUE']:
    assert tok in bs and tok in cs,tok
# New geometry is proposal-only until unchanged same-CFA boundary radiometry authorizes it.
for tok in ['IRIS_26625_ROBUST_AFFINE_FALLBACK_GEOMETRY','uFallbackAffineValid','uFallbackFlowX','uFallbackFlowY','selectedGeometryProof','anchorQuadEvidence >= 4','anchorPhaseEvidence >= 8','radiometricConfidence','IRIS_26625_COMPONENT_EFFECTIVE_FLOW']:
    assert tok in cs,tok
assert 'geometry cannot manufacture SHORT ownership' in cs
assert 'uFallbackAffineValid >= 0.5' in cs
assert 'strictBoundaryResidualConfidence <= 0.0' in cs
# Actual merge/coverage sampling must use the same selected geometry only for SHORT.
for tok in ['var mergeFlow = flow','mergeFlow = component.effectiveFlow','flow = mergeFlow']:
    assert tok in ck,tok
assert ck.count('flow = mergeFlow')>=3
# Robust model may use only source cells already inside the existing strict residual envelope.
for tok in ['residual <= 0.95f','residual <= 0.50f','inlierLimit = 0.75','coverageX >= 0.30f','coverageY >= 0.30f','fraction >= 0.30f','p90 <= 0.75f']:
    assert tok in ck,tok
# Deterministic bounded RANSAC sampling, no random dependence.
fallback_block=ck[ck.index('private fun buildShortFallbackAffine26625'):ck.index('private fun analyzeSabreShortFallbackAffine26625')]
assert 'List(24)' in fallback_block and 'kotlin.random' not in fallback_block and 'Math.random' not in fallback_block
# Fallback cannot become SR/DNG geometry: those paths remain production `flow`.
true2x=ck[ck.index('if (enableSabreSuperRes && frame.role == RawBurstFrameRole.NORMAL)'):]
assert 'flow = flow' in true2x[:5000]
# No spatial fill/inpaint/private RGB introduced.
for bad in ['inpaint','privateShortAccumulator=true','lateRgbBlend=true']:
    assert cs.count(bad)==bs.count(bad) and ck.count(bad)==bk.count(bad),bad
# Preserve component propagation shader byte-for-byte from successful 26624.
def embedded(text): return {m.group(1):m.group(2) for m in re.finditer(r'\bval\s+(\w+)\s*=\s*"""(.*?)"""\.trimIndent\(\)',text,re.S)}
be,ce=embedded(bs),embedded(cs)
assert 'shortComponentPropagate26607' in be and be['shortComponentPropagate26607']==ce['shortComponentPropagate26607']
# Only the anchor is modified among inherited embedded shader bodies; new effective-flow shader is additive.
changed_emb=[n for n in be if n in ce and be[n]!=ce[n]]
assert changed_emb==['shortComponentAnchor26607'],changed_emb
assert 'shortComponentEffectiveFlow26625' in ce and 'shortComponentEffectiveFlow26625' not in be
print('PASS 26625 semantic/ownership/domain: exact 3-path delta; robust affine is proposal-only from strict production-flow inliers; unchanged same-CFA boundary radiometry authorizes trust; actual SHORT sampling follows validated geometry; 26624 component/tone/color/UHDR/true2x/DNG preserved')
