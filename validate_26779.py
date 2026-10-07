#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys, xml.etree.ElementTree as ET
if len(sys.argv)!=3: raise SystemExit("usage: validate_26779.py BASE CAND")
base=Path(sys.argv[1]); cand=Path(sys.argv[2])
allowed=[
"app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java",
"app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java",
"app/src/main/res/values/default_prefs.xml",
"app/src/main/res/values/strings.xml",
"app/src/main/res/xml/preferences.xml",
"app/version.properties",
]
def U(r):
    return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (Path(r)/"app").rglob("*") if p.is_file()}
a,b=U(base),U(cand)
assert len(a)==1779 and len(b)==1779,(len(a),len(b))
assert set(a)==set(b),"file universe changed"
changed=sorted(k for k in a if a[k]!=b[k])
assert changed==allowed,changed
# Version
v=(cand/"app/version.properties").read_text()
assert "VERSION_NAME=0.9726779" in v and "VERSION_BUILD=26779" in v
# UI structure
prefs=(cand/"app/src/main/res/xml/preferences.xml").read_text()
ET.parse(cand/"app/src/main/res/xml/preferences.xml")
keys=[
'pref_iris_chroma_denoise',
'pref_iris_edge_false_color_suppressor',
'pref_iris_demosaic_sharpness',
]
pos=[prefs.index(f'ns0:key="{k}"') for k in keys]
assert pos==sorted(pos),pos
assert prefs.count('ns0:key="pref_iris_edge_false_color_suppressor"')==1
assert prefs.count('ns0:key="pref_iris_demosaic_sharpness"')==1
dline=[l for l in prefs.splitlines() if 'ns0:key="pref_iris_demosaic_sharpness"' in l][0]
for token in ('ns1:maxValue="1.0"','ns1:minValue="0.0"','ns1:isFloat="true"','ns1:stepPerUnit="10"'):
    assert token in dline,(token,dline)
for retired in (
'pref_iris_chroma_correction_strength','pref_iris_adaptive_snr_chroma_denoise',
'pref_iris_residual_chroma_custom','pref_iris_residual_chroma_level1',
'pref_iris_residual_chroma_level2','pref_iris_residual_chroma_level3',
'pref_iris_residual_chroma_level4','pref_iris_residual_chroma_level5'):
    assert f'ns0:key="{retired}"' not in prefs,retired
# Resources
strings=(cand/"app/src/main/res/values/strings.xml").read_text()
ET.parse(cand/"app/src/main/res/values/strings.xml")
for token in ('iris_edge_false_color_suppressor','iris_demosaic_sharpness'):
    assert f'name="{token}"' in strings,token
for retired in (
'iris_chroma_correction_strength','iris_adaptive_snr_chroma_denoise',
'iris_residual_chroma_custom','iris_residual_chroma_level1','iris_residual_chroma_level2',
'iris_residual_chroma_level3','iris_residual_chroma_level4','iris_residual_chroma_level5'):
    assert f'name="{retired}"' not in strings,retired
defaults=(cand/"app/src/main/res/values/default_prefs.xml").read_text()
ET.parse(cand/"app/src/main/res/values/default_prefs.xml")
assert '<bool name="pref_iris_edge_false_color_suppressor_default">true</bool>' in defaults
assert '<string name="pref_iris_demosaic_sharpness_default" translatable="false">1.0</string>' in defaults
# Runtime owner
ims=(cand/"app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java").read_text()
assert 'KEY_EDGE_FALSE_COLOR_SUPPRESSOR = "pref_iris_edge_false_color_suppressor"' in ims
assert 'KEY_DEMOSAIC_SHARPNESS = "pref_iris_demosaic_sharpness"' in ims
assert 'getBoolean(sm, KEY_EDGE_FALSE_COLOR_SUPPRESSOR, true)' in ims
assert 'snap01(getFloat(sm, KEY_DEMOSAIC_SHARPNESS, 1.0f), 0.0f, 1.0f)' in ims
assert 'demosaicSharpness, "VISIBLE_AB_SETTINGS"' in ims
assert '@Tunable(title = "Edge False Color Suppressor"' not in ims
assert '@Tunable(title = "Sabre Demosaic Sharpness"' not in ims
# Retired controls are no longer persisted-value authorities.
for token in (
'getFloat(sm, KEY_CHROMA_CORRECTION_STRENGTH',
'getFloat(sm, KEY_ADAPTIVE_SNR_CHROMA_DENOISE',
'getBoolean(sm, KEY_RESIDUAL_CHROMA_CUSTOM',
'getFloat(sm, KEY_RESIDUAL_CHROMA_LEVEL1',
'getFloat(sm, KEY_RESIDUAL_CHROMA_LEVEL2',
'getFloat(sm, KEY_RESIDUAL_CHROMA_LEVEL3',
'getFloat(sm, KEY_RESIDUAL_CHROMA_LEVEL4',
'getFloat(sm, KEY_RESIDUAL_CHROMA_LEVEL5'):
    assert token not in ims,token
for token in ('float chromaCorrection = 1.0f;','float adaptiveSnrChroma = 1.0f;',
              'boolean residualCustom = false;','float[] residualLevels = DEFAULT_RESIDUAL_CHROMA_LEVELS.clone();'):
    assert token in ims,token
# Per-lens settings seeding for new A/B controls.
pk=(cand/"app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java").read_text()
for token in (
'setInitial(SCOPE_GLOBAL, "pref_iris_edge_false_color_suppressor", "1")',
'setInitial(SCOPE_GLOBAL, "pref_iris_demosaic_sharpness", "1.0")',
'map.putIfAbsent("pref_iris_edge_false_color_suppressor", "1")',
'map.putIfAbsent("pref_iris_demosaic_sharpness", "1.0")'):
    assert token in pk,token
# Shader/reconstruction owners are protected byte-identically.
for rel in (
"app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt",
"app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt",
"app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt",
"app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt"):
    assert a[rel]==b[rel],rel
print("PASS 26779 visible A/B UI: Suppressor toggle + Demosaic Sharpness 0.0..1.0 in exact 0.1 slider steps under Chroma Denoise")
print("PASS 26779 retired chroma controls: removed from visible UI and stale persisted values neutralized to proven defaults")
print("PASS 26779 runtime ownership: existing 26778 suppressor/Resolve/VGN/shader bytes unchanged; only settings authorities changed")
print("PASS 26779 exact runtime allowlist: 6 modified + 0 added + 0 deleted; 1773 protected files unchanged")
