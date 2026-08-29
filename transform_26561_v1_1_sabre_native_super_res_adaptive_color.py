from pathlib import Path
import re,sys
root=Path(sys.argv[1] if len(sys.argv)>1 else '/mnt/data/26561_candidate')

def p(rel): return root/rel

def replace_once(rel, old, new):
    path=p(rel); s=path.read_text()
    n=s.count(old)
    if n!=1: raise SystemExit(f'{rel}: anchor count {n}, expected 1: {old[:100]!r}')
    path.write_text(s.replace(old,new,1))

# 1) GlesMgcRawFusion: SR plumbing remains Sabre-only.
rel='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt'
replace_once(rel,
'''package com.hinnka.mycamera.processor\n\nimport com.hinnka.mycamera.utils.PLog\n''',
'''package com.hinnka.mycamera.processor\n\nimport com.hinnka.mycamera.utils.PLog\nimport java.io.File\n''')
replace_once(rel,
'''    private val exportNormalStackedDng: Boolean = false,\n    private val vgnChromaCorrectionStrength: Float = 1f,\n) {''',
'''    private val exportNormalStackedDng: Boolean = false,\n    private val vgnChromaCorrectionStrength: Float = 1f,\n    private val enableSabreSuperRes: Boolean = false,\n    private val sabreSuperResTempDir: File? = null,\n) {''')
replace_once(rel,
'''            vgnChromaCorrectionStrength = vgnChromaCorrectionStrength,\n            allowShadowLong = allowSabreShadowLong,\n''',
'''            vgnChromaCorrectionStrength = vgnChromaCorrectionStrength,\n            allowShadowLong = allowSabreShadowLong,\n            enableSuperRes = enableSabreSuperRes,\n            superResTempDir = sabreSuperResTempDir,\n''')

# 2) Sabre owner: same 1x authority, optional detail-only SR sidecar.
rel='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt'
replace_once(rel,
'''package com.hinnka.mycamera.processor\n\nimport com.hinnka.mycamera.utils.PLog\n''',
'''package com.hinnka.mycamera.processor\n\nimport com.hinnka.mycamera.utils.PLog\nimport java.io.File\n''')
replace_once(rel,
'''    private val vgnChromaCorrectionStrength: Float = 1f,\n    private val allowShadowLong: Boolean = false,\n) {''',
'''    private val vgnChromaCorrectionStrength: Float = 1f,\n    private val allowShadowLong: Boolean = false,\n    private val enableSuperRes: Boolean = false,\n    private val superResTempDir: File? = null,\n) {''')
replace_once(rel,
'''                "excluded=${excluded.size} shortReferenceImmutable=true spatial=false bento=false output=linear-rgb",\n''',
'''                "excluded=${excluded.size} shortReferenceImmutable=true spatial=false bento=false output=linear-rgb " +\n                    "superRes=$enableSuperRes srEvidence=NORMAL_ONLY",\n''')
replace_once(rel,
'''            vgnChromaCorrectionStrength = vgnChromaCorrectionStrength,\n        ).processFrames(admitted)\n''',
'''            vgnChromaCorrectionStrength = vgnChromaCorrectionStrength,\n            enableSabreSuperRes = enableSuperRes,\n            sabreSuperResTempDir = superResTempDir,\n        ).processFrames(admitted)\n''')

# 3) Low-level Sabre stacker imports/constructor/program handles.
rel='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
replace_once(rel,
'''import com.hinnka.mycamera.utils.PLog\nimport java.nio.ByteBuffer\n''',
'''import com.hinnka.mycamera.utils.PLog\nimport java.io.BufferedOutputStream\nimport java.io.File\nimport java.io.FileOutputStream\nimport java.nio.ByteBuffer\n''')
replace_once(rel,
'''    private val sabreMergeGradientThreshold: Float? = null,\n    private val vgnChromaCorrectionStrength: Float = 1f,\n) {''',
'''    private val sabreMergeGradientThreshold: Float? = null,\n    private val vgnChromaCorrectionStrength: Float = 1f,\n    private val enableSabreSuperRes: Boolean = false,\n    private val sabreSuperResTempDir: File? = null,\n) {''')
replace_once(rel,
'''    private var sabreMergeProgram = 0\n    private var sabreShadowLongMergeProgram = 0\n''',
'''    private var sabreMergeProgram = 0\n    private var sabreSuperResDetailMergeProgram = 0\n    private var sabreSuperResDetailResolveProgram = 0\n    private var sabreShadowLongMergeProgram = 0\n''')

# Add process locals and validate SR temp dir + texture extent after base validation.
replace_once(rel,
'''        var normalStackedDngNoiseProfile: DoubleArray? = null\n        var exportedTexture = 0\n        var returned = false\n''',
'''        var normalStackedDngNoiseProfile: DoubleArray? = null\n        var superResDetailPath: String? = null\n        var exportedTexture = 0\n        var returned = false\n''')
replace_once(rel,
'''            val extractedWidth = ceilDiv(width, 2)\n            val extractedHeight = ceilDiv(height, 2)\n''',
'''            val extractedWidth = ceilDiv(width, 2)\n            val extractedHeight = ceilDiv(height, 2)\n            val superResWidth = if (enableSabreSuperRes) width * 2 else 0\n            val superResHeight = if (enableSabreSuperRes) height * 2 else 0\n            if (enableSabreSuperRes) {\n                requireNotNull(sabreSuperResTempDir) {\n                    "26561 Sabre Super Res requires a temp directory"\n                }\n                val maximumTexture = IntArray(1)\n                GLES30.glGetIntegerv(GLES30.GL_MAX_TEXTURE_SIZE, maximumTexture, 0)\n                require(superResWidth <= maximumTexture[0] && superResHeight <= maximumTexture[0]) {\n                    "26561 Sabre Super Res ${superResWidth}x$superResHeight exceeds GL_MAX_TEXTURE_SIZE=${maximumTexture[0]}"\n                }\n            }\n''')
# Add SR accumulator after native weights.
replace_once(rel,
'''            val accumulatedWeightsGb = createTexture(\n                width,\n                height,\n                GLES30.GL_RG16F,\n                GLES30.GL_NEAREST,\n            )\n            val accumulatedCoverage = createTexture(\n''',
'''            val accumulatedWeightsGb = createTexture(\n                width,\n                height,\n                GLES30.GL_RG16F,\n                GLES30.GL_NEAREST,\n            )\n            /* IRIS_26561_SABRE_NATIVE_2X_DETAIL\n             * The proven 1x Sabre RGB accumulator remains authoritative. Super Res adds only a\n             * two-channel 2x luma/support carrier (RG16F), never a full 2x RGB image. This keeps\n             * VGN/color ownership native and bounds the additional GPU surface to 4 bytes/pixel.\n             */\n            val superResDetailAccumulator = if (enableSabreSuperRes) {\n                createTexture(\n                    superResWidth,\n                    superResHeight,\n                    GLES30.GL_RG16F,\n                    GLES30.GL_NEAREST,\n                )\n            } else {\n                0\n            }\n            val accumulatedCoverage = createTexture(\n''')
# clear SR accumulator.
replace_once(rel,
'''            clearSabreAccumulators(\n                accumulatedColor,\n                accumulatedWeightsGb,\n                accumulatedCoverage,\n                coverageWidth,\n                coverageHeight,\n            )\n            if (normalDngAccumulator != 0) {\n''',
'''            clearSabreAccumulators(\n                accumulatedColor,\n                accumulatedWeightsGb,\n                accumulatedCoverage,\n                coverageWidth,\n                coverageHeight,\n            )\n            if (superResDetailAccumulator != 0) {\n                clearSabreSuperResAccumulator(\n                    superResDetailAccumulator,\n                    superResWidth,\n                    superResHeight,\n                )\n            }\n            if (normalDngAccumulator != 0) {\n''')
# reference contribution SR immediately after native merge.
replace_once(rel,
'''            renderSabreMerge(\n                extracted = referenceExtracted,\n                flow = zeroFlow,\n                covariance = referenceCovariance,\n                weight = identityWeight,\n                calibration = referenceCalibration,\n                accumulatedColor = accumulatedColor,\n                accumulatedWeightsGb = accumulatedWeightsGb,\n                extractedWidth = extractedWidth,\n                extractedHeight = extractedHeight,\n                useFrameWeight = false,\n                shadowLongSourceClipGuard = false,\n            )\n            if (normalDngAccumulator != 0) {\n''',
'''            renderSabreMerge(\n                extracted = referenceExtracted,\n                flow = zeroFlow,\n                covariance = referenceCovariance,\n                weight = identityWeight,\n                calibration = referenceCalibration,\n                accumulatedColor = accumulatedColor,\n                accumulatedWeightsGb = accumulatedWeightsGb,\n                extractedWidth = extractedWidth,\n                extractedHeight = extractedHeight,\n                useFrameWeight = false,\n                shadowLongSourceClipGuard = false,\n            )\n            if (superResDetailAccumulator != 0) {\n                renderSabreSuperResDetailMerge(\n                    extracted = referenceExtracted,\n                    flow = zeroFlow,\n                    covariance = referenceCovariance,\n                    weight = identityWeight,\n                    calibration = referenceCalibration,\n                    accumulator = superResDetailAccumulator,\n                    extractedWidth = extractedWidth,\n                    extractedHeight = extractedHeight,\n                    superResWidth = superResWidth,\n                    superResHeight = superResHeight,\n                    useFrameWeight = false,\n                )\n            }\n            if (normalDngAccumulator != 0) {\n''')
# Aux normal SR contribution after native merge call block, before DNG. Match unique block including closing.
old='''                renderSabreMerge(\n                    extracted = currentExtracted,\n                    flow = flow,\n                    covariance = currentCovariance,\n                    weight = frameWeight,\n                    calibration = calibration,\n                    accumulatedColor = accumulatedColor,\n                    accumulatedWeightsGb = accumulatedWeightsGb,\n                    extractedWidth = extractedWidth,\n                    extractedHeight = extractedHeight,\n                    useFrameWeight = true,\n                    shadowLongSourceClipGuard = frame.role == RawBurstFrameRole.SHADOW_LONG,\n                )\n                if (normalDngAccumulator != 0 && frame.role == RawBurstFrameRole.NORMAL) {\n'''
new='''                renderSabreMerge(\n                    extracted = currentExtracted,\n                    flow = flow,\n                    covariance = currentCovariance,\n                    weight = frameWeight,\n                    calibration = calibration,\n                    accumulatedColor = accumulatedColor,\n                    accumulatedWeightsGb = accumulatedWeightsGb,\n                    extractedWidth = extractedWidth,\n                    extractedHeight = extractedHeight,\n                    useFrameWeight = true,\n                    shadowLongSourceClipGuard = frame.role == RawBurstFrameRole.SHADOW_LONG,\n                )\n                /* IRIS_26561_NIGHT_LONG_EXCLUDED_FROM_SR_DETAIL\n                 * Native Sabre still admits validated SHADOW_LONG evidence. The fine-detail path\n                 * accepts NORMAL/Short exposure frames only, so longer exposure blur cannot become\n                 * high-frequency Super Res evidence.\n                 */\n                if (superResDetailAccumulator != 0 && frame.role == RawBurstFrameRole.NORMAL) {\n                    renderSabreSuperResDetailMerge(\n                        extracted = currentExtracted,\n                        flow = flow,\n                        covariance = currentCovariance,\n                        weight = frameWeight,\n                        calibration = calibration,\n                        accumulator = superResDetailAccumulator,\n                        extractedWidth = extractedWidth,\n                        extractedHeight = extractedHeight,\n                        superResWidth = superResWidth,\n                        superResHeight = superResHeight,\n                        useFrameWeight = true,\n                    )\n                }\n                if (normalDngAccumulator != 0 && frame.role == RawBurstFrameRole.NORMAL) {\n'''
replace_once(rel,old,new)
# Stream detail before native dehomogenize.
replace_once(rel,
'''            renderSabreDehomogenize(\n                accumulatedColor,\n''',
'''            if (superResDetailAccumulator != 0) {\n                superResDetailPath = streamSabreSuperResDetail(\n                    accumulator = superResDetailAccumulator,\n                    superResWidth = superResWidth,\n                    superResHeight = superResHeight,\n                    normalFrameCount = normalFrameCount,\n                )\n                PLog.i(\n                    SABRE_TAG,\n                    "IRIS_26561_SABRE_NATIVE_2X_DETAIL_READY normalFrames=$normalFrameCount " +\n                        "shadowLongExcluded=$shadowLongFrameCount size=${superResWidth}x$superResHeight " +\n                        "detailPath=${superResDetailPath != null} fullHighResRgb=false",\n                )\n            }\n\n            renderSabreDehomogenize(\n                accumulatedColor,\n''')
# Return fields.
replace_once(rel,
'''                normalStackedDngNoiseEquivalentSupport = normalStackedDngSupport.noiseEquivalent,\n            )\n''',
'''                normalStackedDngNoiseEquivalentSupport = normalStackedDngSupport.noiseEquivalent,\n                superResDetailPath = superResDetailPath,\n                superResLinearRawPath = null,\n                superResWidth = if (superResDetailPath != null) superResWidth else 0,\n                superResHeight = if (superResDetailPath != null) superResHeight else 0,\n            )\n''')
# Failure cleanup file.
replace_once(rel,
'''            if (!returned) {\n                LargeDirectBuffer.free(cpuOutput)\n                LargeDirectBuffer.free(normalStackedDngRaw16)\n''',
'''            if (!returned) {\n                runCatching { superResDetailPath?.let { File(it).delete() } }\n                LargeDirectBuffer.free(cpuOutput)\n                LargeDirectBuffer.free(normalStackedDngRaw16)\n''')
# Insert helper methods before clearSabreAccumulators.
anchor='''    private fun clearSabreAccumulators(\n'''
path=p(rel); s=path.read_text();
if s.count(anchor)!=1: raise SystemExit('stacker helper anchor')
helpers=r'''    private fun clearSabreSuperResAccumulator(
        accumulator: Int,
        superResWidth: Int,
        superResHeight: Int,
    ) {
        check(accumulator != 0)
        bindRenderTargets(intArrayOf(accumulator), "IRIS 26561 Sabre SR luma/support clear")
        GLES30.glViewport(0, 0, superResWidth, superResHeight)
        GLES30.glClearBufferfv(GLES30.GL_COLOR, 0, floatArrayOf(0f, 0f, 0f, 0f), 0)
        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
        checkGlError("IRIS 26561 Sabre SR luma/support clear")
    }

    private fun renderSabreSuperResDetailMerge(
        extracted: Int,
        flow: SabreConvertedAlignment,
        covariance: Int,
        weight: Int,
        calibration: FrameCalibration,
        accumulator: Int,
        extractedWidth: Int,
        extractedHeight: Int,
        superResWidth: Int,
        superResHeight: Int,
        useFrameWeight: Boolean,
    ) {
        check(enableSabreSuperRes && sabreSuperResDetailMergeProgram != 0 && accumulator != 0)
        val program = sabreSuperResDetailMergeProgram
        GLES30.glUseProgram(program)
        bindTexture(program, "uExtractedBayer", 0, extracted)
        bindTexture(program, "uFlow", 1, flow.texture)
        bindTexture(program, "uCovariance", 2, covariance)
        bindTexture(program, "uRejection", 3, weight)
        uniform2i(program, "uExtractedSize", extractedWidth, extractedHeight)
        uniform2i(program, "uOutputSize", superResWidth, superResHeight)
        uniformSabreFlowScaleOffset(program, flow)
        uniform4f(
            program,
            "uFrameBorderPadded",
            SABRE_SAMPLE_BORDER_PIXELS / width,
            SABRE_SAMPLE_BORDER_PIXELS / height,
            1f - SABRE_SAMPLE_BORDER_PIXELS / width,
            1f - SABRE_SAMPLE_BORDER_PIXELS / height,
        )
        uniform1i(program, "uCfaPattern", cfaPattern)
        uniform1i(program, "uUseFrameWeight", if (useFrameWeight) 1 else 0)
        uniform4fv(program, "uGains", calibration.gains)
        uniform4fv(program, "uBlackLevelsTimesGains", calibration.blackTerms)
        uniform4f(
            program,
            "uCovRangeRg",
            COV_MIN_R,
            COV_MAX_R - COV_MIN_R,
            COV_MIN_G,
            COV_MAX_G - COV_MIN_G,
        )
        uniform2f(program, "uCovRangeB", COV_MIN_B, COV_MAX_B - COV_MIN_B)
        GLES30.glEnable(GLES30.GL_BLEND)
        try {
            GLES30.glBlendEquation(GLES30.GL_FUNC_ADD)
            GLES30.glBlendFunc(GLES30.GL_ONE, GLES30.GL_ONE)
            draw(
                program,
                superResWidth,
                superResHeight,
                intArrayOf(accumulator),
                preserveBlend = true,
            )
        } finally {
            GLES30.glDisable(GLES30.GL_BLEND)
        }
    }

    private fun streamSabreSuperResDetail(
        accumulator: Int,
        superResWidth: Int,
        superResHeight: Int,
        normalFrameCount: Int,
    ): String {
        check(enableSabreSuperRes && sabreSuperResDetailResolveProgram != 0)
        require((superResWidth and 1) == 0 && (superResHeight and 1) == 0)
        val directory = requireNotNull(sabreSuperResTempDir)
        if (!directory.exists()) check(directory.mkdirs()) {
            "Unable to create 26561 Sabre Super Res temp directory: $directory"
        }
        val detailFile = File.createTempFile("iris26561-sabre-detail-", ".q8", directory)
        val maximumBandHeight = minOf(SABRE_SUPER_RES_DETAIL_BAND_HEIGHT, superResHeight)
        val bandTexture = createTexture(
            superResWidth,
            maximumBandHeight,
            GLES30.GL_R8,
            GLES30.GL_NEAREST,
        )
        try {
            BufferedOutputStream(FileOutputStream(detailFile), 1024 * 1024).use { output ->
                var bandTop = 0
                while (bandTop < superResHeight) {
                    val bandHeight = minOf(maximumBandHeight, superResHeight - bandTop)
                    GLES30.glUseProgram(sabreSuperResDetailResolveProgram)
                    bindTexture(sabreSuperResDetailResolveProgram, "uAccumulatedDetail", 0, accumulator)
                    uniform2i(
                        sabreSuperResDetailResolveProgram,
                        "uOutputSize",
                        superResWidth,
                        superResHeight,
                    )
                    uniform1i(sabreSuperResDetailResolveProgram, "uBandTop", bandTop)
                    uniform1f(
                        sabreSuperResDetailResolveProgram,
                        "uExpectedNormalFrames",
                        normalFrameCount.coerceAtLeast(1).toFloat(),
                    )
                    draw(
                        sabreSuperResDetailResolveProgram,
                        superResWidth,
                        bandHeight,
                        intArrayOf(bandTexture),
                    )
                    val bytes = readR8Mask(
                        texture = bandTexture,
                        label = "IRIS 26561 Sabre SR detail band $bandTop",
                        maskWidth = superResWidth,
                        maskHeight = bandHeight,
                    )
                    output.write(bytes)
                    bandTop += bandHeight
                    GlesGpuScheduler.yieldToUiRenderer()
                }
            }
            val expectedBytes = superResWidth.toLong() * superResHeight.toLong()
            check(detailFile.length() == expectedBytes) {
                "26561 Sabre SR detail bytes=${detailFile.length()} expected=$expectedBytes"
            }
            return detailFile.absolutePath
        } catch (error: Throwable) {
            runCatching { detailFile.delete() }
            throw error
        }
    }

'''
path.write_text(s.replace(anchor,helpers+anchor,1))
# Link SR programs conditionally.
replace_once(rel,
'''        sabreMergeProgram = linkProgram(GlesMgcRawSabreShaders.merge, "mgc_sabre_merge")\n        // IRIS_26558: keep Motion/NORMAL on the exact proven merge program. The Long program\n''',
'''        sabreMergeProgram = linkProgram(GlesMgcRawSabreShaders.merge, "mgc_sabre_merge")\n        if (enableSabreSuperRes) {\n            sabreSuperResDetailMergeProgram = linkProgram(\n                GlesMgcRawSabreShaders.superResDetailMerge26561,\n                "iris_26561_sabre_super_res_detail_merge",\n            )\n            sabreSuperResDetailResolveProgram = linkProgram(\n                GlesMgcRawSabreShaders.superResDetailResolve26561,\n                "iris_26561_sabre_super_res_detail_resolve",\n            )\n        }\n        // IRIS_26558: keep Motion/NORMAL on the exact proven merge program. The Long program\n''')
# Add constant near companion constants: insert before closing likely use unique existing constant.
# Search companion block tail for SABRE constants.
path=p(rel); s=path.read_text()
needle='''        const val SABRE_SAMPLE_BORDER_PIXELS = 1.5f\n'''
if s.count(needle)==1:
    s=s.replace(needle, needle+'''        private const val SABRE_SUPER_RES_DETAIL_BAND_HEIGHT = 256\n''',1)
else:
    # fallback before first SABRE_RESOLVE_INPUT...
    needle2='''        private const val SABRE_RESOLVE_INPUT_WHITE_LEVEL'''
    idx=s.find(needle2)
    if idx<0: raise SystemExit('cannot place SR constant')
    s=s[:idx]+'''        private const val SABRE_SUPER_RES_DETAIL_BAND_HEIGHT = 256\n'''+s[idx:]
path.write_text(s)

# 4) Add exact runtime GLSL for Sabre 2x luma/support accumulation + streamed detail resolve.
rel='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
path=p(rel); s=path.read_text()
anchor='''    /**\n     * IRIS_26545_SABRE_SPARSE_FLOW_CONTRACT\n'''
if s.count(anchor)!=1: raise SystemExit('Sabre shader insertion anchor')
sr_shader=r'''    /* IRIS_26561_SABRE_NATIVE_2X_DETAIL
     * Iris Super Res extension after the current-MGC Sabre alignment/rejection contract.
     * The 1x Sabre merge/Resolve/VGN sources above remain unchanged. This shader reuses the
     * same sparse flow, covariance RBF and rejection decision at a 2x sample grid, but stores
     * only weighted luma + accepted-frame support. It is therefore not a second color owner.
     */
    val superResDetailMerge26561 = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uExtractedBayer;
        uniform sampler2D uFlow;
        uniform sampler2D uCovariance;
        uniform sampler2D uRejection;
        uniform vec4 uFlowScaleOffset;
        uniform ivec2 uExtractedSize;
        uniform ivec2 uOutputSize;
        uniform vec4 uFrameBorderPadded;
        uniform int uCfaPattern;
        uniform int uUseFrameWeight;
        uniform vec4 uGains;
        uniform vec4 uBlackLevelsTimesGains;
        uniform vec4 uCovRangeRg;
        uniform vec2 uCovRangeB;
        layout(location = 0) out vec2 oLumaAndSupport;

        vec2 mirrorUvs(vec2 sampleUv) {
            if (sampleUv.x <= uFrameBorderPadded.x)
                sampleUv.x = 2.0 * uFrameBorderPadded.x - sampleUv.x;
            if (sampleUv.y <= uFrameBorderPadded.y)
                sampleUv.y = 2.0 * uFrameBorderPadded.y - sampleUv.y;
            if (sampleUv.x > uFrameBorderPadded.z)
                sampleUv.x = 2.0 * uFrameBorderPadded.z - sampleUv.x;
            if (sampleUv.y > uFrameBorderPadded.w)
                sampleUv.y = 2.0 * uFrameBorderPadded.w - sampleUv.y;
            return sampleUv;
        }

        float kernelWeight(vec2 pixelOffset, vec3 covariance) {
            float kernelDistance =
                pixelOffset.x * pixelOffset.x * covariance.x +
                pixelOffset.y * pixelOffset.y * covariance.y +
                pixelOffset.x * pixelOffset.y * covariance.z * 2.0;
            return exp2(-0.5 * kernelDistance) + 0.00005;
        }

        vec3 unpackCovariance(vec3 packed) {
            return vec3(
                packed.x * uCovRangeRg.y + uCovRangeRg.x,
                packed.y * uCovRangeRg.w + uCovRangeRg.z,
                packed.z * uCovRangeB.y + uCovRangeB.x
            );
        }

        mat3 get3x3FromExtractedBayer(ivec2 bayerPosition) {
            mat3 values = mat3(0.0);
            int type = (bayerPosition.y % 2) * 2 + (bayerPosition.x % 2);
            vec2 texturePosition = vec2(bayerPosition / 2);
            if (type == 0) texturePosition += vec2(-1.0, -1.0);
            else if (type == 1) texturePosition += vec2(0.0, -1.0);
            else if (type == 2) texturePosition += vec2(-1.0, 0.0);
            texturePosition += vec2(0.5);
            vec2 reciprocalSize = 1.0 / vec2(uExtractedSize);
            vec4 bayer0 = texture(uExtractedBayer, texturePosition * reciprocalSize);
            vec4 bayer1 = texture(uExtractedBayer, (texturePosition + vec2(1.0, 0.0)) * reciprocalSize);
            vec4 bayer2 = texture(uExtractedBayer, (texturePosition + vec2(0.0, 1.0)) * reciprocalSize);
            vec4 bayer3 = texture(uExtractedBayer, (texturePosition + vec2(1.0, 1.0)) * reciprocalSize);
            if (type == 0) {
                values[0][0] = bayer0.w; values[1][0] = bayer1.z; values[2][0] = bayer1.w;
                values[0][1] = bayer2.y; values[1][1] = bayer3.x; values[2][1] = bayer3.y;
                values[0][2] = bayer2.w; values[1][2] = bayer3.z; values[2][2] = bayer3.w;
            } else if (type == 1) {
                values[0][0] = bayer0.z; values[1][0] = bayer0.w; values[2][0] = bayer1.z;
                values[0][1] = bayer2.x; values[1][1] = bayer2.y; values[2][1] = bayer3.x;
                values[0][2] = bayer2.z; values[1][2] = bayer2.w; values[2][2] = bayer3.z;
            } else if (type == 2) {
                values[0][0] = bayer0.y; values[1][0] = bayer1.x; values[2][0] = bayer1.y;
                values[0][1] = bayer0.w; values[1][1] = bayer1.z; values[2][1] = bayer1.w;
                values[0][2] = bayer2.y; values[1][2] = bayer3.x; values[2][2] = bayer3.y;
            } else {
                values[0][0] = bayer0.x; values[1][0] = bayer0.y; values[2][0] = bayer1.x;
                values[0][1] = bayer0.z; values[1][1] = bayer0.w; values[2][1] = bayer1.z;
                values[0][2] = bayer2.x; values[1][2] = bayer2.y; values[2][2] = bayer3.x;
            }
            return values;
        }

        vec4 swizzleForType(vec4 value, int type) {
            if (type == 0) return value.rgba;
            if (type == 1) return value.grab;
            if (type == 2) return value.barg;
            return value.abgr;
        }

        void sampleNeighborhoodRbf(
            vec2 sampleUv,
            vec3 covariance,
            out vec3 accumulatedIntensities,
            out vec3 accumulatedWeights
        ) {
            accumulatedIntensities = vec3(0.0);
            accumulatedWeights = vec3(0.0);
            vec2 coordinateScaled = sampleUv * (vec2(uExtractedSize) * 2.0);
            ivec2 position = ivec2(coordinateScaled);
            mat3 bayerValue = get3x3FromExtractedBayer(position);
            mat3 weights = mat3(0.0);
            vec2 subpixelOffset = floor(coordinateScaled) + 0.5 - coordinateScaled;
            for (int i = -1; i <= 1; ++i) {
                for (int j = -1; j <= 1; ++j) {
                    weights[i + 1][j + 1] = kernelWeight(subpixelOffset + vec2(ivec2(i, j)), covariance);
                }
            }
            ivec2 bayerOffset = ivec2(0);
            if (uCfaPattern == 0) bayerOffset = ivec2(1, 1);
            else if (uCfaPattern == 1) bayerOffset = ivec2(0, 1);
            else if (uCfaPattern == 2) bayerOffset = ivec2(1, 0);
            int type = (((position.y + bayerOffset.y) & 1) << 1) + ((position.x + bayerOffset.x) & 1);
            vec4 cornerWeights = vec4(weights[0][0], weights[0][2], weights[2][0], weights[2][2]);
            vec2 upDownWeights = vec2(weights[1][0], weights[1][2]);
            vec2 leftRightWeights = vec2(weights[0][1], weights[2][1]);
            vec4 value1 = vec4(bayerValue[0][0], bayerValue[0][2], bayerValue[2][0], bayerValue[2][2]);
            vec2 value2 = vec2(bayerValue[1][0], bayerValue[1][2]);
            vec2 value3 = vec2(bayerValue[0][1], bayerValue[2][1]);
            vec4 reorderedGains = swizzleForType(uGains, type);
            vec4 reorderedBlack = swizzleForType(uBlackLevelsTimesGains, type);
            vec4 intensities = vec4(
                dot(value1 * reorderedGains.r + reorderedBlack.r, cornerWeights),
                dot(value2 * reorderedGains.g + reorderedBlack.g, upDownWeights),
                dot(value3 * reorderedGains.b + reorderedBlack.b, leftRightWeights),
                (bayerValue[1][1] * reorderedGains.a + reorderedBlack.a) * weights[1][1]
            );
            vec4 reorderedWeights = vec4(
                dot(cornerWeights, vec4(1.0)),
                dot(upDownWeights, vec2(1.0)),
                dot(leftRightWeights, vec2(1.0)),
                weights[1][1]
            );
            intensities = swizzleForType(intensities, type);
            reorderedWeights = swizzleForType(reorderedWeights, type);
            accumulatedIntensities = vec3(intensities.r, intensities.g + intensities.b, intensities.a);
            accumulatedWeights = vec3(reorderedWeights.r, reorderedWeights.g + reorderedWeights.b, reorderedWeights.a);
        }

        void main() {
            vec2 referenceUv = gl_FragCoord.xy / vec2(uOutputSize);
            vec2 flowUv = referenceUv * uFlowScaleOffset.xy + uFlowScaleOffset.zw;
            vec2 flow = texture(uFlow, flowUv).xy;
            vec2 sampleUv = mirrorUvs(referenceUv + flow);
            vec3 covariance = unpackCovariance(texture(uCovariance, sampleUv).xyz);
            vec3 accumulatedColor = vec3(0.0);
            vec3 accumulatedWeight = vec3(0.0);
            sampleNeighborhoodRbf(sampleUv, covariance, accumulatedColor, accumulatedWeight);
            vec3 frameRgb = accumulatedColor / max(accumulatedWeight, vec3(1.0e-6));
            float frameLuma = dot(frameRgb, vec3(0.25, 0.50, 0.25));
            float frameWeight = uUseFrameWeight != 0 ? texture(uRejection, referenceUv).r : 1.0;
            oLumaAndSupport = vec2(frameLuma * frameWeight, frameWeight);
        }
    """.trimIndent()

    /* Convert the 2x luma/support carrier to the existing 26532 Q8 signed-log-detail contract.
     * A reference-only pixel has support 1 and intentionally resolves to neutral detail. Multiple
     * accepted NORMAL observations progressively unlock real subpixel detail. Deep-black signal is
     * also neutral, preventing SR from magnifying unsupported shadow noise.
     */
    val superResDetailResolve26561 = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uAccumulatedDetail;
        uniform ivec2 uOutputSize;
        uniform int uBandTop;
        uniform float uExpectedNormalFrames;
        layout(location = 0) out float oDetailCode;

        vec2 lumaAndSupportAt(ivec2 p) {
            return texelFetch(uAccumulatedDetail, clamp(p, ivec2(0), uOutputSize - ivec2(1)), 0).rg;
        }

        float resolvedLuma(vec2 packedValue) {
            return packedValue.x / max(packedValue.y, 1.0e-6);
        }

        void main() {
            ivec2 p = ivec2(gl_FragCoord.xy) + ivec2(0, uBandTop);
            ivec2 blockOrigin = (p / 2) * 2;
            vec2 packed0 = lumaAndSupportAt(blockOrigin);
            vec2 packed1 = lumaAndSupportAt(blockOrigin + ivec2(1, 0));
            vec2 packed2 = lumaAndSupportAt(blockOrigin + ivec2(0, 1));
            vec2 packed3 = lumaAndSupportAt(blockOrigin + ivec2(1, 1));
            float luma0 = resolvedLuma(packed0);
            float luma1 = resolvedLuma(packed1);
            float luma2 = resolvedLuma(packed2);
            float luma3 = resolvedLuma(packed3);
            float blockMean = max((luma0 + luma1 + luma2 + luma3) * 0.25, 1.0e-6);
            float currentLuma = resolvedLuma(lumaAndSupportAt(p));
            float minimumSupport = min(min(packed0.y, packed1.y), min(packed2.y, packed3.y));
            float supportEnd = min(max(uExpectedNormalFrames, 2.0), 3.0);
            float supportGate = smoothstep(1.0, supportEnd, minimumSupport);
            float signalGate = smoothstep(0.002, 0.020, blockMean);
            float logDetail = clamp(log2(max(currentLuma, 1.0e-6) / blockMean), -0.75, 0.75);
            float trustedLogDetail = logDetail * supportGate * signalGate;
            oDetailCode = clamp((trustedLogDetail / 0.75) * 0.5 + 0.5, 0.0, 1.0);
        }
    """.trimIndent()

'''
path.write_text(s.replace(anchor,sr_shader+anchor,1))

# 5) Shared post-VGN universal adaptive-color stage (separate from current-MGC VGN parity math).
rel='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
replace_once(rel,
'''    private var finalProgram = 0\n''',
'''    private var finalProgram = 0\n    private var universalAdaptiveColorProgram = 0\n''')
replace_once(rel,
'''        finalProgram = host.linkComputeProgram(Iris26529SpatialRgbChromaShaders.finalCameraRgb, "iris26529_chroma_final")\n''',
'''        finalProgram = host.linkComputeProgram(Iris26529SpatialRgbChromaShaders.finalCameraRgb, "iris26529_chroma_final")\n        universalAdaptiveColorProgram = host.linkComputeProgram(\n            Iris26529SpatialRgbChromaShaders.universalAdaptiveColor26561,\n            "iris26561_universal_adaptive_color",\n        )\n''')
replace_once(rel,
'''        dispatchFinal(filteredYccd, originalYccd)\n        val finalMs = (System.nanoTime() - finalStart) / 1_000_000L\n''',
'''        dispatchFinal(filteredYccd, originalYccd)\n        /* IRIS_26561_UNIVERSAL_ADAPTIVE_COLOR\n         * Current-MGC VGN completes first, unchanged. One shared Iris post-VGN pass then removes\n         * only locally unsupported shadow chroma while protecting coherent color and luminance\n         * edges. Motion and Night therefore use the same color decision layer.\n         */\n        dispatchUniversalAdaptiveColor(assembledRgb, workA)\n        val completedVgn = assembledRgb\n        assembledRgb = workA\n        workA = completedVgn\n        val finalMs = (System.nanoTime() - finalStart) / 1_000_000L\n''')
# Add host dispatch method before runIirError anchor.
path=p(rel); s=path.read_text(); anchor='''    private fun runIirError('''
if s.count(anchor)!=1: raise SystemExit('adaptive dispatch anchor')
method=r'''    private fun dispatchUniversalAdaptiveColor(source: Int, destination: Int) {
        check(universalAdaptiveColorProgram != 0)
        GLES31.glUseProgram(universalAdaptiveColorProgram)
        setImageSize(universalAdaptiveColorProgram)
        bindImage(0, source, GLES31.GL_READ_ONLY)
        bindImage(1, destination, GLES31.GL_WRITE_ONLY)
        trackedDispatch(
            "IRIS 26561 universal adaptive color",
            intArrayOf(source),
            intArrayOf(destination),
        )
        clearImages()
    }

'''
path.write_text(s.replace(anchor,method+anchor,1))
# Add shader inside object before known seed shader. Locate object and seed.
path=p(rel); s=path.read_text(); anchor='''    val seed = """'''
if s.count(anchor)!=1: raise SystemExit('postprocessor shader anchor')
adaptive=r'''    /* IRIS_26561_UNIVERSAL_ADAPTIVE_COLOR
     * Runs only after current-MGC VGN has produced completed camera RGB. It is intentionally
     * hue-agnostic and never boosts saturation: coherent color and luminance edges pass through;
     * only unsupported local shadow chroma is pulled toward the local chroma consensus.
     */
    val universalAdaptiveColor26561 = """
        #version 310 es
        layout(local_size_x = 8, local_size_y = 8, local_size_z = 1) in;
        precision highp float;
        precision highp int;
        layout(rgba16ui, binding = 0) readonly uniform highp uimage2D uSource;
        layout(rgba16ui, binding = 1) writeonly uniform highp uimage2D uDestination;
        uniform ivec2 uImageSize;

        vec3 loadRgb(ivec2 p) {
            uvec4 packedValue = imageLoad(uSource, clamp(p, ivec2(0), uImageSize - ivec2(1)));
            return vec3(packedValue.rgb) / 65535.0;
        }

        float luminanceOf(vec3 rgb) {
            return dot(rgb, vec3(0.25, 0.50, 0.25));
        }

        void main() {
            ivec2 p = ivec2(gl_GlobalInvocationID.xy);
            if (any(greaterThanEqual(p, uImageSize))) return;
            vec3 center = loadRgb(p);
            float centerLuma = luminanceOf(center);
            vec3 localRgb = vec3(0.0);
            float maximumLumaDelta = 0.0;
            for (int y = -1; y <= 1; ++y) {
                for (int x = -1; x <= 1; ++x) {
                    vec3 neighborRgb = loadRgb(p + ivec2(x, y));
                    localRgb += neighborRgb;
                    maximumLumaDelta = max(
                        maximumLumaDelta,
                        abs(luminanceOf(neighborRgb) - centerLuma)
                    );
                }
            }
            localRgb /= 9.0;
            float localLuma = luminanceOf(localRgb);
            vec3 centerChroma = center - vec3(centerLuma);
            vec3 localChroma = localRgb - vec3(localLuma);
            float chromaDisagreement = length(centerChroma - localChroma);
            float localChromaMagnitude = length(localChroma);
            float unsupportedColor = smoothstep(0.010, 0.055, chromaDisagreement) *
                (1.0 - smoothstep(0.020, 0.120, localChromaMagnitude));
            float shadowNeed = 1.0 - smoothstep(0.040, 0.220, centerLuma);
            float edgeProtection = smoothstep(0.018, 0.090, maximumLumaDelta);
            float correction = 0.65 * unsupportedColor * shadowNeed * (1.0 - edgeProtection);
            vec3 correctedChroma = mix(centerChroma, localChroma, correction);
            vec3 correctedRgb = clamp(vec3(centerLuma) + correctedChroma, 0.0, 1.0);
            uvec3 encodedRgb = uvec3(round(correctedRgb * 65535.0));
            imageStore(uDestination, p, uvec4(encodedRgb, 65535u));
        }
    """.trimIndent()

'''
path.write_text(s.replace(anchor,adaptive+anchor,1))

# 6) Bridge enables Sabre SR and wires result; DNG stays native 1:1.
rel='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'
replace_once(rel,
'''            /* IRIS_26560_SABRE_NATIVE_GRID_SR_PLACEHOLDER\n             * Keep the existing public Super Res switch/state, but do not reuse Spatial-RGB 2x\n             * evidence. This cleanup build preserves exact proven Sabre native-grid geometry.\n             */\n''',
'''            /* IRIS_26561_SABRE_NATIVE_2X_SR_AUTHORITY\n             * Sabre remains native-grid for structural RGB/Resolve/VGN. When the existing Super\n             * Res switch is on, the same Sabre flow/covariance/rejection decisions also feed a\n             * compact 2x luma-detail carrier. No deleted Spatial/Wronski reconstruction owner is\n             * restored and DNG remains the proven 1x NORMAL Sabre sidecar.\n             */\n''')
replace_once(rel,
'''            parameters.motionV2SuperResOutputScale = 1f\n            PLog.i(TAG, "IRIS_26560_SABRE_NATIVE_GRID_SR_PLACEHOLDER " +\n                "displayedGlobalZoom=$displayedGlobalZoom localOutputZoom=$localOutputZoom " +\n                "reconstructionZoom=$reconstructionZoom renderResidualZoom=$renderResidualZoom " +\n                "superResRequested=${parameters.motionV2SuperResOutputEnabled} outputScale=1.0 " +\n                "futureBackend=SABRE_SR")\n''',
'''            val sabreSuperResEnabled = parameters.motionV2SuperResOutputEnabled\n            val sabreSuperResOutputScale = if (sabreSuperResEnabled) 2f else 1f\n            parameters.motionV2SuperResOutputScale = sabreSuperResOutputScale\n            PLog.i(TAG, "IRIS_26561_SABRE_NATIVE_2X_SR_AUTHORITY " +\n                "displayedGlobalZoom=$displayedGlobalZoom localOutputZoom=$localOutputZoom " +\n                "reconstructionZoom=$reconstructionZoom renderResidualZoom=$renderResidualZoom " +\n                "superResRequested=$sabreSuperResEnabled outputScale=$sabreSuperResOutputScale " +\n                "baseRgbScale=1.0 detailScale=${if (sabreSuperResEnabled) 2.0 else 1.0} " +\n                "colorOwner=NATIVE_SABRE_VGN dngScale=1.0")\n''')
replace_once(rel,
'''                exportNormalStackedDng = produceNormalStackedDng,\n                vgnChromaCorrectionStrength = vgnChromaCorrectionStrength,\n''',
'''                exportNormalStackedDng = produceNormalStackedDng,\n                vgnChromaCorrectionStrength = vgnChromaCorrectionStrength,\n                enableSabreSuperRes = sabreSuperResEnabled,\n                sabreSuperResTempDir = PhotonCamera.getApplicationContextStatic().cacheDir,\n''')
replace_once(rel,
'''            requireParity(stacked.superResDetailPath == null && stacked.superResLinearRawPath == null &&\n                    stacked.superResWidth == 0 && stacked.superResHeight == 0,\n                "26560 Sabre cleanup unexpectedly produced legacy Spatial-RGB SR evidence")\n''',
'''            val expectedSuperResWidth = if (sabreSuperResEnabled) size.x * 2 else 0\n            val expectedSuperResHeight = if (sabreSuperResEnabled) size.y * 2 else 0\n            if (sabreSuperResEnabled) {\n                requireParity(\n                    stacked.superResDetailPath != null &&\n                        stacked.superResWidth == expectedSuperResWidth &&\n                        stacked.superResHeight == expectedSuperResHeight,\n                    "26561 Sabre SR evidence ${stacked.superResWidth}x${stacked.superResHeight} " +\n                        "path=${stacked.superResDetailPath != null} expected=${expectedSuperResWidth}x$expectedSuperResHeight",\n                )\n                requireParity(stacked.superResLinearRawPath == null,\n                    "26561 Sabre SR must preserve native 1x normalized16 DNG ownership")\n            } else {\n                requireParity(stacked.superResDetailPath == null && stacked.superResLinearRawPath == null &&\n                        stacked.superResWidth == 0 && stacked.superResHeight == 0,\n                    "26561 Sabre SR disabled but evidence was produced")\n            }\n''')
replace_once(rel,
'''                "superResRequested=${parameters.motionV2SuperResOutputEnabled}")\n            PLog.i(TAG, "IRIS_26545_RECONSTRUCTION_TIMING " +\n                "method=SABRE srEnabled=false fusionMs=$iris26535FusionMs " +\n''',
'''                "superResRequested=${parameters.motionV2SuperResOutputEnabled} " +\n                "superResDetail=${stacked.superResDetailPath != null} " +\n                "adaptiveColor=POST_VGN_SHARED")\n            PLog.i(TAG, "IRIS_26545_RECONSTRUCTION_TIMING " +\n                "method=SABRE srEnabled=$sabreSuperResEnabled fusionMs=$iris26535FusionMs " +\n''')
replace_once(rel,
'''                null,\n                0,\n                0,\n                null,\n                0,\n                0,\n''',
'''                stacked.superResDetailPath,\n                stacked.superResWidth,\n                stacked.superResHeight,\n                null,\n                0,\n                0,\n''')

replace_once(rel,
'''            requireParity(parameters.motionV2ReconstructionZoom == 1f &&
                    parameters.motionV2SuperResOutputScale == 1f,
                "Sabre native-grid contract changed during Spatial-RGB cleanup")
''',
'''            requireParity(parameters.motionV2ReconstructionZoom == 1f &&
                    parameters.motionV2SuperResOutputScale == sabreSuperResOutputScale,
                "26561 Sabre base-grid/SR output-scale contract drifted")
''')
replace_once(rel,
'''            /* IRIS_26560_SPATIAL_SR_BACKEND_REMOVED
             * The Super Res request is intentionally preserved in Parameters, but no Spatial-RGB
             * 2x detail/LinearRaw evidence is created or consumed in this cleanup build.
             */
''',
'''            /* IRIS_26561_SABRE_SR_DETAIL_ONLY_BACKEND
             * Full-resolution residual denoise remains native 1x Sabre RGB. The optional 2x
             * detail sidecar is already frozen from Sabre NORMAL-frame evidence and is consumed
             * only by the streamed Super Res JPEG encoder after this native color path completes.
             */
''')

replace_once(rel,
'''import com.particlesdevs.photoncamera.processing.render.Parameters
import java.nio.ByteBuffer
''',
'''import com.particlesdevs.photoncamera.processing.render.Parameters
import java.io.File
import java.nio.ByteBuffer
''')
replace_once(rel,
'''        var halfBuffer: ByteBuffer? = null
        var resultTexture = 0
        val iris26535TotalStartNs = System.nanoTime()
''',
'''        var halfBuffer: ByteBuffer? = null
        var resultTexture = 0
        var superResDetailPathForCleanup: String? = null
        var superResOutputsHandedOff = false
        val iris26535TotalStartNs = System.nanoTime()
''')
replace_once(rel,
'''            val stacked = fusion.processFrames(frames)
                ?: invalid("Iris Sabre owner returned null")
''',
'''            val stacked = fusion.processFrames(frames)
                ?: invalid("Iris Sabre owner returned null")
            superResDetailPathForCleanup = stacked.superResDetailPath
''')
replace_once(rel,
'''            ).also { result ->
                result.sabreSelected = true
            }
''',
'''            ).also { result ->
                result.sabreSelected = true
                superResOutputsHandedOff = true
            }
''')
replace_once(rel,
'''            LargeDirectBuffer.free(halfBuffer)
            egl?.close()
''',
'''            LargeDirectBuffer.free(halfBuffer)
            if (!superResOutputsHandedOff) {
                superResDetailPathForCleanup?.let { path -> runCatching { File(path).delete() } }
            }
            egl?.close()
''')

# 7) Dedicated Super Res icons, not Quad Bayer icons.
rel='app/src/main/java/com/particlesdevs/photoncamera/ui/camera/viewmodel/SettingsBarEntryProvider.java'
replace_once(rel,
'''    private void createSuperResEntry() {\n        // Reuse the existing themed two-state icon pair so the row matches the gear popup.\n        superResEntry.addSettingsBarButtonModels(\n                SettingsBarButtonModel.newButtonModel(R.id.super_res_off_button, R.drawable.ic_quad_off, R.string.off, 0, superResEntry),\n                SettingsBarButtonModel.newButtonModel(R.id.super_res_on_button, R.drawable.ic_quad_on, R.string.on, 1, superResEntry)\n        );\n    }\n''',
'''    private void createSuperResEntry() {\n        /* IRIS_26561_DEDICATED_SUPER_RES_ICONS: keep setting ownership unchanged while making\n         * Super Res visually distinct from the Quad Bayer setting. */\n        superResEntry.addSettingsBarButtonModels(\n                SettingsBarButtonModel.newButtonModel(R.id.super_res_off_button, R.drawable.ic_super_res_off, R.string.off, 0, superResEntry),\n                SettingsBarButtonModel.newButtonModel(R.id.super_res_on_button, R.drawable.ic_super_res_on, R.string.on, 1, superResEntry)\n        );\n    }\n''')

# Dedicated vector icons: same 52x52/white style as adjacent settings icons.
p('app/src/main/res/drawable/ic_super_res_off.xml').write_text('''<?xml version="1.0" encoding="utf-8"?>\n<vector xmlns:android="http://schemas.android.com/apk/res/android"\n    android:width="24dp" android:height="24dp"\n    android:viewportWidth="52" android:viewportHeight="52">\n    <path android:fillColor="#00000000" android:strokeColor="#FFFFFFFF" android:strokeWidth="4"\n        android:strokeLineCap="round" android:strokeLineJoin="round"\n        android:pathData="M17,5 L7,5 Q5,5 5,7 L5,17 M35,5 L45,5 Q47,5 47,7 L47,17 M5,35 L5,45 Q5,47 7,47 L17,47 M47,35 L47,45 Q47,47 45,47 L35,47"/>\n    <path android:fillColor="#00000000" android:strokeColor="#FFFFFFFF" android:strokeWidth="3.5"\n        android:strokeLineCap="round" android:strokeLineJoin="round"\n        android:pathData="M18,26 L34,26 M26,18 L26,34"/>\n</vector>\n''')
p('app/src/main/res/drawable/ic_super_res_on.xml').write_text('''<?xml version="1.0" encoding="utf-8"?>\n<vector xmlns:android="http://schemas.android.com/apk/res/android"\n    android:width="24dp" android:height="24dp"\n    android:viewportWidth="52" android:viewportHeight="52">\n    <path android:fillColor="#FFFFFFFF"\n        android:pathData="M17,3 L7,3 Q3,3 3,7 L3,17 L7,17 L7,7 L17,7 Z M35,3 L45,3 Q49,3 49,7 L49,17 L45,17 L45,7 L35,7 Z M3,35 L7,35 L7,45 L17,45 L17,49 L7,49 Q3,49 3,45 Z M45,35 L49,35 L49,45 Q49,49 45,49 L35,49 L35,45 L45,45 Z"/>\n    <path android:fillColor="#FFFFFFFF"\n        android:pathData="M24,15 L28,15 L28,24 L37,24 L37,28 L28,28 L28,37 L24,37 L24,28 L15,28 L15,24 L24,24 Z"/>\n</vector>\n''')

# 8) version 26561.
rel='app/version.properties'
replace_once(rel,'VERSION_NAME=0.9726560\nVERSION_BUILD=26560\n','VERSION_NAME=0.9726561\nVERSION_BUILD=26561\n')

print('26561 candidate transform applied')
