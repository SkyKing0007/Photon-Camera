#!/usr/bin/env python3
from pathlib import Path
import hashlib,math,sys,xml.etree.ElementTree as ET
if len(sys.argv)!=3:raise SystemExit('usage: validate_26704.py BASE26703 CANDIDATE')
b=Path(sys.argv[1]);c=Path(sys.argv[2])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def files(root):return {'app/'+str(p.relative_to(root/'app')):sha(p) for p in sorted((root/'app').rglob('*')) if p.is_file()}
def txt(root,rel):return (root/rel).read_text()
def method(text,sig):
 i=text.index(sig);brace=text.index('{',i);d=0
 for j in range(brace,len(text)):
  if text[j]=='{':d+=1
  elif text[j]=='}':
   d-=1
   if d==0:return text[i:j+1]
 raise AssertionError(sig)
B=files(b);C=files(c);assert len(B)==len(C)==1823
changed={k for k in set(B)|set(C) if B.get(k)!=C.get(k)}
expected=set(x.strip() for x in (Path(__file__).resolve().parent/'26704_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x.strip())
assert len(expected)==11 and changed==expected,(changed^expected)
# Version only.
v=txt(c,'app/version.properties');bv=txt(b,'app/version.properties');assert 'VERSION_NAME=0.9726704' in v and 'VERSION_BUILD=26704' in v
assert v==bv.replace('VERSION_NAME=0.9726703','VERSION_NAME=0.9726704').replace('VERSION_BUILD=26703','VERSION_BUILD=26704')
# Settings: entries gone, implementations retained, stale TRUE ignored.
prefs=txt(c,'app/src/main/res/xml/preferences.xml'); assert 'pref_highlight_compression_key' not in prefs and 'pref_iris_local_laplacian_tone' not in prefs
ET.parse(c/'app/src/main/res/xml/preferences.xml');ET.parse(c/'app/src/main/res/values/default_prefs.xml')
defp=txt(c,'app/src/main/res/values/default_prefs.xml');assert '<bool name="pref_highlight_compression_default">false</bool>' in defp
pk=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java');assert 'KEY_HIGHLIGHT_COMPRESSION, false' in pk
assert 'public static boolean isHighlightCompressionOn()' in pk and 'return false;' in method(pk,'    public static boolean isHighlightCompressionOn()')
ims=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java');assert 'return false;' in method(ims,'    public static boolean isLocalLaplacianToneEnabled()')
par=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java');assert 'motionV2LocalLaplacianToneEnabled = false;' in par
# Underlying experimental implementations are retained byte-identical where they live outside necessary plumbing.
assert (b/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2PhotonHighlightCompression.java').read_bytes()==(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2PhotonHighlightCompression.java').read_bytes()
br=txt(b,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java');cr=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java')
for sig in ['    private GLTexture iris26621BuildLocalLaplacianTone(','    private GLTexture iris26626ApplyBoundedSourceDomainPreservation(']:assert method(br,sig)==method(cr,sig),sig
# Chroma gate: consensus retained, but valid NORMAL can no longer be overridden by visual deficit.
sabre=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
assert 'localNormalChromaConsensus(' in sabre
assert 'float colorRecoveryNeed = allColorSupportLost;' in sabre
assert 'visualColorDeficit' not in sabre
assert 'IRIS_26704_VALID_NORMAL_CHROMA_IMMUTABLE' in sabre
# SHORT inference: literal physical loss retained, inferred loss requires NORMAL highlight context; low support attenuates, never divides/boosts.
for token in ['float physicalNormalLoss = clamp(1.0 - normalSourceConfidence, 0.0, 1.0);','float normalRadiometricGuide = secondHighest3(max(normalMean.rgb, vec3(0.0)));','float inferredHighlightContext = smoothstep(0.22, 0.50, normalRadiometricGuide);','inferredRadiometricLoss *= inferredHighlightContext;','float measuredNormalLoss = max(physicalNormalLoss, inferredRadiometricLoss);','shortConfidence * measuredNormalLoss * transitionSupport']:
 assert token in sabre,token
assert 'shortConfidence * measuredNormalLoss / max(transitionSupport' not in sabre
# Body tone source/per-pixel contract + true2x mirrors.
for token in ['iris26704BodyToneStrength(Parameters p)','darkBody * darkMass * brightArea','mappedIdentityFrom=0.35']:
 assert token in cr,token
render=txt(c,'app/src/main/assets/shaders/motionv2/render.glsl');assert 'uniform float iris26704BodyToneStrength;' in render and 'mappedGuide=iris26704BodyToneGuide(mappedGuide);' in render
assert 'const float anchorGuide=0.35;' in render and 'smoothstep(0.004,0.018,y)' in render
enc=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java');assert 'MotionV2Render.iris26704BodyToneStrength(parameters)' in enc and 'float bodyToneStrength, boolean motionHdrHandoff' in enc
cpp=txt(c,'app/src/main/cpp/motionv2_jpeg444_jni.cpp')
for token in ['bodyToneStrength=0.f','IRIS_26704_RANGE_SEPARATED_BODY_TONE_TRUE2X_CPU','globalMapped=iris26704BodyToneGuide(globalMapped,p.bodyToneStrength);','uniform float uBodyToneStrength;','IRIS_26704_RANGE_SEPARATED_BODY_TONE_TRUE2X_GPU','globalMapped=iris26704BodyToneGuide(globalMapped);','glUniform1f(loc("uBodyToneStrength"),params->bodyToneStrength)','jfloat sceneWhite,jfloat bodyToneStrength,jboolean motionHdrHandoff']:
 assert token in cpp,token
# No gainmap shader change: recovered highlight/UHDR owner remains protected.
assert (b/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_bytes()==(c/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_bytes()
# Spektra 26703 fix remains byte-identical.
for rel in ['app/src/main/java/com/unspektrawesome/capture/FrameGeometrySnapshot.kt','app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt']:
 assert (b/rel).read_bytes()==(c/rel).read_bytes(),rel
print('PASS validate 26704: exact 11-file scope; settings forced OFF; valid NORMAL chroma immutable; fail-closed inferred SHORT; pointwise body tone + True2x parity; 26703 Spektra/UHDR owners preserved')
