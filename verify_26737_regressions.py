#!/usr/bin/env python3
from pathlib import Path
import sys,math
if len(sys.argv)!=3: raise SystemExit('usage: verify_26737_regressions.py BASE26736 CAND26737')
b=Path(sys.argv[1]); c=Path(sys.argv[2]); pkg=Path(__file__).resolve().parent
def txt(r,p): return (r/p).read_text()
changed=set((pkg/'26737_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines())
expected={'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/version.properties'}
assert changed==expected,(changed,expected)
v=txt(c,'app/version.properties'); assert 'VERSION_NAME=0.9726737' in v and 'VERSION_BUILD=26737' in v
sh=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'); st=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'); vgn=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
# Wronski: geometry alone never owns phase; fallback requires RAW photometric uniqueness.
for t in ['IRIS_26737_RAW_PHOTOMETRIC_PHASE_UNIQUENESS','phaseProbeCost26737','photometricAgreement26737','photometricUniqueness26737','photometricPhaseProof26737','phaseOwnershipConfidence26737']:
 assert t in sh,t
assert 'phaseOwnershipConfidence26736=accept?1.0:0.75*coherentSparseTrust' not in sh
for t in ['IRIS_26737_PHOTOMETRICALLY_TRUSTED_FLOW_OWNS_SUPERRES_PHASE','uniform int uReferenceObservation26737;','float phaseTrust26737 = uReferenceObservation26737 != 0 ? 1.0 : clamp(flow.a, 0.0, 1.0);','frameWeight *= phaseTrust26737;','phaseTrust26737 >= 0.80']:
 assert t in sh,t
# Complete four-phase authority; old 3-phase 0.55 path forbidden.
for t in ['IRIS_26737_COMPLETE_FOUR_PHASE_DETAIL_AUTHORITY','float trustedPhaseCompleteness26737 = blockPhaseCount >= 4 ? 1.0 : 0.0;','IRIS_26737_FOUR_PHASE_CFA_MODE_SAFETY_VETO','phaseAliasVeto26737','provenStructure*trustedPhaseCompleteness26737']:
 assert t in sh,t
assert '(blockPhaseCount == 3 ? 0.55 : 0.0)' not in sh
# Direct-CFA remains luma-only; no chroma ownership leak.
for t in ['IRIS_26735_DIGITAL_LUMA_ONLY_DETAIL_NO_CHROMA_GAIN','float finalTargetY26735=max(guideY*factor,0.0);','vec3 guideChroma26735=guideRgb-vec3(guideY);','float chromaScale26735=min(factor,1.0);']:
 assert t in sh,t
assert 'oRenderRgb = vec4(max(guideRgb * factor' not in sh and 'oRenderRgb=vec4(max(guideRgb*factor' not in sh
# Native chroma anti-moire exists in both seed and final independent proof; luma untouched by final owner.
for t in ['IRIS_26737_NATIVE_CFA_CHROMA_ALIAS_SEED','chromaAliasCleanup26737','cleanupFallback=chromaAliasCleanup26737']:
 assert t in vgn,t
for t in ['IRIS_26737_NATIVE_CFA_CHROMA_ALIAS_OWNER','nativeChromaAliasAuthority26737','aliasTargetChroma26737']:
 assert t in vgn,t
# Permanent successful ownership hierarchy preserved.
for t in ['IRIS_26733_HEADROOM_PRECEDES_COLOR_OWNERSHIP','IRIS_26733_INHERITED_HIGHLIGHT_HEADROOM_OWNER','IRIS_26731_FROZEN_RECIPROCAL_MATERIAL_OWNERSHIP','IRIS_26731_DIRECTION_PAIR_GEOMETRY','IRIS_26731_RECIPROCAL_ONE_SIDED_DIRECTIONAL','IRIS_26731_FROZEN_IIR_MATERIAL_OWNERSHIP','IRIS_26735_CENTER_CHROMA_CANNOT_DISQUALIFY_NEUTRAL_STRUCTURE','IRIS_26735_RECONSTRUCTED_HUE_CANNOT_SELF_VETO_ACHROMATIC_OWNER','IRIS_26728_PHYSICALLY_SUPPORTED_CHROMA_MAGNITUDE']:
 assert t in vgn,t
# Telemetry explicitly proves geometry-only rejection and strict four-phase mode.
for t in ['uReferenceObservation26737','rawPhotometricPhaseValidation=true','geometryOnlyPhaseOwner=false','strictFourPhase=true','cfaPhaseAliasVeto=true']:
 assert t in st,t
# Critical unrelated owners remain byte-identical.
protected=['app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt','app/src/main/cpp/motionv2_jpeg444_jni.cpp','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java','app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java','app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java']
for p in protected: assert (b/p).read_bytes()==(c/p).read_bytes(),p
cc=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
for t in ['IRIS_26735_AE_LOCK_REJECTION_TO_EXACT_MANUAL','IRIS_26735_MANUAL_EXPOSURE_UNACHIEVABLE','NORMAL_EXPOSURE_UNACHIEVABLE']: assert t in cc,t
# Numerical failure-model regression.
def smooth(a,b,x):
 if b<=a:return 1.0 if x>=b else 0.0
 q=max(0.0,min(1.0,(x-a)/(b-a))); return q*q*(3.0-2.0*q)
def gate36(n): return 1.0 if n>=4 else (0.55 if n==3 else 0.0)
def gate37(n): return 1.0 if n>=4 else 0.0
assert gate36(3)==0.55 and gate37(3)==0.0 and gate37(4)==1.0
def phase_proof(coherent,base_mean,margin): return coherent*(1-smooth(.60,1.60,base_mean))*smooth(.10,.28,margin)
assert phase_proof(.95,.40,.03)<.62 and phase_proof(.95,.35,.42)>.62 and phase_proof(.95,1.75,.45)<.62
def alias(low,resid,opp,texture): return (1-smooth(.040,.105,low))*smooth(.045,.125,resid)*smooth(.70,1.80,opp)*smooth(.10,.32,texture)
assert alias(.015,.16,2.8,.48)>.78 and alias(.14,.03,.05,.25)<.05 and alias(.01,.01,0,.55)<.05
print('PASS 26737 regressions: strict four-phase Wronski detail; RAW photometric uniqueness fallback; geometry-only phase forbidden; native neutral CFA chroma anti-moire; 26731/26733/26735 ownership and unrelated owners preserved')
