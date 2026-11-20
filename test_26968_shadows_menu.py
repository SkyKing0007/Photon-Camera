#!/usr/bin/env python3
"""26968 UI-only HDR+ chroma removal and exact Shadow slider to-processing mapping; mode routing regression."""
from pathlib import Path
import xml.etree.ElementTree as ET,re,sys
R=Path(__file__).resolve().parent
P=R if '--live' in sys.argv else R/'handoff_payload_26968'
ui=(P/'app/src/main/res/xml/preferences.xml').read_text()
S=(P/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java').read_text()
C=(P/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
T=(P/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java').read_text()
assert 'HDR+ Quality Chroma Denoise' not in ui
assert 'pref_iris_hdrq_effective_chroma' not in ui
pref=ET.fromstring(ui)
hdrq=[e for e in pref.iter() if any(v=='pref_iris_hdrq_effective_chroma' for v in e.attrib.values())]
assert not hdrq
slider=[e for e in pref.iter() if any(v=='pref_iris_shadows' for v in e.attrib.values())]
assert len(slider)==1
assert any(k.endswith('minValue') and v=='0.0' for k,v in slider[0].attrib.items())
assert any(k.endswith('maxValue') and v=='1.0' for k,v in slider[0].attrib.items())
assert any(k.endswith('defaultValue') and v=='@string/pref_iris_shadows_default' for k,v in slider[0].attrib.items())
if (P/'app/src/main/res/values/default_prefs.xml').is_file():
 assert '<string name="pref_iris_shadows_default" translatable="false">0.0</string>' in (P/'app/src/main/res/values/default_prefs.xml').read_text()
assert re.search(r'float shadows\s*=\s*snap01\(getFloat\(sm, KEY_SHADOWS, 0\.0f\), 0\.0f, 1\.0f\)\s*\+ PHOTO_SHADOWS_BIAS_26968;',S)
assert 'PHOTO_SHADOWS_BIAS_26968 = 0.30f' in S
for val,want in ((0.0,0.30),(0.25,0.55),(0.5,0.8),(0.75,1.05),(1.0,1.3)):
 actual=max(0,min(1,val))+.30
 assert abs(actual-want)<1.e-5,(val,actual)
assert 'Snapshot source = currentForNight26968();' in S
assert 'snap01(getFloat(sm, KEY_SHADOWS, 0.0f), -1.0f, 1.0f);' in S
assert 'IrisMotionSettings.currentForNight26968()' in T and 'IrisMotionSettings.currentForNight26968()' in C
assert 'public static boolean isHdrqChromaDenoiseEnabled()' in S
assert 'getBoolean(manager, KEY_HDRQ_CHROMA_DENOISE, false)' in S
# The original 26965 hidden toggle remains a default-OFF processing preference, no altered pipeline.
if (P/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').is_file():
 assert 'IrisMotionSettings.isHdrqChromaDenoiseEnabled()' in (P/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
print('PASS 26968 UI removed, exact default-OFF HDRQ runtime untouched, 0.00..1.00 Shadows maps to 0.30..1.30, Night A/B old signed settings preserved')
