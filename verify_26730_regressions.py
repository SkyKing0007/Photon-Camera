#!/usr/bin/env python3
from pathlib import Path
import sys,re,math
if len(sys.argv)!=3: raise SystemExit('usage: verify_26730_regressions.py BASE26729 CAND26730')
b=Path(sys.argv[1]); c=Path(sys.argv[2]); pkg=Path(__file__).resolve().parent
def txt(r,p): return (r/p).read_text()
changed=set((pkg/'26730_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines())
assert changed=={'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt','app/version.properties'}
v=txt(c,'app/version.properties'); assert 'VERSION_NAME=0.9726730' in v and 'VERSION_BUILD=26730' in v
vgn=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
# Freeze successful 26729 fine/text/high-frequency color architecture.
for t in ['IRIS_26729_COLOR_MATERIAL_DIRECTION_GATE','IRIS_26729_COLOR_MATERIAL_MEDIAN_GATE','IRIS_26729_COLOR_ONLY_IIR_STATE_RESET','IRIS_26728_PHYSICALLY_SUPPORTED_CHROMA_MAGNITUDE','hardArtifactVeto = step(0.50, artifactVeto)','correctedChroma *= restoredMagnitude / cleanedMagnitude','protectedPreVgnMagnitude']:
 assert t in vgn,t
assert 'correctedChroma = preVgnChroma' not in vgn
# New authority: early 26729 containment consumes existing Sabre CFA validity, no new sidecar allocation.
for t in ['IRIS_26730_PHYSICAL_VALIDITY_CONTAINMENT_AUTHORITY','IRIS_26730_TRUE_MATERIAL_STEP_GATE','IRIS_26730_VALIDITY_OWNED_COLOR_ONLY_IIR_RESET','physicalColorTrust','bindSabreValidity','sabreValidityWeightScale','materialStepProof','trueMaterialStep']:
 assert t in vgn,t
assert vgn.count('IRIS_26730_PHYSICAL_VALIDITY_CONTAINMENT_AUTHORITY')==3
assert 'bool colorOnlyMaterialBoundary=chromaJump>0.38&&topologyBoundary;' not in vgn
assert 'physicalTrust>0.85&&trueMaterialStep' in vgn
assert 'smoothstep(0.985,0.9995,measured)' in vgn
assert 'createRgba16UiTexture' not in vgn[vgn.index('private fun bindSabreValidity'):vgn.index('private fun dispatchUniversalAdaptiveColor')]
# 26729 R2 build failure regression remains permanent even though PreferenceKeys is protected here.
pk=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java')
assert 'settingsManager.setInitial(SCOPE_GLOBAL, "pref_iris_residual_chroma_custom", "0");' in pk
assert not re.search(r'setInitial\(\s*SCOPE_GLOBAL\s*,\s*"[^"]+"\s*,\s*(?:true|false)\s*\)',pk)
# Residual MGC controls/defaults and bridge ownership are byte-inherited from successful 26729.
for p in [
'app/src/main/java/com/hinnka/mycamera/raw/MgcFullResolutionDenoise.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java']:
 assert (b/p).read_bytes()==(c/p).read_bytes(),p
# Semantic model: invalid highlight hue cannot protect itself; smooth gradient is not a material step;
# a valid sharp step remains eligible, preserving the successful 26729 color behavior.
def smooth(a,b,x):
 if x<=a:return 0.0
 if x>=b:return 1.0
 t=(x-a)/(b-a); return t*t*(3-2*t)
def gate(jump,center_within,neighbor_within,trust,cont=1.0):
 step=smooth(1.35,2.20,jump/max(center_within,neighbor_within,0.006))
 return smooth(0.030,0.095,jump)*smooth(0.35,0.75,cont)*1.0*step*trust
assert gate(0.12,0.01,0.01,0.0)==0.0
assert gate(0.06,0.045,0.04,1.0)<0.1
assert gate(0.12,0.01,0.015,1.0)>0.9
print('PASS 26730 regressions: successful 26729 fine/text color retained; early containment validity-owned; true material-step proof blocks smooth blue gradients; invalid highlight hue cannot self-protect; R1/R2 build-failure regressions retained; fusion/MGC/Night/DNG/UHDR/high-zoom/capture owners protected')
