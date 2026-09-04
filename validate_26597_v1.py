#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
CHANGED=[x for x in '''app/src/main/assets/shaders/motionv2/render.glsl
app/src/main/cpp/motionv2_jpeg444_jni.cpp
app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
app/version.properties'''.splitlines() if x]
def fail(m): raise SystemExit('FAIL: '+m)
def req(c,m):
    if not c: fail(m)
def H(p): return hashlib.sha256(p.read_bytes()).hexdigest()
if len(sys.argv)!=3: fail('usage base candidate')
b,c=map(Path,sys.argv[1:])
bp={str(p.relative_to(b)):H(p) for p in sorted((b/'app').rglob('*')) if p.is_file()}
cp={str(p.relative_to(c)):H(p) for p in sorted((c/'app').rglob('*')) if p.is_file()}
req(set(bp)==set(cp) and len(bp)==1708,'full app universe')
changed=[r for r in bp if bp[r]!=cp[r]]
req(changed==CHANGED,'exact changed allowlist '+repr(changed))
render=(c/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
native=(c/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
sabre=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
ver=(c/'app/version.properties').read_text()
# Universal body-anchored highlight reserve. Exposure solve / display gain owners are protected, not changed.
for t in ['IRIS_26597_BODY_ANCHORED_UNIVERSAL_HIGHLIGHT_RESERVE','IRIS_26597_V1_1_ESSL_CONSTANT_INITIALIZER_FIX','const float sceneAnchor=0.834284246','const float tailSlope=5.03442907','shaped=sceneAnchor*max(u,0.0)','1.0-(1.0-sceneAnchor)/(1.0+tailSlope*(u-1.0))']:
    req(t in render,'1x highlight reserve '+t)
req('logCoordinate=log(1.0+logShape*u)/log(1.0+logShape)' not in render,'old concave Motion HDR shoulder survived in 1x')
for t in ['IRIS_26597_BODY_ANCHORED_UNIVERSAL_HIGHLIGHT_RESERVE','const float a=std::tanh(1.2020679f)','shaped=u<=1.f?a*std::max(u,0.f):1.f-(1.f-a)/(1.f+k*(u-1.f))','float a=tanh(1.2020679)','shaped=u<=1.0?a*max(u,0.0):1.0-(1.0-a)/(1.0+k*(u-1.0))']:
    req(t in native,'true2x highlight mirror '+t)
# Remaining SHORT restriction corrected only for actual sensor-loss phases; near-clip path retains all-phase reserve.
for t in ['IRIS_26597_PHASE_SCOPED_SHORT_HEADROOM','if (supportPeak >= 0.995) return false','shortSupportPeak[phase] >= uShortHeadroomThreshold','allShortPhasesHaveStrongHeadroom','if (!allShortPhasesHaveStrongHeadroom(shortSupportPeak))']:
    req(t in sabre,'phase-scoped SHORT '+t)
mask=sabre[sabre.index('val shortRestoreMask26596'):sabre.index('val shortRestoreMaskProbe26590')]
req('if (samePhasePeak(support) >= uShortHeadroomThreshold) return false' not in mask,'old all-phase 0.90 veto survived')
for banned in ['uShortWeight','uUnblocker','uShortWeightThreshold','uUnblockerThreshold']:
    req(banned not in mask,'photometric/unblocker final veto revived '+banned)
# Explicitly prove global exposure/tone-body owners and 26596 UHDR metadata are byte-identical.
protected=[
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java']
for rr in protected:
    req((b/rr).is_file() and H(b/rr)==H(c/rr),'protected owner changed '+rr)
req('VERSION_NAME=0.9726597' in ver and 'VERSION_BUILD=26597' in ver,'version/build')
print('PASS exact four-file runtime scope; global exposure/display solve, UHDR metadata, DNG/ImageSaver/Hdrx unchanged')
print('PASS 1x + true2x universal body-anchored highlight reserve; old concave Motion HDR shoulder absent')
print('PASS actual-sensor-loss SHORT headroom scoped to clipped phases; near-clip path remains all-phase fail-closed')
