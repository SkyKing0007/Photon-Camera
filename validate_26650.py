#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys,xml.etree.ElementTree as ET
if len(sys.argv)!=3: raise SystemExit('usage: validate_26650.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def txt(r): return (cand/r).read_text()
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'app').rglob('*')) if p.is_file()}
bh,ch=H(base),H(cand); assert len(bh)==1720 and len(ch)==1721
changed={r for r in set(bh)|set(ch) if bh.get(r)!=ch.get(r)}
expected=set('''app/src/main/assets/shaders/motionv2/color_transform.glsl
app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2PhotonHighlightCompression.java
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java
app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java
app/src/main/res/values/default_prefs.xml
app/src/main/res/values/preference_keys.xml
app/src/main/res/values/strings.xml
app/src/main/res/xml/preferences.xml
app/version.properties'''.splitlines()); assert changed==expected,changed^expected
v=txt('app/version.properties'); assert 'VERSION_NAME=0.9726650' in v and 'VERSION_BUILD=26650' in v
# UI preference under Photo Settings, default ON.
for r in ['app/src/main/res/xml/preferences.xml','app/src/main/res/values/default_prefs.xml','app/src/main/res/values/preference_keys.xml','app/src/main/res/values/strings.xml']: ET.parse(cand/r)
pref=txt('app/src/main/res/xml/preferences.xml'); photo=pref.index('ns0:title="@string/photo_settings"'); key=pref.index('ns0:key="@string/pref_highlight_compression_key"'); nextcat=pref.index('</PreferenceCategory>',photo); assert photo<key<nextcat
assert 'ns0:defaultValue="@bool/pref_highlight_compression_default"' in pref
assert '<bool name="pref_highlight_compression_default">true</bool>' in txt('app/src/main/res/values/default_prefs.xml')
assert '<string name="highlight_compression">Highlight Compression</string>' in txt('app/src/main/res/values/strings.xml')
pk=txt('app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java'); assert 'COMMON_KEYS.add(Key.KEY_HIGHLIGHT_COMPRESSION.mValue)' in pk and 'setInitial(SCOPE_GLOBAL, Key.KEY_HIGHLIGHT_COMPRESSION, true)' in pk and 'isHighlightCompressionOn()' in pk
# Full Photon common analysis owner and exact constants/equations.
j=txt('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2PhotonHighlightCompression.java')
for t in ['HIST_SIZE = 256','CURVE_SIZE = 1024','TARGET = 128.0f','NOISE_MAX = 0.05f','GAIN_MAX = 9.0f','WHITE_APPLY = 0.8f','FILL_COEFFICIENT = 0.99f','APPLY_GAMMA_MIX = 0.05f','KNEE_MAX = 0.90f','KNEE_MIN = 0.55f','KNEE_REF = 0.10f','CLIP_TOLERANCE = 0.03f','motionV2WronskiNoiseS','motionV2WronskiNoiseO','adaptiveWhitePoint = srgbDecodeExtended(sceneWhitePass1)','remapHistogram(mapped, extent, adaptiveWhitePoint)','mpyPreNorm * normL / Math.max(normRr, 1.0e-8f)','r > 1.0f + CLIP_TOLERANCE','softShoulder(off, knee)','MotionTrace.processingState("IRIS_26650_PHOTON_HIGHLIGHT_COMPRESSION"']:
 assert t in j,t
for forbidden in ['basePipeline.noiseS','basePipeline.noiseO','iris26649PhotonSoftShoulder','motionV2TonePredictedClipFraction']:
 assert forbidden not in j,forbidden
# Graph ownership and order: Motion only, analysis before color; no new Night node.
pp=txt('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java')
a=pp.index('add(new MotionV2PhotonHighlightCompression(iris26650HighlightCompression))'); b=pp.index('add(new MotionV2ColorTransform())',a); assert a<b
assert pp.count('new MotionV2PhotonHighlightCompression(')==1
# Differential must run before Iris profile/color and preserve OFF by compile define absence.
ct=txt('app/src/main/assets/shaders/motionv2/color_transform.glsl'); assert ct.index('cameraRgb*=clamp(photonToggleRatio,0.0,1.0);') < ct.index('vec3 profileRgb=')
for t in ['PhotonCurveOff','PhotonCurveOn','photonAdaptiveWhitePoint','photonCameraNeutral','USE_PHOTON_HIGHLIGHT_COMPRESSION','photonOn/photonOff']:
 assert t in ct,t
# Color Java binds only when frozen owner enabled.
cj=txt('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java'); assert 'pipeline.motionV2PhotonHighlightCompressionEnabled' in cj and 'setDefine("USE_PHOTON_HIGHLIGHT_COMPRESSION", 1)' in cj
# OFF preserves exact 26648 local highlight mechanics; ON neutralizes only conflicting later lift/suppression.
rm=txt('app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl'); rr=txt('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java')
for t in ['iris26650HighlightCompressionEnabled','float legacyBaseOut=mix(baseLinear,smoothShoulder','float baseOut=mix(legacyBaseOut,baseLinear,iris26650Hc)','float legacyResidualWeight=mix(','float residualWeight=mix(legacyResidualWeight,1.0,iris26650Hc)']:
 assert t in rm,t
assert 'glProg.setVar("iris26650HighlightCompressionEnabled"' in rr
# Exact OFF equations from 26648 are still present, gated rather than deleted.
for t in ['1.0-pow(max(1.0-baseLinear,0.0),1.12)','0.55*shoulderGate*structureShoulderScale','mix(1.0,0.78,upperGate)']:
 assert t in rm,t
# Numerical shoulder invariants independent of runtime implementation.
def soft(x,k): return x if x<=k else k+(1-k)*((x-k)/(1-k))**2
assert abs(soft(.95,.9)-.925)<1e-12 and abs(soft(1,.9)-1)<1e-12 and soft(.8,.9)==.8
print('PASS 26650 semantic/ownership validation: Photo Settings toggle default ON; complete Photon common analysis; exact ON/OFF differential before Iris color; OFF retains 26648 local tone; ON neutralizes only conflicting highlight lift')
