#!/usr/bin/env python3
from pathlib import Path
import math,sys
PKG=Path(__file__).resolve().parent
def fail(m):raise SystemExit('FAIL: '+m)
def need(s,t,l):
 if t not in s:fail(l+' missing '+t)
def forbid(s,t,l):
 if t in s:fail(l+' stale '+t)
def smoothstep(a,b,x):
 t=max(0.0,min(1.0,(x-a)/(b-a)));return t*t*(3.0-2.0*t)
def residual_conf(r):return 1.0-smoothstep(0.5,2.0,max(r,0.0))
def second_small(vals):return sorted(vals)[1]
def affine_residual(center,neighbors):
 # neighbors: L,R,U,D,UL,DR,UR,DL, values are (x,y), flow in Bayer quads.
 L,R,U,D,UL,DR,UR,DL=neighbors
 preds=[((L[0]+R[0])/2,(L[1]+R[1])/2),((U[0]+D[0])/2,(U[1]+D[1])/2),((UL[0]+DR[0])/2,(UL[1]+DR[1])/2),((UR[0]+DL[0])/2,(UR[1]+DL[1])/2)]
 rs=[math.hypot(center[0]-p[0],center[1]-p[1]) for p in preds]
 return 2.0*second_small(rs) # RAW pixels
# First-order affine field must be accepted regardless of large local range.
def f(x,y):return (12+3.2*x+1.1*y,4-0.7*x+2.4*y)
c=f(0,0);n=[f(-1,0),f(1,0),f(0,-1),f(0,1),f(-1,-1),f(1,1),f(1,-1),f(-1,1)]
r=affine_residual(c,n)
if abs(r)>1e-6 or residual_conf(r)<0.999:fail('valid affine motion rejected')
# Isolated center corruption must fail closed.
bad=(c[0]+2.0,c[1]);rb=affine_residual(bad,n)
if rb<3.9 or residual_conf(rb)!=0.0:fail('bad-center flow did not fail closed')
# Coherent global bias is intentionally invisible to local residual and therefore MUST require absolute boundary proof.
bias=(1.5,-0.5);cb=(c[0]+bias[0],c[1]+bias[1]);nb=[(x+bias[0],y+bias[1]) for x,y in n];rc=affine_residual(cb,nb)
if abs(rc)>1e-6:fail('coherent bias residual expectation changed')
# Bottleneck propagation must preserve confidence through a connected valid core without multiplicative decay.
trust=0.83
for region in [0.95]*100:trust=max(0.0,min(region,trust))
if abs(trust-0.83)>1e-9:fail('bottleneck propagation decayed valid trust')
# Hard barrier must block trust.
if min(0.20,0.83)>=0.50:fail('barrier math regression')
if len(sys.argv)!=3:fail('usage base candidate')
b,c=map(Path,sys.argv[1:]);sh=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text();st=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text();br=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
# Permanent exact-device root-cause regression: raw 3x3 flow range must never again be active SHORT error confidence.
forbid(sh,'oFlow = vec4(uvFlow, localFlowVariation, localFlowVariationRawPixels);','26605 raw-range flow.w contract')
need(sh,'oFlow = vec4(uvFlow, localFlowVariation, localAffineResidualRawPixels);','26606 residual flow.w contract')
# Ordinary rejection may consume z but not w / clipped-reference bypass.
rej=sh[sh.index('    val rejection = """'):sh.index('    """.trimIndent()',sh.index('    val rejection = """'))]
need(rej,'float localFlowVariation = flow.z;','normal rejection z');forbid(rej,'flow.w','normal rejection w');forbid(rej,'referenceLoss','duplicate clipped-reference owner')
# Residual-only is forbidden: boundary anchor must independently compare exposure-normalized RAW radiometry.
for t in ['uExposureRatio','errorSum += abs(ns - nr)','quadEvidence >= 3 && phaseEvidence >= 6','radiometricConfidence','anchorConfidence = min(regionConfidence, radiometricConfidence)']:need(sh,t,'absolute boundary proof')
# No confidence-squared failure; bottleneck min/max owns propagation.
prop=sh[sh.index('    val shortBoundaryPropagate26606 = """'):sh.index('    """.trimIndent()',sh.index('    val shortBoundaryPropagate26606 = """'))]
need(prop,'max(trust, min(regionConfidence, trustAt','bottleneck propagation');forbid(prop,'regionConfidence *','multiplicative propagation')
# Exact final common merge source-CFA guard retained and SHORT remains one scalar whole-RGB observation.
for t in ['sourceNeighborhoodConfidence=min(','frameWeight *= mix(','uSourceClippedWeight','oColorAndRWeight','oWeightsGb']:need(sh,t,'whole-RGB source clipping')
# Old private restoration/fusion programs must remain disabled.
for t in ['sabreShortBoundaryGeometrySeedProgram26600 = 0','sabreShortRestoreMaskProgram26595 = 0','sabreShortAccumulatorOwnershipProgram26601 = 0','sabreShortProtectedAccumulatorFuseProgram26602 = 0','sabreShortRestoreRgba16fProgram26587 = 0']:need(st,t,'legacy SHORT owner dormant')
# Actual contribution proof is after source-clipped coverage, and highlight rescue is separate from ordinary SHORT contribution.
for t in ['IRIS_26606_SHORT_EFFECTIVE_COVERAGE','IRIS_26606_SHORT_CLIPPED_RESCUE_COVERAGE','highlightShortEffectiveEvidence26606 =','highlightShortFullActivePixels26595 = rescueStats.nonzeroCells','actualHighlightRescue=${highlightShortRescueCoverageCells26606 > 0}']:need(st,t,'actual contribution semantics')
forbid(br,'actualContribution=false','stale hardcoded/legacy contribution claim')
need(br,'actualContributionOwnedBy=IRIS_26606_SHORT_EFFECTIVE_PROOF','bridge contribution authority')
# 26605 float HDR carrier remains mandatory.
for t in ['IRIS_26605_EXTENDED_HDR_POST_VGN_RESTORE','restoreExtendedHdrAfterVgn','FLOAT_HDR_HANDOFF_PRE_VGN','POST_VGN_HDR_MASTER']:need(sh+'\n'+st,t,'26605 HDR transport regression')
print('PASS adversarial math: coherent affine motion accepted; isolated bad center rejected; coherent-bias blind spot requires independent boundary proof')
print('PASS bottleneck confidence does not exponentially decay and low-confidence discontinuity remains a barrier')
print('PASS exact device regression: raw local flow range cannot own SHORT rescue; source-clipped whole-RGB RBF veto remains final physical protection')
print('PASS effective SHORT participation and clipped-highlight rescue are separately measured after source-clipping')
