#!/usr/bin/env python3
import shutil, sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit('usage: transform_26666.py BASE OUT')
base=Path(sys.argv[1]).resolve(); out=Path(sys.argv[2]).resolve()
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out)

def edit(rel, old, new, count=1):
    p=out/rel
    s=p.read_text()
    n=s.count(old)
    if n != count:
        raise SystemExit(f'anchor count {rel}: expected {count}, got {n}: {old[:100]!r}')
    p.write_text(s.replace(old,new,count))

# Version
edit('app/version.properties','VERSION_NAME=0.9726665\nVERSION_BUILD=26665\n','VERSION_NAME=0.9726666\nVERSION_BUILD=26666\n')

# Parameters: independent post-capture high-DR body recovery scalar.
edit('app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
'''    public float motionV2GlobalBodyLiftEv = 0.0f;\n    /* IRIS_26665_BLACK_SAFE_SHADOW_DEPTH\n''',
'''    public float motionV2GlobalBodyLiftEv = 0.0f;\n    /* IRIS_26666_HIGH_DR_BODY_RECOVERY\n     * Additional post-capture body-only recovery for a photon-starved high-DR Motion scene.\n     * It is zero for the exact 26665 path, black-safe, and reaches identity before highlights. */\n    public float motionV2HighDrBodyLiftEv = 0.0f;\n    /* IRIS_26665_BLACK_SAFE_SHADOW_DEPTH\n''')

# Matcher reset and high-DR decision. Keep the 65% global solve byte-equivalent.
matcher='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java'
edit(matcher,
'''        basePipeline.mParameters.motionV2GlobalBodyLiftEv = 0.0f;\n        basePipeline.mParameters.motionV2ShadowDepthEv = 0.0f;\n''',
'''        basePipeline.mParameters.motionV2GlobalBodyLiftEv = 0.0f;\n        basePipeline.mParameters.motionV2HighDrBodyLiftEv = 0.0f;\n        basePipeline.mParameters.motionV2ShadowDepthEv = 0.0f;\n''')
edit(matcher,
'''            if (!Float.isFinite(gain) || gain <= 0.0f) {\n                throw new IllegalStateException("non-finite solved viewfinder gain");\n            }\n''',
'''            /* IRIS_26666_POST_CAPTURE_HIGH_DR_BODY_RECOVERY\n             * Preserve the proven 26660/26665 65% global presentation solve exactly. Only after\n             * shutter/reconstruction, detect the failure class seen in 26665: a severely starved\n             * canonical body (low P50), a real bright tail (P99), and a large measured viewfinder\n             * mismatch. The new scalar only supplies the portion not already owned by 26664 body\n             * recovery. No ISO/shutter/sun semantic/effective-support input participates. */\n            float iris26666HighDrIntent = 0.0f;\n            float iris26666HighDrExtraBodyLiftEv = 0.0f;\n            if (!iris26550Night\n                    && Float.isFinite(rawSolvedEv)\n                    && Float.isFinite(iris26639CandidateP50Guide)\n                    && Float.isFinite(iris26550CandidateP99Guide)) {\n                float bodyStarved26666 = 1.0f - clamp(\n                        (iris26639CandidateP50Guide - 0.040f) / (0.080f - 0.040f),\n                        0.0f, 1.0f);\n                float brightTail26666 = clamp(\n                        (iris26550CandidateP99Guide - 0.25f) / (0.45f - 0.25f),\n                        0.0f, 1.0f);\n                float mismatch26666 = clamp((rawSolvedEv - 1.40f) / (2.20f - 1.40f),\n                        0.0f, 1.0f);\n                float rawIntent26666 = bodyStarved26666 * brightTail26666 * mismatch26666;\n                iris26666HighDrIntent = rawIntent26666 <= 0.20f ? 0.0f\n                        : clamp((rawIntent26666 - 0.20f) / 0.80f, 0.0f, 1.0f);\n                float postSolveErrorEv26666 = exposureError(candidate, solvedEv, targetLog);\n                float remainingDarkEv26666 = clamp(-postSolveErrorEv26666, 0.0f, 2.50f);\n                float desiredTotalBodyLiftEv26666 = clamp(\n                        0.90f * remainingDarkEv26666 * iris26666HighDrIntent, 0.0f, 1.40f);\n                float inheritedBodyLiftEv26666 = clamp(\n                        basePipeline.mParameters.motionV2GlobalBodyLiftEv, 0.0f, 1.25f);\n                iris26666HighDrExtraBodyLiftEv = clamp(\n                        desiredTotalBodyLiftEv26666 - inheritedBodyLiftEv26666, 0.0f, 1.40f);\n                basePipeline.mParameters.motionV2HighDrBodyLiftEv =\n                        iris26666HighDrExtraBodyLiftEv;\n                Log.i(Name, "IRIS_26666_POST_CAPTURE_HIGH_DR_BODY_RECOVERY"\n                        + " candidateP50Guide=" + iris26639CandidateP50Guide\n                        + " candidateP99Guide=" + iris26550CandidateP99Guide\n                        + " rawSolvedEv=" + rawSolvedEv\n                        + " solvedEv=" + solvedEv\n                        + " intent=" + iris26666HighDrIntent\n                        + " postSolveErrorEv=" + postSolveErrorEv26666\n                        + " remainingDarkEv=" + remainingDarkEv26666\n                        + " inherited26664BodyLiftEv=" + inheritedBodyLiftEv26666\n                        + " extraBodyLiftEv=" + iris26666HighDrExtraBodyLiftEv\n                        + " maxExtraEv=1.40 global65PercentFrozen=true"\n                        + " postCaptureOnly=true previewWrite=false sceneSemantic=false"\n                        + " nearBlackIdentity=0.004 highlightIdentity=0.65");\n            }\n            if (!Float.isFinite(gain) || gain <= 0.0f) {\n                throw new IllegalStateException("non-finite solved viewfinder gain");\n            }\n''')

# Capture: adaptive LONG depth from fresh RAW evidence only; old +2.5 EV path is exact when gate=0.
cap='app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java'
edit(cap,
'''        if (rawAgeNs > 180_000_000L) return false;\n\n        boolean manual = false;\n''',
'''        if (rawAgeNs > 180_000_000L) return false;\n\n        /* IRIS_26666_ADAPTIVE_SHADOW_LONG_PHOTON_EVIDENCE\n         * This is capture-only and RAW-only: preview request/AE/tone remain the exact 26660 path.\n         * Deepen LONG beyond the proven +2.5 EV baseline only when fresh sensor-normalized RAW\n         * simultaneously proves a photon-starved body and real high dynamic range. No scene or sun\n         * classifier exists. The baseline is bit-for-bit selected whenever this gate is zero. */\n        float floorNeed26666 = Float.isFinite(mMotion26380RawFloorFraction)\n                ? motion26368Clamp01((mMotion26380RawFloorFraction - 0.10f) / (0.55f - 0.10f))\n                : 0.0f;\n        float shadowNeed26666 = Float.isFinite(mMotion26380RawShadowFraction)\n                ? motion26368Clamp01((mMotion26380RawShadowFraction - 0.24f) / (0.75f - 0.24f))\n                : 0.0f;\n        float meanNeed26666 = Float.isFinite(mMotion26380RawMeanSignal)\n                ? 1.0f - motion26368Clamp01((mMotion26380RawMeanSignal - 0.035f) / (0.16f - 0.035f))\n                : 0.0f;\n        float bodyStarved26666 = Math.max(floorNeed26666, 0.75f * shadowNeed26666)\n                * (0.35f + 0.65f * meanNeed26666);\n        float drNeed26666 = Float.isFinite(mMotion26608RawDynamicRangeEv)\n                ? motion26368Clamp01((mMotion26608RawDynamicRangeEv - 2.25f) / (4.25f - 2.25f))\n                : 0.0f;\n        float tailNeed26666 = Float.isFinite(mMotion26608RawP995)\n                ? motion26368Clamp01((mMotion26608RawP995 - 0.30f) / (0.70f - 0.30f))\n                : 0.0f;\n        float conflictNeed26666 = (mMotion26608CurrentHdrConflict\n                || mMotion26608BroadHdrConflict || mMotion26608MixedHdrConflict\n                || mMotion26608CompactHdrConflict) ? 1.0f : 0.0f;\n        float rawLongIntent26666 = motion26368Clamp01(bodyStarved26666\n                * Math.max(drNeed26666, Math.max(0.70f * tailNeed26666,\n                0.80f * conflictNeed26666)));\n        float adaptiveLongGate26666 = rawLongIntent26666 <= 0.35f ? 0.0f\n                : motion26368Clamp01((rawLongIntent26666 - 0.35f) / 0.65f);\n        final double requestedLongTargetEv26666 = MOTION_26505_LONG_TARGET_EV\n                + MOTION_26666_LONG_EXTRA_MAX_EV * adaptiveLongGate26666;\n        final double requestedLongMultiplier26666 = Math.pow(2.0, requestedLongTargetEv26666);\n\n        boolean manual = false;\n''')
edit(cap,
'''        double targetEnergy = ticket.baselineEnergy * MOTION_26505_LONG_TARGET_MULTIPLIER;\n''',
'''        double targetEnergy = ticket.baselineEnergy * requestedLongMultiplier26666;\n''')
edit(cap,
'''        long reqExp = Math.round(baseExp * MOTION_26505_LONG_TARGET_MULTIPLIER);\n''',
'''        long reqExp = Math.round(baseExp * requestedLongMultiplier26666);\n''')
edit(cap,
'''                                + " targetDeltaEv=" + MOTION_26505_LONG_TARGET_EV\n''',
'''                                + " targetDeltaEv=" + requestedLongTargetEv26666\n                                + " adaptiveHighDrGate=" + adaptiveLongGate26666\n''')
edit(cap,
'''                    + " targetEv=" + MOTION_26505_LONG_TARGET_EV\n                    + " requestedExposureNs=" + requestedExp\n''',
'''                    + " targetEv=" + requestedLongTargetEv26666\n                    + " baselineTargetEv=" + MOTION_26505_LONG_TARGET_EV\n                    + " adaptiveHighDrGate=" + adaptiveLongGate26666\n                    + " rawFloorFraction=" + mMotion26380RawFloorFraction\n                    + " rawShadowFraction=" + mMotion26380RawShadowFraction\n                    + " rawMeanSignal=" + mMotion26380RawMeanSignal\n                    + " rawDynamicRangeEv=" + mMotion26608RawDynamicRangeEv\n                    + " rawP995=" + mMotion26608RawP995\n                    + " requestedExposureNs=" + requestedExp\n''')
edit(cap,
'''    private static final double MOTION_26505_LONG_TARGET_MULTIPLIER =\n            5.656854249492381;\n    private static final long MOTION_26658_LONG_MAX_EXPOSURE_NS = 66_666_667L;\n''',
'''    private static final double MOTION_26505_LONG_TARGET_MULTIPLIER =\n            5.656854249492381;\n    /* IRIS_26666: baseline remains exact +2.5 EV; only proven high-DR body starvation may add 1.5 EV. */\n    private static final double MOTION_26666_LONG_EXTRA_MAX_EV = 1.5;\n    private static final long MOTION_26658_LONG_MAX_EXPOSURE_NS = 66_666_667L;\n''')

# Parameters -> render host bindings/logging.
render_java='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
edit(render_java,
'''            glProg.setVar("iris26664GlobalBodyLiftEv",\n                    basePipeline.mParameters.motionV2GlobalBodyLiftEv);\n            glProg.setVar("iris26665ShadowDepthEv",\n''',
'''            glProg.setVar("iris26664GlobalBodyLiftEv",\n                    basePipeline.mParameters.motionV2GlobalBodyLiftEv);\n            glProg.setVar("iris26666HighDrBodyLiftEv",\n                    basePipeline.mParameters.motionV2HighDrBodyLiftEv);\n            glProg.setVar("iris26665ShadowDepthEv",\n''')
edit(render_java,
'''                    + " c1=true monotone=true highlightOwner26660Frozen=true");\n            Log.i(Name, "IRIS_26665_BLACK_SAFE_SHADOW_DEPTH_RENDER"\n''',
'''                    + " c1=true monotone=true highlightOwner26660Frozen=true");\n            Log.i(Name, "IRIS_26666_HIGH_DR_BODY_RECOVERY_RENDER"\n                    + " extraBodyLiftEv=" + basePipeline.mParameters.motionV2HighDrBodyLiftEv\n                    + " nearBlackIdentityThrough=0.004 fullLiftFrom=0.025 fadeFrom=0.08"\n                    + " highlightIdentityFrom=0.65 postCaptureOnly=true previewUnchanged=true");\n            Log.i(Name, "IRIS_26665_BLACK_SAFE_SHADOW_DEPTH_RENDER"\n''')
edit(render_java,
'''                glProg.setVar("motionHdrHandoff", basePipeline.mParameters.motionV2Active ? 1 : 0);\n                glProg.setVar("iris26665ShadowDepthEv",\n''',
'''                glProg.setVar("motionHdrHandoff", basePipeline.mParameters.motionV2Active ? 1 : 0);\n                glProg.setVar("iris26666HighDrBodyLiftEv",\n                        basePipeline.mParameters.motionV2HighDrBodyLiftEv);\n                glProg.setVar("iris26665ShadowDepthEv",\n''')

# Render shader: black-safe additional lift, exact identity outside the high-DR scalar and above 0.65.
render_glsl='app/src/main/assets/shaders/motionv2/render.glsl'
edit(render_glsl,
'''uniform float iris26664GlobalBodyLiftEv;\nuniform float iris26665ShadowDepthEv;\n''',
'''uniform float iris26664GlobalBodyLiftEv;\nuniform float iris26666HighDrBodyLiftEv;\nuniform float iris26665ShadowDepthEv;\n''')
edit(render_glsl,
'''/* IRIS_26665_BLACK_SAFE_SHADOW_DEPTH\n''',
'''/* IRIS_26666_BLACK_SAFE_HIGH_DR_BODY_RECOVERY\n * Extra recovery beyond the frozen 65% global solve is permitted only by the Java high-DR gate.\n * Preserve exact black through 0.004, ramp smoothly to full recovery at 0.025, hold through 0.08,\n * then fade C1 to exact identity at 0.65. The 1.40 EV cap keeps the log-domain derivative positive. */\nfloat iris26666HighDrBodyRecovery(float mappedGuide){\n    float y=max(mappedGuide,0.0);\n    if(iris26592MotionHdrHandoff==0 || y<=0.004 || y>=0.65) return y;\n    float liftEv=clamp(iris26666HighDrBodyLiftEv,0.0,1.40);\n    if(liftEv<=1.0e-7) return y;\n    const float floorLog=-7.9657842847;  /* log2(0.004) */\n    const float fullLog=-5.3219280949;   /* log2(0.025) */\n    const float fadeStartLog=-3.6438561898; /* log2(0.08) */\n    const float fadeEndLog=-0.6214883767;   /* log2(0.65) */\n    float logY=log2(max(y,1.0e-8));\n    float enter=clamp((logY-floorLog)/(fullLog-floorLog),0.0,1.0);\n    enter=enter*enter*(3.0-2.0*enter);\n    float exitT=clamp((logY-fadeStartLog)/(fadeEndLog-fadeStartLog),0.0,1.0);\n    exitT=exitT*exitT*(3.0-2.0*exitT);\n    float gate=enter*(1.0-exitT);\n    return y*exp2(liftEv*gate);\n}\n\n/* IRIS_26665_BLACK_SAFE_SHADOW_DEPTH\n''')
edit(render_glsl,
'''    mappedGuide=iris26664GlobalBodyTone(mappedGuide);\n    mappedGuide=iris26665BlackSafeShadowDepth(mappedGuide);\n''',
'''    mappedGuide=iris26664GlobalBodyTone(mappedGuide);\n    mappedGuide=iris26666HighDrBodyRecovery(mappedGuide);\n    mappedGuide=iris26665BlackSafeShadowDepth(mappedGuide);\n''')
edit(render_glsl,
'''            mappedGuide=iris26664GlobalBodyTone(mappedGuide);\n            mappedGuide=iris26665BlackSafeShadowDepth(mappedGuide);\n''',
'''            mappedGuide=iris26664GlobalBodyTone(mappedGuide);\n            mappedGuide=iris26666HighDrBodyRecovery(mappedGuide);\n            mappedGuide=iris26665BlackSafeShadowDepth(mappedGuide);\n''')

# Gain-map intent mirrors only the new 26666 SDR transfer, preserving successful HDR numerator.
gain='app/src/main/assets/shaders/motionv2/gainmap.glsl'
edit(gain,
'''uniform float iris26653AdaptiveWhitePoint;\nuniform float iris26665ShadowDepthEv;\n''',
'''uniform float iris26653AdaptiveWhitePoint;\nuniform float iris26666HighDrBodyLiftEv;\nuniform float iris26665ShadowDepthEv;\n''')
edit(gain,
'''/* IRIS_26665_UHDR_SHADOW_DEPTH_PARITY\n''',
'''/* IRIS_26666_UHDR_HIGH_DR_BODY_PARITY\n * Exact scalar mirror of the additional SDR high-DR body recovery. HDR numerator remains the\n * successful 26658 target; only the matched SDR intent denominator follows the saved SDR base. */\nfloat iris26666HighDrBodyRecovery(float mappedGuide){\n    float y=max(mappedGuide,0.0);\n    if(motionHdrHandoff==0 || y<=0.004 || y>=0.65) return y;\n    float liftEv=clamp(iris26666HighDrBodyLiftEv,0.0,1.40);\n    if(liftEv<=1.0e-7) return y;\n    const float floorLog=-7.9657842847;\n    const float fullLog=-5.3219280949;\n    const float fadeStartLog=-3.6438561898;\n    const float fadeEndLog=-0.6214883767;\n    float logY=log2(max(y,1.0e-8));\n    float enter=clamp((logY-floorLog)/(fullLog-floorLog),0.0,1.0);\n    enter=enter*enter*(3.0-2.0*enter);\n    float exitT=clamp((logY-fadeStartLog)/(fadeEndLog-fadeStartLog),0.0,1.0);\n    exitT=exitT*exitT*(3.0-2.0*exitT);\n    float gate=enter*(1.0-exitT);\n    return y*exp2(liftEv*gate);\n}\n\n/* IRIS_26665_UHDR_SHADOW_DEPTH_PARITY\n''')
edit(gain,
'''    float sharedGuide26665=iris26640SharedSdrGuide(sourceGuide,masterSourcePixel);\n    sharedGuide26665=iris26665BlackSafeShadowDepth(sharedGuide26665);\n''',
'''    float sharedGuide26665=iris26640SharedSdrGuide(sourceGuide,masterSourcePixel);\n    sharedGuide26665=iris26666HighDrBodyRecovery(sharedGuide26665);\n    sharedGuide26665=iris26665BlackSafeShadowDepth(sharedGuide26665);\n''')

# Sabre embedded merge: bounded extra weight for Motion-only LONG photon evidence above old +2.5EV.
sabre='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
edit(sabre,
'''        uniform float uSourceClippedWeight;\n        uniform float uValidityWeightScale;\n''',
'''        uniform float uSourceClippedWeight;\n        /* IRIS_26666_MOTION_LONG_PHOTON_EVIDENCE_WEIGHT\n         * Host keeps this exactly 1 for reference/NORMAL/Night and old +2.5 EV Motion LONG. */\n        uniform float uLongEvidenceWeight26666;\n        uniform float uValidityWeightScale;\n''')
edit(sabre,
'''            if (uSourceClipGuard != 0) {\n                frameWeight *= mix(\n                    uSourceClippedWeight,1.0,\n                    clamp(sourceNeighborhoodConfidence,0.0,1.0));\n            }\n            accumulatedColor *= frameWeight;\n''',
'''            if (uSourceClipGuard != 0) {\n                frameWeight *= mix(\n                    uSourceClippedWeight,1.0,\n                    clamp(sourceNeighborhoodConfidence,0.0,1.0));\n            }\n            frameWeight *= max(uLongEvidenceWeight26666,1.0);\n            accumulatedColor *= frameWeight;\n''')

stack='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
# Compute Motion-only LONG evidence weight in the Sabre loop; no Night change because preserveExtendedHdrThroughVgn is false in Night.
edit(stack,
'''                val durationRobustness = sabreExposureDurationRobustness(frames.first(), frame)\n                renderSabreRejection(\n''',
'''                val durationRobustness = sabreExposureDurationRobustness(frames.first(), frame)\n                /* IRIS_26666_MOTION_LONG_PHOTON_EVIDENCE_WEIGHT\n                 * The old +2.5 EV LONG keeps weight 1. Extra authority starts only above the exact\n                 * old acceptance ceiling (~7.46x energy), so ordinary 26665 Motion is unchanged.\n                 * Motion-only is proven by preserveExtendedHdrThroughVgn; Night remains exactly 1.\n                 * At >=9 NORMAL frames the 2.80 cap also stays within the existing 6*frame packed\n                 * validity budget (5*(N-1+2.8) <= 6*N). */\n                val longEvidenceWeight26666 = if (\n                    preserveExtendedHdrThroughVgn && frame.role == RawBurstFrameRole.SHADOW_LONG\n                        && normalFrameCount >= 9\n                ) {\n                    val longEnergyRatio26666 = (1.0 / exposureScale.toDouble())\n                        .takeIf { it.isFinite() } ?: 1.0\n                    if (longEnergyRatio26666 <= 7.50) {\n                        1f\n                    } else {\n                        (1.0 + (longEnergyRatio26666 - 7.50) / (16.0 - 7.50) * (2.80 - 1.0))\n                            .coerceIn(1.0, 2.80).toFloat()\n                    }\n                } else {\n                    1f\n                }\n                renderSabreRejection(\n''')
edit(stack,
'''                            "meanWeight=${sum.toDouble() / (255.0 * cells.toDouble())} " +\n                            "peakWeight=${peak / 255.0} postSourceClip=true " +\n''',
'''                            "meanWeight=${sum.toDouble() / (255.0 * cells.toDouble())} " +\n                            "peakWeight=${peak / 255.0} longEvidenceWeight26666=$longEvidenceWeight26666 " +\n                            "postSourceClip=true " +\n''')
edit(stack,
'''                        validityWeightScale26614 = validityWeightScale26614,\n                    )\n                } else {\n''',
'''                        validityWeightScale26614 = validityWeightScale26614,\n                        longEvidenceWeight26666 = longEvidenceWeight26666,\n                    )\n                } else {\n''', count=1)
# Add optional arg + uniform in host merge.
edit(stack,
'''        accumulatedValidity26614: Int = 0,\n        validityWeightScale26614: Float = 1f,\n    ) {\n''',
'''        accumulatedValidity26614: Int = 0,\n        validityWeightScale26614: Float = 1f,\n        longEvidenceWeight26666: Float = 1f,\n    ) {\n''')
edit(stack,
'''        uniform1f(program, "uSourceClippedWeight", sourceClippedWeight.coerceIn(0f, 1f))\n        uniform1f(program, "uValidityWeightScale", validityWeightScale26614.coerceAtLeast(1f))\n''',
'''        uniform1f(program, "uSourceClippedWeight", sourceClippedWeight.coerceIn(0f, 1f))\n        uniform1f(program, "uLongEvidenceWeight26666", longEvidenceWeight26666.coerceIn(1f, 2.80f))\n        uniform1f(program, "uValidityWeightScale", validityWeightScale26614.coerceAtLeast(1f))\n''')

print('TRANSFORM_26666_OK')
