from pathlib import Path
import re, shutil, sys

if len(sys.argv) != 4:
    raise SystemExit('usage: transform_26788.py BASE_ROOT CANDIDATE_ROOT PAYLOAD_ROOT')
BASE = Path(sys.argv[1]); OUT = Path(sys.argv[2]); PAYLOAD = Path(sys.argv[3])
if OUT.exists(): shutil.rmtree(OUT)
shutil.copytree(BASE, OUT)
ROOT = OUT/'app'
S = ROOT/'src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
T = ROOT/'src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
V = ROOT/'version.properties'

def once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f'{label}: expected one anchor, got {n}')
    return text.replace(old, new, 1)

def block(text, start, end, label):
    a = text.find(start)
    if a < 0: raise RuntimeError(f'{label}: start missing')
    b = text.find(end, a)
    if b < 0: raise RuntimeError(f'{label}: end missing')
    b += len(end)
    return a,b,text[a:b]

s = S.read_text()
t = T.read_text()
v = V.read_text()

# ---- Version ----
v = once(v, 'VERSION_NAME=0.9726787\nVERSION_BUILD=26787\n',
         'VERSION_NAME=0.9726788\nVERSION_BUILD=26788\n', 'version')

# ---- New phase-safe packed-CFA LCA shader; retire post-RGB LCA shader ----
start = '    /* IRIS_26787_JPEG_LCA_PRE_RESOLVE\n'
end = '    """.trimIndent()\n'
a,b,old_lca = block(s, start, end, '26787 post-RGB LCA shader')
new_lca = r'''    /* IRIS_26788_JPEG_PHASE_SAFE_CFA_LCA
     * 26787 moved already-reconstructed RGB channels and therefore could amplify CFA-periodic
     * opponent color. 26788 applies the exact 26786 radial model while samples are still on their
     * physical Bayer phase lattice. R reads only R, B only B, and both greens are byte-identical
     * passthroughs. The merge keeps its original unwarped source texture separately for physical
     * headroom/validity ownership, so this optical registration cannot invent source validity. */
    val jpegPhaseSafeCfaLca26788 = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uSource;
        uniform ivec2 uExtractedSize;
        uniform ivec2 uRawSize;
        uniform int uCfaPattern;
        uniform vec2 uKrKb26788;
        layout(location = 0) out vec4 oExtractedBayer;

        ivec2 phaseOffset26788(int phaseIndex) {
            return ivec2(phaseIndex & 1, (phaseIndex >> 1) & 1);
        }
        float phaseK26788(int phaseIndex) {
            if (phaseIndex == uCfaPattern) return uKrKb26788.x;
            if (phaseIndex == 3 - uCfaPattern) return uKrKb26788.y;
            return 0.0;
        }
        float component26788(vec4 v, int phaseIndex) {
            if (phaseIndex == 0) return v.r;
            if (phaseIndex == 1) return v.g;
            if (phaseIndex == 2) return v.b;
            return v.a;
        }
        float samePhaseBilinear26788(vec2 rawPixelCenter, int phaseIndex) {
            ivec2 offset = phaseOffset26788(phaseIndex);
            vec2 lattice = 0.5 * (rawPixelCenter - (vec2(offset) + vec2(0.5)));
            vec2 maximum = vec2(max(uExtractedSize - ivec2(1), ivec2(0)));
            lattice = clamp(lattice, vec2(0.0), maximum);
            ivec2 q0 = ivec2(floor(lattice));
            ivec2 q1 = min(q0 + ivec2(1), uExtractedSize - ivec2(1));
            vec2 f = fract(lattice);
            float c00 = component26788(texelFetch(uSource, q0, 0), phaseIndex);
            float c10 = component26788(texelFetch(uSource, ivec2(q1.x, q0.y), 0), phaseIndex);
            float c01 = component26788(texelFetch(uSource, ivec2(q0.x, q1.y), 0), phaseIndex);
            float c11 = component26788(texelFetch(uSource, q1, 0), phaseIndex);
            return mix(mix(c00, c10, f.x), mix(c01, c11, f.x), f.y);
        }
        void main() {
            ivec2 q = ivec2(gl_FragCoord.xy);
            vec4 center = texelFetch(uSource, q, 0);
            vec4 corrected = center;
            vec2 opticalCenter = 0.5 * vec2(uRawSize);
            for (int phaseIndex = 0; phaseIndex < 4; ++phaseIndex) {
                float k = phaseK26788(phaseIndex);
                if (abs(k) < 1.0e-12) continue; // both green phases remain exact source values
                ivec2 offset = phaseOffset26788(phaseIndex);
                vec2 targetCenter = vec2(q * 2 + offset) + vec2(0.5);
                vec2 correctedCenter = opticalCenter +
                    (targetCenter - opticalCenter) * (1.0 - k);
                corrected[phaseIndex] = samePhaseBilinear26788(correctedCenter, phaseIndex);
            }
            oExtractedBayer = corrected;
        }
    """.trimIndent()
'''
s = s[:a] + new_lca + s[b:]

# ---- Merge shader: corrected CFA is signal only; original CFA remains headroom/validity owner ----
ma,mb,merge = block(s, '    val merge = """\n', '    """.trimIndent()\n', 'merge shader')
merge = once(merge,
    '        uniform sampler2D uExtractedBayer;\n',
    '        uniform sampler2D uExtractedBayer;\n        uniform sampler2D uExtractedBayerValidity;\n',
    'merge validity sampler')
helper_anchor = '''        mat3 get3x3FromExtractedBayer(ivec2 bayerPosition) {\n'''
ha = merge.find(helper_anchor)
if ha < 0: raise RuntimeError('merge helper missing')
# Find whole function by locating next swizzle function.
hb = merge.find('        vec4 swizzleForType', ha)
if hb < 0: raise RuntimeError('merge helper end missing')
helper = merge[ha:hb]
valid_helper = helper.replace('get3x3FromExtractedBayer(', 'get3x3FromExtractedBayerValidity(', 1).replace(
    'uExtractedBayer', 'uExtractedBayerValidity')
merge = merge[:hb] + valid_helper + merge[hb:]
merge = once(merge,
    '            mat3 bayerValue = get3x3FromExtractedBayer(position);\n            mat3 sourceValidity = mat3(1.0);',
    '            mat3 bayerValue = get3x3FromExtractedBayer(position);\n            mat3 validityBayerValue26788 = get3x3FromExtractedBayerValidity(position);\n            mat3 sourceValidity = mat3(1.0);',
    'merge validity matrix')
merge = once(merge,
    '                        bayerValue[sx][sy]);\n                    sourceValidity[sx][sy]=sampleConfidence;',
    '                        validityBayerValue26788[sx][sy]);\n                    sourceValidity[sx][sy]=sampleConfidence;',
    'merge validity values')
s = s[:ma] + merge + s[mb:]

# ---- SHORT fusion shader: same separation of corrected signal from original source validity ----
sa,sb,short = block(s, '    val universalNormalMasterShortFusion26651 = """\n', '    """.trimIndent()\n', 'short fusion shader')
short = once(short,
    '        uniform sampler2D uShortExtractedBayer;\n',
    '        uniform sampler2D uShortExtractedBayer;\n        uniform sampler2D uShortExtractedBayerValidity;\n',
    'short validity sampler')
short = once(short,
    '            vec4 q = texture(uShortExtractedBayer, clamp(uv, vec2(0.0), vec2(1.0)));\n',
    '            vec4 q = texture(uShortExtractedBayerValidity, clamp(uv, vec2(0.0), vec2(1.0)));\n',
    'short guide keeps unwarped geometry owner')
ha = short.find(helper_anchor)
if ha < 0: raise RuntimeError('short helper missing')
hb = short.find('        vec4 swizzleForType', ha)
if hb < 0: raise RuntimeError('short helper end missing')
helper = short[ha:hb]
valid_helper = helper.replace('get3x3FromExtractedBayer(', 'get3x3FromExtractedBayerValidity(', 1).replace(
    'uShortExtractedBayer', 'uShortExtractedBayerValidity')
short = short[:hb] + valid_helper + short[hb:]
short = once(short,
    '            mat3 bayerValue = get3x3FromExtractedBayer(position);\n            mat3 sourceValidity = mat3(1.0);',
    '            mat3 bayerValue = get3x3FromExtractedBayer(position);\n            mat3 validityBayerValue26788 = get3x3FromExtractedBayerValidity(position);\n            mat3 sourceValidity = mat3(1.0);',
    'short validity matrix')
short = once(short,
    '                        bayerValue[sx][sy]);\n                }\n            }',
    '                        validityBayerValue26788[sx][sy]);\n                }\n            }',
    'short validity values')
s = s[:sa] + short + s[sb:]

# ---- Stacker program ownership: new pre-merge CFA LCA, old post-RGB program retired ----
t = once(t,
    '    private var sabreJpegNeutralHighlightClampProgram26787 = 0\n    private var sabreJpegLcaPreResolveProgram26787 = 0\n',
    '    private var sabreJpegNeutralHighlightClampProgram26787 = 0\n    private var sabreJpegPhaseSafeCfaLcaProgram26788 = 0\n',
    'program field')

# Replace renderer with packed-CFA phase-safe renderer.
ra,rb,old_renderer = block(t,
    '    private fun renderSabreJpegLcaPreResolve26787(\n',
    '    }\n',
    'old JPEG LCA renderer')
new_renderer = '''    private fun renderSabreJpegPhaseSafeCfaLca26788(\n        source: Int,\n        extractedWidth: Int,\n        extractedHeight: Int,\n        kR: Float,\n        kB: Float,\n    ): Int {\n        val program = sabreJpegPhaseSafeCfaLcaProgram26788\n        check(program != 0 && source != 0)\n        val output = createTexture(\n            extractedWidth, extractedHeight, GLES30.GL_RGBA16F, GLES30.GL_NEAREST,\n        )\n        GLES30.glUseProgram(program)\n        bindTexture(program, "uSource", 0, source)\n        uniform2i(program, "uExtractedSize", extractedWidth, extractedHeight)\n        uniform2i(program, "uRawSize", width, height)\n        uniform1i(program, "uCfaPattern", cfaPattern)\n        uniform2f(program, "uKrKb26788", kR, kB)\n        draw(program, extractedWidth, extractedHeight, intArrayOf(output))\n        return output\n    }\n'''
t = t[:ra] + new_renderer + t[rb:]

# Link new program instead of retired post-RGB program.
t = once(t,
'''        sabreJpegLcaPreResolveProgram26787 = linkProgram(\n            GlesMgcRawSabreShaders.jpegLcaPreResolve26787,\n            "iris_26787_jpeg_lca_pre_resolve",\n        )\n''',
'''        sabreJpegPhaseSafeCfaLcaProgram26788 = linkProgram(\n            GlesMgcRawSabreShaders.jpegPhaseSafeCfaLca26788,\n            "iris_26788_jpeg_phase_safe_cfa_lca",\n        )\n''',
'program link')

# Extend merge renderer signature and bind corrected signal + original validity.
t = once(t,
'''        validityWeightScale26614: Float = 1f,\n        rowFlickerFrame26720: RawStackFrame? = null,\n    ) {\n        val rowFlickerActive26720 = rowFlickerFrame26720?.let(::hasRowFlickerEvidence26720) == true\n        val program = sabreMergeProgram\n        GLES30.glUseProgram(program)\n        bindTexture(program, "uExtractedBayer", 0, extracted)\n        bindTexture(program, "uFlow", 1, flow.texture)\n        bindTexture(program, "uCovariance", 2, covariance)\n        bindTexture(program, "uRejection", 3, weight)\n''',
'''        validityWeightScale26614: Float = 1f,\n        rowFlickerFrame26720: RawStackFrame? = null,\n        jpegPhaseSafeLca26788: Boolean = false,\n        jpegLcaKr26788: Float = 0f,\n        jpegLcaKb26788: Float = 0f,\n    ) {\n        val rowFlickerActive26720 = rowFlickerFrame26720?.let(::hasRowFlickerEvidence26720) == true\n        val signalExtracted26788 = if (jpegPhaseSafeLca26788) {\n            renderSabreJpegPhaseSafeCfaLca26788(\n                source = extracted, extractedWidth = extractedWidth, extractedHeight = extractedHeight,\n                kR = jpegLcaKr26788, kB = jpegLcaKb26788,\n            )\n        } else extracted\n        val program = sabreMergeProgram\n        GLES30.glUseProgram(program)\n        bindTexture(program, "uExtractedBayer", 0, signalExtracted26788)\n        bindTexture(program, "uFlow", 1, flow.texture)\n        bindTexture(program, "uCovariance", 2, covariance)\n        bindTexture(program, "uRejection", 3, weight)\n        bindTexture(program, "uExtractedBayerValidity", 4, extracted)\n''',
'merge renderer header')
# Release local corrected CFA after draw while retaining old blend semantics.
t = once(t,
'''        } finally {\n            GLES30.glDisable(GLES30.GL_BLEND)\n        }\n    }\n\n    private fun clearSabreSuperResAccumulator''',
'''        } finally {\n            GLES30.glDisable(GLES30.GL_BLEND)\n            if (signalExtracted26788 != extracted) {\n                releaseOwnedTexture(signalExtracted26788, "26788 phase-safe CFA LCA merge signal")\n            }\n        }\n    }\n\n    private fun clearSabreSuperResAccumulator''',
'merge temp release')

# Main reference and alternate NORMAL/LONG merge calls get same settings as proven DNG LCA.
ref_anchor = '''                rowFlickerFrame26720 = frames.first().takeIf(::hasRowFlickerEvidence26720),\n            )'''
t = once(t, ref_anchor,
'''                rowFlickerFrame26720 = frames.first().takeIf(::hasRowFlickerEvidence26720),\n                jpegPhaseSafeLca26788 = dngOptions26786.lcaEnabled,\n                jpegLcaKr26788 = dngOptions26786.kR,\n                jpegLcaKb26788 = dngOptions26786.kB,\n            )''', 'reference merge LCA args')
alt_anchor = '''                        rowFlickerFrame26720 = frame.takeIf(::hasRowFlickerEvidence26720),\n                    )'''
t = once(t, alt_anchor,
'''                        rowFlickerFrame26720 = frame.takeIf(::hasRowFlickerEvidence26720),\n                        jpegPhaseSafeLca26788 = dngOptions26786.lcaEnabled,\n                        jpegLcaKr26788 = dngOptions26786.kR,\n                        jpegLcaKb26788 = dngOptions26786.kB,\n                    )''', 'alternate merge LCA args')

# SHORT fusion renderer: correct signal in CFA domain while source validity remains original.
t = once(t,
'''        validityWeightScale: Float,\n        referenceProtectionEv: Float,\n    ) {\n        val program = sabreNormalMasterShortFusionProgram26651\n        check(program != 0)\n        GLES30.glUseProgram(program)\n''',
'''        validityWeightScale: Float,\n        referenceProtectionEv: Float,\n        jpegPhaseSafeLca26788: Boolean,\n        jpegLcaKr26788: Float,\n        jpegLcaKb26788: Float,\n    ) {\n        val program = sabreNormalMasterShortFusionProgram26651\n        check(program != 0)\n        val shortSignal26788 = if (jpegPhaseSafeLca26788) {\n            renderSabreJpegPhaseSafeCfaLca26788(\n                source = shortExtracted, extractedWidth = extractedWidth, extractedHeight = extractedHeight,\n                kR = jpegLcaKr26788, kB = jpegLcaKb26788,\n            )\n        } else shortExtracted\n        GLES30.glUseProgram(program)\n''',
'short renderer signature')
t = once(t,
'''        bindTexture(program, "uShortExtractedBayer", 4, shortExtracted)\n        bindTexture(program, "uShortFlow", 5, shortFlow.texture)\n        bindTexture(program, "uShortCovariance", 6, shortCovariance)\n        bindTexture(program, "uShortPhysicalReverseWeight", 7, shortPhysicalReverseWeight)\n''',
'''        bindTexture(program, "uShortExtractedBayer", 4, shortSignal26788)\n        bindTexture(program, "uShortFlow", 5, shortFlow.texture)\n        bindTexture(program, "uShortCovariance", 6, shortCovariance)\n        bindTexture(program, "uShortPhysicalReverseWeight", 7, shortPhysicalReverseWeight)\n        bindTexture(program, "uShortExtractedBayerValidity", 8, shortExtracted)\n''',
'short renderer bindings')
t = once(t,
'''        uniform1f(program, "uReferenceProtectionEv", referenceProtectionEv.coerceIn(0f, 1.5f))\n        draw(program, width, height, intArrayOf(fusedOutput, decisionOutput, shortColorValidityOutput))\n    }\n''',
'''        uniform1f(program, "uReferenceProtectionEv", referenceProtectionEv.coerceIn(0f, 1.5f))\n        try {\n            draw(program, width, height, intArrayOf(fusedOutput, decisionOutput, shortColorValidityOutput))\n        } finally {\n            if (shortSignal26788 != shortExtracted) {\n                releaseOwnedTexture(shortSignal26788, "26788 phase-safe CFA LCA SHORT signal")\n            }\n        }\n    }\n''',
'short temp release')
# Call supplies same LCA settings.
t = once(t,
'''                    validityWeightScale = validityWeightScale26614,\n                    referenceProtectionEv = referenceProtectionEv,\n                )''',
'''                    validityWeightScale = validityWeightScale26614,\n                    referenceProtectionEv = referenceProtectionEv,\n                    jpegPhaseSafeLca26788 = dngOptions26786.lcaEnabled,\n                    jpegLcaKr26788 = dngOptions26786.kR,\n                    jpegLcaKb26788 = dngOptions26786.kB,\n                )''',
'short call LCA args')

# Retire post-RGB LCA routing completely. The Resolve carrier is now already phase-corrected.
old_route_start = '            /* IRIS_26787_SHARE_DNG_LCA_WITH_JPEG\n'
old_route_end = '            if (resolveExtendedLinear26651 != resolveAccumulatedColor26604) {'
a = t.find(old_route_start)
b = t.find(old_route_end, a)
if a < 0 or b < 0: raise RuntimeError('old post-RGB LCA route missing')
new_route = '''            /* IRIS_26788_ONE_PHASE_SAFE_LCA_OWNER\n             * The R/B optical correction now occurs on same-phase packed CFA measurements before\n             * NORMAL/LONG RBF reconstruction and before optional SHORT fusion. Resolve consumes the\n             * resulting extended-linear master directly; the 26787 post-RGB channel warp is retired. */\n            PLog.i(\n                SABRE_TAG,\n                "IRIS_26788_JPEG_CFA_OPTIONS lca=${dngOptions26786.lcaEnabled} " +\n                    "kR=${dngOptions26786.kR} kB=${dngOptions26786.kB} " +\n                    "neutralClamp=${dngOptions26786.neutralClamp} " +\n                    "headroomScope=${dngOptions26786.headroomScopeName()} " +\n                    "deAlias=${dngOptions26786.edgeDeAlias} settingsSource=${dngOptions26786.source} " +\n                    "owner=PRE_RBF_SAME_PHASE_CFA postRgbLcaRetired=true validityOwner=UNWARPED_SOURCE_CFA",\n            )\n            sabreAccumulatedReadback = readSabreAccumulatedRgba16f(resolveExtendedLinear26651)\n'''
t = t[:a] + new_route + t[b:]

# ---- 26788 narrow material-baseline periodic residual guard ----
old_guard = '''          /* IRIS_26782_COHERENT_BIPOLAR_EDGE_GUARD\n           * A long cyan/yellow-red fringe can agree with its 3x3 median and evade 26778. Use the\n           * dominant luma-gradient axis only to inspect the two +/-2px chroma lobes. Correction is\n           * allowed only when those lobes are genuinely opposite and their midpoint is near neutral. */\n          float yLeft = lumaOf(fetchLin(p + ivec2(-2, 0), sz));\n          float yRight = lumaOf(fetchLin(p + ivec2(2, 0), sz));\n          float yUp = lumaOf(fetchLin(p + ivec2(0, -2), sz));\n          float yDown = lumaOf(fetchLin(p + ivec2(0, 2), sz));\n          bool horizontalNormal = abs(yRight - yLeft) >= abs(yDown - yUp);\n          ivec2 edgeStep = horizontalNormal ? ivec2(2, 0) : ivec2(0, 2);\n          vec2 cNeg = sqrtChromaAt(p - edgeStep, sz);\n          vec2 cPos = sqrtChromaAt(p + edgeStep, sz);\n          vec2 pairMid = 0.5 * (cNeg + cPos);\n          float negLen = length(cNeg);\n          float posLen = length(cPos);\n          float opposition = clamp(-dot(cNeg, cPos) / max(negLen * posLen, 1.0e-6), 0.0, 1.0);\n          float bipolarMagnitude = min(negLen, posLen);\n          float midpointNeutral = 1.0 - smoothstep(0.055, 0.14, length(pairMid));\n          float coherentW = gate *\n            smoothstep(max(0.018, uOutlierLo * 0.65), max(0.055, uOutlierHi * 0.80), bipolarMagnitude) *\n            smoothstep(0.35, 0.80, opposition) * midpointNeutral;\n'''
new_guard = '''          /* IRIS_26788_MATERIAL_BASELINE_PERIODIC_FALSE_COLOR\n           * 26787's coherent guard required the +/-2px endpoint midpoint itself to be near neutral.\n           * Device evidence shows the remaining 1-2px cyan/yellow/magenta/green alternation can ride\n           * on a legitimate colored material baseline, so neutrality is not a valid prerequisite.\n           * Along the dominant luma-gradient normal, compare +/-1 against +/-2 on BOTH sides. A true\n           * material edge is locally monotonic (same-side near/far chroma agrees); CFA false color\n           * alternates near/far coherently on both sides. Build a nonzero local material baseline\n           * from both phases and remove only the alternating component. */\n          float yLeft = lumaOf(fetchLin(p + ivec2(-2, 0), sz));\n          float yRight = lumaOf(fetchLin(p + ivec2(2, 0), sz));\n          float yUp = lumaOf(fetchLin(p + ivec2(0, -2), sz));\n          float yDown = lumaOf(fetchLin(p + ivec2(0, 2), sz));\n          bool horizontalNormal = abs(yRight - yLeft) >= abs(yDown - yUp);\n          ivec2 step1 = horizontalNormal ? ivec2(1, 0) : ivec2(0, 1);\n          ivec2 step2 = step1 * 2;\n          vec2 cNeg2 = sqrtChromaAt(p - step2, sz);\n          vec2 cNeg1 = sqrtChromaAt(p - step1, sz);\n          vec2 cPos1 = sqrtChromaAt(p + step1, sz);\n          vec2 cPos2 = sqrtChromaAt(p + step2, sz);\n          vec2 farMid = 0.5 * (cNeg2 + cPos2);\n          vec2 nearMid = 0.5 * (cNeg1 + cPos1);\n          vec2 materialBaseline26788 = 0.5 * (farMid + nearMid);\n          vec2 periodicVector26788 = nearMid - farMid;\n          vec2 centerDeviation26788 = centerC - materialBaseline26788;\n          vec2 leftAlternation26788 = cNeg1 - cNeg2;\n          vec2 rightAlternation26788 = cPos1 - cPos2;\n          float periodicMagnitude26788 = length(periodicVector26788);\n          float centerMagnitude26788 = length(centerDeviation26788);\n          float samePhaseOpposition26788 = clamp(\n            -dot(centerDeviation26788, periodicVector26788) /\n              max(centerMagnitude26788 * periodicMagnitude26788, 1.0e-6), 0.0, 1.0);\n          float leftMagnitude26788 = length(leftAlternation26788);\n          float rightMagnitude26788 = length(rightAlternation26788);\n          float bilateralCoherence26788 = clamp(\n            dot(leftAlternation26788, rightAlternation26788) /\n              max(leftMagnitude26788 * rightMagnitude26788, 1.0e-6), 0.0, 1.0);\n          float bilateralMagnitude26788 = min(leftMagnitude26788, rightMagnitude26788);\n          float coherentW = gate *\n            smoothstep(max(0.012, uOutlierLo * 0.45), max(0.050, uOutlierHi * 0.70),\n                min(periodicMagnitude26788, bilateralMagnitude26788)) *\n            smoothstep(0.30, 0.75, samePhaseOpposition26788) *\n            smoothstep(0.45, 0.85, bilateralCoherence26788);\n          /* Keep the residual owner narrow. The causal 26788 CFA-phase registration acts first; this\n           * guard may remove at most 70% of a surviving periodic component in one pass. */\n          coherentW = min(coherentW, 0.70);\n'''
t = once(t, old_guard, new_guard, 'periodic guard')
# Retired clipped-neutral context previously depended on pairMid/midpointNeutral. Replace with material baseline.
t = once(t,
'''          float medianNeutral = 1.0 - smoothstep(0.050, 0.135, length(medianC));\n          float neutralContext = max(midpointNeutral, medianNeutral);\n''',
'''          float medianNeutral = 1.0 - smoothstep(0.050, 0.135, length(medianC));\n          float baselineNeutral26788 = 1.0 - smoothstep(0.050, 0.135, length(materialBaseline26788));\n          float neutralContext = max(baselineNeutral26788, medianNeutral);\n''',
'retired neutral telemetry compatibility')
t = once(t,
'''          correctedC = mix(correctedC, pairMid, coherentW);\n''',
'''          correctedC = mix(correctedC, materialBaseline26788, coherentW);\n''',
'periodic correction target')

# Update runtime telemetry wording without changing stats layout.
t = once(t,
'''PLog.i(SABRE_TAG, "IRIS_26784_NARROW_FALSE_COLOR_OWNER coherentGt05=${counts26778[3]} retiredClippedNeutralCandidateGt05=${counts26778[4]} broadClippedNeutralApplied=false rawValidityOwner=IRIS_26614 lumaPreserved=true old26778OutlierPathPreserved=true")''',
'''PLog.i(SABRE_TAG, "IRIS_26788_MATERIAL_BASELINE_FALSE_COLOR_OWNER coherentGt05=${counts26778[3]} retiredClippedNeutralCandidateGt05=${counts26778[4]} broadClippedNeutralApplied=false rawValidityOwner=IRIS_26614 lumaPreserved=true old26778OutlierPathPreserved=true neutralMidpointRequired=false maxPeriodicBlend=0.70")''',
'false color telemetry')

# The inherited 26781 log called the entire 26778 suppressor byte-unchanged. 26788 intentionally
# advances only its coherent periodic guard, so keep the log truthful without changing behavior.
t = once(t,
'''             * linear master directly; NORMAL/SHORT admission/fusion and the protected 26778 downstream
             * false-color suppressor remain byte-owned by their existing stages. */''',
'''             * linear master directly; NORMAL/SHORT admission/fusion stays inherited. The 26778
             * suppressor path remains active, with only its coherent periodic guard advanced by 26788. */''',
'26781 stale suppressor comment')
t = once(t,
'''                    "normalShortFusionUnchanged=true edgeSuppressor26778Unchanged=true",''',
'''                    "normalShortFusionUnchanged=true edgeSuppressor26778PeriodicGuard26788=true",''',
'26781 stale suppressor telemetry')
t = once(t,
'''periodicGate=COHERENT_BIPOLAR_26782''',
'''periodicGate=MATERIAL_BASELINE_PERIODIC_26788''',
'26778 periodic owner telemetry')
t = once(t,
'''           * either the bipolar endpoints or the local median before collapsing only chroma to zero. */''',
'''           * either the local material baseline or the local median before counting the retired candidate. */''',
'retired clipped-neutral comment')
t = once(t,
'''           * edges while the successful coherent bipolar path fired only on the narrow fringe set.''',
'''           * edges while the narrow coherent periodic path fired only on the fringe set.''',
'retired broad-clip comment')

S.write_text(s)
T.write_text(t)
V.write_text(v)
expected = [
    'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
    'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
    'app/version.properties',
]
payload_files = sorted(str(p.relative_to(PAYLOAD)) for p in PAYLOAD.rglob('*') if p.is_file())
if payload_files != expected:
    raise RuntimeError(f'payload allowlist mismatch: {payload_files}')
for rel in expected:
    if (OUT/rel).read_bytes() != (PAYLOAD/rel).read_bytes():
        raise RuntimeError(f'payload differs from deterministic transform: {rel}')
print('PASS 26788 deterministic authority-seeded transform: 3 intended runtime files over exact successful 26787 candidate')
