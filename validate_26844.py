#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,xml.etree.ElementTree as ET
B,C=map(Path,sys.argv[1:3])
ALLOW={
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java',
'app/src/main/res/xml/preferences.xml',
'app/version.properties'}
def H(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def U(root): return {str(p.relative_to(root)):H(p) for p in (root/'app').rglob('*') if p.is_file()}
b,c=U(B),U(C)
assert set(b)==set(c),(len(b),len(c),sorted(set(b)^set(c))[:20])
changed={p for p in b if b[p]!=c[p]}
assert changed==ALLOW,(changed,ALLOW)
assert len(b)==1786 and len(c)==1786

# XML: exact 11 historical controls absent and Chroma Denoise flows directly to Iris Saturation.
xmlp=C/'app/src/main/res/xml/preferences.xml'
ET.parse(xmlp)
x=xmlp.read_text()
removed=[
'pref_iris_edge_false_color_suppressor','pref_iris_edge_false_color_all_edges','pref_iris_sdr_body_contrast_zero',
'pref_iris_demosaic_sharpness','pref_iris_dng_lca','pref_iris_dng_lca_kr','pref_iris_dng_lca_kb',
'pref_iris_dng_quad_headroom','pref_iris_dng_edge_dealias','pref_iris_dng_neutral_clamp','pref_iris_dng_reset_defaults']
for key in removed: assert f'ns0:key="{key}"' not in x,key
assert x.count('ns0:key="pref_iris_chroma_denoise"')==1
assert x.count('ns0:key="pref_iris_saturation"')==1
ci=x.index('ns0:key="pref_iris_chroma_denoise"'); si=x.index('ns0:key="pref_iris_saturation"')
between=x[ci:si]
for key in removed: assert key not in between,key
assert '@string/pref_category_device_key' not in x
assert '@string/pref_fetch_configurations_key' not in x
assert 'IRIS_26844_RETIRED_DIAGNOSTIC_UI' in x

# Settings UI owner: no fetch handler, no DNG A/B UI binder, dynamic per-lens title is Lens:<id> only.
sa=(C/'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java').read_text()
for dead in ['setFetchConfigurationsPref()','setupIris26786DngOptions()','setupIris26786Coefficient(']: assert dead not in sa,dead
assert 'p.setTitle("Lens:" + PreferenceKeys.getCameraID());' in sa
assert 'mContext.getString(R.string.hdrx) + "\\t(Lens:' not in sa

# Hidden diagnostic keys are no longer runtime authorities. Production defaults are fixed.
ims=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java').read_text()
assert 'IRIS_26844_RETIRED_EDGE_AB_UI_DEFAULTS' in ims
assert 'boolean enabled = true;' in ims
assert 'float demosaicSharpness = 1.0f;' in ims
assert 'boolean edgeFalseColorAllEdges26792 = false;' in ims
assert 'float sdrBodyContrast26792 = 0.35f;' in ims
assert 'IRIS_26844_RETIRED_DNG_AB_UI_DEFAULTS' in ims
assert 'return new Snapshot(false, DEFAULT_KR, DEFAULT_KB, false, false, false, "FIXED_26844_DEFAULTS");' in ims
assert 'return new Snapshot(false, DEFAULT_KR, DEFAULT_KB, false, false, false, "DEFAULTS_26844_LCA_OFF");' in ims
assert 'sm.set(SettingsManager.SCOPE_GLOBAL, KEY_DNG_LCA, false);' in ims
# Ensure the old active reads cannot survive.
for old in [
'getBoolean(sm, KEY_DNG_LCA, true)',
'getBoolean(sm, KEY_EDGE_FALSE_COLOR_ALL_EDGES, false)',
'getBoolean(sm, KEY_SDR_BODY_CONTRAST_ZERO, false)',
'getFloat(sm, KEY_DEMOSAIC_SHARPNESS, 1.0f)']:
    assert old not in ims,old

# 26843 fast-protect exposure owner and all shaders remain inherited byte-identically.
cap='app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java'
assert (B/cap).read_bytes()==(C/cap).read_bytes()
assert 'IRIS_26843_FAST_PROTECTIVE_HDR_ARM' in (C/cap).read_text()
shader_root='app/src/main/assets/shaders'
for p in (B/shader_root).rglob('*'):
    if p.is_file():
        rel=p.relative_to(B); assert (C/rel).is_file() and p.read_bytes()==(C/rel).read_bytes(),str(rel)
# Kotlin embedded shader carriers and native source also remain protected by changed-file equality.
for rel in [
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp']:
    assert (B/rel).read_bytes()==(C/rel).read_bytes(),rel
v=(C/'app/version.properties').read_text()
assert 'VERSION_NAME=0.9726844' in v and 'VERSION_BUILD=26844' in v
print('PASS 26844 semantic validation: exact 4-path UI/default scope; 11 per-lens diagnostics removed; Device/Fetch removed; Lens:<id> title; edge suppressor fixed ON; DNG LCA fixed default OFF; successful 26843 fast-protect/IQ/shaders/DNG writer/native/UHDR/SR bytes otherwise protected')
