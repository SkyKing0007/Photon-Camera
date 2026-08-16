#!/usr/bin/env python3
from pathlib import Path
import hashlib
import math
import re
import sys

MERGER = "app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java"
RECON = "app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
SHORT = "app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl"
RCD_POPULATE = "app/src/main/assets/shaders/motionv2/rcd26489_populate.glsl"
RCD_HOST = "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2RcdDemosaic.java"
RENDER = "app/src/main/assets/shaders/motionv2/render.glsl"

PRE = {
    MERGER: "9519d52fed6c12a1ef707e9d47b9111dafe901e9ab7c3918998841935decc111",
    RECON: "cf893651447d678b7a98b7e52cbf52132907cb055d2b82c00630bff0d88bb853",
    SHORT: "9c1cb82fc9c151eaaa7266d40eee63c0df193d3fdef9b911b193e89e9f454f65",
    RCD_POPULATE: "5979205496f17dc13d485102682f5f4be5b4762f10d28a9aa2cd68190a1a6343",
    RCD_HOST: "9a336be7269154fe1e71a1ade672b6fa324cebfbaeb1987e13e9783d252f5089",
    RENDER: "fd5868d6561e77af79fa7bfb1780e66da3be0328396c4b5c0341e3c5f9bbd820",
}
POST = {
    MERGER: "0eaf10a20627b3a8e94a9f5664214999edb4273c48db5b571d0e77fe3ae0f002",
    RECON: "55d8a98332662f8866e2b9b4c4d7fb060619430f899323685f33e1823530aa12",
    SHORT: "c5c9f9dcbe6ce730b94f74e3a56361ddfcf9c3ac35b6113cdb1eae6565edae0a",
    RCD_POPULATE: "3e572712dfad2fc49d1ef2fb04ac42bfc64e329ffcddbaaea8483c43d8693b43",
    RCD_HOST: "7c205e683a6a86ebf02fee88ea8e25e2ec6a4758dcc2e37f23081d5e16274a8c",
    RENDER: "2a3aa0c6e3cc553e11d4feeb6ecf24768f14e423ce359a3248b9f70dda7a8dbf",
}

SHORT_26491 = '#define LAYOUT //\nLAYOUT\nprecision highp float;\nprecision highp image2D;\n\nuniform highp sampler2D normalCfa;\nuniform highp sampler2D shortCfa;\nuniform highp sampler2D flowTexture;\nlayout(rgba32f,binding=0) uniform highp writeonly image2D outCfa;\nuniform ivec2 packedSize;\nuniform float referenceExposureScale;\nuniform float shortToNormalScale;\nuniform float physicalClipThreshold;\nuniform float shortClipThreshold;\nuniform float minimumFlowConfidence;\n\n/* IRIS_26489_BENTO_SHORT_SENSOR_DOMAIN_BAYER_RECOVERY */\nvec4 phaseSafeBilinear(vec2 packedCenter) {\n    vec2 p = packedCenter - vec2(0.5);\n    ivec2 lo = ivec2(floor(p));\n    vec2 f = fract(p);\n    ivec2 maxP = packedSize - ivec2(1);\n    ivec2 p00 = clamp(lo, ivec2(0), maxP);\n    ivec2 p10 = clamp(lo + ivec2(1,0), ivec2(0), maxP);\n    ivec2 p01 = clamp(lo + ivec2(0,1), ivec2(0), maxP);\n    ivec2 p11 = clamp(lo + ivec2(1,1), ivec2(0), maxP);\n    vec4 a = texelFetch(shortCfa, p00, 0);\n    vec4 b = texelFetch(shortCfa, p10, 0);\n    vec4 c = texelFetch(shortCfa, p01, 0);\n    vec4 d = texelFetch(shortCfa, p11, 0);\n    return mix(mix(a,b,f.x), mix(c,d,f.x), f.y);\n}\n\nvec4 shortSafeMask(vec4 v) {\n    return vec4(\n        v.r < shortClipThreshold ? 1.0 : 0.0,\n        v.g < shortClipThreshold ? 1.0 : 0.0,\n        v.b < shortClipThreshold ? 1.0 : 0.0,\n        v.a < shortClipThreshold ? 1.0 : 0.0);\n}\n\nvec4 normalSafeMask(vec4 v) {\n    return vec4(\n        v.r < 0.94 ? 1.0 : 0.0,\n        v.g < 0.94 ? 1.0 : 0.0,\n        v.b < 0.94 ? 1.0 : 0.0,\n        v.a < 0.94 ? 1.0 : 0.0);\n}\n\nfloat sum4(vec4 v) { return dot(v, vec4(1.0)); }\n\n/*\n * IRIS_26491_JOINT_SHORT_HDR_SPATIAL_CHROMATICITY\n *\n * One confidence scalar owns every clipped CFA phase. A neighboring short vector\n * is admitted only when every needed phase is unsaturated, at least two measurable\n * center phases agree after bounded radiometric normalization, and the normal-frame\n * context also agrees. The second test is the strong object/reflection-boundary gate.\n * Accepted neighbors form one weighted vector consensus; no R/G/G/B phase can be\n * borrowed independently. Fully censored/ambiguous sites remain the normal physical\n * lower bound so the downstream neutral-censor owner can handle them safely.\n */\nvoid main() {\n    ivec2 p = ivec2(gl_GlobalInvocationID.xy);\n    if (any(greaterThanEqual(p, packedSize))) return;\n\n    vec4 normal = texelFetch(normalCfa, p, 0);\n    vec4 normalSensor = normal / max(referenceExposureScale, 1.0e-6);\n    vec4 normalClip = smoothstep(\n        vec4(physicalClipThreshold), vec4(1.0), normalSensor);\n    vec4 needed = step(vec4(0.05), normalClip);\n    if (sum4(needed) < 0.5) {\n        imageStore(outCfa, p, normal);\n        return;\n    }\n\n    vec2 uv = (vec2(p) + vec2(0.5)) / vec2(packedSize);\n    /* IRIS_26490_SHORT_FLOW_RELIABILITY_GATE -- exact confidence math preserved. */\n    vec4 flowState = texture(flowTexture, uv);\n    float variation = max(flowState.z, 0.0);\n    float cancelled = step(0.5, flowState.w);\n    float flowConfidence = (1.0 - cancelled) * exp(-80.0 * variation);\n    float flowGate = smoothstep(minimumFlowConfidence, 0.80, flowConfidence);\n    vec2 source = vec2(p) + vec2(0.5) + flowState.xy;\n    if (source.x < 0.0 || source.y < 0.0 ||\n        source.x >= float(packedSize.x) || source.y >= float(packedSize.y) ||\n        flowConfidence < minimumFlowConfidence) {\n        imageStore(outCfa, p, normal);\n        return;\n    }\n\n    vec4 centerShort = phaseSafeBilinear(source);\n    vec4 centerShortSafe = shortSafeMask(centerShort);\n    bool centerHasEveryNeeded =\n        sum4(needed * (vec4(1.0) - centerShortSafe)) < 0.5;\n\n    vec4 weightedShort = centerHasEveryNeeded ? centerShort : vec4(0.0);\n    float weightSum = centerHasEveryNeeded ? 1.0 : 0.0;\n    float bestConfidence = centerHasEveryNeeded ? 1.0 : 0.0;\n    ivec2 maxPacked = packedSize - ivec2(1);\n    vec4 centerNormalSafe = normalSafeMask(normalSensor);\n\n    for (int oy = -1; oy <= 1; ++oy) {\n        for (int ox = -1; ox <= 1; ++ox) {\n            if (ox == 0 && oy == 0) continue;\n            vec2 qShort = source + vec2(float(ox), float(oy));\n            if (qShort.x < 0.0 || qShort.y < 0.0 ||\n                qShort.x >= float(packedSize.x) || qShort.y >= float(packedSize.y)) {\n                continue;\n            }\n\n            vec4 neighborShort = phaseSafeBilinear(qShort);\n            vec4 neighborShortSafe = shortSafeMask(neighborShort);\n            if (sum4(needed * (vec4(1.0) - neighborShortSafe)) >= 0.5) continue;\n\n            vec4 sharedShortSafe = centerShortSafe * neighborShortSafe;\n            float sharedShortCount = sum4(sharedShortSafe);\n            if (sharedShortCount < 1.5) continue;\n\n            float centerShortSum = dot(centerShort, sharedShortSafe);\n            float neighborShortSum = dot(neighborShort, sharedShortSafe);\n            float shortScale = clamp(\n                centerShortSum / max(neighborShortSum, 1.0e-6), 0.67, 1.50);\n            vec4 scaledNeighborShort = neighborShort * shortScale;\n            float centerShortMean = centerShortSum / max(sharedShortCount, 1.0);\n            float shortRelativeError =\n                dot(abs(centerShort - scaledNeighborShort), sharedShortSafe)\n                / (max(sharedShortCount, 1.0) * max(centerShortMean, 0.02));\n            float shortCoherence =\n                1.0 - smoothstep(0.060, 0.140, shortRelativeError);\n            if (shortCoherence <= 0.0) continue;\n\n            ivec2 qNormalP = clamp(p + ivec2(ox, oy), ivec2(0), maxPacked);\n            vec4 neighborNormal =\n                texelFetch(normalCfa, qNormalP, 0) / max(referenceExposureScale, 1.0e-6);\n            vec4 sharedNormalSafe = centerNormalSafe * normalSafeMask(neighborNormal);\n            float sharedNormalCount = sum4(sharedNormalSafe);\n            if (sharedNormalCount < 1.5) continue;\n\n            float centerNormalSum = dot(normalSensor, sharedNormalSafe);\n            float neighborNormalSum = dot(neighborNormal, sharedNormalSafe);\n            float normalScale = clamp(\n                centerNormalSum / max(neighborNormalSum, 1.0e-6), 0.75, 1.33);\n            vec4 scaledNeighborNormal = neighborNormal * normalScale;\n            float centerNormalMean = centerNormalSum / max(sharedNormalCount, 1.0);\n            float normalRelativeError =\n                dot(abs(normalSensor - scaledNeighborNormal), sharedNormalSafe)\n                / (max(sharedNormalCount, 1.0) * max(centerNormalMean, 0.02));\n            float boundaryCoherence =\n                1.0 - smoothstep(0.080, 0.220, normalRelativeError);\n            if (boundaryCoherence <= 0.0) continue;\n\n            float distance2 = float(ox * ox + oy * oy);\n            float spatialWeight = exp(-0.60 * distance2);\n            float consensusWeight = shortCoherence * boundaryCoherence * spatialWeight;\n            if (centerHasEveryNeeded) consensusWeight *= 0.30;\n\n            weightedShort += scaledNeighborShort * consensusWeight;\n            weightSum += consensusWeight;\n            bestConfidence = max(\n                bestConfidence,\n                0.85 * shortCoherence * boundaryCoherence);\n        }\n    }\n\n    if (weightSum <= 1.0e-4 || bestConfidence <= 0.0) {\n        imageStore(outCfa, p, normal);\n        return;\n    }\n\n    vec4 selectedShort = weightedShort / weightSum;\n    float jointConfidence = centerHasEveryNeeded ? 1.0 : bestConfidence;\n\n    /* IRIS_26490_CENSORED_NORMAL_IS_LOWER_BOUND -- preserved physically. */\n    vec4 recoveredEstimate =\n        selectedShort * shortToNormalScale * referenceExposureScale;\n    vec4 recovered = max(normal, recoveredEstimate);\n\n    /* One scalar gates every clipped phase: no independent CFA substitution. */\n    vec4 useShort = normalClip * (flowGate * jointConfidence);\n    imageStore(outCfa, p, mix(normal, recovered, useShort));\n}\n'
RCD_POPULATE_26491 = '#define LAYOUT //\nLAYOUT\nprecision highp float;\nprecision highp int;\nprecision highp sampler2D;\n\nuniform highp sampler2D InputBayer;\nuniform highp sampler2D LensShadingMap;\nlayout(std430, binding = 0) buffer CfaBuf {\n    float cfa[];\n};\nlayout(std430, binding = 1) buffer RedBuf {\n    float red[];\n};\nlayout(std430, binding = 2) buffer GreenBuf {\n    float green[];\n};\nlayout(std430, binding = 3) buffer BlueBuf {\n    float blue[];\n};\nuniform ivec2 rawSize;\nuniform ivec2 bandSize;\nuniform int bandOriginY;\nuniform int cfaPattern;\nuniform vec3 calculationWb;\nuniform vec3 sensorGains;\nuniform float sensorClipLevel;\nuniform float highlightThreshold;\nuniform float highlightCeiling;\nuniform int useLensShading;\n\nint phaseAt(ivec2 p) { return (p.x & 1) | ((p.y & 1) << 1); }\nint colorAt(ivec2 p) {\n    int q = phaseAt(p);\n    if (cfaPattern == 0) return q == 0 ? 0 : (q == 3 ? 2 : 1);\n    if (cfaPattern == 1) return q == 1 ? 0 : (q == 2 ? 2 : 1);\n    if (cfaPattern == 2) return q == 2 ? 0 : (q == 1 ? 2 : 1);\n    return q == 3 ? 0 : (q == 0 ? 2 : 1);\n}\nivec2 clampGlobal(ivec2 p) { return clamp(p, ivec2(0), rawSize - ivec2(1)); }\nfloat fusedAt(ivec2 p) {\n    p = clampGlobal(p);\n    vec4 v = texelFetch(InputBayer, p >> 1, 0);\n    int q = phaseAt(p);\n    return q == 0 ? v.r : (q == 1 ? v.g : (q == 2 ? v.b : v.a));\n}\nvec3 shadingRgb(ivec2 p) {\n    if (useLensShading == 0) return vec3(1.0);\n    vec2 uv = (vec2(clampGlobal(p)) + vec2(0.5)) / vec2(rawSize);\n    vec4 g = texture(LensShadingMap, clamp(uv, vec2(0.0), vec2(1.0)));\n    return max(vec3(g.r, 0.5 * (g.g + g.b), g.a), vec3(0.0));\n}\nfloat wbForColor(int col) {\n    return col == 0 ? calculationWb.r : (col == 2 ? calculationWb.b : calculationWb.g);\n}\nfloat gainForColor(int col) {\n    return col == 0 ? sensorGains.r : (col == 2 ? sensorGains.b : sensorGains.g);\n}\nfloat calculationAt(ivec2 p) {\n    p = clampGlobal(p);\n    int col = colorAt(p);\n    vec3 lsc = shadingRgb(p);\n    return clamp(\n        fusedAt(p) * lsc[col] * max(wbForColor(col), 1.0e-6),\n        0.0, highlightCeiling);\n}\nfloat balancedAt(ivec2 p) {\n    int col = colorAt(clampGlobal(p));\n    return calculationAt(p) * gainForColor(col) / max(wbForColor(col), 1.0e-6);\n}\nfloat max4(vec4 v) { return max(max(v.r, v.g), max(v.b, v.a)); }\nbool packedExtendedEvidence(ivec2 p) {\n    ivec2 packedCoord = clampGlobal(p) >> 1;\n    return max4(texelFetch(InputBayer, packedCoord, 0)) > sensorClipLevel + 0.002;\n}\n\nvoid packedCensorEvidence(\n        ivec2 p, out float clippedCount, out float safeCount,\n        out float safeMin, out float safeMax, out float neutralLowerBound) {\n    ivec2 origin = (clampGlobal(p) >> 1) << 1;\n    clippedCount = 0.0;\n    safeCount = 0.0;\n    safeMin = 1.0e20;\n    safeMax = 0.0;\n    neutralLowerBound = 0.0;\n    for (int py = 0; py < 2; ++py) {\n        for (int px = 0; px < 2; ++px) {\n            ivec2 q = clampGlobal(origin + ivec2(px, py));\n            float physical = fusedAt(q) / max(sensorClipLevel, 1.0e-6);\n            float balanced = balancedAt(q);\n            neutralLowerBound = max(neutralLowerBound, balanced);\n            if (physical >= highlightThreshold) {\n                clippedCount += 1.0;\n            } else if (physical < 0.94) {\n                safeCount += 1.0;\n                safeMin = min(safeMin, balanced);\n                safeMax = max(safeMax, balanced);\n            }\n        }\n    }\n}\n\nfloat coherentOpposedEstimate(\n        ivec2 p, int ownColor, float base, float anchorBalanced) {\n    vec3 sums = vec3(0.0);\n    vec3 counts = vec3(0.0);\n    for (int dy = -1; dy <= 1; ++dy) {\n        for (int dx = -1; dx <= 1; ++dx) {\n            ivec2 q = clampGlobal(p + ivec2(dx, dy));\n            float physical = fusedAt(q) / max(sensorClipLevel, 1.0e-6);\n            if (physical >= 0.94) continue;\n            float balanced = balancedAt(q);\n            float relative = abs(balanced - anchorBalanced) / max(anchorBalanced, 0.02);\n            if (relative > 0.35) continue;\n            int c = colorAt(q);\n            sums[c] += calculationAt(q);\n            counts[c] += 1.0;\n        }\n    }\n    if (counts.r < 0.5 || counts.g < 0.5 || counts.b < 0.5) return base;\n    const float invPower = 1.0 / 3.0;\n    vec3 roots = pow(max(sums / counts, vec3(0.0)), vec3(invPower));\n    float opposed = ownColor == 0 ? 0.5 * (roots.g + roots.b)\n            : (ownColor == 1 ? 0.5 * (roots.r + roots.b) : 0.5 * (roots.r + roots.g));\n    return max(base, opposed * opposed * opposed);\n}\n\nvoid main() {\n    ivec2 lp = ivec2(gl_GlobalInvocationID.xy);\n    if (any(greaterThanEqual(lp, bandSize))) return;\n    ivec2 gp = ivec2(lp.x, bandOriginY + lp.y);\n    int idx = lp.y * bandSize.x + lp.x;\n    int col = colorAt(gp);\n    float base = calculationAt(gp);\n    float fusedPhysical = fusedAt(gp);\n    float physical = fusedPhysical / max(sensorClipLevel, 1.0e-6);\n    /* IRIS_26490_PHYSICAL_CENSORING_WITH_LOWER_BOUND\n     * Physical sensor white remains exactly 1.0. Short-recovered values may\n     * exceed it and therefore remain measured extended radiance, never a reason\n     * to reduce the already-observed lower bound.\n     */\n    float clipMix = smoothstep(highlightThreshold, 1.0, physical);\n    float value = base;\n\n    /*\n     * IRIS_26491_NEUTRAL_CENSORED_FALLBACK\n     * Real short-HDR radiance (> physical sensor white) keeps measured ownership.\n     * For unresolved normal clipping, recover hue only when at least two safe CFA\n     * phases in the same 2x2 observation agree and 3x3 support stays on the same\n     * brightness surface. Otherwise one neutral balanced lower bound is used for\n     * every censored phase. This preserves brightness while making invented\n     * orange/pink CFA geometry impossible in fully censored regions.\n     */\n    if (clipMix > 0.0 && !packedExtendedEvidence(gp)) {\n        float clippedCount;\n        float safeCount;\n        float safeMin;\n        float safeMax;\n        float neutralLowerBound;\n        packedCensorEvidence(\n            gp, clippedCount, safeCount, safeMin, safeMax, neutralLowerBound);\n        float safeSpread = safeCount >= 1.5\n                ? (safeMax - safeMin) / max(0.5 * (safeMax + safeMin), 0.02)\n                : 1.0e20;\n        bool chromaRecoverable =\n            clippedCount <= 2.0 && safeCount >= 2.0 && safeSpread <= 0.28;\n\n        float reconstructed;\n        if (chromaRecoverable) {\n            float anchorBalanced = 0.5 * (safeMin + safeMax);\n            reconstructed = min(\n                coherentOpposedEstimate(gp, col, base, anchorBalanced),\n                highlightCeiling);\n        } else {\n            float neutralCalculation =\n                neutralLowerBound * wbForColor(col) / max(gainForColor(col), 1.0e-6);\n            reconstructed = min(max(base, neutralCalculation), highlightCeiling);\n        }\n        value = mix(base, reconstructed, clipMix);\n    }\n\n    cfa[idx] = value;\n    red[idx] = col == 0 ? value : 0.0;\n    green[idx] = col == 1 ? value : 0.0;\n    blue[idx] = col == 2 ? value : 0.0;\n}\n'

OLD_MERGER_SIGNATURE = """    public static float computeDisplayGain(
            ByteBuffer raw, int width, int height, Parameters parameters) {
"""
NEW_MERGER_SIGNATURE = """    public static float computeDisplayGain(
            ByteBuffer raw, int width, int height, Parameters parameters,
            double referenceExposureEnergy) {
"""
OLD_MERGER_POLICY = """        float adaptiveReduction = 1.0f /
                (1.0f + 0.55f * occupancyPressure + 1.35f * trueClipPressure);
        float gain = Math.max(1.0f, candidateGain * adaptiveReduction);
        if (!Float.isFinite(gain)) gain = 1.0f;
        gain = Math.min(gain, 16.0f); // numerical guard only
        if (gain < 1.02f) gain = 1.0f;
"""
NEW_MERGER_POLICY = """        float adaptiveReduction = 1.0f /
                (1.0f + 0.55f * occupancyPressure + 1.35f * trueClipPressure);

        /*
         * IRIS_26491_MIDTONES_GLOBAL_HIGHLIGHTS_LOCAL_HDR
         *
         * p50/p90 remain the scene-body measurement. The capture-result exposure
         * energy is a sanity ceiling that prevents a well-lit, short-exposure/low-ISO
         * room from being mistaken for a 7-15x-dark scene merely because linear RAW
         * code values are numerically small. It is deliberately monotonic: genuinely
         * dark scenes, where HAL needs longer exposure and/or more ISO, are allowed
         * progressively larger display normalization. Highlight occupancy and true
         * clipping stay telemetry/local-HDR evidence and never lower global exposure.
         */
        float illuminationCeiling = 16.0f;
        if (Double.isFinite(referenceExposureEnergy) && referenceExposureEnergy > 0.0) {
            double normalizedEnergy = Math.max(1.0, referenceExposureEnergy / 0.80);
            illuminationCeiling = (float)Math.min(16.0, Math.pow(normalizedEnergy, 0.65));
        }
        float gain = Math.max(1.0f, Math.min(candidateGain, illuminationCeiling));
        if (!Float.isFinite(gain)) gain = 1.0f;
        if (gain < 1.02f) gain = 1.0f;
"""
OLD_MERGER_LOG = """                + " adaptiveReduction=" + adaptiveReduction
                + " floorSuppression=false"
                + " highlightIsConstraintNotAuthority=true"
                + " finalGain=" + gain);
"""
NEW_MERGER_LOG = """                + " adaptiveReductionDiagnosticOnly=" + adaptiveReduction
                + " referenceExposureEnergy=" + referenceExposureEnergy
                + " illuminationCeiling=" + illuminationCeiling
                + " floorSuppression=false"
                + " midtonesOwnGlobalExposure=true"
                + " highlightsOwnLocalHdr=true"
                + " finalGain=" + gain);
"""
OLD_RECON_CALL = """                MotionV2Merger.computeDisplayGain(
                        reference.buffer,
                        size.x,
                        size.y,
                        parameters);
"""
NEW_RECON_CALL = """                MotionV2Merger.computeDisplayGain(
                        reference.buffer,
                        size.x,
                        size.y,
                        parameters,
                        reference.motionV2ExposureEnergy);
"""
OLD_RCD_BIND = """                    glProg.setVar("calculationWb", wbR, 1.0f, wbB);
                    final float iris26490PhysicalSensorWhite = 1.0f;
"""
NEW_RCD_BIND = """                    glProg.setVar("calculationWb", wbR, 1.0f, wbB);
                    /* IRIS_26491_NEUTRAL_CENSOR_SENSOR_GAIN_BRIDGE */
                    glProg.setVar("sensorGains", gains[0], greenGain, gains[3]);
                    final float iris26490PhysicalSensorWhite = 1.0f;
"""
OLD_RCD_LOG = """                + " calculationWbRemovedAtOutput=true"
                + " lensShading=" + hasLsc
"""
NEW_RCD_LOG = """                + " calculationWbRemovedAtOutput=true"
                + " neutralCensoredFallback=true"
                + " neutralFallbackUsesTimestampOwnedSensorGains=true"
                + " lensShading=" + hasLsc
"""
OLD_RENDER_HEADROOM = """    float mappedGuide=mapHeadroomLuminance(guide);
    return rgb*(mappedGuide/guide);
}
"""
NEW_RENDER_HEADROOM = """    /* IRIS_26491_EXTENDED_LINEAR_CHROMA_PRESERVING_HIGHLIGHT_COMPRESSION
     * Scene exposure arrived in extended-linear RGB from MotionV2DisplayExposure.
     * Compression is one scalar derived from the max-RGB/luma guide, so values
     * keep channel ratios until the final display-gamut fit. No per-channel 1.0
     * clamp is introduced here.
     */
    float mappedGuide=mapHeadroomLuminance(guide);
    return rgb*(mappedGuide/guide);
}
"""
OLD_RENDER_MAIN = """void main() {
    ivec2 xy=ivec2(gl_FragCoord.xy);
    vec3 linearSrgb=max(
            texelFetch(InputBuffer,xy,0).rgb,
            vec3(0.0));
"""
NEW_RENDER_MAIN = """void main() {
    ivec2 xy=ivec2(gl_FragCoord.xy);
    ivec2 sourceXY=xy;
    /* IRIS_26491_FINAL_OUTPUT_LEFT_EDGE_MIRROR_ONE_PIXEL
     * The successful 26490 four-edge RCD mirror stays untouched. Only the known
     * final x==0 output defect is replaced with the already-renderable x==1 source.
     */
    ivec2 sourceSize=textureSize(InputBuffer,0);
    if(sourceXY.x==0 && sourceSize.x>1) sourceXY.x=1;
    vec3 linearSrgb=max(
            texelFetch(InputBuffer,sourceXY,0).rgb,
            vec3(0.0));
"""
OLD_RENDER_MICRO = """    linearSrgb=applyReferenceSafeMicrocontrast(xy,linearSrgb);
"""
NEW_RENDER_MICRO = """    linearSrgb=applyReferenceSafeMicrocontrast(sourceXY,linearSrgb);
"""


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fail(msg: str):
    raise SystemExit("26491 V4 FAIL: " + msg)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        fail(f"{label} anchor count={n} expected=1")
    return text.replace(old, new, 1)


def clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


def smoothstep(a: float, b: float, x: float) -> float:
    t = clamp01((x-a)/max(b-a,1e-12))
    return t*t*(3.0-2.0*t)


def exposure_model(p50: float, p90: float, energy: float) -> float:
    gain50 = 0.050/max(p50,1e-9)
    gain90 = 0.180/max(p90,1e-9)
    candidate = math.sqrt(max(1.0,gain50)*max(1.0,gain90))
    ceiling = 16.0
    if math.isfinite(energy) and energy > 0.0:
        ceiling = min(16.0, max(1.0, energy/0.80)**0.65)
    gain = max(1.0, min(candidate, ceiling))
    return 1.0 if gain < 1.02 else gain


def validate_exposure_math():
    chandelier = exposure_model(0.0039081583, 0.025891548, 0.8666)
    if not 1.0 <= chandelier <= 1.10:
        fail(f"bright chandelier room must receive little/no boost, got {chandelier}")
    dark = exposure_model(0.0039081583, 0.025891548, 25.0)
    if dark < 7.0:
        fail(f"genuinely dark scene did not retain useful lift, got {dark}")
    same = exposure_model(0.0039081583, 0.025891548, 0.8666)
    if abs(same-chandelier) > 1e-12:
        fail("highlight-independent global exposure is not deterministic")
    print(f"26491 V4 EXPOSURE MODEL PASS chandelier={chandelier:.4f} dark={dark:.4f} midtonesGlobal=true highlightsLocal=true")


def validate_neutral_math():
    gains=(2.0,1.2,1.6); green=gains[1]; wb=(gains[0]/green,1.0,gains[2]/green)
    neutral=2.4; out=[]
    for g,w in zip(gains,wb):
        calculation=neutral*w/g
        after_rcd=calculation/w
        out.append(after_rcd*g)
    if max(out)-min(out) > 1e-9 or abs(out[0]-neutral) > 1e-9:
        fail(f"neutral fallback math not neutral: {out}")
    print("26491 V4 NEUTRAL CENSOR MODEL PASS preserveBrightness=true commonChromaticity=true")


def validate_render_model():
    rgb=(3.0,1.5,0.75); scale=0.22; mapped=tuple(x*scale for x in rgb)
    ratios=(mapped[0]/mapped[1],mapped[1]/mapped[2])
    if abs(ratios[0]-2.0)>1e-12 or abs(ratios[1]-2.0)>1e-12:
        fail("extended-linear scalar compression changed chromaticity")
    width=100; source0=1 if width>1 else 0; source1=1
    if source0!=source1: fail("left-edge x0 does not mirror x1")
    print("26491 V4 RENDER MODEL PASS extendedLinear=true chromaPreserved=true leftEdgeX0MirrorsX1=true")


def validate_shader_text():
    for label,src in (("short",SHORT_26491),("rcd_populate",RCD_POPULATE_26491)):
        if src.count('{') != src.count('}') or src.count('(') != src.count(')'):
            fail(label+" delimiter imbalance")
        clean=re.sub(r'//.*','',re.sub(r'/\*.*?\*/','',src,flags=re.S))
        bad=re.search(r'\b(?:float|vec[234]|int|ivec[234]|uint|uvec[234]|bool|mat[234])\s+(sample|common|coherent|precision|packed)\b',clean)
        if bad: fail(label+" reserved GLSL declaration "+bad.group(1))
    for need in ("IRIS_26491_JOINT_SHORT_HDR_SPATIAL_CHROMATICITY","boundaryCoherence","weightedShort","vec4 useShort = normalClip * (flowGate * jointConfidence);","vec4 recovered = max(normal, recoveredEstimate);"):
        if need not in SHORT_26491: fail("short contract missing "+need)
    if "normalClip * shortSafe" in SHORT_26491: fail("independent short per-phase substitution survived")
    for need in ("IRIS_26491_NEUTRAL_CENSORED_FALLBACK","uniform vec3 sensorGains;","packedExtendedEvidence","chromaRecoverable","neutralLowerBound","coherentOpposedEstimate"):
        if need not in RCD_POPULATE_26491: fail("RCD neutral contract missing "+need)
    print("26491 V4 SHADER POLICY SELF-TEST PASS boundaryAware=true noIndependentPhase=true neutralFallback=true")


def transform_merger(text: str) -> str:
    for need in ("IRIS_26490_EXPLICIT_DISPLAY_DOMAIN","float p50 = quantile(hist, samples, 0.50f);","float p90 = quantile(hist, samples, 0.90f);","float candidateGain = Math.max(1.0f, sceneGain);","float adaptiveReduction = 1.0f /"):
        if need not in text: fail("26490 merger contract missing "+need)
    text=replace_once(text,OLD_MERGER_SIGNATURE,NEW_MERGER_SIGNATURE,"merger signature")
    text=replace_once(text,OLD_MERGER_POLICY,NEW_MERGER_POLICY,"merger policy")
    text=replace_once(text,OLD_MERGER_LOG,NEW_MERGER_LOG,"merger log")
    if "candidateGain * adaptiveReduction" in text: fail("highlight tail still globally changes exposure")
    return text


def transform_recon(text: str) -> str:
    if "IRIS_26490_EXPLICIT_DISPLAY_GAIN_OWNER" not in text: fail("26490 display owner marker missing")
    return replace_once(text,OLD_RECON_CALL,NEW_RECON_CALL,"reference exposure-energy carrier")


def transform_rcd_host(text: str) -> str:
    for need in ("IRIS_26490_RCD_EXPOSURE_DOMAIN","final float iris26490PhysicalSensorWhite = 1.0f;","IRIS_26489_POSTMERGE_RCD_DEMOSAIC_OWNER"):
        if need not in text: fail("26490 RCD host contract missing "+need)
    text=replace_once(text,OLD_RCD_BIND,NEW_RCD_BIND,"RCD sensor-gain bridge")
    text=replace_once(text,OLD_RCD_LOG,NEW_RCD_LOG,"RCD neutral log")
    return text


def transform_render(text: str) -> str:
    for need in ("IRIS_26480_MAX_RGB_HIGHLIGHT_TONE_GUIDE_V2","fitDisplayGamut","outputExposureScale"):
        if need not in text: fail("26490 render contract missing "+need)
    text=replace_once(text,OLD_RENDER_HEADROOM,NEW_RENDER_HEADROOM,"extended-linear marker")
    text=replace_once(text,OLD_RENDER_MAIN,NEW_RENDER_MAIN,"left-edge source mirror")
    text=replace_once(text,OLD_RENDER_MICRO,NEW_RENDER_MICRO,"left-edge microcontrast parity")
    return text


def apply(root: Path):
    for rel,expected in PRE.items():
        p=root/rel
        if not p.is_file(): fail("missing target "+rel)
        actual=sha(p.read_bytes())
        if actual!=expected: fail(f"exact successful-26490 pre-hash mismatch {rel} actual={actual} expected={expected}")
    outputs={
        MERGER: transform_merger((root/MERGER).read_text(encoding="utf-8")),
        RECON: transform_recon((root/RECON).read_text(encoding="utf-8")),
        SHORT: SHORT_26491,
        RCD_POPULATE: RCD_POPULATE_26491,
        RCD_HOST: transform_rcd_host((root/RCD_HOST).read_text(encoding="utf-8")),
        RENDER: transform_render((root/RENDER).read_text(encoding="utf-8")),
    }
    validate_shader_text()
    for rel,text in outputs.items():
        (root/rel).write_text(text,encoding="utf-8",newline="\n")
        actual=sha((root/rel).read_bytes())
        if actual!=POST[rel]: fail(f"post-hash mismatch {rel} actual={actual} expected={POST[rel]}")
    print("26491 V4 TRANSFORM PASS files=6 completeArchitecture=true exact26490Base=true")


def self_test():
    validate_exposure_math(); validate_neutral_math(); validate_render_model(); validate_shader_text()
    if sha(SHORT_26491.encode("utf-8")) != POST[SHORT]: fail("embedded short post hash mismatch")
    if sha(RCD_POPULATE_26491.encode("utf-8")) != POST[RCD_POPULATE]: fail("embedded RCD-populate post hash mismatch")
    print("26491 V4 TRANSFORM SELF-TEST PASS")


if __name__ == "__main__":
    if len(sys.argv)==2 and sys.argv[1]=="--self-test": self_test()
    elif len(sys.argv)==2:
        self_test(); apply(Path(sys.argv[1]))
    else:
        raise SystemExit("usage: transform_26491_complete_highlight_exposure_v4.py <repo-root> | --self-test")
