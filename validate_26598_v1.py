#!/usr/bin/env python3
from pathlib import Path
import hashlib, re, sys

CHANGED=[x for x in '''app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl
app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java
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

render_java=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
appearance_java=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java').read_text()
appearance_shader=(c/'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl').read_text()
encoder=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java').read_text()
ver=(c/'app/version.properties').read_text()

# New single final-publication semantic authority. Motion uses body/physical base sceneWhite;
# Night deliberately retains the successful pre-26598 adaptive scene-white authority.
for t in [
    'IRIS_26598_MOTION_PUBLICATION_SCENE_WHITE_AUTHORITY',
    'public static float iris26598PublicationSceneWhite(Parameters parameters)',
    'if (parameters.motionV2Active) return baseWhite;',
    'float adaptiveWhite = parameters.motionV2ToneAdaptiveSceneWhite;',
    'float sceneWhite = iris26598PublicationSceneWhite(basePipeline.mParameters);',
    'publicationSceneWhiteSource=',
    'IRIS_26598_SEMANTIC_AUTHORITY=true']:
    req(t in render_java,'render semantic authority '+t)
req('import com.particlesdevs.photoncamera.processing.render.Parameters;' in render_java,'render Parameters import')

# Tone-aware highlight chroma prediction must consume the same publication sceneWhite and model
# the exact successful-26597 Motion publication curve, while Night keeps the old predictor.
for t in [
    'MotionV2Render.iris26598PublicationSceneWhite(basePipeline.mParameters)',
    'glProg.setVar("iris26598MotionPublication",',
    'EXACT_26597_MOTION',
    'PRESERVED_26585_NIGHT']:
    req(t in appearance_java,'appearance semantic parity '+t)
for t in [
    'uniform int iris26598MotionPublication;',
    'IRIS_26598_TONE_AWARE_PREDICTOR_PARITY',
    'const float sceneAnchor = 0.834284246;',
    'const float tailSlope = 5.03442907;',
    'shaped = sceneAnchor * u;',
    'shaped = 1.0 - (1.0 - sceneAnchor) / (1.0 + tailSlope * (u - 1.0));',
    'shaped = log(1.0 + logShape * x) / log(1.0 + logShape);']:
    req(t in appearance_shader,'appearance shader parity '+t)

# True-2x native publication already mirrors 26597; Java must now pass the same single publication
# scale as the normal render instead of stale adaptiveSceneWhite.
for t in [
    'import com.particlesdevs.photoncamera.processing.opengl.postpipeline.MotionV2Render;',
    'MotionV2Render.iris26598PublicationSceneWhite(parameters)',
    'publicationSceneWhite, parameters.motionV2Active',
    'IRIS_26598_TRUE2X_TONE_PARITY=true']:
    req(t in encoder,'true2x semantic parity '+t)
req('parameters.motionV2ToneAdaptiveSceneWhite, parameters.motionV2Active' not in encoder,
    'stale adaptive sceneWhite still drives true2x publication')

# Stale-behavior absence: the adaptive value may now exist only as producer/state, Night fallback,
# and diagnostics. It must not directly drive any final Motion publication consumer.
all_java='\n'.join(p.read_text(errors='ignore') for p in sorted((c/'app/src/main/java').rglob('*.java')))
req('glProg.setVar("sceneWhite", basePipeline.mParameters.motionV2ToneAdaptiveSceneWhite)' not in all_java,
    'direct adaptive sceneWhite shader publication survived')
req('writeTrue2xNative' in encoder,'true2x call missing')
# Exact direct-field occurrence universe is intentional: selector Night branch + three diagnostics +
# Viewfinder producer reset/write + Parameters state declaration.
occ=[]
for p in sorted((c/'app/src/main/java').rglob('*.java')):
    for i,line in enumerate(p.read_text(errors='ignore').splitlines(),1):
        if 'motionV2ToneAdaptiveSceneWhite' in line:
            occ.append((str(p.relative_to(c)),i,line.strip()))
req(len(occ)==7,'unexpected adaptiveSceneWhite occurrence count '+repr(occ))
allowed_files={
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java'}
req({x[0] for x in occ}==allowed_files,'unexpected adaptiveSceneWhite owner file '+repr(occ))

# Preserve successful 26597 highlight math and every unrelated architectural owner byte-identically.
protected=[
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java']
for rr in protected:
    req((b/rr).is_file() and H(b/rr)==H(c/rr),'protected owner changed '+rr)

# Explicitly prove the stored base value still comes from the frozen display/body solve and that the
# old adaptive producer is retained for diagnostics/Night rather than deleted or repurposed.
matcher=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java').read_text()
for t in [
    'basePipeline.mParameters.motionV2DisplayGain = gain;',
    'basePipeline.mParameters.motionV2ToneBaseSceneWhite = iris26583Tone.baseSceneWhite;',
    'basePipeline.mParameters.motionV2ToneAdaptiveSceneWhite = iris26583Tone.adaptiveSceneWhite;',
    'float baseWhite = MotionV2Render.iris26582BaseSceneWhite(gain);',
    'IRIS_26586_VIEWFINDER_TONE_AUTHORITY_SPLIT']:
    req(t in matcher,'upstream body/scene-white ownership '+t)

# 26598 exact Motion capture ownership: same slider budget, immutable pre-shutter NORMALs,
# timestamp-owned missing NORMALs, one-deep deferred shutter, and SR as downstream consumer only.
capture=(c/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
for t in [
 'IRIS_26598_MOTION_HAL_QUEUE_DRAIN_OWNER',
 'IRIS_26598_GENERATION_OWNED_NORMAL_RAW_INGRESS',
 'IRIS_26598_PRE_SHUTTER_NORMAL_OWNERSHIP_TRANSFER',
 'IRIS_26598_EXPLICIT_GENERATION_OWNED_NORMAL_TOPUP',
 'IRIS_26598_IMMUTABLE_NORMAL_SET_DRAIN',
 'IRIS_26598_ONE_DEEP_DEFERRED_MOTION_SHUTTER',
 'IRIS_26598_EXACT_TOTAL_OWNERSHIP_PROOF',
 'mZslRingBuffer.iterator()',
 'iris26598Plan.tryOwnTopUpRaw(img)',
 'new Motion26598NormalTopUpTag(ticket)',
 'captureStartedTimestampNs',
 'resultTimestampNs',
 'if (missingNormals > 0 || auxiliaryExpected) return MOTION_26593_MAX_CAPTURE_COMPLETION_MS;',
 'latchMotion26598DeferredShutter',
 'scheduleMotion26598DeferredShutterReplay']:
    req(t in capture,'capture ownership '+t)
req('List<Image> rawImages = validAtDrain >= mMotionTopUpMinimumFrames\n                ? iris26593Plan.takeOwnedNormalImages() : null;' in capture,
    'finalization does not exclusively consume plan-owned NORMALs')
req('new ArrayList<>(mZslRingBuffer)' not in capture[capture.index('private void finalizeMotionZslCapture'):capture.index('// IRIS_26343_GENERATION_SAFE_ZSL')],
    'rolling ZSL ring survived as post-shutter finalization source')
req('if (mZslCapturing\n                || mMotion26486InFlightBatches.get() >= MOTION_26486_MAX_INFLIGHT_BATCHES) {\n            latchMotion26598DeferredShutter' in capture,
    'old trigger busy early-return survived without deferred intent')
req('mMotion26575SuperResAtShutter = PreferenceKeys.isIrisSuperResOn();' in capture,
    'SR shutter snapshot missing')
req('final int iris26593NormalTarget = iris26593TotalTarget - iris26593AuxCount;' in capture,
    'exact total NORMAL budget formula changed')
# Critical downstream owners stay byte-identical; SR must not become a second acquisition authority.
for rr in [
 'app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java']:
    req((b/rr).read_bytes()==(c/rr).read_bytes(),'capture/SR downstream owner changed '+rr)

# Version/build increment is part of the frozen candidate, not a later live mutation.
req('VERSION_NAME=0.9726598' in ver and 'VERSION_BUILD=26598' in ver,'version/build')

print('PASS exact six-file runtime scope; successful-26597 render/SHORT/Sabre/global-exposure/UHDR owners otherwise byte-identical')
print('PASS Motion publication sceneWhite single-owner: BASE; Night adaptive authority preserved')
print('PASS adaptive highlight-chroma predictor uses exact 26597 Motion curve and preserved Night curve')
print('PASS normal 1x + true2x publication consume one sceneWhite selector; stale adaptive Motion consumer absent')
