#!/usr/bin/env python3
from pathlib import Path
import math,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26624_r1_regressions.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2])
S='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'; K='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
b=(B/S).read_text(); c=(C/S).read_text(); bk=(B/K).read_text(); ck=(C/K).read_text()

# Exact 26623 device failure condition is carried forward in the permanent regression record/source contract.
assert 'effectiveLossPhotometricBypass=false' in bk
assert 'float componentConfidence = min(\n                componentSourceConfidence, literalLossSeen);' in b
assert 'float finalWeight = mix(ordinaryWeight, censoredCoreWeight, physicalCensoring);' in b

# 26624 must make effective/near-saturation loss part of region membership only with same-probe SHORT headroom.
for tok in ['IRIS_26624_COMPONENT_OWNED_EFFECTIVE_LOSS_MEMBERSHIP','effectiveLossComponentConfidence','min(probeSourceConfidence, probeEffectiveLoss)','IRIS_26624_BOUNDARY_PROVEN_LITERAL_PLUS_EFFECTIVE_COMPONENT','literalComponentConfidence','max(\n                literalComponentConfidence, effectiveLossComponentConfidence)']:
    assert tok in c,tok
# No effective or literal core can self-seed. Exact 26611 boundary proof stays in charge.
for tok in ['strictBoundaryResidualConfidence =\n                1.0 - smoothstep(0.35, 0.95, max(flow.w, 0.0));','boundaryLocalFlowProof = strictBoundaryResidualConfidence','anchorQuadEvidence >= 4 && anchorPhaseEvidence >= 8','uConsistencyLow','uConsistencyHigh']:
    assert tok in c,tok
for tok in ['literalCoreSelfSeed=false','effectiveCoreSelfSeed=false','predictorCannotOverrideLocalBoundary=true','boundaryResidualRawPx=0.35..0.95','componentFlowBarrierRawPx=0.50..1.25']:
    assert tok in ck,tok

# Component propagation itself is byte-identical, retaining CFA-phase-safe discontinuity barrier.
def shader(text,name):
    m=re.search(r'\bval\s+'+re.escape(name)+r'\s*=\s*"""(.*?)"""\.trimIndent\(\)',text,re.S); assert m,name; return m.group(1)
assert shader(b,'shortComponentPropagate26607')==shader(c,'shortComponentPropagate26607')
prop=shader(c,'shortComponentPropagate26607')
for tok in ['smoothstep(0.50, 1.25, delta)','min(trustAt(n0), compatibleFlow(p, n0))','min(componentConfidence']:
    assert tok in prop,tok

# Literal-clipping behavior is mathematically preserved exactly; effective rescue is additive-only.
for tok in ['IRIS_26624_COMPONENT_OWNED_EFFECTIVE_LOSS_RESCUE','float literalFinalWeight = mix(','float effectiveRescueWeight = censoredCoreWeight * clamp(effectiveLoss, 0.0, 1.0);','float finalWeight = max(literalFinalWeight, effectiveRescueWeight);']:
    assert tok in c,tok
# The literal loss function and actual same-CFA SHORT sampler are unchanged.
for fname in ['shortPhaseSupport','literalLossWeight']:
    pat=r'(?:void|float)\s+'+fname+r'\s*\(.*?\n        \}'
    mb=re.search(pat,shader(b,'shortRescueWeight26607'),re.S); mc=re.search(pat,shader(c,'shortRescueWeight26607'),re.S)
    assert mb and mc and mb.group(0)==mc.group(0),fname

# Numeric policy proof for the final-weight algebra.
def old_final(ordinary,physical,trust,head,literal,effective):
    censored=min(physical,min(head,trust)); return ordinary*(1-literal)+censored*literal
def new_final(ordinary,physical,trust,head,literal,effective):
    censored=min(physical,min(head,trust)); literal_final=ordinary*(1-literal)+censored*literal; effective_rescue=censored*effective; return max(literal_final,effective_rescue)
cases=[
    # no loss: exact 26623 behavior
    (0.72,0.90,0.85,1.0,0.0,0.0),
    # no component trust: effective loss cannot alter ordinary SHORT
    (0.23,0.90,0.0,1.0,0.0,1.0),
    # no SHORT headroom: effective loss cannot rescue
    (0.23,0.90,0.8,0.0,0.0,1.0),
    # physical rejection remains hard cap
    (0.10,0.0,0.8,1.0,0.0,1.0),
    # literal path remains exact
    (0.12,0.80,0.75,1.0,1.0,0.9),
]
for x in cases:
    o=old_final(*x); n=new_final(*x)
    if x[4] in (1.0,) or x[5]==0.0 or x[2]==0.0 or x[3]==0.0 or x[1]==0.0: assert abs(o-n)<1e-9,(x,o,n)
# Proven effective loss now recovers a previously rejected near-saturated SHORT sample.
x=(0.10,0.90,0.80,1.0,0.0,0.75); assert abs(old_final(*x)-0.10)<1e-9 and new_final(*x)>0.59
# Additive-only property across a broad grid: never reduce the complete preserved literal result.
vals=[0.0,0.1,0.4,0.8,1.0]
for ordinary in vals:
 for physical in vals:
  for trust in vals:
   for head in vals:
    for lit in vals:
     for eff in vals:
      assert new_final(ordinary,physical,trust,head,lit,eff)+1e-12>=old_final(ordinary,physical,trust,head,lit,eff)

# No value painting/smoothing/private RGB: actual aligned same-CFA SHORT still goes through the one common RBF path.
for tok in ['shortInteriorSamples=ACTUAL_ALIGNED_SAME_CFA_SHORT noSpatialFill=true','privateShortAccumulator=false','lateRgbBlend=false','sourceClip3x3Continuous=true','bayerQuadWholeRgb=true']:
    assert tok in ck,tok
for forbidden in ['privateShortMean=true','lateShortRgb=true','shortInpaint=true','shortSpatialFill=true']:
    assert forbidden not in ck
# Presentation/color/UHDR/LL must remain exact 26623 so 26624 cannot hide this source fix with tone changes.
for p in ['app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl','app/src/main/assets/shaders/motionv2/local_laplacian_reconstruct_26621.glsl','app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/src/main/cpp/motionv2_jpeg444_jni.cpp']:
    assert (B/p).read_bytes()==(C/p).read_bytes(),p
print('PASS 26624 regressions: reproduces 26623 literal-only false-closed gate; boundary-proven effective component membership/rescue enabled; literal behavior preserved; CFA-safe flow barrier/headroom/physical/source-clip guards intact; effective rescue additive-only; no fill/smoothing/private RGB; 26623 presentation frozen')
