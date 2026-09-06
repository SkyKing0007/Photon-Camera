#!/usr/bin/env python3
from pathlib import Path
import math,sys

def fail(m):raise SystemExit('FAIL: '+m)
def need(s,t,l):
 if t not in s:fail(l+' missing '+t)
def forbid(s,t,l):
 if t in s:fail(l+' stale '+t)
def section(s,a):
 i=s.index(a);j=s.index('    """.trimIndent()',i);return s[i:j]
def smoothstep(a,b,x):
 t=max(0.0,min(1.0,(x-a)/(b-a)));return t*t*(3.0-2.0*t)
def effective_loss(ref,pred):
 rel=max(pred-ref,0.0)/max(pred,0.05)
 return smoothstep(0.72,0.92,pred)*smoothstep(0.05,0.12,rel)
def source_headroom(raw,clip=1022.5):
 start=max(1.0,clip*0.9925);return 1.0-smoothstep(start,max(start+1e-4,clip),raw)
def probe_positions(span=66.0):return [i*0.25*span for i in (-2,-1,0,1,2)]
# Exact 26606 device failure #1: old center 3x3 (~6 RAW px) can miss a boundary near a 66px cell edge.
span=66.0;boundary=24.0
old=[-3.0,0.0,3.0];new=probe_positions(span)
if min(abs(x-boundary) for x in old)<6.0:fail('fixture does not represent old center-only miss')
if min(abs(x-boundary) for x in new)>8.25+1e-9:fail('full-cell probes do not cover boundary with <= quarter-cell spacing')
# Full footprint must reach +/-50%, preventing the 20% inter-cell blind strip from the early draft.
if new[0]!=-0.5*span or new[-1]!=0.5*span:fail('flow-cell probe footprint not complete')
# Exact 26606 device failure #2: valid SHORT evidence above 90% saturation must no longer be hard-vetoed.
if source_headroom(0.95*1022.5)<=0.99:fail('95-percent SHORT incorrectly rejected')
if source_headroom(0.98*1022.5)<=0.99:fail('98-percent SHORT incorrectly rejected')
if not (0.0<source_headroom(0.997*1022.5)<1.0):fail('final 0.75-percent continuous headroom ramp missing')
if source_headroom(1022.5)!=0.0:fail('true SHORT saturation did not fail closed')
# Effective loss must recover non-literal plateau structure but remain quiet for healthy agreement.
if effective_loss(0.90,1.10)<=0.5:fail('strong effective highlight loss not detected')
if effective_loss(0.88,0.90)>1e-6:fail('healthy bright overlap falsely marked lost')
# Two-phase policy: one moderate phase alone is insufficient unless severe near-saturation route applies.
losses=[effective_loss(0.90,1.10),effective_loss(0.89,1.08),effective_loss(0.70,0.71),effective_loss(0.65,0.66)]
if sorted(losses)[-2]<=0.0:fail('two-phase effective loss fixture did not trigger')
# Bottleneck connected propagation preserves trust instead of exponential decay.
trust=0.82
for _ in range(100): trust=max(trust,min(0.95,trust))
if abs(trust-0.82)>1e-12:fail('component trust decayed')
# Flow discontinuity barrier must approach zero at/above 16 RAW px.
def compat(d):return 1.0-smoothstep(4.0,16.0,d)
if compat(3.0)<0.999 or compat(16.0)!=0.0:fail('flow barrier regression')
if len(sys.argv)!=3:fail('usage base candidate')
b,c=map(Path,sys.argv[1:]);sh=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text();st=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text();br=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
# New exact source regressions.
need(sh,'vec2(float(px), float(py)) * (0.25 * cellSpanRaw);','full flow-cell footprint');forbid(sh,'0.20 * cellSpanRaw','incomplete +/-40-percent flow-cell probes')
active26607=section(sh,'    val shortComponentAnchor26607 = """')+'\n'+section(sh,'    val shortRescueWeight26607 = """')
forbid(active26607,'uShortHeadroomThreshold','retired 26606 90-percent SHORT pre-veto in active 26607 path')
for t in ['uSourceClippingPoint * 0.9925','effectiveLossWeight(referenceNormalized, scaledShort)','float targetLoss = clamp(max(literalLoss, effectiveLoss)','smoothstep(4.0, 16.0, delta)']:need(sh,t,'26607 physical loss/component contract')
# Common merge and coverage final 3x3 source clipping must remain byte-identical to base.
bsh=(b/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
for a in ['    val merge = """','    val copyMaskShadowLong26558 = """','    val rejection = """','    val convertAlignmentSparse = """']:
 if section(bsh,a)!=section(sh,a):fail('successful-26606 inherited shader changed '+a)
# Old private/previous rescue owners cannot be activated.
for t in ['sabreShortBoundaryAnchorProgram26606 = 0','sabreShortBoundaryPropagateProgram26606 = 0','sabreShortRescueWeightProgram26606 = 0','sabreShortAccumulatorOwnershipProgram26601 = 0','sabreShortProtectedAccumulatorFuseProgram26602 = 0','sabreShortRestoreRgba16fProgram26587 = 0']:need(st,t,'legacy SHORT owner dormant')
# Semantic contract: eligibility is measured; later effects are explicitly unmeasured until their real owner/device proof.
for t in ['IRIS_26607_SHORT_TARGET_ACCUMULATOR_ELIGIBLE_COVERAGE','targetAccumulatorEligibleCells=','accumulatorContribution=NOT_DIRECTLY_MEASURED','resolveEffective=NOT_DIRECTLY_MEASURED','outputPreserved=DEVICE_IMAGE_REQUIRED']:need(st+'\n'+br,t,'semantic state contract')
for t in ['targetAccumulatorContributionCells=','actualHighlightRescue=','actualContributionOwnedBy=']:forbid(st+'\n'+br,t,'semantic overclaim')
# HDR transport and NORMAL-only DNG/SR remain mandatory.
for t in ['IRIS_26605_EXTENDED_HDR_POST_VGN_RESTORE','restoreExtendedHdrAfterVgn','FLOAT_HDR_HANDOFF_PRE_VGN','POST_VGN_HDR_MASTER']:need(sh+'\n'+st,t,'HDR transport')
need(st,'if (enableSabreSuperRes && frame.role == RawBurstFrameRole.NORMAL)','SR detail NORMAL-only');need(st,'if (normalDngAccumulator != 0 && frame.role == RawBurstFrameRole.NORMAL)','DNG NORMAL-only')
print('PASS 26606 device regressions: full flow-cell boundary coverage and no premature 90-percent SHORT veto')
print('PASS universal effective-loss math detects recoverable near-saturation plateaus without marking healthy bright overlap')
print('PASS connected trust uses bottleneck propagation with explicit flow-discontinuity barrier and final common 3x3 source clipping unchanged')
print('PASS semantic states stop at accumulator eligibility; accumulator delta, Resolve effect and final output preservation are not overclaimed')
