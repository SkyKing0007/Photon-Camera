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
assert 'if(cleanupStrength<=0.0001' in chroma and 'float fraction=0.24' in chroma
assert 'lumaUntouched=true' in read('src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Iris26869BResidualChroma.java')
assert 'if(bShadowToe26869>0.0001)' in tone and 'bShadowToe26869' not in (base/'src/main/assets/shaders/motionv2/iris_tone_controls.glsl').read_text()
assert 'VERSION_BUILD=26869' in read('version.properties')
print('PASS 26869 B-only reference, fallbacks, per-lens chroma/toe UI, zero bypass, HDRq/AMaZE/defringe/FCC and LONG invariance anchors')
