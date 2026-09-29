#!/usr/bin/env python3
from pathlib import Path
import sys,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26733_regressions.py BASE26732 CAND26733')
b=Path(sys.argv[1]); c=Path(sys.argv[2]); pkg=Path(__file__).resolve().parent
def txt(r,p): return (r/p).read_text()
changed=set((pkg/'26733_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()); assert len(changed)==3
expected={
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/version.properties'}
assert changed==expected,(changed,expected)
v=txt(c,'app/version.properties'); assert 'VERSION_NAME=0.9726733' in v and 'VERSION_BUILD=26733' in v
vgn=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
# Preserve 26729-26732 proven real-color/material transport mechanics.
for t in [
 'IRIS_26729_COLOR_MATERIAL_DIRECTION_GATE','IRIS_26730_PHYSICAL_VALIDITY_CONTAINMENT_AUTHORITY','IRIS_26730_TRUE_MATERIAL_STEP_GATE',
 'IRIS_26731_ISOLATED_FALSE_COLOR_CLEANUP_FLAG','IRIS_26731_FROZEN_RECIPROCAL_MATERIAL_OWNERSHIP','IRIS_26731_DIRECTION_PAIR_GEOMETRY',
 'IRIS_26731_RECIPROCAL_ONE_SIDED_DIRECTIONAL','IRIS_26731_FROZEN_IIR_MATERIAL_OWNERSHIP',
 'IRIS_26728_PHYSICALLY_SUPPORTED_CHROMA_MAGNITUDE','IRIS_26580_FAIL_CLOSED_MULTICOLOR_OBJECT_VETO',
 'IRIS_26732_TRUSTED_ONE_WAY_CLEANUP_TRANSPORT','IRIS_26732_HIGH_ZOOM_FAIL_CLOSED_NATIVE_FALLBACK' if False else 'IRIS_26732_CLUSTER_CLEANUP_WITHOUT_COLOR_LOSS']:
 assert t in vgn,t
# 26733 audit-derived hierarchy: inherited headroom veto precedes all color-only ownership.
for t in [
 'IRIS_26733_HEADROOM_PRECEDES_COLOR_OWNERSHIP','IRIS_26733_INHERITED_HIGHLIGHT_HEADROOM_OWNER',
 'inheritedHighlightPermission=1.0-smoothstep(0.72,0.92,centerNormalizedY)',
 'highlightColorOwnershipPermission=max(inheritedHighlightPermission,realBrightColorProof)',
 'materialStepProof * physicalTrust * highlightColorOwnershipPermission',
 'IRIS_26733_HEADROOM_FAILS_NEUTRAL']:
 assert t in vgn,t
# Bright real color exception must require physical support + substantial chroma + topology/continuation.
for t in ['brightPhysicalColorException = measuredColorProtection','smoothstep(0.10, 0.18, centerNormalizedMagnitude)','smoothstep(0.50, 0.82, brightTopologyProof)','realBrightColorProof=centerTrust*','smoothstep(0.10,0.18,centerChromaMagnitude)','smoothstep(0.55,0.82,centerContinuation)']:
 assert t in vgn,t
# Neutral/black fine structure is an early physical topology owner, not OCR/semantic logic.
for t in ['IRIS_26733_EARLY_ACHROMATIC_STRUCTURE_OWNER','neutralStructure << 14','neutralStructureAt','IRIS_26733_ACHROMATIC_STRUCTURE_CLEANUP','neutralCleanupChromaSum','neutralCleanupWeight','originalHuePermission']:
 assert t in vgn,t
assert 'textRecognition(' not in vgn and 'Tesseract' not in vgn
# Prevent the 26728 magnitude floor from restoring neutral-surface contamination.
for t in ['IRIS_26733_NEUTRAL_FLOOR_VETO','validNeutralConsensus','neutralFloorVeto','max(max(validCfaNeutralLeakAuthority, phaseArtifactAuthority), neutralFloorVeto)']:
 assert t in vgn,t
# Exact 26731 geometry that fixed horizontal teeth is still present.
for t in ['ivec2(-1,0),3,1,ivec2(1,0),1,3','ivec2(0,-1),0,2,ivec2(0,1),2,0','ivec2(1,-1),4,6,ivec2(-1,1),6,4','ivec2(-1,-1),7,5,ivec2(1,1),5,7']:
 assert t in vgn,t
# Motion Auto residual chroma is genuinely loosened; Custom Exact and Night are unchanged.
br=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
for t in ['IRIS_26733_MOTION_AUTO_RESIDUAL_CHROMA_HALF_SCALE','(0.5f * chromaScale).coerceIn(0f, 2f)','!parameters.irisNightActive && customResidualChroma == null','CUSTOM_EXACT','AUTO_SNR_HALF','appliedAutoScale=$automaticResidualChromaScale26733','chromaStrengthScale = if (customResidualChroma != null) 0f else automaticResidualChromaScale26733']:
 assert t in br,t
assert 'customChromaStrength = customResidualChroma' in br
# 26732 high-zoom hardening is byte-protected, including direct shader owners and clean native fallback.
for p in [
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt']:
 assert (b/p).read_bytes()==(c/p).read_bytes(),p
sh=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
st=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
for t in ['IRIS_26732_DIRECT_HIGH_ZOOM_FLOW_RUNTIME_OWNER','IRIS_26732_DIRECT_HIGH_ZOOM_RGB_RUNTIME_OWNER']:
 assert t in sh,t
for t in ['IRIS_26732_HIGH_ZOOM_FAIL_CLOSED_NATIVE_FALLBACK','fallback=NATIVE_SABRE_VGN_NO_DETAIL staleOverlayImpossible=true']:
 assert t in st,t
# MGC implementation/tuning table, settings, capture, UHDR, matrices and native owners are untouched.
protected=[
'app/src/main/java/com/hinnka/mycamera/raw/MgcFullResolutionDenoise.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java',
'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java']
for p in protected: assert (b/p).read_bytes()==(c/p).read_bytes(),p
pk=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java')
assert not re.search(r'setInitial\(\s*SCOPE_GLOBAL\s*,\s*"[^"]+"\s*,\s*(?:true|false)\s*\)',pk)
# Permanent artifact classes: keep explicit source markers for dots/lines/teeth/neutral contamination ownership.
for t in ['highlightInvalidCleanup','cleanupFallbackAt','physicalColorTrust','microObjectProtection','topologyProtection']:
 assert t in vgn,t
print('PASS 26733 regressions: 26727/26728 highlight headroom restored ahead of 26729+ ownership; 26731 teeth fix frozen; early achromatic owner; neutral residual-floor veto; Motion Auto chroma 0.5x; 26732 high-zoom hardening and unrelated owners byte-protected')
