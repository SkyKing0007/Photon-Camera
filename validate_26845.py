#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
B,C=map(Path,sys.argv[1:3])
ALLOW={
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/version.properties'}
def H(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def U(root): return {str(p.relative_to(root)):H(p) for p in (root/'app').rglob('*') if p.is_file()}
b,c=U(B),U(C)
assert set(b)==set(c),(len(b),len(c),sorted(set(b)^set(c))[:20])
changed={p for p in b if b[p]!=c[p]}
assert changed==ALLOW,(changed,ALLOW)
assert len(b)==1786 and len(c)==1786
S=C/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
T=C/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
s=S.read_text(); t=T.read_text()
# New owner is confined to the existing LONG luma gain/publication pair.
assert s.count('IRIS_26845_SHADOW_LONG_LOW_FREQUENCY_LUMA_AUTHORITY')==2
assert s.count('IRIS_26845_SHADOW_LONG_POST_VGN_LUMINANCE_ONLY')==2
assert 'layout(location = 0) out vec2 oGainTrust;' in s
assert 'float cleanup = 0.78 * trust;' in s
assert 'float adaptiveLong = 0.88 * trust;' in s
assert 'coherentDetail' in s and 'cleanupTrust = trust * (1.0 - coherentDetail)' in s
assert 'oColor = vec4(source.rgb * scale, source.a);' in s
# Existing isolation remains: no LONG RGB publication or color/detail ownership is introduced.
for forbidden in ['longColorAuthority=true','longTemporalSupport=true','longRgbAccumulator=true']:
    assert forbidden not in t,forbidden
assert 'longColorAuthority=false longTemporalSupport=false' in t
assert 'longLumaEvidence=true publication=POST_VGN_EQUAL_RGB_SCALE' in t
assert 'GLES30.GL_RG16F' in t[t.rindex('private fun renderSabreShadowLongLumaGainMap26833'):t.rindex('private fun renderSabreShadowLongPostVgnLumaApply26833')]
assert 'IRIS_26845_LONG_LUMA_GAIN_READY' in t and 'IRIS_26845_LONG_LUMA_FUSED' in t
# Preserve current successful 26844 exposure, UI cleanup, DNG/UHDR/SR and all asset shaders byte-identically.
protected=[
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java',
'app/src/main/res/xml/preferences.xml',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp']
for rel in protected: assert (B/rel).read_bytes()==(C/rel).read_bytes(),rel
for p in (B/'app/src/main/assets/shaders').rglob('*'):
    if p.is_file():
        rel=p.relative_to(B); assert p.read_bytes()==(C/rel).read_bytes(),str(rel)
v=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726845' in v and 'VERSION_BUILD=26845' in v
print('PASS 26845 semantic validation: exact 3-path shadow-SNR scope; LONG stays luminance-only/post-VGN; NORMAL retains RGB/chroma/detail/motion ownership; successful 26844 exposure/UI/highlight/color/DNG/UHDR/SR/shader-assets otherwise byte-protected')
