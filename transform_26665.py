#!/usr/bin/env python3
from pathlib import Path
import shutil, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: transform_26665.py BASE DEST')
base=Path(sys.argv[1]); dest=Path(sys.argv[2])
if dest.exists(): shutil.rmtree(dest)
shutil.copytree(base,dest)

def replace(path, old, new, count=1):
    p=dest/path
    s=p.read_text()
    actual=s.count(old)
    if actual != count:
        raise SystemExit(f'anchor count {path}: expected {count}, got {actual}: {old[:120]!r}')
    p.write_text(s.replace(old,new))

# Parameters: one new presentation-only scalar. No capture/noise/merge owner consumes it.
replace(Path('app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java'),
'''    public float motionV2GlobalBodyLiftEv = 0.0f;\n''',
'''    public float motionV2GlobalBodyLiftEv = 0.0f;\n    /* IRIS_26665_BLACK_SAFE_SHADOW_DEPTH\n     * Scene-global lower-body depth in EV. The final transfer is identity below the protected\n     * near-black floor and by normal body tones, so it restores depth without creating empty black. */\n    public float motionV2ShadowDepthEv = 0.0f;\n''')

matcher=Path('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java')
replace(matcher,
'''        basePipeline.mParameters.motionV2GlobalBodyLiftEv = 0.0f;\n''',
'''        basePipeline.mParameters.motionV2GlobalBodyLiftEv = 0.0f;\n        basePipeline.mParameters.motionV2ShadowDepthEv = 0.0f;\n''')

replace(matcher,
'''                Log.i(Name, "IRIS_26662_CANONICAL_REFERENCE_PRESENTATION_SOLVE"\n                        + " referenceProtectionEv=" + referenceProtectionEv\n                        + " referenceRestoreGain=" + referenceRestoreGain\n                        + " candidateMeterCanonicalized=true"\n                        + " protectionResidualEvAdded=false"\n                        + " longGlobalBrightnessAuthority=false");\n            }\n            float gain = (float)Math.pow(2.0, solvedEv);\n''',
'''                Log.i(Name, "IRIS_26662_CANONICAL_REFERENCE_PRESENTATION_SOLVE"\n                        + " referenceProtectionEv=" + referenceProtectionEv\n                        + " referenceRestoreGain=" + referenceRestoreGain\n                        + " candidateMeterCanonicalized=true"\n                        + " protectionResidualEvAdded=false"\n                        + " longGlobalBrightnessAuthority=false");\n            }\n\n            /* IRIS_26665_LOW_KEY_SCENE_INTENT\n             * The viewfinder remains scene-key guidance, never a literal black/highlight target.\n             * Reduce presentation exposure only when three independent scene-global conditions\n             * agree: the canonical median is very dark, the canonical P95 is also dark, and the\n             * decoded viewfinder body is dark. Highlight-protected HDR captures fail closed to the\n             * exact 26664 solve. ISO/shutter/scene semantics do not participate. */\n            float iris26665LowKeyIntent = 0.0f;\n            float iris26665LowKeyReductionEv = 0.0f;\n            if (!iris26550Night\n                    && Float.isFinite(iris26639CandidateP50Guide)\n                    && Float.isFinite(iris26582CandidateP95Guide)\n                    && Float.isFinite(targetLog)) {\n                float targetLinearLuma26665 = (float)Math.pow(2.0, targetLog);\n                float unprotected26665 = 1.0f - smoothstep(0.02f, 0.08f, referenceProtectionEv);\n                float medianDark26665 = 1.0f - smoothstep(0.010f, 0.030f, iris26639CandidateP50Guide);\n                float upperDark26665 = 1.0f - smoothstep(0.035f, 0.090f, iris26582CandidateP95Guide);\n                float previewDark26665 = 1.0f - smoothstep(0.035f, 0.080f, targetLinearLuma26665);\n                iris26665LowKeyIntent = clamp(unprotected26665 * medianDark26665\n                        * upperDark26665 * previewDark26665, 0.0f, 1.0f);\n                iris26665LowKeyReductionEv = 0.70f * iris26665LowKeyIntent;\n                solvedEv = clamp(solvedEv - iris26665LowKeyReductionEv, MIN_EV, MAX_EV);\n                Log.i(Name, "IRIS_26665_LOW_KEY_SCENE_INTENT"\n                        + " candidateP50Guide=" + iris26639CandidateP50Guide\n                        + " candidateP95Guide=" + iris26582CandidateP95Guide\n                        + " viewfinderBodyLinear=" + targetLinearLuma26665\n                        + " referenceProtectionEv=" + referenceProtectionEv\n                        + " intent=" + iris26665LowKeyIntent\n                        + " reductionEv=" + iris26665LowKeyReductionEv\n                        + " maxReductionEv=0.70"\n                        + " isoDriven=false shutterDriven=false sceneSemantic=false"\n                        + " protectedHdrExact26664=true nightRouteUnchanged=true");\n            }\n            float gain = (float)Math.pow(2.0, solvedEv);\n''')

replace(matcher,
'''            basePipeline.mParameters.motionV2ShadowBodyStrength = shadowStrength26639;\n            basePipeline.mParameters.motionV2ShadowBodyEnd = shadowBodyEnd26639;\n            Log.i(Name, "IRIS_26639_SIGNAL_DRIVEN_SHADOW_BODY"\n''',
'''            basePipeline.mParameters.motionV2ShadowBodyStrength = shadowStrength26639;\n            basePipeline.mParameters.motionV2ShadowBodyEnd = shadowBodyEnd26639;\n\n            /* IRIS_26665_BLACK_SAFE_SHADOW_DEPTH_DECISION\n             * Restore lower-body separation only when the completed global map crowds P25 toward\n             * P50. This is a scene-global scalar, not a spatial mask. Existing 26639 correction\n             * wins if already active, and deliberate highlight protection disables this correction\n             * entirely so the successful 26664 chandelier/HDR presentation remains exact. */\n            float shadowDepthEv26665 = 0.0f;\n            if (!iris26550Night && Float.isFinite(lowerCrowding26639)\n                    && Float.isFinite(bodyDrEv26639)) {\n                float unprotected26665 = 1.0f - smoothstep(0.02f, 0.08f, referenceProtectionEv);\n                float legacyFree26665 = 1.0f - smoothstep(0.05f, 0.20f, shadowStrength26639);\n                float crowdingExcessEv26665 = clamp(\n                        log2(Math.max(lowerCrowding26639, 1.0e-6f) / 0.40f),\n                        0.0f, 0.45f);\n                float bodyDrGate26665 = smoothstep(0.80f, 1.20f, bodyDrEv26639);\n                shadowDepthEv26665 = clamp(crowdingExcessEv26665 * bodyDrGate26665\n                        * unprotected26665 * legacyFree26665, 0.0f, 0.45f);\n            }\n            basePipeline.mParameters.motionV2ShadowDepthEv = shadowDepthEv26665;\n            Log.i(Name, "IRIS_26665_BLACK_SAFE_SHADOW_DEPTH"\n                    + " mappedP25=" + mappedP25\n                    + " mappedP50=" + mappedP50\n                    + " lowerCrowding=" + lowerCrowding26639\n                    + " bodyDrEv=" + bodyDrEv26639\n                    + " legacy26639Strength=" + shadowStrength26639\n                    + " referenceProtectionEv=" + referenceProtectionEv\n                    + " shadowDepthEv=" + shadowDepthEv26665\n                    + " maxDepthEv=0.45 nearBlackIdentity=0.004 bodyIdentity=0.30"\n                    + " spatialMask=false monotone=true nightRouteUnchanged=true");\n            Log.i(Name, "IRIS_26639_SIGNAL_DRIVEN_SHADOW_BODY"\n''')

# Final render + gain-map uniform handoff and telemetry.
render_java=Path('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java')
replace(render_java,
'''            glProg.setVar("iris26664GlobalBodyLiftEv",\n                    basePipeline.mParameters.motionV2GlobalBodyLiftEv);\n            glProg.setVar("iris26621LocalToneEnabled", iris26621LocalTone != null ? 1 : 0);\n''',
'''            glProg.setVar("iris26664GlobalBodyLiftEv",\n                    basePipeline.mParameters.motionV2GlobalBodyLiftEv);\n            glProg.setVar("iris26665ShadowDepthEv",\n                    basePipeline.mParameters.motionV2ShadowDepthEv);\n            glProg.setVar("iris26621LocalToneEnabled", iris26621LocalTone != null ? 1 : 0);\n''')
replace(render_java,
'''            Log.i(Name, "IRIS_26664_GLOBAL_LOG_BODY_TONE"\n                    + " bodyLiftEv=" + basePipeline.mParameters.motionV2GlobalBodyLiftEv\n                    + " fullLiftBelowGuide=0.08 fadeToIdentityGuide=0.65"\n                    + " residualResponsePercent=65.0 spatialMask=false"\n                    + " c1=true monotone=true highlightOwner26660Frozen=true");\n''',
'''            Log.i(Name, "IRIS_26664_GLOBAL_LOG_BODY_TONE"\n                    + " bodyLiftEv=" + basePipeline.mParameters.motionV2GlobalBodyLiftEv\n                    + " fullLiftBelowGuide=0.08 fadeToIdentityGuide=0.65"\n                    + " residualResponsePercent=65.0 spatialMask=false"\n                    + " c1=true monotone=true highlightOwner26660Frozen=true");\n            Log.i(Name, "IRIS_26665_BLACK_SAFE_SHADOW_DEPTH_RENDER"\n                    + " shadowDepthEv=" + basePipeline.mParameters.motionV2ShadowDepthEv\n                    + " nearBlackIdentityThrough=0.004 bodyIdentityFrom=0.30"\n                    + " spatialMask=false c1=true monotone=true"\n                    + " localLaplacianBytesUnchanged=true highlightOwner26660Frozen=true");\n''')
replace(render_java,
'''                glProg.setVar("displayGain", basePipeline.mParameters.motionV2DisplayGain);\n                glProg.setVar("motionHdrHandoff", basePipeline.mParameters.motionV2Active ? 1 : 0);\n                glProg.setVar("maxGainRatio", encodingMaxGainRatio);\n''',
'''                glProg.setVar("displayGain", basePipeline.mParameters.motionV2DisplayGain);\n                glProg.setVar("motionHdrHandoff", basePipeline.mParameters.motionV2Active ? 1 : 0);\n                glProg.setVar("iris26665ShadowDepthEv",\n                        basePipeline.mParameters.motionV2ShadowDepthEv);\n                glProg.setVar("maxGainRatio", encodingMaxGainRatio);\n''')

# Runtime final-render shadow curve: exact identity at true near-black and >=0.30, C1 and monotone.
render_glsl=Path('app/src/main/assets/shaders/motionv2/render.glsl')
replace(render_glsl,
'''uniform float iris26664GlobalBodyLiftEv;\n''',
'''uniform float iris26664GlobalBodyLiftEv;\nuniform float iris26665ShadowDepthEv;\n''')
replace(render_glsl,
'''float iris26660ObjectColorGamma(float mappedGuide){\n''',
'''/* IRIS_26665_BLACK_SAFE_SHADOW_DEPTH\n * Scene-global lower-body depth without a spatial mask. Values at/below 0.004 linear remain exact\n * 26664 so real near-black information cannot be pushed into empty black. The C1 quartic log-domain\n * bump reaches its bounded maximum inside the broad-shadow range and is exact identity again by\n * 0.30. At the 0.45 EV cap the minimum log-domain derivative remains >0.77. */\nfloat iris26665BlackSafeShadowDepth(float mappedGuide){\n    float y=max(mappedGuide,0.0);\n    if(iris26592MotionHdrHandoff==0 || y<=0.004 || y>=0.30) return y;\n    float depthEv=clamp(iris26665ShadowDepthEv,0.0,0.45);\n    if(depthEv<=1.0e-7) return y;\n    const float floorLog=-7.9657842847; /* log2(0.004) */\n    const float bodyLog=-1.7369655942;  /* log2(0.30) */\n    float logY=log2(max(y,1.0e-8));\n    float t=clamp((logY-floorLog)/(bodyLog-floorLog),0.0,1.0);\n    float bump=16.0*t*t*(1.0-t)*(1.0-t);\n    return y*exp2(-depthEv*bump);\n}\n\nfloat iris26660ObjectColorGamma(float mappedGuide){\n''')
replace(render_glsl,
'''    mappedGuide=iris26664GlobalBodyTone(mappedGuide);\n    mappedGuide=iris26660ObjectColorGamma(mappedGuide);\n''',
'''    mappedGuide=iris26664GlobalBodyTone(mappedGuide);\n    mappedGuide=iris26665BlackSafeShadowDepth(mappedGuide);\n    mappedGuide=iris26660ObjectColorGamma(mappedGuide);\n''')
replace(render_glsl,
'''            mappedGuide=iris26664GlobalBodyTone(mappedGuide);\n            mappedGuide=iris26660ObjectColorGamma(mappedGuide);\n''',
'''            mappedGuide=iris26664GlobalBodyTone(mappedGuide);\n            mappedGuide=iris26665BlackSafeShadowDepth(mappedGuide);\n            mappedGuide=iris26660ObjectColorGamma(mappedGuide);\n''')

# Gain-map model mirrors only the new SDR shadow-depth transfer. 26664 body lift starts at 0.10 EV protection;
# 26665 shadow-depth reaches exact zero by 0.08 EV, so these two correction domains never overlap.
gain=Path('app/src/main/assets/shaders/motionv2/gainmap.glsl')
replace(gain,
'''uniform float iris26653AdaptiveWhitePoint;\n''',
'''uniform float iris26653AdaptiveWhitePoint;\nuniform float iris26665ShadowDepthEv;\n''')
replace(gain,
'''float iris26640SharedSdrGuide(float sourceGuide,vec2 masterSourcePixel){\n''',
'''/* IRIS_26665_UHDR_SHADOW_DEPTH_PARITY\n * Exact scalar mirror of the final SDR lower-body transfer. The gain-map numerator remains the\n * successful 26658 HDR target; only the matched SDR intent model follows the completed SDR base. */\nfloat iris26665BlackSafeShadowDepth(float mappedGuide){\n    float y=max(mappedGuide,0.0);\n    if(motionHdrHandoff==0 || y<=0.004 || y>=0.30) return y;\n    float depthEv=clamp(iris26665ShadowDepthEv,0.0,0.45);\n    if(depthEv<=1.0e-7) return y;\n    const float floorLog=-7.9657842847;\n    const float bodyLog=-1.7369655942;\n    float logY=log2(max(y,1.0e-8));\n    float t=clamp((logY-floorLog)/(bodyLog-floorLog),0.0,1.0);\n    float bump=16.0*t*t*(1.0-t)*(1.0-t);\n    return y*exp2(-depthEv*bump);\n}\n\nfloat iris26640SharedSdrGuide(float sourceGuide,vec2 masterSourcePixel){\n''')
replace(gain,
'''float iris26660SharedSdrGuide(float sourceGuide,vec2 masterSourcePixel){\n    return iris26660ObjectColorGamma(iris26640SharedSdrGuide(sourceGuide,masterSourcePixel));\n}\n''',
'''float iris26660SharedSdrGuide(float sourceGuide,vec2 masterSourcePixel){\n    float sharedGuide26665=iris26640SharedSdrGuide(sourceGuide,masterSourcePixel);\n    sharedGuide26665=iris26665BlackSafeShadowDepth(sharedGuide26665);\n    return iris26660ObjectColorGamma(sharedGuide26665);\n}\n''')

# Version/build together with runtime change.
version=dest/'app/version.properties'
vs=version.read_text()
for old,new in [('VERSION_NAME=0.9726664','VERSION_NAME=0.9726665'),('VERSION_BUILD=26664','VERSION_BUILD=26665')]:
    if vs.count(old)!=1: raise SystemExit(f'version anchor count {old}: {vs.count(old)}')
    vs=vs.replace(old,new)
version.write_text(vs)

print('PASS 26665 deterministic transform: scene-key intent + black-safe shadow depth; exact 6-file scope')
