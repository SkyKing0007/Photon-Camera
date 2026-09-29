#!/usr/bin/env python3
from pathlib import Path
import sys,re
if len(sys.argv)!=3: raise SystemExit('usage: verify_26729_regressions.py BASE26728 CAND26729')
b=Path(sys.argv[1]); c=Path(sys.argv[2])
def txt(r,p): return (r/p).read_text()
changed=set((Path(__file__).resolve().parent/'26729_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()); assert len(changed)==10
v=txt(c,'app/version.properties'); assert 'VERSION_NAME=0.9726729' in v and 'VERSION_BUILD=26729' in v
ims=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java')
for t in ['KEY_RESIDUAL_CHROMA_CUSTOM','KEY_RESIDUAL_CHROMA_LEVEL1','KEY_RESIDUAL_CHROMA_LEVEL2','KEY_RESIDUAL_CHROMA_LEVEL3','KEY_RESIDUAL_CHROMA_LEVEL4','KEY_RESIDUAL_CHROMA_LEVEL5','DEFAULT_RESIDUAL_CHROMA_LEVELS','residualChromaCustom','residualChromaLevels']:
 assert t in ims,t
assert '0.0f, source.chromaDenoise, false, DEFAULT_RESIDUAL_CHROMA_LEVELS' in ims
pk=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java')
# IRIS_26729_R2_STRING_KEY_BOOLEAN_DEFAULT_REGRESSION: SettingsManager has no
# setInitial(String,String,boolean); raw String keys must use the persisted "0"/"1" String convention.
assert 'settingsManager.setInitial(SCOPE_GLOBAL, "pref_iris_residual_chroma_custom", "0");' in pk
assert 'settingsManager.setInitial(SCOPE_GLOBAL, "pref_iris_residual_chroma_custom", false);' not in pk
assert not re.search(r'setInitial\(\s*SCOPE_GLOBAL\s*,\s*"[^"]+"\s*,\s*(?:true|false)\s*\)',pk)
for key,default in [('pref_iris_residual_chroma_custom','0'),('pref_iris_residual_chroma_level1','5.0'),('pref_iris_residual_chroma_level2','4.0'),('pref_iris_residual_chroma_level3','4.0'),('pref_iris_residual_chroma_level4','0.8'),('pref_iris_residual_chroma_level5','1.0')]:
 assert key in pk,key
 assert f'map.putIfAbsent("{key}", "{default}")' in pk,(key,'legacy default')
px=txt(c,'app/src/main/res/xml/preferences.xml')
assert px.count('ns0:dependency="pref_iris_residual_chroma_custom"')==5
for n in range(1,6):
 key=f'pref_iris_residual_chroma_level{n}'; assert key in px
 m=re.search(r'<com\.particlesdevs\.photoncamera\.ui\.settings\.custompreferences\.UniversalSeekBarPreference[^>]*ns0:key="'+key+r'"[^>]*/>',px); assert m,key
 tag=m.group(0); assert 'ns1:maxValue="5.0"' in tag and 'ns1:minValue="0.0"' in tag and 'ns1:stepPerUnit="10"' in tag
sa=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java')
for t in ['KEY_RESIDUAL_CHROMA_CUSTOM','KEY_RESIDUAL_CHROMA_LEVEL1','KEY_RESIDUAL_CHROMA_LEVEL2','KEY_RESIDUAL_CHROMA_LEVEL3','KEY_RESIDUAL_CHROMA_LEVEL4','KEY_RESIDUAL_CHROMA_LEVEL5']:
 assert f'removePreferenceAnywhere(IrisMotionSettings.{t})' in sa,t
mgc=txt(c,'app/src/main/java/com/hinnka/mycamera/raw/MgcFullResolutionDenoise.kt')
for t in ['customChromaStrength: FloatArray? = null','values.size == 5','it in 0f..5f','customChroma?.any { it > 0f }','automaticChromaTuning.copy(strength = customChroma)','CUSTOM_EXACT']:
 assert t in mgc,t
br=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
for t in ['IRIS_26729_ONE_PRIMARY_CHROMA_OWNER','!parameters.irisNightActive && irisSettings.residualChromaCustom','customResidualChroma?.any { it > 0f }','residualChromaEnabled','IRIS_26729_RESIDUAL_CHROMA_CONTROL','customChromaStrength = customResidualChroma']:
 assert t in br,t
vgn=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt')
for t in ['IRIS_26729_COLOR_MATERIAL_DIRECTION_GATE','IRIS_26729_COLOR_MATERIAL_MEDIAN_GATE','colorBoundaryProtection','IRIS_26729_COLOR_ONLY_IIR_STATE_RESET','colorOnlyMaterialBoundary=chromaJump>0.38&&topologyBoundary']:
 assert t in vgn,t
for t in ['IRIS_26728_PHYSICALLY_SUPPORTED_CHROMA_MAGNITUDE','hardArtifactVeto = step(0.50, artifactVeto)','correctedChroma *= restoredMagnitude / cleanedMagnitude','protectedPreVgnMagnitude']:
 assert t in vgn,t
assert 'correctedChroma = preVgnChroma' not in vgn
protected=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java']
for p in protected: assert (b/p).read_bytes()==(c/p).read_bytes(),p
print('PASS 26729 regressions: VGN primary chroma containment; 26728 physical hue safety retained; five exact per-lens Motion residual levels 0.0..5.0; all-zero chroma bypass; Night/unrelated owners protected')
def loadm(n):
 d={}
 for l in (Path(__file__).resolve().parent/n).read_text().splitlines():
  if l.strip(): h,p=l.split(None,1); d[p.strip()]=h
 return d
for stem,count in [('NATIVE_FULL',820),('VENDOR_PROTECTED',1),('DNG',6)]:
 x=loadm(f'26729_{stem}_BASE.sha256'); y=loadm(f'26729_{stem}_CANDIDATE.sha256'); assert len(x)==len(y)==count and x==y
