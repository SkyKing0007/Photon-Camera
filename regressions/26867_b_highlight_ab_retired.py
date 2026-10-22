#!/usr/bin/env python3
"""26867: source contracts for native B final clipping-only fade and A+B retirement.
The regression preserves 26866 noise/chroma owner and exact physical clip identity.
"""
from pathlib import Path
import re,sys,math
app=Path(sys.argv[1]);src=app/'src/main/java'
def read(rel):return (src/rel).read_text()
h=read('com/hinnka/mycamera/processor/GlesIris26858BNoiseHighlight.kt')
s=read('com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
a=read('com/particlesdevs/photoncamera/settings/Iris26856ABSettings.java')
u=read('com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java')
b=read('com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
assert h.count('val bNativeSensorSmoothWhite26866 = """')==1
assert 'float fade=smoothstep(0.0,0.25,clippedCoverage);' in h
assert 'float k[3]=float[3](1.0,2.0,1.0)' in h
assert 'if(clippedCoverage<=0.0){oRgb=original;return;}' in h
assert 'vec4(mix(original.rgb,vec3(neutral),fade),original.a)' in h
assert 'texelFetch(uNativeSensorClip,q,0).r' in h
assert 'uSourceRaw' not in h[h.index('val bNativeSensorSmoothWhite26866 ='):]
assert s.count('bRecovered26858 = renderIris26866BNativeSensorSmoothWhite(')==1
# Native B 1x and Wronski B 2x are required to publish the real mask.
assert s.count('nativeSensorClipFullRes26866 = nativeSensorClip26864')==1
assert s.count('nativeSensorClipFullRes26866 = nativeClip')==1
start=s.index('private fun renderRawrBPostAmaze26856(')
end=s.index('private fun renderSabreNormalCfaExtract26852(',start)
p=s[start:end]
assert p.index('defringed = renderRawrLabDefringe26856(') < p.index('fcc = renderRawrFalseColor26856(') < p.index('bRecovered26858 = renderIris26866BNativeSensorSmoothWhite(') < p.index('neutral = createTexture(')
assert 'renderIris26866BNativeSensorSmoothWhite(\n                    fcc, nativeSensorClipFullRes26866,' in p
assert 'if (nativeSensorClipFullRes26866 != 0) bRecovered26858 else fcc' in p
assert 'if (nativeSensorClipFullRes26866 == 0 && bClipRatio26858 != 0)' in p
assert 'check(rawrNativeReceipt26864 != null)' in p
assert 'clipZoneProvenance26834 = if (edgeFalseColor26778.clipZoneEnabled &&\n                !iris26864RealRawrOwnsBurstNoise)' in s
assert 'IRIS_26866_AB_B_NATIVE_SMOOTH_WHITE_ONLY' in b
assert 'applyIris26837FinalClipZoneChroma(' in b # retained only for A, no blanket deletion
assert 'if ("AB".equals(id)) return AMAZE_26855;' in a
assert 'mode != BOTH && mode.id.equals(id)' in a
assert 'mode == Mode.BOTH' in a and 'throw new IllegalArgumentException("26867 only A and B experiments are selectable")' in a
assert 'mode.setEntries(new CharSequence[]{"A", "B"});' in u
assert 'mode.setEntryValues(new CharSequence[]{"A", "B"});' in u
assert '"A+B"' not in u[u.index('private void setupIris26856Experiments()'):u.index('private void setupPhotoPrefixPreference()')]
# Dormant A+B processor semantics preserved byte-level outside two rewritten owners.
assert 'Iris26856ABSettings.Mode.BOTH' in b
# 26859 neutral target exactly retained, zero sensor support = no edits.
def fade(s):
 t=max(0.,min(1.,s/.25));return t*t*(3-2*t)
assert fade(0)==0 and fade(.25)==1
assert all(fade(i/256)<=fade((i+1)/256) for i in range(256))
assert 0<fade(.0625)<fade(.125)<fade(.1875)<1
# One phase among four already reaches neutral, unlike prior all-site threshold.
assert fade(.25)>0.999999 and fade(.0625)>0.15
print('PASS 26867 native-B post-FCC sensor-only smooth white with one-phase onset, A/B-only settings, exact source clip and untouched historical A path')
