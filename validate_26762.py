#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26762.py BASE CANDIDATE')
b,c=map(Path,sys.argv[1:]); root=Path(__file__).parent
allow=[x.strip() for x in (root/'26762_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip()]
def H(r): return {p.relative_to(r).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
hb,hc=H(b),H(c)
assert len(hb)==len(hc)==1823,(len(hb),len(hc)); assert set(hb)==set(hc)
changed=sorted(k for k in hb if hb[k]!=hc[k]); assert changed==sorted(allow),(changed,allow)
assert len(changed)==12
v=(c/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726762' in v and 'VERSION_BUILD=26762' in v
# explicit frozen protected owners
for rel in ['app/src/main/java/com/hinnka/mycamera/raw/MgcFullResolutionDenoise.kt','app/src/main/java/com/hinnka/mycamera/processor/MgcSabreKernelTuning.kt']:
    assert hb[rel]==hc[rel],rel
# required ownership/UI markers
checks={
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt':['IRIS_26762_FROZEN_ADAPTIVE_CHROMA_CAPTURE_STATE','IRIS_26762_CUSTOM_BROAD_CHROMA_PRECEDENCE','IRIS_26762_ADAPTIVE_SNR_CHROMA_USER_AUTHORITY'],
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt':['IRIS_26762_SUPER_RES_BOUNDED_ADAPTIVE_CHROMA_BLEND'],
'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java':['IRIS_26762_CUSTOM_ADAPTIVE_UI_PRECEDENCE'],
'app/src/main/res/xml/preferences.xml':['IRIS_26762_ADAPTIVE_SNR_CHROMA_UI'],
}
for rel,marks in checks.items():
    s=(c/rel).read_text()
    for m in marks: assert s.count(m)==1,(rel,m,s.count(m))
xml=(c/'app/src/main/res/xml/preferences.xml').read_text()
order=['pref_iris_luma_denoise_v2','pref_iris_chroma_denoise','pref_iris_adaptive_snr_chroma_denoise','pref_iris_residual_chroma_custom','pref_iris_residual_chroma_level1','pref_iris_residual_chroma_level2','pref_iris_residual_chroma_level3','pref_iris_residual_chroma_level4','pref_iris_residual_chroma_level5']
pos=[xml.index(x) for x in order]; assert pos==sorted(pos)
shader=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
assert 'mix(selectedChroma, denoisedChroma26760, adaptive26762)' not in shader
assert 'clamp(uChromaDenoiseStrength26762, 0.50, 2.00)' in shader
# Permanent regression: SettingsManager String-key boolean access must use the 3-argument overload.
sa=(c/'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java').read_text()
bad='mSettingsManager.getBoolean(SettingsManager.SCOPE_GLOBAL,\n                    IrisMotionSettings.KEY_RESIDUAL_CHROMA_CUSTOM);'
good='mSettingsManager.getBoolean(SettingsManager.SCOPE_GLOBAL,\n                    IrisMotionSettings.KEY_RESIDUAL_CHROMA_CUSTOM, false);'
assert bad not in sa, '26762 regression: String key passed to PreferenceKeys.Key overload'
assert sa.count(good)==1, '26762 regression: corrected String-key boolean overload missing/duplicated'
print('PASS 26762 validate: 1823 authority-seeded files; exact 12 existing changes; 0 additions/deletions; ownership/UI invariants')
