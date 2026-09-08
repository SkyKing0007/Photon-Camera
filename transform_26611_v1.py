#!/usr/bin/env python3
from pathlib import Path
import shutil, sys

# Exact successful-26610 candidate-first transform mechanics: immutable authority in argv[1],
# fresh copied candidate in argv[2], then all edits apply only to the copied candidate.
if len(sys.argv) != 3:
    raise SystemExit('usage: transform_26611_v1.py <base> <out>')
base = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
if out.exists():
    shutil.rmtree(out)
shutil.copytree(base, out)
ROOT = out
APP = out / 'app' if (out/'app').is_dir() else out

def replace_once(path_rel, old, new, label):
    p = APP / path_rel
    s = p.read_text()
    n = s.count(old)
    if n != 1:
        raise SystemExit(f'{label}: expected exactly 1 anchor in {path_rel}, found {n}')
    p.write_text(s.replace(old, new, 1))

def must_contain(path_rel, text, label):
    s=(APP/path_rel).read_text()
    if text not in s:
        raise SystemExit(f'{label}: required text missing from {path_rel}')

SABRE='src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
STACK='src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
VGN='src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
VER='version.properties'

# Version: exact successful 26610 -> 26611.
replace_once(VER, 'VERSION_NAME=0.9726610\nVERSION_BUILD=26610\n',
                 'VERSION_NAME=0.9726611\nVERSION_BUILD=26611\n', 'version')

# 1) SHORT boundary ownership: only same-CFA measurable boundary proof seeds a physically
# clipped connected component. The exact 16:38 device failure had flow.w p50=2.46 RAW px;
# a Bayer phase can change after one RAW pixel, so the measurable boundary must fail closed
# before a one-pixel residual. Predictor agreement may strengthen a good local boundary but
# can never create one.
old = '''            float localResidualConfidence =\n                1.0 - smoothstep(2.0, 8.0, max(flow.w, 0.0));\n            float neighborhoodPredictorConfidence = predictorConsensus(tile);\n            /* IRIS_26608_PROTECTED_ONE_TUNNEL_SHORT_BOUNDARIES\n             * Predictor coherence may preserve connectivity through a featureless clipped core,\n             * but it may never overrule poor local residual evidence at a measurable boundary. */\n            float connectivityFlowProof = max(\n                localResidualConfidence, neighborhoodPredictorConfidence);\n            float boundaryLocalFlowProof = localResidualConfidence * mix(\n                0.75, 1.0, neighborhoodPredictorConfidence);\n'''
new = '''            /* IRIS_26611_SAME_CFA_MEASURABLE_BOUNDARY_SEED\n             * Device 26610 proved that 2..8 RAW-pixel residual confidence is unsafe at Bayer\n             * highlight edges: p50=2.46 RAW px still received ~98% trust. A one-RAW-pixel\n             * displacement can cross CFA phase, so only a sub-pixel local residual may seed a\n             * clipped component. Same-phase radiometry below supplies the independent measurement\n             * proof. Predictor coherence may strengthen a valid seed but can never manufacture it. */\n            float strictBoundaryResidualConfidence =\n                1.0 - smoothstep(0.35, 0.95, max(flow.w, 0.0));\n            float neighborhoodPredictorConfidence = predictorConsensus(tile);\n            float boundaryLocalFlowProof = strictBoundaryResidualConfidence * mix(\n                0.85, 1.0, neighborhoodPredictorConfidence);\n'''
replace_once(SABRE, old, new, 'strict SHORT measurable-boundary residual')

# Track literal physical censorship only when at least two CFA phases are clipped.
old = '''                    bool literalHere = false;\n                    for (int phase = 0; phase < 4; ++phase) {\n                        if (rawAt(uReferenceRaw, referenceQuad + phaseOffset(phase)) >=\n                                uSourceClippingPoint) literalHere = true;\n                    }\n                    if (literalHere) literalLossSeen = 1.0;\n'''
new = '''                    int literalPhasesHere = 0;\n                    for (int phase = 0; phase < 4; ++phase) {\n                        if (rawAt(uReferenceRaw, referenceQuad + phaseOffset(phase)) >=\n                                uSourceClippingPoint) literalPhasesHere += 1;\n                    }\n                    if (literalPhasesHere >= 2) literalLossSeen = 1.0;\n'''
replace_once(SABRE, old, new, 'two-phase component censorship')

# A clipped region may carry propagated trust, but literal clipping can never self-create geometry.
# effective loss is telemetry only for rescue because ordinary normalized photometry remains valid.
old = '''            float lossConnectivity = max(literalLossSeen, effectiveLossSeen);\n            float geometryForComponent = max(\n                connectivityFlowProof, 0.85 * literalLossSeen);\n            float componentConfidence = min(\n                componentSourceConfidence,\n                min(max(componentBrightness, lossConnectivity), geometryForComponent));\n'''
new = '''            /* IRIS_26611_CLIPPED_INTERIOR_CANNOT_SELF_SEED\n             * z is region membership only: a two-phase physically censored NORMAL component with\n             * valid SHORT source headroom. It intentionally contains no geometry confidence.\n             * Geometry enters exclusively through w (same-CFA measurable-boundary anchor) and is\n             * then propagated through z by the bottleneck pass. Literal clipping itself can never\n             * create trust. Effective/sub-clipping loss remains telemetry and retains ordinary\n             * exposure-normalized NORMAL rejection. */\n            float componentConfidence = min(\n                componentSourceConfidence, literalLossSeen);\n'''
replace_once(SABRE, old, new, 'component cannot self-seed')

# Tighten flow discontinuity during propagation so trust cannot cross a CFA-meaningful displacement.
old = '''        float compatibleFlow(ivec2 a, ivec2 b) {\n            float delta = length(rawFlowAtAnchor(a) - rawFlowAtAnchor(b));\n            return 1.0 - smoothstep(4.0, 16.0, delta);\n        }\n'''
new = '''        float compatibleFlow(ivec2 a, ivec2 b) {\n            /* IRIS_26611_CFA_PHASE_SAFE_COMPONENT_PROPAGATION\n             * Trust may cross only a smoothly registered physically clipped interior. A neighbor\n             * flow jump approaching one RAW pixel can change CFA phase ownership and therefore\n             * terminates propagation instead of painting SHORT chroma across a material edge. */\n            float delta = length(rawFlowAtAnchor(a) - rawFlowAtAnchor(b));\n            return 1.0 - smoothstep(0.50, 1.25, delta);\n        }\n'''
replace_once(SABRE, old, new, 'CFA-safe component propagation')

# Rescue uses boundary-proven propagated component trust; no loose 2..8 RAW-pixel direct residual
# can re-authorize a clipped core. The shared ordinary physical protection and final source clip
# remain unchanged.
old = '''            /* IRIS_26610_NO_LITERAL_CORE_GEOMETRY_BYPASS\n             * A clipped NORMAL core makes NORMAL-reference photometry invalid, but it does not make\n             * SHORT geometry automatically valid. The same local affine residual proof remains a\n             * hard requirement everywhere, including two-phase literal clipping. This permanently\n             * removes the 26608/26609 literalCore -> geometry=1 escape that device samples showed\n             * could admit pink/magenta/blue boundary disagreement under large residuals. */\n            float localResidualConfidence =\n                1.0 - smoothstep(2.0, 8.0, max(flow.w, 0.0));\n            float localGeometry = localResidualConfidence;\n            float rescueConfidence = min(\n                shortHeadroom, min(componentTrust, localGeometry));\n\n            /* IRIS_26610_SHORT_COMPLETE_PHYSICAL_CAP\n             * ordinaryWeight remains bit-for-bit the measurable NORMAL-style weight whenever\n             * physicalCensoring=0. In a proven censored core only the invalid NORMAL-reference\n             * photometric term may relax; the inherited ordinary-rejection unblocker protection,\n             * exact common dilation, SHORT headroom, component trust, and local residual remain\n             * mandatory. No clipping state may erase the local residual cap. */\n            float sharedPhysicalProtection = min(physicalWeight, localResidualConfidence);\n            float censoredCoreWeight = min(sharedPhysicalProtection, rescueConfidence);\n'''
new = '''            /* IRIS_26611_BOUNDARY_PROVEN_SHORT_RESCUE_ONLY\n             * componentTrust can exist only if a sub-pixel, same-CFA, exposure-normalized\n             * measurable boundary seed was proven and then propagated through the two-phase clipped\n             * interior without a CFA-meaningful flow discontinuity. The old 2..8 RAW-pixel local\n             * residual curve is deliberately absent here: it was the 26610 device-proven path that\n             * treated a 2.46-pixel residual as ~98% trustworthy. */\n            float rescueConfidence = min(shortHeadroom, componentTrust);\n\n            /* IRIS_26611_SHORT_COMPLETE_COMMON_PHYSICAL_CAP\n             * Only NORMAL-reference photometry is relaxable in a proven censored core. The exact\n             * ordinary-rejection physical/unblocker weight after the same dilation remains a hard\n             * cap, and the common RBF 3x3 source-clipping guard still runs afterward. */\n            float censoredCoreWeight = min(physicalWeight, rescueConfidence);\n'''
replace_once(SABRE, old, new, 'boundary-proven SHORT rescue')

old = '''            float finalWeight = mix(ordinaryWeight, censoredCoreWeight, physicalCensoring);\n            oWeight = clamp(finalWeight, 0.0, 1.0);\n            oRescueOnlyWeight = clamp(censoredCoreWeight * physicalCensoring, 0.0, 1.0);\n'''
new = '''            float finalWeight = mix(ordinaryWeight, censoredCoreWeight, physicalCensoring);\n            oWeight = clamp(finalWeight, 0.0, 1.0);\n            oRescueOnlyWeight = clamp(max(finalWeight - ordinaryWeight, 0.0), 0.0, 1.0);\n'''
replace_once(SABRE, old, new, 'actual rescue-only telemetry')

# 2) VGN must see HDR-independent color direction. Below white this is bit-identical to the old
# normalized carrier; above white the entire RGB vector is scaled together rather than per-channel
# clipping, so chroma evidence cannot be distorted by the HDR magnitude.
anchor = '''    val outputTransformFloat = """\n        #version 300 es\n        $outputTransformBody\n        layout(location = 0) out vec4 oResolved;\n        void main() {\n            ivec2 p = ivec2(gl_FragCoord.xy);\n            oResolved = vec4(transformOutput(p), 1.0);\n        }\n    """.trimIndent()\n\n\n    /* IRIS_26605_EXTENDED_HDR_POST_VGN_RESTORE\n'''
replacement = '''    val outputTransformFloat = """\n        #version 300 es\n        $outputTransformBody\n        layout(location = 0) out vec4 oResolved;\n        void main() {\n            ivec2 p = ivec2(gl_FragCoord.xy);\n            oResolved = vec4(transformOutput(p), 1.0);\n        }\n    """.trimIndent()\n\n    /* IRIS_26611_HDR_INDEPENDENT_VGN_COLOR_DIRECTION\n     * Below white this is exactly the existing normalized camera RGB. Above white the physical\n     * RGB vector is divided by one scalar max-RGB magnitude before RGBA16UI quantization. VGN thus\n     * sees the true color direction without per-channel clipping, while the unclipped physical\n     * magnitude remains in the separate RGBA16F carrier for scalar restoration after cleanup. */\n    val outputTransformHdrDirectionUint16 = """\n        #version 300 es\n        $outputTransformBody\n        layout(location = 0) out highp uvec4 oResolved;\n        float max3(vec3 v) { return max(v.r, max(v.g, v.b)); }\n        void main() {\n            ivec2 p = ivec2(gl_FragCoord.xy);\n            vec3 physical = max(transformOutput(p), vec3(0.0));\n            float magnitude = max(max3(physical), 1.0);\n            vec3 directionDomain = clamp(physical / magnitude, 0.0, 1.0);\n            oResolved = uvec4(uvec3(round(directionDomain * 65535.0)), 65535u);\n        }\n    """.trimIndent()\n\n\n    /* IRIS_26605_EXTENDED_HDR_POST_VGN_RESTORE\n'''
replace_once(SABRE, anchor, replacement, 'insert HDR-independent VGN direction owner')

# Replace dirty per-channel excess resurrection with sole cleaned RGB direction + scalar physical maxRGB.
old = '''    /* IRIS_26605_EXTENDED_HDR_POST_VGN_RESTORE\n     * VGN remains the validated normalized color/noise processor. Physical highlight radiance\n     * stays in the unclipped float Resolve carrier. Apply VGN only as a normalized-domain delta:\n     * below white this is exactly VGN; above white the original per-channel excess survives.\n     */\n    val restoreExtendedHdrAfterVgn = """\n        #version 300 es\n        precision highp float;\n        precision highp int;\n        precision highp usampler2D;\n        uniform sampler2D uPhysicalHdr;\n        uniform highp usampler2D uVgnNormalized;\n        uniform ivec2 uImageSize;\n        layout(location = 0) out vec4 oHdr;\n        void main() {\n            ivec2 p = clamp(ivec2(gl_FragCoord.xy), ivec2(0), uImageSize - ivec2(1));\n            vec3 physical = max(texelFetch(uPhysicalHdr, p, 0).rgb, vec3(0.0));\n            vec3 normalizedProxy = clamp(physical, 0.0, 1.0);\n            vec3 vgn = vec3(texelFetch(uVgnNormalized, p, 0).rgb) / 65535.0;\n            vec3 restored = physical + (vgn - normalizedProxy);\n            oHdr = vec4(max(restored, vec3(0.0)), 1.0);\n        }\n    """.trimIndent()\n'''
new = '''    /* IRIS_26611_CLEAN_DIRECTION_SCALAR_HDR_RESTORE\n     * VGN-cleaned RGB is the sole post-clean hue/chroma authority. The old physical RGB vector may\n     * contribute exactly one scalar: its max-RGB HDR magnitude, which is also the source-domain\n     * guide consumed by the validated 26610 rendition. Below white the output remains exactly VGN.\n     * Above white, one scalar magnitude multiplies the cleaned direction; no pre-clean R/G/B excess\n     * can cross the cleanup boundary independently, so dirty magenta/cyan cannot be resurrected. */\n    val restoreExtendedHdrAfterVgn = """\n        #version 300 es\n        precision highp float;\n        precision highp int;\n        precision highp usampler2D;\n        uniform sampler2D uPhysicalHdr;\n        uniform highp usampler2D uVgnNormalized;\n        uniform ivec2 uImageSize;\n        layout(location = 0) out vec4 oHdr;\n        float max3(vec3 v) { return max(v.r, max(v.g, v.b)); }\n        void main() {\n            ivec2 p = clamp(ivec2(gl_FragCoord.xy), ivec2(0), uImageSize - ivec2(1));\n            vec3 physical = max(texelFetch(uPhysicalHdr, p, 0).rgb, vec3(0.0));\n            float physicalMagnitude = max3(physical);\n            vec3 cleaned = max(vec3(texelFetch(uVgnNormalized, p, 0).rgb) / 65535.0, vec3(0.0));\n            vec3 restored = cleaned;\n            if (physicalMagnitude > 1.0) {\n                float cleanedMagnitude = max3(cleaned);\n                vec3 cleanedDirection = cleanedMagnitude > 1.0e-6 ?\n                    cleaned / cleanedMagnitude : vec3(1.0);\n                restored = cleanedDirection * physicalMagnitude;\n            }\n            oHdr = vec4(max(restored, vec3(0.0)), 1.0);\n        }\n    """.trimIndent()\n'''
replace_once(SABRE, old, new, 'clean direction scalar HDR restore')

# 3) Universal false-color cleanup: retain old fail-closed cap for ambiguous/real-color cases, but
# when all existing neutral-surface + Bayer-phase + no-real-color gates are overwhelming, allow the
# observed neutral consensus to become authoritative in one pass. This addresses the second proven
# 26610 failure without globally desaturating highlights.
old = '''            /* Correction cannot invent a new hue or repaint a pixel. A non-neutral target with a\n             * substantially different hue is ambiguous and therefore untouched. The actual chroma\n             * displacement is then capped to 40% of the original chroma magnitude and 0.05 in the\n             * normalized camera-RGB domain, whichever is smaller.\n             */\n            float targetAgreement = hueAgreement(centerChroma, targetChroma);\n            float targetNeutral = 1.0 - smoothstep(0.010, 0.045, targetMagnitude);\n            float supportedTarget = max(targetNeutral, smoothstep(0.82, 0.94, targetAgreement));\n            float correction = falseColorGate * supportedTarget;\n            vec3 desiredDelta = targetChroma - centerChroma;\n            float desiredLength = length(desiredDelta);\n            float maximumMove = min(0.050, 0.40 * centerMagnitude);\n            float boundedScale = desiredLength > 1.0e-7 ? min(1.0, maximumMove / desiredLength) : 0.0;\n            vec3 correctedChroma = centerChroma + desiredDelta * boundedScale * correction;\n'''
new = '''            /* IRIS_26611_DECISIVE_NEUTRAL_CFA_FALSE_COLOR_OWNER\n             * Ambiguous and genuinely colored pixels retain the proven fail-closed 26578 cap. But\n             * when every independent gate already says "neutral same-surface Bayer-phase outlier"\n             * with overwhelming confidence, the old min(0.05,40%) cap is itself a known failure:\n             * device 26610 can carry a strong 1-2 px opponent fringe through VGN. In that narrow\n             * decisive case the observed neutral consensus is allowed to become authoritative in a\n             * single pass. Real-color topology remains a multiplicative veto through falseColorScore. */\n            float targetAgreement = hueAgreement(centerChroma, targetChroma);\n            float targetNeutral = 1.0 - smoothstep(0.010, 0.045, targetMagnitude);\n            float supportedTarget = max(targetNeutral, smoothstep(0.82, 0.94, targetAgreement));\n            float correction = falseColorGate * supportedTarget;\n            vec3 desiredDelta = targetChroma - centerChroma;\n            float desiredLength = length(desiredDelta);\n            float decisiveNeutralCfaProof =\n                smoothstep(0.92, 0.985, falseColorScore) *\n                smoothstep(0.88, 0.985, phaseLikeEvidence) *\n                smoothstep(0.90, 0.995, neutralSurfaceSupport) *\n                smoothstep(0.90, 0.995, targetNeutral) *\n                (1.0 - smoothstep(0.02, 0.12, realColorConfidence));\n            float legacyMaximumMove = min(0.050, 0.40 * centerMagnitude);\n            float maximumMove = mix(legacyMaximumMove, desiredLength, decisiveNeutralCfaProof);\n            float boundedScale = desiredLength > 1.0e-7 ? min(1.0, maximumMove / desiredLength) : 0.0;\n            vec3 correctedChroma = centerChroma + desiredDelta * boundedScale * correction;\n'''
replace_once(VGN, old, new, 'decisive neutral CFA cleanup')

# Stacker: use scalar-normalized HDR direction as the VGN input only when extended-HDR preservation
# is active. This changes no non-HDR path and keeps the physical RGBA16F carrier untouched.
old = '''        sabreOutputTransformProgram = linkProgram(\n            GlesMgcRawSabreShaders.outputTransformUint16,\n            "mgc_sabre_output_transform_rgba16ui_pre_vgn",\n        )\n'''
new = '''        sabreOutputTransformProgram = linkProgram(\n            if (preserveExtendedHdrThroughVgn) {\n                GlesMgcRawSabreShaders.outputTransformHdrDirectionUint16\n            } else {\n                GlesMgcRawSabreShaders.outputTransformUint16\n            },\n            if (preserveExtendedHdrThroughVgn) {\n                "iris_26611_sabre_output_transform_clean_direction_pre_vgn"\n            } else {\n                "mgc_sabre_output_transform_rgba16ui_pre_vgn"\n            },\n        )\n'''
replace_once(STACK, old, new, 'VGN HDR direction program selection')

# Update restore diagnostics and stale semantic-funnel wording so device logs describe the active contract.
replace_once(STACK,
'''        check(program != 0) { "26605 extended HDR restore program is not initialized" }\n''',
'''        check(program != 0) { "26611 clean-direction scalar HDR restore program is not initialized" }\n''', 'restore program label')
replace_once(STACK,
'''        checkGlError("26605 post-VGN extended HDR restoration")\n''',
'''        checkGlError("26611 clean-direction scalar HDR restoration")\n''', 'restore GL label')
replace_once(STACK,
'''                            "absoluteOwner=FLOW_CELL_FOOTPRINT_BOUNDARY_RADIOMETRY probes=5x5 " +\n                            "boundaryError=0.03..0.08 componentFlowBarrierRawPx=4..16 " +\n                            "boundaryLocalResidualRequired=true predictorCannotOverrideLocalBoundary=true " +\n                            "literalCoreTwoPhaseClipBypass=true " +\n''',
'''                            "absoluteOwner=SAME_CFA_MEASURABLE_BOUNDARY_RADIOMETRY probes=5x5 " +\n                            "boundaryError=0.03..0.08 boundaryResidualRawPx=0.35..0.95 " +\n                            "componentFlowBarrierRawPx=0.50..1.25 " +\n                            "boundaryLocalResidualRequired=true predictorCannotOverrideLocalBoundary=true " +\n                            "literalCoreSelfSeed=false effectiveLossPhotometricBypass=false " +\n''', 'SHORT funnel truth')

# Authority assertions: old proven bad mechanisms must be gone from the active files.
must_contain(SABRE, 'IRIS_26611_SAME_CFA_MEASURABLE_BOUNDARY_SEED', 'SHORT seed marker')
must_contain(SABRE, 'IRIS_26611_CLEAN_DIRECTION_SCALAR_HDR_RESTORE', 'clean restore marker')
must_contain(VGN, 'IRIS_26611_DECISIVE_NEUTRAL_CFA_FALSE_COLOR_OWNER', 'VGN marker')

sabre=(APP/SABRE).read_text()
if 'physical + (vgn - normalizedProxy)' in sabre:
    raise SystemExit('old dirty per-channel HDR resurrection survived')
if '1.0 - smoothstep(2.0, 8.0, max(flow.w, 0.0));' in sabre[sabre.index('val shortComponentAnchor26607'):sabre.index('val shortComponentPropagate26607')]:
    raise SystemExit('old loose boundary residual survived active component anchor')

print('PASS transform 26611 V1')
