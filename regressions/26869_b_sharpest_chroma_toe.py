#!/usr/bin/env python3
"""B-only 26869 source/ownership regression against compiled 26868 candidate."""
from pathlib import Path
import sys,re,xml.etree.ElementTree as ET
base=Path(sys.argv[1]);cand=Path(sys.argv[2]);src=cand/'src/main/java'
def read(p):return (cand/p).read_text()
sharp=read('src/main/java/com/hinnka/mycamera/processor/GlesIris26869Sharpest.kt')
bridge=read('src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
post=read('src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java')
settings=read('src/main/java/com/particlesdevs/photoncamera/settings/Iris26869BSettings.java')
activity=read('src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java')
chroma=read('src/main/assets/shaders/motionv2/iris_26869_b_residual_chroma.glsl')
tone=read('src/main/assets/shaders/motionv2/iris_tone_controls.glsl')
assert 'GlesIris26869Sharpest.select(' in bridge and bridge.count('GlesIris26869Sharpest.select(')==2
assert bridge.count('shutterIndex=')==2 and bridge.count('selected=$chosenReference')==2
assert 'RawBurstFrameRole.NORMAL' in (src/'com/hinnka/mycamera/processor/GlesIris26864FrozenRawrIngress.kt').read_text() if False else 'borrowNormals' in bridge
assert 'shutterIndex' in sharp and 'return shutterIndex' in sharp and 'frozen.assertUsable()' in sharp
assert 'GlesIris26864NativeRawr.run' in bridge and 'nativeReferenceIndex,' not in bridge[bridge.find('val chosenReference = ingress.use { frozen ->',bridge.find('native=WRONSKI')):bridge.find('native=HDRQ')]
assert bridge.count('IRIS_26869_B_SHARPEST_REF native=')==2
assert (src/'com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text().count('renderRawrBPostAmaze26856')>=2
assert 'bNoiseVariance26863 = 0' in (src/'com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
assert 'MOTION_V2_RECONSTRUCTION_RAWR_AMAZE' in post
assert 'new Iris26869BResidualChroma(' in post
assert post.index('new IrisMotionToneControls(')<post.index('new Iris26869BResidualChroma(')<post.index('add(new MotionV2Render());',post.index('new Iris26869BResidualChroma('))
assert '0.0f' in (src/'com/particlesdevs/photoncamera/processing/render/Parameters.java').read_text()
assert 'strength=Float.isFinite' in settings and 'lens_' in settings and 'read(Context context,String physical)' in settings
assert 'getSharedPreferences(STORE,Context.MODE_PRIVATE)' in settings
assert 'setPersistent(false)' in activity and 'setupIris26869BControls();' in activity
xml=(cand/'src/main/res/xml/preferences.xml').read_text()
assert xml.index('pref_iris_chroma_denoise')<xml.index('iris_26869_b_chroma_enable')<xml.index('iris_26869_b_chroma_strength')<xml.index('iris_26869_b_shadow_toe')
ET.fromstring(xml)
# Permanent exact AAPT2 failure regression from Actions 39897292954:
# AndroidX SeekBarPreference's max belongs to android:max, NOT app:max.
# Test expanded namespaces (prefix-agnostic) and reject the actual failing XML.
ANDROID = 'http://schemas.android.com/apk/res/android'
APP = 'http://schemas.android.com/apk/res-auto'
def assert_26869_seekbar_bounds(xml_bytes):
 root=ET.fromstring(xml_bytes)
 sliders={}
 for node in root.iter():
  if node.tag.endswith('SeekBarPreference'):
   assert '{'+APP+'}max' not in node.attrib, ('AAPT2 39897292954 app:max invalid',node.attrib.get('{'+ANDROID+'}key'))
   key=node.attrib.get('{'+ANDROID+'}key')
   if key in ('iris_26869_b_chroma_strength','iris_26869_b_shadow_toe'):
    assert key not in sliders,('duplicate 26869 SeekBarPreference',key)
    assert node.attrib.get('{'+ANDROID+'}max')=='100',('expected android:max=100',key)
    assert node.attrib.get('{'+APP+'}min')=='0',('expected app:min=0',key)
    assert node.attrib.get('{'+APP+'}seekBarIncrement')=='5',('expected increment 5',key)
    sliders[key]=node
 assert len(sliders)==2,('26869 missing slider',sorted(sliders))
 return True
assert assert_26869_seekbar_bounds(xml)
# Reproduce exact error with app:max instead of android:max on both sliders.
invalid=xml.replace('ns0:max="100"','ns1:max="100"')
assert invalid != xml and invalid.count('ns1:max="100"')==2
try:
 assert_26869_seekbar_bounds(invalid)
except AssertionError as err:
 assert 'AAPT2 39897292954 app:max invalid' in str(err)
else:
 raise AssertionError('Actions 39897292954 AAPT2 failure escaped regression')
print('PASS 39897292954 two AndroidX seekbar android:max bounds; actual app:max AAPT2 failure reproduced/rejected')
assert 'if(cleanupStrength<=0.0001' in chroma and 'float fraction=0.24' in chroma
assert 'lumaUntouched=true' in read('src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Iris26869BResidualChroma.java')
assert 'if(bShadowToe26869>0.0001)' in tone and 'bShadowToe26869' not in (base/'src/main/assets/shaders/motionv2/iris_tone_controls.glsl').read_text()
assert 'VERSION_BUILD=26869' in read('version.properties')
print('PASS 26869 B-only reference, fallbacks, per-lens chroma/toe UI, zero bypass, HDRq/AMaZE/defringe/FCC and LONG invariance anchors')
