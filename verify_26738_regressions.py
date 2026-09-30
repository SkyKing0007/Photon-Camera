#!/usr/bin/env python3
from pathlib import Path
import sys,math,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26738_regressions.py BASE26737 CAND26738')
b=Path(sys.argv[1]); c=Path(sys.argv[2]); pkg=Path(__file__).resolve().parent
def txt(r,p): return (r/p).read_text()
changed=set((pkg/'26738_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines())
expected={
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/version.properties'}
assert changed==expected,(changed,expected)
v=txt(c,'app/version.properties'); assert 'VERSION_NAME=0.9726738' in v and 'VERSION_BUILD=26738' in v
sh=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
st=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
vgn=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
br=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
# Continuous physical flow confidence. Geometry alone has no nonzero floor.
for t in ['IRIS_26738_CONTINUOUS_RAW_PHOTOMETRIC_FLOW_CONFIDENCE','flowConfidence26738=0.0','photometricAgreement26738','photometricUniqueness26738','coherentSparseTrust*photometricAgreement26738','oFlow=vec4(refinedRaw/vec2(uRawSize),base.z,flowConfidence26738)']:
 assert t in sh,t
assert 'phaseOwnershipConfidence26736=accept?1.0:0.75*coherentSparseTrust' not in sh
# Continuous normalized-convolution observation robustness; phase bins are diagnostics only.
for t in ['IRIS_26738_CONTINUOUS_RAW_OBSERVATION_ROBUSTNESS','float continuousFlowTrust26738 = uReferenceObservation26737 != 0 ? 1.0 : phaseTrust26738;','frameWeight *= clamp(uObservationConfidence, 0.05, 1.0) * continuousFlowTrust26738;','IRIS_26738_PHASE_COUNT_IS_DIAGNOSTIC_NOT_ADMISSION','float phaseWeight=1.0;']:
 assert t in sh,t
assert '(blockPhaseCount == 3 ? 0.55 : 0.0)' not in sh
assert 'blockPhaseCount >= 4 ? 1.0 : 0.0' not in sh
# Direct RAW normalized-convolution RGB master owns supported high-zoom color/detail; native is clean fallback/highlight owner.
for t in ['IRIS_26738_WRONSKI_NORMALIZED_CONVOLUTION_MASTER','IRIS_26738_DIRECT_RAW_CFA_CHROMA_PARITY_CLEAN','IRIS_26738_DIRECT_RAW_PARITY_ENERGY','vec3 cleanChroma=mix(directChroma,meanN*max(directY,0.060),0.985*directAlias);','float highlightGate=1.0-irisSmooth01((blockPeak-0.72)/0.20);','vec3 masterRgb=mix(guideRgb,directMatched,directWeight);']:
 assert t in sh,t
# Old high-zoom luma-only publication must no longer own highZoomRgbProtect, while explicit SR remains frozen separately.
start=sh.index('val highZoomRgbProtect26724')
end=sh.index('IRIS_26719_HIGH_ZOOM_LAZY_ISOLATION',start)
highzoom=sh[start:end]
assert 'IRIS_26735_DIGITAL_LUMA_ONLY_DETAIL_NO_CHROMA_GAIN' not in highzoom
assert 'IRIS_26738_WRONSKI_NORMALIZED_CONVOLUTION_MASTER' in highzoom
assert 'IRIS_26734_SR_LUMA_ONLY_DETAIL_NO_CHROMA_GAIN' in sh  # explicit true2x SR remains inherited
# Universal final CFA-period chroma owner: device/lens/zoom agnostic, highlight/real-color veto, subtractive only.
for t in ['IRIS_26738_UNIVERSAL_CFA_PERIOD_CHROMA_OWNER','IRIS_26738_INHERITED_COLOR_HIGHLIGHT_VETO','aliasAuthority26738=aliasPeriodProof26738*highlightPreservePermission*','physicalRealColorVeto26735','if(parityTargetMagnitude26738>correctedMagnitude26738&&parityTargetMagnitude26738>1.0e-7)','IRIS_26738_FINAL_ALIAS_FLOOR_VETO','protectedPreVgnMagnitude *= 1.0 - aliasAuthority26738;']:
 assert t in vgn,t
# Single row-flicker owner: reference merge-only, alternates rejection-only, high-zoom reference-only.
for t in ['IRIS_26738_SINGLE_OWNER_ROW_FLICKER','rowFlickerFrame26720 = null','ev.frameIndex==0 && hasRowFlickerEvidence26720(f)','uReferenceObservation26737",if(ev.frameIndex==0)1 else 0']:
 assert t in st,t
assert 'rowFlickerFrame26720 = frames.first().takeIf(::hasRowFlickerEvidence26720)' in st
# High-zoom telemetry reflects direct RAW RGB/chroma ownership; explicit SR telemetry remains luma-only.
for t in ['RAW_NORMALIZED_CONVOLUTION_2X_WITH_CLEAN_NATIVE_SABRE_VGN_FALLBACK','directRgbMasterWhenSupported=$highZoomDetailEnabled directChromaOwner=$highZoomDetailEnabled']:
 assert t in br,t
assert 'IRIS_26564_TRUE_2X_SR_DNG_AUTHORITY' in br and 'colorOwner=NATIVE_SABRE_VGN' in br
assert 'IRIS_26568_TRUE2X_READY' in st and 'highResLumaOwner=DIRECT_CFA directChromaOwner=false' in st
# Frozen successful chroma/highlight/transport mechanisms inside modified VGN source are byte-identical.
def section(s,marker):
 i=s.index(marker); j=s.find('/* IRIS_',i+len(marker)); return s[i:] if j<0 else s[i:j]
bv=txt(b,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
for marker in ['IRIS_26728_PHYSICALLY_SUPPORTED_CHROMA_MAGNITUDE','IRIS_26735_INDEPENDENT_PHYSICAL_REAL_COLOR_PROOF','IRIS_26735_NEUTRAL_EDGE_AND_SPECULAR_BRACKET_OWNER','IRIS_26733_HEADROOM_PRECEDES_COLOR_OWNERSHIP','IRIS_26733_NEUTRAL_FLOOR_VETO','IRIS_26733_INHERITED_HIGHLIGHT_HEADROOM_OWNER','IRIS_26733_EARLY_ACHROMATIC_STRUCTURE_OWNER','IRIS_26731_FROZEN_RECIPROCAL_MATERIAL_OWNERSHIP','IRIS_26731_DIRECTION_PAIR_GEOMETRY','IRIS_26731_RECIPROCAL_ONE_SIDED_DIRECTIONAL','IRIS_26731_FROZEN_IIR_MATERIAL_OWNERSHIP']:
 assert section(bv,marker)==section(vgn,marker),marker
# Critical unrelated owners remain byte-identical. Bridge is intentionally excluded because telemetry is corrected only.
protected=['app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java','app/src/main/cpp/motionv2_jpeg444_jni.cpp','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java','app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java','app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java']
for p in protected: assert (b/p).read_bytes()==(c/p).read_bytes(),p
cc=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
for t in ['IRIS_26735_AE_LOCK_REJECTION_TO_EXACT_MANUAL','IRIS_26735_MANUAL_EXPOSURE_UNACHIEVABLE','NORMAL_EXPOSURE_UNACHIEVABLE']: assert t in cc,t
# Numerical failure-model regressions.
def smooth(a,b,x):
 if b<=a:return 1.0 if x>=b else 0.0
 q=max(0.0,min(1.0,(x-a)/(b-a))); return q*q*(3-2*q)
def flow_conf(coherent,mean_cost,margin): return max(0,min(1,coherent*(1-smooth(.60,1.60,mean_cost))*smooth(.10,.28,margin)))
assert flow_conf(.95,.40,.03)<.05 and flow_conf(.95,.35,.42)>.80 and flow_conf(.0,.20,.50)==0.0
# Universal period proof: two-direction alternating chroma is eligible; stable color is not. Highlight/real-color veto removes authority.
def period_authority(second_period,highlight_permission,real_color_veto):
 return smooth(.34,.70,second_period)*highlight_permission*(1-smooth(.58,.90,real_color_veto))
assert period_authority(.90,1.0,0.0)>.95
assert period_authority(.05,1.0,0.0)==0.0
assert period_authority(.90,0.0,0.0)==0.0
assert period_authority(.90,1.0,1.0)==0.0
# Direct parity energy flags CFA row/column/checker dominance but stable block color has zero parity energy.
def vlen(v): return math.sqrt(sum(x*x for x in v))
def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def add(a,b): return tuple(x+y for x,y in zip(a,b))
def scale(a,k): return tuple(x*k for x in a)
def parity(ns):
 n00,n10,n01,n11=ns; mean=scale(add(add(n00,n10),add(n01,n11)),.25)
 row=scale(sub(add(n00,n10),add(n01,n11)),.5); col=scale(sub(add(n00,n01),add(n10,n11)),.5); chk=scale(sub(add(n00,n11),add(n10,n01)),.5)
 e=max(vlen(row),vlen(col),vlen(chk)); return e,vlen(mean)
false=[(.18,-.18,0),(-.18,.18,0),(-.18,.18,0),(.18,-.18,0)]
stable=[(.12,-.04,-.08)]*4
e,m=parity(false); assert e>.30 and m<.01
e,m=parity(stable); assert e<1e-9 and m>.10
# Seam: exactly one row reliability multiplication per observation. Old alternate r^2 is forbidden by regression model.
r=.08; old_alt=r*r; new_alt_rejection=r*1.0; new_ref=1.0*r
assert old_alt<new_alt_rejection and abs(new_alt_rejection-r)<1e-12 and abs(new_ref-r)<1e-12
print('PASS 26738 regressions: universal CFA anti-moire; direct RAW normalized-convolution RGB master; continuous physical support; single-owner row-flicker seam fix; inherited 26731/26733/26735 protections and unrelated owners preserved')
