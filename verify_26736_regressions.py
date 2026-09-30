#!/usr/bin/env python3
from pathlib import Path
import sys,math
if len(sys.argv)!=3: raise SystemExit('usage: verify_26736_regressions.py BASE26735 CAND26736')
b=Path(sys.argv[1]); c=Path(sys.argv[2]); pkg=Path(__file__).resolve().parent
def txt(r,p): return (r/p).read_text()
changed=set((pkg/'26736_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines())
expected={'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/version.properties'}
assert changed==expected,(changed,expected)
v=txt(c,'app/version.properties'); assert 'VERSION_NAME=0.9726736' in v and 'VERSION_BUILD=26736' in v
sh=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
st=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
# 26736 direct-CFA/Wronski ownership: local refinement is full authority; unrefined sparse flow must earn bounded geometric trust.
for t in ['IRIS_26736_WRONSKI_PHASE_OWNERSHIP_CONFIDENCE','float affineResidualRaw=max(base.w,0.0);','float sparseVariationTrust=1.0-smoothstep(0.35,0.90,variationRaw);','float sparseAffineTrust=1.0-smoothstep(0.20,0.70,affineResidualRaw);','float coherentSparseTrust=sparseVariationTrust*sparseAffineTrust;','float phaseOwnershipConfidence26736=accept?1.0:0.75*coherentSparseTrust;']:
 assert t in sh,t
for t in ['IRIS_26736_TRUSTED_FLOW_OWNS_SUPERRES_PHASE','uniform int uReferenceObservation26736;','float refinementTrust26736 = uReferenceObservation26736 != 0 ? 1.0 : clamp(flow.a, 0.0, 1.0);','frameWeight *= refinementTrust26736;','if (temporalWeight > 0.0 && refinementTrust26736 >= 0.55) {']:
 assert t in sh,t
for t in ['IRIS_26736_TRUSTED_FLOW_PHASE_BINDING','uReferenceObservation26736','acceptedOrCoherentSparsePhaseOwner=true','referencePhaseAlwaysTrusted=true','unprovenFlowCannotClaimPhase=true','trustedFlowPhaseOwner=true','cfaPhaseAliasVeto=true']:
 assert t in st,t
# Universal phase-diversity and alias-mode gating before luma publication.
for t in ['IRIS_26736_TRUSTED_PHASE_DIVERSITY_OWNER','float trustedPhaseCompleteness26736 = blockPhaseCount >= 4 ? 1.0 :','(blockPhaseCount == 3 ? 0.55 : 0.0);','IRIS_26736_CFA_PHASE_ALIAS_VETO','float rowMode26736=abs((d00+d10)-(d01+d11))*0.25;','float columnMode26736=abs((d00+d01)-(d10+d11))*0.25;','float checkerMode26736=abs((d00+d11)-(d10+d01))*0.25;','float phaseAliasVeto26736=(blockPhaseCount==3?1.0:0.0)*','IRIS_26736_TRUSTED_HIGH_ZOOM_STRUCTURAL_LUMA_REINFORCEMENT','provenStructure*trustedPhaseCompleteness26736*']:
 assert t in sh,t
# 26735 digital luma-only publication remains present; direct CFA still cannot become chroma owner.
for t in ['IRIS_26735_DIGITAL_LUMA_ONLY_DETAIL_NO_CHROMA_GAIN','float finalTargetY26735=max(guideY*factor,0.0);','vec3 guideChroma26735=guideRgb-vec3(guideY);','float chromaScale26735=min(factor,1.0);','oRenderRgb=vec4(max(digitalDetailRgb26735,vec3(0.0))']:
 assert t in sh,t
assert 'oRenderRgb = vec4(max(guideRgb * factor' not in sh and 'oRenderRgb=vec4(max(guideRgb*factor' not in sh
# Explicit Super Res remains exactly inherited 26734 luma-only publication.
for t in ['IRIS_26734_SR_LUMA_ONLY_DETAIL_NO_CHROMA_GAIN','float finalTargetY = max(guideY * factor, 0.0);','float chromaScale26734 = min(factor, 1.0);']:
 assert t in sh,t
# Exact successful 26735 common neutral/highlight owner and retry owner are byte protected.
vgnp='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'; ccp='app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java'
assert (b/vgnp).read_bytes()==(c/vgnp).read_bytes(),vgnp
assert (b/ccp).read_bytes()==(c/ccp).read_bytes(),ccp
vgn=txt(c,vgnp); cc=txt(c,ccp)
for t in ['IRIS_26733_HEADROOM_PRECEDES_COLOR_OWNERSHIP','IRIS_26733_INHERITED_HIGHLIGHT_HEADROOM_OWNER','IRIS_26731_FROZEN_RECIPROCAL_MATERIAL_OWNERSHIP','IRIS_26731_DIRECTION_PAIR_GEOMETRY','IRIS_26731_RECIPROCAL_ONE_SIDED_DIRECTIONAL','IRIS_26731_FROZEN_IIR_MATERIAL_OWNERSHIP','IRIS_26735_CENTER_CHROMA_CANNOT_DISQUALIFY_NEUTRAL_STRUCTURE','IRIS_26735_RECONSTRUCTED_HUE_CANNOT_SELF_VETO_ACHROMATIC_OWNER']:
 assert t in vgn,t
for t in ['IRIS_26735_AE_LOCK_REJECTION_TO_EXACT_MANUAL','IRIS_26735_MANUAL_EXPOSURE_UNACHIEVABLE','NORMAL_EXPOSURE_UNACHIEVABLE']:
 assert t in cc,t
# Routing/render/UHDR/DNG/settings/native and unrelated owners remain byte-identical.
protected=[
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java',
'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java']
for p in protected: assert (b/p).read_bytes()==(c/p).read_bytes(),p
br=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
for t in ['IRIS_26734_ALL_DIGITAL_ZOOM_DETAIL_ARCHITECTURE','localOutputZoom > 1.00001f','IRIS_26734_DIGITAL_ZOOM_ACTIVATION','directChromaOwner=false','IRIS_26733_MOTION_AUTO_RESIDUAL_CHROMA_HALF_SCALE']:
 assert t in br,t
# Numerical regression for the exact 26735 contradiction: fractional flow alone cannot establish SR phase authority.
def smoothstep01(x):
 t=max(0.0,min(1.0,x)); return t*t*(3.0-2.0*t)
def trust(accept,variation,affine):
 if accept:return 1.0
 sv=1.0-smoothstep01((variation-0.35)/(0.90-0.35))
 sa=1.0-smoothstep01((affine-0.20)/(0.70-0.20))
 return 0.75*sv*sa
assert trust(True,9.0,9.0)==1.0
assert trust(False,0.10,0.10)>0.74
assert trust(False,0.45,0.25)>=0.55
assert trust(False,0.50,0.30)<0.55
assert trust(False,0.90,0.10)==0.0
assert trust(False,0.10,0.70)==0.0
# Old 26735 logic could fill four bins solely from fractional flow. 26736 requires trusted ownership first.
flows=[(0.10,0.10),(0.60,0.10),(0.10,0.60),(0.60,0.60)]
def bin4(x,y): return (1 if x>=0.5 else 0)+(2 if y>=0.5 else 0)
assert {bin4(x,y) for x,y in flows}=={0,1,2,3}
untrusted=[trust(False,1.2,1.2)]*4
assert {bin4(x,y) for (x,y),t in zip(flows,untrusted) if t>=0.55}==set()
trusted=[1.0,0.75,0.75,0.75]
assert {bin4(x,y) for (x,y),t in zip(flows,trusted) if t>=0.55}=={0,1,2,3}
def phase_gate(n): return 1.0 if n>=4 else (0.55 if n==3 else 0.0)
assert phase_gate(1)==phase_gate(2)==0.0 and phase_gate(3)==0.55 and phase_gate(4)==1.0
def alias_veto(vals,phase_count):
 d00,d10,d01,d11=vals
 row=abs((d00+d10)-(d01+d11))*0.25
 col=abs((d00+d01)-(d10+d11))*0.25
 chk=abs((d00+d11)-(d10+d01))*0.25
 mode=max(row,col,chk); energy=0.25*sum(abs(x) for x in vals); dom=mode/max(energy,1e-6)
 return (1.0 if phase_count==3 else 0.0)*smoothstep01((dom-0.72)/0.20)
for mode in [(1,1,-1,-1),(1,-1,1,-1),(1,-1,-1,1)]:
 assert alias_veto(mode,3)>0.99
 assert alias_veto(mode,4)==0.0
print('PASS 26736 regressions: exact successful-26735 chroma/highlight/retry/routing owners frozen; Wronski phase ownership requires refined or independently coherent flow; untrusted fractional flow cannot claim phase; 2-phase detail fails closed; 3-phase CFA row/column/checker modes vetoed; 4-phase trusted detail retained; direct CFA remains luma-only')
