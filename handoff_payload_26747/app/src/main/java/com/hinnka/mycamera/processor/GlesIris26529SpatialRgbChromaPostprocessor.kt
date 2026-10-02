package com.hinnka.mycamera.processor

import android.opengl.GLES30
import android.opengl.GLES31
import com.hinnka.mycamera.utils.DirectBufferPixelPacker
import com.hinnka.mycamera.utils.LargeDirectBuffer
import java.nio.ByteBuffer
import kotlin.math.acos
import kotlin.math.cos
import kotlin.math.max
import kotlin.math.sin

/**
 * IRIS_26529_SPATIAL_RGB_CHROMA_REWRITE_OWNER
 *
 * Iris-owned current-MGC VGN/color-noise/IIR stage shared by Spatial and Sabre. bjzhou c317/MGC is used only as
 * a pinned semantic reference for equations, coefficients, coordinate domains, and stage ordering.
 * This owner is intentionally integrated around Iris' existing Spatial-RGB accumulator, texture
 * lifecycle, diagnostics, Motion ownership, and GPU export path rather than vendoring bjzhou code.
 *
 * Input is one full contiguous RGBA16UI camera-RGB image. RGB contains normalized camera color.
 * Direction selection is rebuilt from RGB gradients exactly at the VGN boundary; the packed fused
 * green direction carried by Spatial remains a merge diagnostic and is not a VGN seed authority.
 * All directional and recursive filtering runs in global image coordinates so processing bands can
 * never become visible tile boundaries.
 */
internal class GlesIris26529SpatialRgbChromaPostprocessor(
    private val imageWidth: Int,
    private val imageHeight: Int,
    calculationWbGains: FloatArray,
    outputScale: Float,
    chromaCorrectionStrength: Float = 1f,
    private val host: Host,
    private val exportFullSizeTexture: Boolean = false,
) {
    interface Host {
        fun linkComputeProgram(source: String, name: String): Int
        fun createRgba16UiTexture(width: Int, height: Int, label: String): Int
        fun releaseTexture(texture: Int, label: String)
        fun transferTextureOwnership(texture: Int, label: String)
        fun uniformLocation(program: Int, name: String): Int
        fun checkGlError(label: String)
        fun yieldToUiRenderer()
    }

    data class Result(
        val exportedTextureId: Int,
        val chromaSubmissionMs: Long,
        val finalSubmissionMs: Long,
        val cpuBufferPopulated: Boolean,
    )

    private val calculationRgbGains = floatArrayOf(
        calculationWbGains.getOrElse(0) { 1f },
        1f,
        calculationWbGains.getOrElse(3) { 1f },
    ).also { gains ->
        require(gains.all { it.isFinite() && it > 0f })
    }
    private val chromaCorrectionStrength = chromaCorrectionStrength.coerceIn(0f, 1f)
    private val coefficients = Iris26529SpatialRgbIirCoefficients.forOutputScale(
        outputScale.takeIf { it.isFinite() && it > 0f } ?: 1f,
    )
    private val passWindow = GlesGpuScheduler.PassWindow("IrisCurrentMgcVgn", 2)

    private var seedProgram = 0
    private var localClampProgram = 0
    private var localMedianProgram = 0
    private var directionalProgram = 0
    private var restoreDirectionProgram = 0
    private var iirRgbProgram = 0
    private var errorProgram = 0
    private var iirErrorProgram = 0
    private var blendProgram = 0
    private var finalProgram = 0
    private var universalAdaptiveColorProgram = 0

    private var assembledRgb = 0
    private var workA = 0
    private var workB = 0
    private var writtenBands = 0
    private var bands: List<MgcSpatialRgbTile> = emptyList()
    private var readbackFbo = 0
    private val owned = LinkedHashSet<Int>()

    init {
        require(imageWidth > 0 && imageHeight > 0)
    }

    fun initPrograms() {
        if (seedProgram != 0) return
        seedProgram = host.linkComputeProgram(Iris26529SpatialRgbChromaShaders.seed, "iris26529_chroma_seed")
        localClampProgram = host.linkComputeProgram(Iris26529SpatialRgbChromaShaders.localClamp, "iris26529_chroma_local_clamp")
        localMedianProgram = host.linkComputeProgram(Iris26529SpatialRgbChromaShaders.localMedian, "iris26529_chroma_local_median")
        directionalProgram = host.linkComputeProgram(Iris26529SpatialRgbChromaShaders.directionalSmooth, "iris26529_chroma_directional")
        restoreDirectionProgram = host.linkComputeProgram(Iris26529SpatialRgbChromaShaders.restoreDirection, "iris26529_chroma_restore_direction")
        iirRgbProgram = host.linkComputeProgram(Iris26529SpatialRgbChromaShaders.iirRgb, "iris26529_chroma_iir_rgb")
        errorProgram = host.linkComputeProgram(Iris26529SpatialRgbChromaShaders.calculateError, "iris26529_chroma_error")
        iirErrorProgram = host.linkComputeProgram(Iris26529SpatialRgbChromaShaders.iirError, "iris26529_chroma_iir_error")
        blendProgram = host.linkComputeProgram(Iris26529SpatialRgbChromaShaders.blendChroma, "iris26529_chroma_blend")
        finalProgram = host.linkComputeProgram(Iris26529SpatialRgbChromaShaders.finalCameraRgb, "iris26529_chroma_final")
        universalAdaptiveColorProgram = host.linkComputeProgram(
            Iris26529SpatialRgbChromaShaders.universalAdaptiveColor26561,
            "iris26561_universal_adaptive_color",
        )
    }

    fun beginFullFrame(newBands: List<MgcSpatialRgbTile>) {
        check(seedProgram != 0) { "Iris 26529 chroma programs are not initialized" }
        check(assembledRgb == 0) { "Iris 26529 chroma storage already active" }
        require(newBands.isNotEmpty())
        validateCoverage(newBands)
        val maxTexture = IntArray(1)
        GLES30.glGetIntegerv(GLES30.GL_MAX_TEXTURE_SIZE, maxTexture, 0)
        require(imageWidth <= maxTexture[0] && imageHeight <= maxTexture[0]) {
            "Iris 26529 contiguous chroma surface ${imageWidth}x$imageHeight exceeds GL_MAX_TEXTURE_SIZE=${maxTexture[0]}"
        }
        bands = newBands.toList()
        writtenBands = 0
        assembledRgb = allocate("assembled RGB")
    }

    fun normalizationTargetTexture(): Int {
        check(assembledRgb != 0)
        return assembledRgb
    }

    fun markBandWritten(tile: MgcSpatialRgbTile) {
        check(writtenBands < bands.size)
        check(bands[writtenBands].index == tile.index) {
            "Iris 26529 Spatial RGB bands must be written row-major"
        }
        writtenBands += 1
    }

    fun process(
        obtainCpuOutput: () -> ByteBuffer,
        deferCpuReadback: Boolean,
        onFinalSubmitted: (() -> Unit)? = null,
        sabreSupportR: Int = 0,
        sabreSupportGb: Int = 0,
        sabreValidWeights: Int = 0,
        sabreValidityWeightScale: Float = 1f,
        preVgnPhysicalRgb: Int = 0,
    ): Result {
        check(assembledRgb != 0)
        check(writtenBands == bands.size) {
            "Iris 26529 chroma input incomplete: $writtenBands/${bands.size} bands"
        }
        workA = allocate("YCCD A")
        workB = allocate("YCCD B")
        val sabreSupportValid = sabreSupportR != 0 && sabreSupportGb != 0 && sabreValidWeights != 0
        check((sabreSupportR == 0) == (sabreSupportGb == 0) &&
            (sabreSupportR == 0) == (sabreValidWeights == 0)) {
            "Sabre validity provenance must be provided as total R + total GB + valid RGB"
        }
        val chromaStart = System.nanoTime()

        // Keep the c317/MGC stage domains but use Iris-owned storage rotation:
        // workA = seed YCCD, workB = local-clamped YCCD, assembledRgb = median YCCD,
        // then workA = directional YCCD and assembledRgb = restored-direction YCCD.
        dispatchSeed(
            assembledRgb, workA, sabreSupportR, sabreSupportGb, sabreValidWeights,
            sabreValidityWeightScale, sabreSupportValid,
        )
        dispatchLocal(localClampProgram, workA, workB, "local clamp")
        dispatchLocalMedian(
            workB, assembledRgb, chromaCorrectionStrength, sabreSupportR, sabreSupportGb,
            sabreValidWeights, sabreValidityWeightScale, sabreSupportValid,
        )
        dispatchDirectional(workB, assembledRgb, workA)
        dispatchRestoreDirection(workA, workB, assembledRgb)

        // Preserve the restored-direction YCCD as the original reference until the final blend.
        // This rotation mirrors the reference stage ownership without copying its host structure.
        val originalYccd = assembledRgb
        var smoothYccd = workA
        var scratchYccd = workB
        runIirRgb(
            smoothYccd, scratchYccd, originalYccd, coefficients.pass1, filterLuma = true, "IIR1",
            sabreSupportR, sabreSupportGb, sabreValidWeights, sabreValidityWeightScale, sabreSupportValid,
        ).also {
            smoothYccd = it.first
            scratchYccd = it.second
        }
        dispatchError(originalYccd, smoothYccd, scratchYccd)
        var filteredError = scratchYccd
        var spare = smoothYccd
        runIirError(filteredError, spare, coefficients.pass1.a10, coefficients.pass1.b10).also {
            filteredError = it.first
            spare = it.second
        }
        dispatchBlend(originalYccd, filteredError, spare)
        var filteredYccd = spare
        var finalScratch = filteredError
        runIirRgb(
            filteredYccd, finalScratch, originalYccd, coefficients.pass3, filterLuma = false, "IIR3",
            sabreSupportR, sabreSupportGb, sabreValidWeights, sabreValidityWeightScale, sabreSupportValid,
        ).also {
            filteredYccd = it.first
            finalScratch = it.second
        }
        val chromaMs = (System.nanoTime() - chromaStart) / 1_000_000L

        val finalStart = System.nanoTime()
        dispatchFinal(filteredYccd, originalYccd)
        /* IRIS_26571_COHERENT_EDGE_COLOR_OWNER
         * Current-MGC VGN still completes first. The shared post-VGN pass keeps the successful
         * 26570 illumination-independent surface cleanup, but coherent real subject chroma is no
         * longer pulled toward a weaker opposite-side consensus. Clean sky remains pass-through;
         * highlight false-color suppression remains authoritative.
         */
        dispatchUniversalAdaptiveColor(
            assembledRgb, workA, sabreSupportR, sabreSupportGb, sabreValidWeights,
            sabreValidityWeightScale, preVgnPhysicalRgb,
        )
        val completedVgn = assembledRgb
        assembledRgb = workA
        workA = completedVgn
        val finalMs = (System.nanoTime() - finalStart) / 1_000_000L
        onFinalSubmitted?.invoke()

        val exported = if (exportFullSizeTexture) assembledRgb else 0
        val populateCpu = !exportFullSizeTexture || !deferCpuReadback
        if (populateCpu) {
            readbackRgb16(assembledRgb, obtainCpuOutput())
        }

        if (exported != 0) {
            host.transferTextureOwnership(exported, "Iris 26529 filtered Spatial RGB")
            owned.remove(exported)
        }
        releaseOwnedExcept(exported)
        assembledRgb = 0
        workA = 0
        workB = 0
        bands = emptyList()
        writtenBands = 0
        return Result(exported, chromaMs, finalMs, populateCpu)
    }

    fun release() {
        passWindow.drain("Iris 26529 chroma release")
        releaseOwnedExcept(0)
        assembledRgb = 0
        workA = 0
        workB = 0
        bands = emptyList()
        writtenBands = 0
        if (readbackFbo != 0) {
            GLES30.glDeleteFramebuffers(1, intArrayOf(readbackFbo), 0)
            readbackFbo = 0
        }
    }

    private fun validateCoverage(tiles: List<MgcSpatialRgbTile>) {
        val rows = tiles.groupBy { it.outputCore.top }.toSortedMap().values
        var expectedTop = 0
        var expectedIndex = 0
        rows.forEach { row ->
            val ordered = row.sortedBy { it.outputCore.left }
            val bottom = ordered.first().outputCore.bottom
            var expectedLeft = 0
            ordered.forEach { tile ->
                require(tile.index == expectedIndex++)
                require(tile.outputCore.left == expectedLeft && tile.outputCore.top == expectedTop)
                require(tile.outputCore.bottom == bottom)
                expectedLeft = tile.outputCore.right
            }
            require(expectedLeft == imageWidth)
            expectedTop = bottom
        }
        require(expectedTop == imageHeight)
    }

    private fun allocate(label: String): Int = host.createRgba16UiTexture(imageWidth, imageHeight, label).also {
        owned += it
        host.checkGlError("Iris 26529 allocate $label")
    }

    private fun releaseOwnedExcept(retain: Int) {
        owned.toList().filter { it != retain }.forEach { texture ->
            host.releaseTexture(texture, "Iris 26529 chroma work")
            owned.remove(texture)
        }
    }

    private fun dispatchSeed(
        source: Int,
        destination: Int,
        sabreSupportR: Int,
        sabreSupportGb: Int,
        sabreValidWeights: Int,
        sabreValidityWeightScale: Float,
        sabreSupportValid: Boolean,
    ) {
        GLES31.glUseProgram(seedProgram)
        setImageSize(seedProgram)
        GLES31.glUniform3fv(host.uniformLocation(seedProgram, "uCalculationGains"), 1, calculationRgbGains, 0)
        GLES31.glUniform1f(host.uniformLocation(seedProgram, "uMinimumDirectionGradient"), 8f)
        bindImage(0, source, GLES31.GL_READ_ONLY)
        bindImage(1, destination, GLES31.GL_WRITE_ONLY)
        bindSabreValidity(seedProgram, sabreSupportR, sabreSupportGb, sabreValidWeights, sabreValidityWeightScale, sabreSupportValid)
        trackedDispatch(
            "seed",
            if (sabreSupportValid) intArrayOf(source, sabreSupportR, sabreSupportGb, sabreValidWeights) else intArrayOf(source),
            intArrayOf(destination),
        )
        clearSabreValidityBindings()
        clearImages()
    }

    private fun dispatchLocal(
        program: Int,
        source: Int,
        destination: Int,
        label: String,
        chromaStrength: Float? = null,
    ) {
        GLES31.glUseProgram(program)
        setImageSize(program)
        chromaStrength?.let {
            GLES31.glUniform1f(host.uniformLocation(program, "uChromaStrength"), it)
        }
        dispatch2d(program, intArrayOf(source), destination, label)
    }

    private fun dispatchLocalMedian(
        source: Int,
        destination: Int,
        chromaStrength: Float,
        sabreSupportR: Int,
        sabreSupportGb: Int,
        sabreValidWeights: Int,
        sabreValidityWeightScale: Float,
        sabreSupportValid: Boolean,
    ) {
        GLES31.glUseProgram(localMedianProgram)
        setImageSize(localMedianProgram)
        GLES31.glUniform1f(host.uniformLocation(localMedianProgram, "uChromaStrength"), chromaStrength)
        bindImage(0, source, GLES31.GL_READ_ONLY)
        bindImage(1, destination, GLES31.GL_WRITE_ONLY)
        bindSabreValidity(localMedianProgram, sabreSupportR, sabreSupportGb, sabreValidWeights, sabreValidityWeightScale, sabreSupportValid)
        trackedDispatch(
            "local median",
            if (sabreSupportValid) intArrayOf(source, sabreSupportR, sabreSupportGb, sabreValidWeights) else intArrayOf(source),
            intArrayOf(destination),
        )
        clearSabreValidityBindings()
        clearImages()
    }

    private fun dispatchDirectional(source: Int, destination: Int, directionalSource: Int) {
        GLES31.glUseProgram(directionalProgram)
        setImageSize(directionalProgram)
        bindImage(0, source, GLES31.GL_READ_ONLY)
        bindImage(1, destination, GLES31.GL_READ_ONLY)
        bindImage(2, directionalSource, GLES31.GL_WRITE_ONLY)
        trackedDispatch("directional smooth", intArrayOf(source, destination), intArrayOf(directionalSource))
        clearImages()
    }

    private fun dispatchRestoreDirection(smooth: Int, direction: Int, destination: Int) {
        GLES31.glUseProgram(restoreDirectionProgram)
        setImageSize(restoreDirectionProgram)
        bindImage(0, smooth, GLES31.GL_READ_ONLY)
        bindImage(1, direction, GLES31.GL_READ_ONLY)
        bindImage(2, destination, GLES31.GL_WRITE_ONLY)
        trackedDispatch("restore direction", intArrayOf(smooth, direction), intArrayOf(destination))
        clearImages()
    }

    private fun dispatchError(original: Int, smooth: Int, destination: Int) {
        GLES31.glUseProgram(errorProgram)
        setImageSize(errorProgram)
        bindImage(0, original, GLES31.GL_READ_ONLY)
        bindImage(1, smooth, GLES31.GL_READ_ONLY)
        bindImage(2, destination, GLES31.GL_WRITE_ONLY)
        trackedDispatch("error", intArrayOf(original, smooth), intArrayOf(destination))
        clearImages()
    }

    private fun dispatchBlend(original: Int, smooth: Int, destination: Int) {
        GLES31.glUseProgram(blendProgram)
        setImageSize(blendProgram)
        GLES31.glUniform1f(host.uniformLocation(blendProgram, "uChromaStrength"), chromaCorrectionStrength)
        bindImage(0, original, GLES31.GL_READ_ONLY)
        bindImage(1, smooth, GLES31.GL_READ_ONLY)
        bindImage(2, destination, GLES31.GL_WRITE_ONLY)
        trackedDispatch("blend", intArrayOf(original, smooth), intArrayOf(destination))
        clearImages()
    }

    private fun dispatchFinal(source: Int, destination: Int) {
        GLES31.glUseProgram(finalProgram)
        setImageSize(finalProgram)
        GLES31.glUniform3fv(host.uniformLocation(finalProgram, "uCalculationGains"), 1, calculationRgbGains, 0)
        dispatch2d(finalProgram, intArrayOf(source), destination, "final")
    }

    private fun runIirRgb(
        source: Int,
        destination: Int,
        ownership: Int,
        pass: Iris26529SpatialRgbIirCoefficients.Pass,
        filterLuma: Boolean,
        label: String,
        sabreSupportR: Int,
        sabreSupportGb: Int,
        sabreValidWeights: Int,
        sabreValidityWeightScale: Float,
        sabreSupportValid: Boolean,
    ): Pair<Int, Int> {
        var input = source
        var output = destination
        val directions = arrayOf(intArrayOf(0,0), intArrayOf(1,0), intArrayOf(0,1), intArrayOf(1,1))
        directions.forEachIndexed { index, d ->
            GLES31.glUseProgram(iirRgbProgram)
            setImageSize(iirRgbProgram)
            setIirCoefficients(iirRgbProgram, pass)
            GLES31.glUniform1i(host.uniformLocation(iirRgbProgram, "uFilterLuma"), if (filterLuma) 1 else 0)
            GLES31.glUniform1i(host.uniformLocation(iirRgbProgram, "uDirection"), d[0])
            GLES31.glUniform1i(host.uniformLocation(iirRgbProgram, "uAxis"), d[1])
            bindImage(0, input, GLES31.GL_READ_ONLY)
            bindImage(1, output, GLES31.GL_WRITE_ONLY)
            bindImage(2, ownership, GLES31.GL_READ_ONLY)
            bindSabreValidity(iirRgbProgram, sabreSupportR, sabreSupportGb, sabreValidWeights, sabreValidityWeightScale, sabreSupportValid)
            trackedIirDispatch(
                d[1], "$label/$index", input, output,
                intArrayOf(ownership) + if (sabreSupportValid) intArrayOf(sabreSupportR, sabreSupportGb, sabreValidWeights) else intArrayOf(),
            )
            clearSabreValidityBindings()
            clearImages()
            input = output.also { output = input }
        }
        return input to output
    }

    private fun bindSabreValidity(
        program: Int,
        sabreSupportR: Int,
        sabreSupportGb: Int,
        sabreValidWeights: Int,
        sabreValidityWeightScale: Float,
        sabreSupportValid: Boolean,
    ) {
        GLES31.glUniform1i(host.uniformLocation(program, "uSabreSupportValid"), if (sabreSupportValid) 1 else 0)
        GLES31.glUniform1f(
            host.uniformLocation(program, "uSabreValidityWeightScale"),
            sabreValidityWeightScale.coerceAtLeast(1f),
        )
        if (!sabreSupportValid) return
        GLES30.glActiveTexture(GLES30.GL_TEXTURE0 + 2)
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, sabreSupportR)
        GLES31.glUniform1i(host.uniformLocation(program, "uSabreWeightR"), 2)
        GLES30.glActiveTexture(GLES30.GL_TEXTURE0 + 3)
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, sabreSupportGb)
        GLES31.glUniform1i(host.uniformLocation(program, "uSabreWeightsGb"), 3)
        GLES30.glActiveTexture(GLES30.GL_TEXTURE0 + 4)
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, sabreValidWeights)
        GLES31.glUniform1i(host.uniformLocation(program, "uSabreValidWeights"), 4)
        GLES30.glActiveTexture(GLES30.GL_TEXTURE0)
    }

    private fun clearSabreValidityBindings() {
        for (unit in 4 downTo 2) {
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0 + unit)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, 0)
        }
        GLES30.glActiveTexture(GLES30.GL_TEXTURE0)
    }

    private fun dispatchUniversalAdaptiveColor(
        source: Int,
        destination: Int,
        sabreSupportR: Int,
        sabreSupportGb: Int,
        sabreValidWeights: Int,
        sabreValidityWeightScale: Float,
        preVgnPhysicalRgb: Int,
    ) {
        check(universalAdaptiveColorProgram != 0)
        val sabreSupportValid = sabreSupportR != 0 && sabreSupportGb != 0 && sabreValidWeights != 0
        val preVgnPhysicalValid = preVgnPhysicalRgb != 0
        check(!preVgnPhysicalValid || sabreSupportValid) {
            "26728 pre-VGN physical chroma evidence requires exact Sabre CFA validity provenance"
        }
        GLES31.glUseProgram(universalAdaptiveColorProgram)
        setImageSize(universalAdaptiveColorProgram)
        bindImage(0, source, GLES31.GL_READ_ONLY)
        bindImage(1, destination, GLES31.GL_WRITE_ONLY)
        GLES31.glUniform1i(
            host.uniformLocation(universalAdaptiveColorProgram, "uSabreSupportValid"),
            if (sabreSupportValid) 1 else 0,
        )
        GLES31.glUniform1f(
            host.uniformLocation(universalAdaptiveColorProgram, "uSabreValidityWeightScale"),
            sabreValidityWeightScale.coerceAtLeast(1f),
        )
        GLES31.glUniform1i(
            host.uniformLocation(universalAdaptiveColorProgram, "uPhysicalPreVgnValid"),
            if (preVgnPhysicalValid) 1 else 0,
        )
        /* IRIS_26743_VISIBLE_HIGHLIGHT_NEUTRALITY_WB_DOMAIN
         * Final highlight hue authority is evaluated in calculation-WB space, never sensor RGB. */
        GLES31.glUniform3fv(
            host.uniformLocation(universalAdaptiveColorProgram, "uCalculationGains"),
            1, calculationRgbGains, 0,
        )
        if (sabreSupportValid) {
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0 + 2)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, sabreSupportR)
            GLES31.glUniform1i(host.uniformLocation(universalAdaptiveColorProgram, "uSabreWeightR"), 2)
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0 + 3)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, sabreSupportGb)
            GLES31.glUniform1i(host.uniformLocation(universalAdaptiveColorProgram, "uSabreWeightsGb"), 3)
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0 + 4)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, sabreValidWeights)
            GLES31.glUniform1i(host.uniformLocation(universalAdaptiveColorProgram, "uSabreValidWeights"), 4)
        }
        if (preVgnPhysicalValid) {
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0 + 5)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, preVgnPhysicalRgb)
            GLES31.glUniform1i(host.uniformLocation(universalAdaptiveColorProgram, "uPhysicalPreVgn"), 5)
        }
        trackedDispatch(
            "IRIS 26614 RAW-CFA-validity-owned universal adaptive color",
            when {
                sabreSupportValid && preVgnPhysicalValid ->
                    intArrayOf(source, sabreSupportR, sabreSupportGb, sabreValidWeights, preVgnPhysicalRgb)
                sabreSupportValid -> intArrayOf(source, sabreSupportR, sabreSupportGb, sabreValidWeights)
                else -> intArrayOf(source)
            },
            intArrayOf(destination),
        )
        if (preVgnPhysicalValid) {
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0 + 5)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, 0)
        }
        if (sabreSupportValid) {
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0 + 4)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, 0)
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0 + 3)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, 0)
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0 + 2)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, 0)
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0)
        }
        clearImages()
    }

    private fun runIirError(source: Int, destination: Int, a10: FloatArray, b10: FloatArray): Pair<Int, Int> {
        var input = source
        var output = destination
        val directions = arrayOf(intArrayOf(0,0), intArrayOf(1,0), intArrayOf(0,1), intArrayOf(1,1))
        directions.forEachIndexed { index, d ->
            GLES31.glUseProgram(iirErrorProgram)
            setImageSize(iirErrorProgram)
            GLES31.glUniform4fv(host.uniformLocation(iirErrorProgram, "uA10"), 1, a10, 0)
            GLES31.glUniform4fv(host.uniformLocation(iirErrorProgram, "uB10"), 1, b10, 0)
            GLES31.glUniform1i(host.uniformLocation(iirErrorProgram, "uDirection"), d[0])
            GLES31.glUniform1i(host.uniformLocation(iirErrorProgram, "uAxis"), d[1])
            bindImage(0, input, GLES31.GL_READ_ONLY)
            bindImage(1, output, GLES31.GL_WRITE_ONLY)
            trackedIirDispatch(d[1], "IIR2/$index", input, output)
            clearImages()
            input = output.also { output = input }
        }
        return input to output
    }

    private fun setIirCoefficients(program: Int, pass: Iris26529SpatialRgbIirCoefficients.Pass) {
        GLES31.glUniform4fv(host.uniformLocation(program, "uA10"), 1, pass.a10, 0)
        GLES31.glUniform4fv(host.uniformLocation(program, "uB10"), 1, pass.b10, 0)
        GLES31.glUniform4fv(host.uniformLocation(program, "uADyn1"), 1, pass.aDyn1, 0)
        GLES31.glUniform4fv(host.uniformLocation(program, "uBDyn1"), 1, pass.bDyn1, 0)
        GLES31.glUniform4fv(host.uniformLocation(program, "uADyn2"), 1, pass.aDyn2, 0)
        GLES31.glUniform4fv(host.uniformLocation(program, "uBDyn2"), 1, pass.bDyn2, 0)
    }

    private fun dispatch2d(program: Int, sources: IntArray, destination: Int, label: String) {
        sources.forEachIndexed { unit, texture -> bindImage(unit, texture, GLES31.GL_READ_ONLY) }
        bindImage(sources.size, destination, GLES31.GL_WRITE_ONLY)
        trackedDispatch(label, sources, intArrayOf(destination))
        clearImages()
    }

    private fun trackedDispatch(label: String, reads: IntArray, writes: IntArray) {
        passWindow.beginPass(
            label,
            reads = reads.map(GlesGpuScheduler::textureResource).toLongArray(),
            writes = writes.map(GlesGpuScheduler::textureResource).toLongArray(),
        )
        GLES31.glDispatchCompute(groupCount(imageWidth), groupCount(imageHeight), 1)
        GlesGpuScheduler.memoryBarrier()
        host.checkGlError("Iris 26529 chroma $label")
        passWindow.endPass()
    }

    private fun trackedIirDispatch(
        axis: Int,
        label: String,
        read: Int,
        write: Int,
        extraReads: IntArray = intArrayOf(),
    ) {
        passWindow.beginPass(
            label,
            reads = (intArrayOf(read) + extraReads).map(GlesGpuScheduler::textureResource).toLongArray(),
            writes = longArrayOf(GlesGpuScheduler.textureResource(write)),
        )
        if (axis == 0) GLES31.glDispatchCompute(1, imageHeight, 1)
        else GLES31.glDispatchCompute(imageWidth, 1, 1)
        GlesGpuScheduler.memoryBarrier()
        host.checkGlError("Iris 26529 chroma $label")
        passWindow.endPass()
    }

    private fun setImageSize(program: Int) {
        GLES31.glUniform2i(host.uniformLocation(program, "uImageSize"), imageWidth, imageHeight)
    }

    private fun bindImage(unit: Int, texture: Int, access: Int) {
        GLES31.glBindImageTexture(unit, texture, 0, false, 0, access, GLES30.GL_RGBA16UI)
    }

    private fun clearImages() {
        for (unit in 0..2) {
            GLES31.glBindImageTexture(unit, 0, 0, false, 0, GLES31.GL_READ_ONLY, GLES30.GL_RGBA16UI)
        }
    }

    private fun readbackRgb16(texture: Int, output: ByteBuffer) {
        GlesGpuCompletion.awaitSubmittedWork("Iris 26529 Spatial RGB CPU readback", host::checkGlError)
        if (readbackFbo == 0) {
            val ids = IntArray(1)
            GLES30.glGenFramebuffers(1, ids, 0)
            readbackFbo = ids[0]
        }
        val maxBandWidth = bands.maxOf { it.outputCore.width }
        val maxBandHeight = bands.maxOf { it.outputCore.height }
        val scratch = LargeDirectBuffer.allocate(
            maxBandWidth.toLong() * maxBandHeight * 8L,
            "Iris 26529 Spatial RGB readback",
        ) ?: error("Unable to allocate Iris 26529 readback scratch")
        output.clear()
        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, readbackFbo)
        try {
            GLES30.glFramebufferTexture2D(
                GLES30.GL_FRAMEBUFFER,
                GLES30.GL_COLOR_ATTACHMENT0,
                GLES30.GL_TEXTURE_2D,
                texture,
                0,
            )
            check(GLES30.glCheckFramebufferStatus(GLES30.GL_FRAMEBUFFER) == GLES30.GL_FRAMEBUFFER_COMPLETE)
            GLES30.glReadBuffer(GLES30.GL_COLOR_ATTACHMENT0)
            GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT, 8)
            bands.forEach { tile ->
                scratch.clear()
                GLES30.glReadPixels(
                    tile.outputCore.left,
                    tile.outputCore.top,
                    tile.outputCore.width,
                    tile.outputCore.height,
                    GLES30.GL_RGBA_INTEGER,
                    GLES30.GL_UNSIGNED_SHORT,
                    scratch,
                )
                check(
                    DirectBufferPixelPacker.unpackRgba16TileToRgb16(
                        source = scratch,
                        sourceWidth = tile.outputCore.width,
                        sourceHeight = tile.outputCore.height,
                        destination = output,
                        destinationWidth = imageWidth,
                        destinationHeight = imageHeight,
                        destinationLeft = tile.outputCore.left,
                        destinationTop = tile.outputCore.top,
                    ),
                )
                host.yieldToUiRenderer()
            }
        } finally {
            GLES30.glFramebufferTexture2D(
                GLES30.GL_FRAMEBUFFER,
                GLES30.GL_COLOR_ATTACHMENT0,
                GLES30.GL_TEXTURE_2D,
                0,
                0,
            )
            GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
            LargeDirectBuffer.free(scratch)
        }
        output.rewind()
    }

    private fun groupCount(value: Int): Int = GlesComputeWorkGroup.imageGroupCount(value)
}

/** Iris-local coefficient owner. Numeric values are pinned to the c317/MGC VGN reference. */
internal data class Iris26529SpatialRgbIirCoefficients(val pass1: Pass, val pass3: Pass) {
    data class Pass(
        val a10: FloatArray,
        val b10: FloatArray,
        val aDyn1: FloatArray,
        val bDyn1: FloatArray,
        val aDyn2: FloatArray,
        val bDyn2: FloatArray,
    )

    companion object {
        private val pass1Base = Pass(
            floatArrayOf(0.0674552768f, 0.134910554f, 0.0674552768f, 0f),
            floatArrayOf(1f, -1.14298046f, 0.412801594f, 0f),
            floatArrayOf(0.00580812711f, 0.0116162542f, 0.00580812711f, 0f),
            floatArrayOf(1f, -1.86380053f, 0.887032986f, 0f),
            floatArrayOf(0.00537849404f, 0.0107569881f, 0.00537849404f, 0f),
            floatArrayOf(1f, -1.72593343f, 0.747447371f, 0f),
        )
        private val pass3Base = Pass(
            pass1Base.a10,
            pass1Base.b10,
            floatArrayOf(0.0331984349f, 0.0663968697f, 0.0331984349f, 0f),
            floatArrayOf(1f, -1.61172712f, 0.744520843f, 0f),
            floatArrayOf(0.0281187538f, 0.0562375076f, 0.0281187538f, 0f),
            floatArrayOf(1f, -1.36511719f, 0.47759226f, 0f),
        )

        fun forOutputScale(outputScale: Float): Iris26529SpatialRgbIirCoefficients {
            val scale = outputScale.takeIf { it.isFinite() && it > 0f }?.coerceAtLeast(1f) ?: 1f
            return Iris26529SpatialRgbIirCoefficients(scalePass(pass1Base, scale), scalePass(pass3Base, scale))
        }

        private fun scalePass(pass: Pass, scale: Float): Pass {
            val (a10, b10) = scaleLowPass(pass.a10, pass.b10, scale)
            val (a1, b1) = scaleLowPass(pass.aDyn1, pass.bDyn1, scale)
            val (a2, b2) = scaleLowPass(pass.aDyn2, pass.bDyn2, scale)
            return Pass(a10, b10, a1, b1, a2, b2)
        }

        private fun scaleLowPass(numerator: FloatArray, denominator: FloatArray, scale: Float): Pair<FloatArray, FloatArray> {
            if (scale == 1f) return numerator.copyOf() to denominator.copyOf()
            val a1 = denominator[1].toDouble()
            val a2 = denominator[2].toDouble()
            val alpha = (1.0 - a2) / (1.0 + a2)
            val cosOmega = (-a1 * (1.0 + alpha) * 0.5).coerceIn(-1.0, 1.0)
            val omega = acos(cosOmega)
            val q = if (alpha > 1e-9) sin(omega) / (2.0 * alpha) else 0.7071067811865476
            val scaledOmega = (omega / scale.toDouble()).coerceIn(1e-5, Math.PI - 1e-5)
            val scaledAlpha = sin(scaledOmega) / (2.0 * max(q, 1e-6))
            val norm = 1.0 / (1.0 + scaledAlpha)
            val b0 = (1.0 - cos(scaledOmega)) * 0.5 * norm
            val b1 = (1.0 - cos(scaledOmega)) * norm
            val scaledA1 = -2.0 * cos(scaledOmega) * norm
            val scaledA2 = (1.0 - scaledAlpha) * norm
            return floatArrayOf(b0.toFloat(), b1.toFloat(), b0.toFloat(), 0f) to
                floatArrayOf(1f, scaledA1.toFloat(), scaledA2.toFloat(), 0f)
        }
    }
}

/**
 * Iris-owned GLSL translation of the latest post-c317 MGC Spatial-RGB post-fusion behavior.
 * The mathematical invariants are intentionally recognizable; ownership and integration are Iris.
 */
internal object Iris26529SpatialRgbChromaShaders {
    private val common = """
        uniform ivec2 uImageSize;
        ivec2 safePos(ivec2 p) { return clamp(p, ivec2(0), uImageSize - ivec2(1)); }
        int signedChroma(uint c) { int v = int(c); return v > 32767 ? v - 65536 : v; }
        uint unsignedChroma(int v) { return uint(v & 0xFFFF); }
        float decodeU16(uint value) {
            uint hi = value >> 8u;
            uint lo = value & 255u;
            const float finiteScale = 65504.0 / 65535.0;
            return float(hi) * (256.0 * finiteScale) + float(lo) * finiteScale;
        }
    """.trimIndent()

    /* IRIS_26578_FAIL_CLOSED_REAL_COLOR_GATE
     * IRIS_26571_COHERENT_CHROMA_PRESERVATION remains a hard inherited real-color veto.
     * Inherits the successful 26570/26571/26574 one-sided material, foliage/sky and radius-two
     * topology protections. The final post-VGN cleanup now fails closed: original camera chroma
     * is preserved unless several independent signals agree that the center is unsupported false
     * color. Real color continuing through a contour/curve wins. A Bayer-like two-pixel phase
     * pattern is suspicious only when immediate same-surface support is weak and the surrounding
     * consensus is nearly neutral. Correction is chroma-only, can never increase chroma magnitude,
     * and is hard-capped so one pass cannot repaint a real colored pixel.
     */
    val universalAdaptiveColor26561 = """
        #version 310 es
        layout(local_size_x = 8, local_size_y = 8, local_size_z = 1) in;
        precision highp float;
        precision highp int;
        // IRIS_26578_FAIL_CLOSED_REAL_COLOR_GATE
        layout(rgba16ui, binding = 0) readonly uniform highp uimage2D uSource;
        layout(rgba16ui, binding = 1) writeonly uniform highp uimage2D uDestination;
        uniform ivec2 uImageSize;
        /* IRIS_26614_RAW_CFA_CHANNEL_VALIDITY_PROVENANCE
         * Total R/G/B reconstruction weights plus the additive subset backed by source CFA samples
         * that retained real sensor-code headroom. The ratio is measurement validity, not a color
         * classifier. Valid measured color is protected; invalid color cannot protect itself merely
         * because the reconstructed RGB artifact forms a coherent contour. */
        uniform highp sampler2D uSabreWeightR;
        uniform highp sampler2D uSabreWeightsGb;
        uniform highp sampler2D uSabreValidWeights;
        uniform highp float uSabreValidityWeightScale;
        uniform int uSabreSupportValid;
        /* IRIS_26728_PHYSICALLY_SUPPORTED_CHROMA_MAGNITUDE
         * Read-only pre-VGN physical RGB. It can supply chroma magnitude evidence only; hue/direction
         * remains owned by the cleaned VGN result below. */
        uniform highp sampler2D uPhysicalPreVgn;
        uniform int uPhysicalPreVgnValid;
        /* IRIS_26743_VISIBLE_HIGHLIGHT_NEUTRALITY_WB_DOMAIN
         * This is the same calculation-WB domain used by the VGN seed. Neutrality decisions are
         * made only after these gains, so R=G=B means visually neutral on this camera. */
        uniform highp vec3 uCalculationGains;

        vec3 loadRgb(ivec2 p) {
            uvec4 packedValue = imageLoad(uSource, clamp(p, ivec2(0), uImageSize - ivec2(1)));
            return vec3(packedValue.rgb) / 65535.0;
        }

        vec3 loadSabreChannelValidity(ivec2 p) {
            if (uSabreSupportValid == 0) return vec3(1.0);
            ivec2 q = clamp(p, ivec2(0), uImageSize - ivec2(1));
            vec3 totalWeight = vec3(
                max(texelFetch(uSabreWeightR, q, 0).r, 0.0),
                max(texelFetch(uSabreWeightsGb, q, 0).r, 0.0),
                max(texelFetch(uSabreWeightsGb, q, 0).g, 0.0));
            vec3 validWeight = max(texelFetch(uSabreValidWeights, q, 0).rgb, vec3(0.0)) *
                max(uSabreValidityWeightScale, 1.0);
            return clamp(validWeight / max(totalWeight, vec3(1.0e-6)), vec3(0.0), vec3(1.0));
        }

        float minimum3(vec3 v) { return min(v.r, min(v.g, v.b)); }
        float maximum3(vec3 v) { return max(v.r, max(v.g, v.b)); }

        float luminanceOf(vec3 rgb) {
            return dot(rgb, vec3(0.25, 0.50, 0.25));
        }

        float hueAgreement(vec3 a, vec3 b) {
            return clamp(dot(a, b) / max(length(a) * length(b), 1.0e-6), -1.0, 1.0);
        }

        /* IRIS_26743_RENDERED_HIGHLIGHT_APPEARANCE_AUTHORITY
         * Prefer the extended-linear calculation-WB physical carrier when available. This makes
         * NORMAL/LONG/SHORT fusion and HDR magnitude irrelevant to the final hue rule. Non-fusion
         * routes use the current camera RGB transformed into the identical calculation-WB domain. */
        vec3 visiblePhysicalRgb26743(ivec2 p) {
            ivec2 q = clamp(p, ivec2(0), uImageSize - ivec2(1));
            if (uPhysicalPreVgnValid != 0) {
                return max(texelFetch(uPhysicalPreVgn, q, 0).rgb, vec3(0.0));
            }
            return max(loadRgb(q) * uCalculationGains, vec3(0.0));
        }

        float visibleHighlightLuma26743(ivec2 p) {
            /* What can visibly publish is bounded to display white. Extended HDR magnitude still
             * remains separate and is restored later as one scalar, exactly as in 26611. */
            return luminanceOf(clamp(visiblePhysicalRgb26743(p), vec3(0.0), vec3(1.0)));
        }

        void main() {
            ivec2 p = ivec2(gl_GlobalInvocationID.xy);
            if (any(greaterThanEqual(p, uImageSize))) return;
            vec3 center = loadRgb(p);
            float centerLuma = luminanceOf(center);
            float centerScale = max(centerLuma, 0.060);
            vec3 centerChroma = center - vec3(centerLuma);
            vec3 centerNormalizedChroma = centerChroma / centerScale;
            float centerNormalizedMagnitude = length(centerNormalizedChroma);
            vec3 centerChannelValidity = loadSabreChannelValidity(p);
            float centerMeasuredValidity = minimum3(centerChannelValidity);
            float measuredColorProtection = uSabreSupportValid != 0
                ? smoothstep(0.985, 0.9995, centerMeasuredValidity) : 0.0;
            float centerValidConsensusWeight = uSabreSupportValid != 0
                ? smoothstep(0.90, 0.985, centerMeasuredValidity) : 0.0;

            vec3 normalizedChromaSum = centerNormalizedChroma;
            float weightSum = 1.0;
            vec3 validNormalizedChromaSum = centerNormalizedChroma * centerValidConsensusWeight;
            float validWeightSum = centerValidConsensusWeight;
            float validNeighborSupport = 0.0;
            float neighborSupport = 0.0;
            float neutralNeighborSupport = 0.0;
            float maximumRelativeLumaDelta = 0.0;
            int brighterSide = 0;
            int darkerSide = 0;
            for (int y = -1; y <= 1; ++y) {
                for (int x = -1; x <= 1; ++x) {
                    if (x == 0 && y == 0) continue;
                    vec3 neighborRgb = loadRgb(p + ivec2(x, y));
                    float neighborLuma = luminanceOf(neighborRgb);
                    float lumaScale = max(max(centerLuma, neighborLuma), 0.060);
                    float signedRelativeLumaDelta = (neighborLuma - centerLuma) / lumaScale;
                    float relativeLumaDelta = abs(signedRelativeLumaDelta);
                    maximumRelativeLumaDelta = max(maximumRelativeLumaDelta, relativeLumaDelta);
                    if (signedRelativeLumaDelta > 0.16) brighterSide++;
                    if (signedRelativeLumaDelta < -0.16) darkerSide++;
                    float sameSurfaceWeight = 1.0 - smoothstep(0.16, 0.55, relativeLumaDelta);
                    vec3 neighborChroma = neighborRgb - vec3(neighborLuma);
                    vec3 neighborNormalizedChroma = neighborChroma / max(neighborLuma, 0.060);
                    normalizedChromaSum += neighborNormalizedChroma * sameSurfaceWeight;
                    weightSum += sameSurfaceWeight;
                    neighborSupport += sameSurfaceWeight;
                    float neighborNormalizedMagnitude = length(neighborNormalizedChroma);
                    neutralNeighborSupport += sameSurfaceWeight *
                        (1.0 - smoothstep(0.035, 0.100, neighborNormalizedMagnitude));
                    if (uSabreSupportValid != 0) {
                        vec3 neighborChannelValidity = loadSabreChannelValidity(p + ivec2(x, y));
                        float neighborMeasuredValidity = minimum3(neighborChannelValidity);
                        float measuredNeighborWeight = smoothstep(0.90, 0.985, neighborMeasuredValidity);
                        float validSameSurfaceWeight = sameSurfaceWeight * measuredNeighborWeight;
                        validNormalizedChromaSum += neighborNormalizedChroma * validSameSurfaceWeight;
                        validWeightSum += validSameSurfaceWeight;
                        validNeighborSupport += validSameSurfaceWeight;
                    }
                }
            }

            vec3 consensusNormalizedChroma = normalizedChromaSum / max(weightSum, 1.0e-6);
            float chromaDisagreement = length(centerNormalizedChroma - consensusNormalizedChroma);
            float consensusMagnitude = length(consensusNormalizedChroma);
            float chromaAgreement = hueAgreement(centerNormalizedChroma, consensusNormalizedChroma);
            float surfaceSupport = smoothstep(2.5, 5.75, neighborSupport);
            float neutralSurfaceSupport = smoothstep(2.50, 4.00, neutralNeighborSupport);
            vec3 validConsensusNormalizedChroma = validWeightSum > 1.0e-6
                ? validNormalizedChromaSum / validWeightSum : centerNormalizedChroma;
            float validConsensusSupport = uSabreSupportValid != 0
                ? clamp(validNeighborSupport / 3.50, 0.0, 1.0) : 0.0;
            float physicalChromaDisagreement =
                length(centerNormalizedChroma - validConsensusNormalizedChroma);
            /* Physical provenance has no hard "artifact must be this strong" dead zone. Once a
             * channel is known to be radiometrically invalid, disagreement with valid same-surface
             * color is continuous evidence rather than another scene-tuned classification gate. */
            float physicalOutlierEvidence = clamp(physicalChromaDisagreement / 0.180, 0.0, 1.0);
            float legacyEdgeProtection = smoothstep(0.45, 0.90, maximumRelativeLumaDelta);

            /* IRIS_26571_SAME_SIDE_MATERIAL_BOUNDARY: preserve the proven 26571 material-boundary ownership. */
            float oneSidedLuma = ((brighterSide >= 4 && darkerSide <= 1) ||
                (darkerSide >= 4 && brighterSide <= 1)) ? 1.0 : 0.0;
            float highlightPreservePermission = 1.0 - smoothstep(0.72, 0.92, centerLuma);
            float materialBoundary = oneSidedLuma *
                (1.0 - smoothstep(0.72, 0.92, chromaAgreement)) * highlightPreservePermission;

            /* Radius-two evidence inherited from 26574, plus a new near+far chain test. The chain
             * is the real-color topology proof: a contour/curve/letter/leaf only needs one or more
             * directions where its own hue continues on the same surface. Conversely, a CFA-like
             * phase pattern has a far sample that repeats the center while the nearer sample does
             * not support that hue. That pattern is suspicious but is never sufficient by itself.
             */
            float topologySupport = 0.0;
            float nearTopologySupport = 0.0;
            float contourChainSupport = 0.0;
            float phasePatternSupport = 0.0;
            /* IRIS_26579_MICRO_OBJECT_COLOR_TOPOLOGY
             * A real tiny print/icon may contain several different hues inside only a few native
             * pixels, so same-hue continuation is not a sufficient real-color definition. Measure
             * non-neutral chroma occupancy over radius two as a 2-D shape instead. The minor second
             * moment is near zero for a thin edge-following CFA fringe (including diagonal fringes)
             * but positive for a compact colored area. Hue agreement is deliberately not required.
             */
            float microChromaWeight = 0.0;
            float microNearWeight = 0.0;
            float microMomentXX = 0.0;
            float microMomentYY = 0.0;
            float microMomentXY = 0.0;
            /* IRIS_26580_MICRO_OBJECT_AREA_VS_RIBBON
             * Track independent near-field horizontal/vertical occupancy. A genuine tiny printed
             * object may change hue inside only a few pixels, but it still occupies area in both
             * image axes. A one-pixel CFA/text fringe remains line-like even when it is diagonal.
             */
            float microNearLeft = 0.0;
            float microNearRight = 0.0;
            float microNearUp = 0.0;
            float microNearDown = 0.0;
            const ivec2 topologyDirections[8] = ivec2[8](
                ivec2(1,0), ivec2(-1,0), ivec2(0,1), ivec2(0,-1),
                ivec2(1,1), ivec2(-1,-1), ivec2(1,-1), ivec2(-1,1));
            float centerChromaPresent = smoothstep(0.035, 0.090, centerNormalizedMagnitude);
            if (centerLuma > 0.58 || oneSidedLuma > 0.5 || legacyEdgeProtection > 0.25 ||
                centerChromaPresent > 0.0) {
                for (int yy = -2; yy <= 2; ++yy) {
                    for (int xx = -2; xx <= 2; ++xx) {
                        if (xx == 0 && yy == 0) continue;
                        vec3 objectRgb = loadRgb(p + ivec2(xx, yy));
                        float objectLuma = luminanceOf(objectRgb);
                        float relativeObjectLuma = abs(objectLuma - centerLuma) /
                            max(max(objectLuma, centerLuma), 0.060);
                        vec3 objectChroma = (objectRgb - vec3(objectLuma)) / max(objectLuma, 0.060);
                        float chromatic = smoothstep(0.050, 0.115, length(objectChroma));
                        /* Broad luma compatibility rejects unrelated remote surfaces without
                         * demanding one brightness inside a multicolor micro-print. */
                        float objectCompatibility = 1.0 - smoothstep(0.72, 1.20, relativeObjectLuma);
                        float w = chromatic * objectCompatibility;
                        microChromaWeight += w;
                        if (abs(xx) <= 1 && abs(yy) <= 1) {
                            microNearWeight += w;
                            if (xx < 0) microNearLeft = max(microNearLeft, w);
                            if (xx > 0) microNearRight = max(microNearRight, w);
                            if (yy < 0) microNearUp = max(microNearUp, w);
                            if (yy > 0) microNearDown = max(microNearDown, w);
                        }
                        microMomentXX += w * float(xx * xx);
                        microMomentYY += w * float(yy * yy);
                        microMomentXY += w * float(xx * yy);
                    }
                }
                for (int i = 0; i < 8; ++i) {
                    vec3 nearRgb = loadRgb(p + topologyDirections[i]);
                    vec3 farRgb = loadRgb(p + topologyDirections[i] * 2);
                    float nearLuma = luminanceOf(nearRgb);
                    float farLuma = luminanceOf(farRgb);
                    float nearLumaDelta = abs(nearLuma - centerLuma) /
                        max(max(nearLuma, centerLuma), 0.060);
                    float farLumaDelta = abs(farLuma - centerLuma) /
                        max(max(farLuma, centerLuma), 0.060);
                    vec3 nearChroma = (nearRgb - vec3(nearLuma)) / max(nearLuma, 0.060);
                    vec3 farChroma = (farRgb - vec3(farLuma)) / max(farLuma, 0.060);
                    float nearAgreement = hueAgreement(centerNormalizedChroma, nearChroma);
                    float farAgreement = hueAgreement(centerNormalizedChroma, farChroma);
                    float nearSameLuma = 1.0 - smoothstep(0.10, 0.26, nearLumaDelta);
                    float farSameLuma = 1.0 - smoothstep(0.10, 0.26, farLumaDelta);
                    float nearSameHue = smoothstep(0.82, 0.94, nearAgreement);
                    float farSameHue = smoothstep(0.82, 0.94, farAgreement);

                    topologySupport += farSameLuma * mix(1.0, farSameHue, centerChromaPresent);
                    nearTopologySupport += nearSameLuma * nearSameHue * centerChromaPresent;
                    contourChainSupport += nearSameLuma * farSameLuma * nearSameHue * farSameHue *
                        centerChromaPresent;
                    phasePatternSupport += nearSameLuma * farSameLuma * farSameHue *
                        (1.0 - smoothstep(0.20, 0.72, nearAgreement)) * centerChromaPresent;
                }
            }
            /* IRIS_26574_TOPOLOGY_PRESERVED_BRIGHT_SURFACE: radius-two contour/curve continuation remains authoritative. */
            float radiusTwoTopologyProtection = smoothstep(1.25, 2.75, topologySupport) *
                smoothstep(0.20, 0.55, max(legacyEdgeProtection, oneSidedLuma));
            float nearTopologyProtection = smoothstep(0.55, 1.45, nearTopologySupport);
            float contourTopologyProtection = smoothstep(0.55, 1.60, contourChainSupport);
            float phaseLikeEvidence = smoothstep(1.10, 2.80, phasePatternSupport);
            float topologyProtection = max(max(nearTopologyProtection, contourTopologyProtection),
                radiusTwoTopologyProtection * (1.0 - 0.90 * phaseLikeEvidence));
            float microTrace = microMomentXX + microMomentYY;
            float microDeterminant = max(microMomentXX * microMomentYY -
                microMomentXY * microMomentXY, 0.0);
            float microMinorMoment = microTrace > 1.0e-6 ?
                0.5 * (microTrace - sqrt(max(microTrace * microTrace -
                    4.0 * microDeterminant, 0.0))) / max(microChromaWeight, 1.0e-6) : 0.0;
            float microAreaEvidence = smoothstep(1.35, 3.25, microChromaWeight) *
                smoothstep(1.15, 2.75, microNearWeight) *
                smoothstep(0.10, 0.32, microMinorMoment) * centerChromaPresent;
            float microHorizontalPresence = max(microNearLeft, microNearRight);
            float microVerticalPresence = max(microNearUp, microNearDown);
            float microTwoAxisEvidence = smoothstep(0.18, 0.60, microHorizontalPresence) *
                smoothstep(0.18, 0.60, microVerticalPresence);
            float microCompactAreaEvidence = microAreaEvidence * microTwoAxisEvidence;

            /* IRIS_26581_OCCLUSION_GAP_BACKGROUND_OWNER
             * A tiny bright background opening between two darker foreground edges must not be
             * classified by the local foreground majority. Require an opposing dark near-pair plus
             * a matching bright/color-consistent far pair before assigning background ownership.
             * This is deliberately strict: a tiny LED/flower/logo cannot satisfy the far-background
             * continuation proof merely because it is small or saturated. */
            const ivec2 gapAxes[4] = ivec2[4](
                ivec2(1,0), ivec2(0,1), ivec2(1,1), ivec2(1,-1));
            float gapBackgroundWeight = 0.0;
            vec3 gapBackgroundChromaSum = vec3(0.0);
            float gapPairEvidence = 0.0;
            /* IRIS_26732_INVALID_HIGHLIGHT_PAIR_CONSENSUS + IRIS_26732_NEUTRAL_INK_PAIR_PROOF
             * Pair evidence is source-measured and symmetric: it can repair a bad center but cannot
             * invent a hue from a single neighboring edge. */
            float invalidHighlightPairWeight = 0.0;
            vec3 invalidHighlightPairChromaSum = vec3(0.0);
            float invalidHighlightPairEvidence = 0.0;
            float neutralInkPairWeight = 0.0;
            vec3 neutralInkPairChromaSum = vec3(0.0);
            float neutralInkPairEvidence = 0.0;
            /* IRIS_26735_INDEPENDENT_PHYSICAL_REAL_COLOR_PROOF
             * Reconstructed RGB topology may describe an artifact and therefore cannot by itself
             * veto achromatic cleanup. Preserve genuine colored text/logos through independently
             * CFA-valid near/far color continuation or physically supported compact 2-D color. */
            float physicalColorContinuation26735 = 0.0;
            /* IRIS_26741_HEADROOM_QUALIFIED_REAL_COLOR_PROOF
             * A clipped/flattened center may keep bright color only when the same hue continues into
             * independently valid radius-two evidence that is itself below the highlight shoulder. */
            float physicalHeadroomColorContinuation26741 = 0.0;
            float physicalColorAxisSupport26735 = 0.0;
            float neutralSpecularTransition26735 = 0.0;
            /* IRIS_26747_CONNECTED_UNRECOVERABLE_HIGHLIGHT_OWNER
             * A colored transition may use the modern material/color architecture only while no
             * connected radius-one/two highlight core has exhausted physical CFA color support.
             * This carries the successful 26727 0.72..0.92 highlight ownership across the visible
             * fringe without globally muting physically recoverable bright color. */
            float connectedUnrecoverableHighlight26747 = 0.0;
            for (int g = 0; g < 4; ++g) {
                ivec2 d = gapAxes[g];
                vec3 nearA = loadRgb(p + d);
                vec3 nearB = loadRgb(p - d);
                vec3 farA = loadRgb(p + 2 * d);
                vec3 farB = loadRgb(p - 2 * d);
                float nearAY = luminanceOf(nearA);
                float nearBY = luminanceOf(nearB);
                float farAY = luminanceOf(farA);
                float farBY = luminanceOf(farB);
                float nearDarkA = smoothstep(0.18, 0.48,
                    (centerLuma - nearAY) / max(max(centerLuma, nearAY), 0.060));
                float nearDarkB = smoothstep(0.18, 0.48,
                    (centerLuma - nearBY) / max(max(centerLuma, nearBY), 0.060));
                float farSameA = 1.0 - smoothstep(0.09, 0.27,
                    abs(farAY - centerLuma) / max(max(farAY, centerLuma), 0.060));
                float farSameB = 1.0 - smoothstep(0.09, 0.27,
                    abs(farBY - centerLuma) / max(max(farBY, centerLuma), 0.060));
                vec3 farNormA = (farA - vec3(farAY)) / max(farAY, 0.060);
                vec3 farNormB = (farB - vec3(farBY)) / max(farBY, 0.060);
                float farMagA = length(farNormA);
                float farMagB = length(farNormB);
                float farNeutralPair = (1.0 - smoothstep(0.035, 0.090, farMagA)) *
                    (1.0 - smoothstep(0.035, 0.090, farMagB));
                float farHuePair = smoothstep(0.72, 0.92, hueAgreement(farNormA, farNormB));
                float farColorAgreement = max(farNeutralPair, farHuePair);
                float pairEvidence = nearDarkA * nearDarkB * farSameA * farSameB *
                    farColorAgreement;
                gapPairEvidence = max(gapPairEvidence, pairEvidence);
                gapBackgroundWeight += pairEvidence;
                gapBackgroundChromaSum += 0.5 * (farNormA + farNormB) * pairEvidence;

                vec3 farValidityA = loadSabreChannelValidity(p + 2 * d);
                vec3 farValidityB = loadSabreChannelValidity(p - 2 * d);
                float farPhysicalPair = smoothstep(0.985, 0.9995,
                    min(minimum3(farValidityA), minimum3(farValidityB)));
                float invalidHighlightSameA = 1.0 - smoothstep(0.18, 0.58,
                    abs(farAY - centerLuma) / max(max(farAY, centerLuma), 0.060));
                float invalidHighlightSameB = 1.0 - smoothstep(0.18, 0.58,
                    abs(farBY - centerLuma) / max(max(farBY, centerLuma), 0.060));
                float invalidHighlightPair = farPhysicalPair * invalidHighlightSameA *
                    invalidHighlightSameB * farColorAgreement;
                invalidHighlightPairEvidence = max(invalidHighlightPairEvidence,
                    invalidHighlightPair);
                invalidHighlightPairWeight += invalidHighlightPair;
                invalidHighlightPairChromaSum += 0.5 * (farNormA + farNormB) *
                    invalidHighlightPair;

                float nearBrightA = smoothstep(0.18, 0.50,
                    (nearAY - centerLuma) / max(max(nearAY, centerLuma), 0.060));
                float nearBrightB = smoothstep(0.18, 0.50,
                    (nearBY - centerLuma) / max(max(nearBY, centerLuma), 0.060));
                vec3 nearNormA = (nearA - vec3(nearAY)) / max(nearAY, 0.060);
                vec3 nearNormB = (nearB - vec3(nearBY)) / max(nearBY, 0.060);
                float nearMagA = length(nearNormA);
                float nearMagB = length(nearNormB);
                float nearNeutralPair = (1.0 - smoothstep(0.030, 0.085, nearMagA)) *
                    (1.0 - smoothstep(0.030, 0.085, nearMagB));
                vec3 nearValidityA = loadSabreChannelValidity(p + d);
                vec3 nearValidityB = loadSabreChannelValidity(p - d);
                float nearPhysicalA = smoothstep(0.985, 0.9995, minimum3(nearValidityA));
                float nearPhysicalB = smoothstep(0.985, 0.9995, minimum3(nearValidityB));
                float nearPhysicalPair = min(nearPhysicalA, nearPhysicalB);

                /* IRIS_26735_NEUTRAL_EDGE_AND_SPECULAR_BRACKET_OWNER
                 * A neutral edge pixel may be bracketed by one dark and one bright neutral material;
                 * 26734's same-polarity requirement missed those boundary pixels. Near and radius-two
                 * pairs can now prove an achromatic transition without consulting contaminated center
                 * hue. This also covers neutral bright-light/reflection transition fringes. */
                float nearPairSpan = abs(nearAY - nearBY) / max(max(nearAY, nearBY), 0.060);
                float nearCenterContrast = max(
                    abs(nearAY - centerLuma) / max(max(nearAY, centerLuma), 0.060),
                    abs(nearBY - centerLuma) / max(max(nearBY, centerLuma), 0.060));
                float nearEdgeBracket = smoothstep(0.08, 0.30, nearPairSpan) *
                    smoothstep(0.08, 0.35, nearCenterContrast);
                float nearSamePolarity = max(nearBrightA * nearBrightB, nearDarkA * nearDarkB);
                float nearNeutralTopology = max(nearSamePolarity, nearEdgeBracket);
                float neutralNearPair = nearNeutralTopology * nearNeutralPair * nearPhysicalPair;

                float farBrightA26735 = smoothstep(0.18, 0.50,
                    (farAY - centerLuma) / max(max(farAY, centerLuma), 0.060));
                float farBrightB26735 = smoothstep(0.18, 0.50,
                    (farBY - centerLuma) / max(max(farBY, centerLuma), 0.060));
                float farDarkA26735 = smoothstep(0.18, 0.50,
                    (centerLuma - farAY) / max(max(centerLuma, farAY), 0.060));
                float farDarkB26735 = smoothstep(0.18, 0.50,
                    (centerLuma - farBY) / max(max(centerLuma, farBY), 0.060));
                float farPairSpan26735 = abs(farAY - farBY) / max(max(farAY, farBY), 0.060);
                float farCenterContrast26735 = max(
                    abs(farAY - centerLuma) / max(max(farAY, centerLuma), 0.060),
                    abs(farBY - centerLuma) / max(max(farBY, centerLuma), 0.060));
                float farEdgeBracket26735 = smoothstep(0.08, 0.30, farPairSpan26735) *
                    smoothstep(0.08, 0.35, farCenterContrast26735);
                float farSamePolarity26735 = max(farBrightA26735 * farBrightB26735,
                    farDarkA26735 * farDarkB26735);
                float farNeutralTopology26735 = max(farSamePolarity26735, farEdgeBracket26735);
                float neutralFarPair26735 = farNeutralTopology26735 * farNeutralPair * farPhysicalPair;
                float neutralAxisPair26735 = max(neutralNearPair, 0.90 * neutralFarPair26735);
                neutralInkPairEvidence = max(neutralInkPairEvidence, neutralAxisPair26735);
                neutralInkPairWeight += neutralNearPair + 0.90 * neutralFarPair26735;
                neutralInkPairChromaSum += 0.5 * (nearNormA + nearNormB) * neutralNearPair +
                    0.45 * (farNormA + farNormB) * neutralFarPair26735;
                float axisPeakLuma26735 = max(max(nearAY, nearBY), max(farAY, farBY));
                neutralSpecularTransition26735 = max(neutralSpecularTransition26735,
                    neutralAxisPair26735 * smoothstep(0.58, 0.86, axisPeakLuma26735));

                /* Independent real-color continuation: valid non-neutral color must persist from a
                 * near sample into the corresponding far sample on a similar-luma material. A
                 * center artifact cannot manufacture this proof by itself. */
                float farPhysicalA26735 = smoothstep(0.985, 0.9995, minimum3(farValidityA));
                float farPhysicalB26735 = smoothstep(0.985, 0.9995, minimum3(farValidityB));
                float centerBrightBridge26747 = smoothstep(0.58, 0.72, centerLuma);
                float nearUnrecoverableA26747 = max(
                    smoothstep(0.90, 0.92, nearAY),
                    smoothstep(0.72, 0.92, nearAY) * (1.0 - nearPhysicalA));
                float nearUnrecoverableB26747 = max(
                    smoothstep(0.90, 0.92, nearBY),
                    smoothstep(0.72, 0.92, nearBY) * (1.0 - nearPhysicalB));
                float farUnrecoverableA26747 = max(
                    smoothstep(0.90, 0.92, farAY),
                    smoothstep(0.72, 0.92, farAY) * (1.0 - farPhysicalA26735));
                float farUnrecoverableB26747 = max(
                    smoothstep(0.90, 0.92, farBY),
                    smoothstep(0.72, 0.92, farBY) * (1.0 - farPhysicalB26735));
                connectedUnrecoverableHighlight26747 = max(
                    connectedUnrecoverableHighlight26747,
                    centerBrightBridge26747 * max(max(nearUnrecoverableA26747,
                        nearUnrecoverableB26747), max(farUnrecoverableA26747,
                        farUnrecoverableB26747)));
                float nearColorA26735 = smoothstep(0.080, 0.160, nearMagA);
                float nearColorB26735 = smoothstep(0.080, 0.160, nearMagB);
                float farColorA26735 = smoothstep(0.080, 0.160, farMagA);
                float farColorB26735 = smoothstep(0.080, 0.160, farMagB);
                float chainLumaA26735 = 1.0 - smoothstep(0.10, 0.32,
                    abs(nearAY - farAY) / max(max(nearAY, farAY), 0.060));
                float chainLumaB26735 = 1.0 - smoothstep(0.10, 0.32,
                    abs(nearBY - farBY) / max(max(nearBY, farBY), 0.060));
                float chainA26735 = nearPhysicalA * farPhysicalA26735 * nearColorA26735 *
                    farColorA26735 * chainLumaA26735 *
                    smoothstep(0.88, 0.97, hueAgreement(nearNormA, farNormA));
                float chainB26735 = nearPhysicalB * farPhysicalB26735 * nearColorB26735 *
                    farColorB26735 * chainLumaB26735 *
                    smoothstep(0.88, 0.97, hueAgreement(nearNormB, farNormB));
                physicalColorContinuation26735 = max(physicalColorContinuation26735,
                    max(chainA26735, chainB26735));
                float farHeadroomA26741 = 1.0 - smoothstep(0.76, 0.90, farAY);
                float farHeadroomB26741 = 1.0 - smoothstep(0.76, 0.90, farBY);
                physicalHeadroomColorContinuation26741 = max(physicalHeadroomColorContinuation26741,
                    max(chainA26735 * farHeadroomA26741, chainB26735 * farHeadroomB26741));
                physicalColorAxisSupport26735 += smoothstep(0.45, 0.90,
                    max(nearPhysicalA * nearColorA26735, nearPhysicalB * nearColorB26735));
            }
            /* IRIS_26580_FAIL_CLOSED_MULTICOLOR_OBJECT_VETO
             * Compact 2-D chroma wins over weak/moderate phase resemblance, which is common inside
             * tiny multicolor prints. Only an overwhelming repeated near-opposite/far-matching phase
             * signature can extinguish this veto; that preserves the proven 26578 neutral CFA-fringe
             * regression. Uncertain cases remain biased toward keeping scene color. */
            float phaseOverride = smoothstep(0.78, 0.96, phaseLikeEvidence);
            float microObjectProtection = max(
                microAreaEvidence * (1.0 - 0.98 * phaseOverride),
                microCompactAreaEvidence * (1.0 - phaseOverride));
            float physicalContinuationProof26735 = smoothstep(0.62, 0.90,
                physicalColorContinuation26735);
            float physicalCompactColorProof26735 = measuredColorProtection *
                smoothstep(1.45, 2.70, physicalColorAxisSupport26735) *
                smoothstep(0.35, 0.72, microCompactAreaEvidence);
            float physicalRealColorVeto26735 = clamp(max(physicalContinuationProof26735,
                physicalCompactColorProof26735), 0.0, 1.0);
            float physicalHeadroomColorProof26741 = smoothstep(0.50, 0.82,
                physicalHeadroomColorContinuation26741);
            float supportedMaterialBoundary = materialBoundary * nearTopologyProtection;

            /* Coherent center color remains protected. This is intentionally asymmetric: evidence
             * for real color can veto cleanup, while evidence for false color must pass every gate.
             */
            float coherentHue = smoothstep(0.76, 0.95, chromaAgreement) *
                smoothstep(0.050, 0.180, consensusMagnitude);
            float centerToConsensusMagnitude = centerNormalizedMagnitude /
                max(consensusMagnitude, 0.025);
            float plausibleCenterMagnitude = 1.0 - smoothstep(2.0, 3.5, centerToConsensusMagnitude);
            /* IRIS_26733_HEADROOM_PRECEDES_COLOR_OWNERSHIP
             * Restore the successful 26727/26728 hierarchy: near-white/flattened highlights do not
             * get to self-declare protected hue merely because reconstructed RGB is spatially
             * coherent. The only exception is a genuinely bright colored material with all-channel
             * physical support, substantial non-neutral chroma, and coherent real-color topology. */
            float brightTopologyProof = max(max(nearTopologyProtection, contourTopologyProtection),
                microObjectProtection);
            /* IRIS_26740_HEADROOM_OVERRIDE_REQUIRES_PHYSICAL_REAL_COLOR
             * Spatial coherence alone is no longer enough to override the proven highlight veto.
             * The already-computed physical continuation/compact-color proof must agree, preserving
             * genuine bright color while rejecting coherent cyan/yellow/magenta reconstruction. */
            float brightPhysicalColorException = measuredColorProtection *
                smoothstep(0.10, 0.18, centerNormalizedMagnitude) *
                smoothstep(0.50, 0.82, brightTopologyProof) *
                smoothstep(0.55, 0.88, physicalRealColorVeto26735) *
                physicalHeadroomColorProof26741;
            /* IRIS_26747_FULL_26727_UNRECOVERABLE_HEADROOM_VETO
             * Preserve 26745 color ownership when bright color remains physically recoverable.
             * Restore the full successful 26727 0.72..0.92 authority when the center itself, or a
             * connected radius-one/two bright core, has exhausted physical color support. */
            float centerUnrecoverableHighlight26747 = max(
                smoothstep(0.90, 0.92, centerLuma),
                smoothstep(0.72, 0.92, centerLuma) *
                    (1.0 - smoothstep(0.985, 0.9995, centerMeasuredValidity)));
            connectedUnrecoverableHighlight26747 = clamp(max(
                connectedUnrecoverableHighlight26747, centerUnrecoverableHighlight26747), 0.0, 1.0);
            brightPhysicalColorException *= 1.0 - connectedUnrecoverableHighlight26747;
            float highlightColorOwnershipPermission = max(highlightPreservePermission,
                brightPhysicalColorException);
            float coherentCenterProtection = coherentHue * plausibleCenterMagnitude *
                highlightColorOwnershipPermission;
            /* A luma edge by itself is no longer a chroma veto. Color topology still protects
             * ordinary/tiny real color, but cannot bypass the inherited highlight-headroom owner. */
            float realColorConfidence = clamp(max(max(max(supportedMaterialBoundary,
                coherentCenterProtection), topologyProtection), microObjectProtection), 0.0, 1.0) *
                highlightColorOwnershipPermission;

            /* IRIS_26614_PHYSICAL_COLOR_VALIDITY_AUTHORITY
             * 26613 used total contribution imbalance, then allowed reconstructed-RGB topology to
             * veto it. That let a coherent magenta rail classify itself as real color. 26614 uses
             * the ratio of valid source-CFA weight to total reconstruction weight instead. The
             * correction direction is measured from neighboring pixels whose own R/G/B validity
             * is high and whose luminance places them on the same local surface. */
            vec3 channelInvalidity = uSabreSupportValid != 0
                ? vec3(1.0) - centerChannelValidity : vec3(0.0);
            vec3 physicalTargetChroma = validConsensusNormalizedChroma * centerScale;
            vec3 physicalDesiredDelta = physicalTargetChroma - centerChroma;
            float physicalDesiredLength = length(physicalDesiredDelta);
            float invalidChannelDirection = physicalDesiredLength > 1.0e-7
                ? clamp(length(physicalDesiredDelta * channelInvalidity) / physicalDesiredLength,
                    0.0, 1.0) : 0.0;
            float physicalValidityEvidence = invalidChannelDirection * validConsensusSupport;

            /* Fail-closed false-color proof.
             * 1) The center must disagree materially with same-surface consensus.
             * 2) That consensus must be close to neutral; colored-on-colored boundaries are thus
             *    ambiguous and untouched.
             * 3) There must be broad same-surface support and several genuinely neutral neighbors;
             *    opposing real colors that merely average to neutral remain ambiguous and untouched.
             * 4) A Bayer-like near/far phase signature must be present. Isolation by itself never
             *    authorizes cleanup, so a tiny LED, flower, fabric thread or saturated object is
             *    preserved when temporal/CFA certainty is unavailable at this post-VGN boundary.
             * 5) Any convincing real-color topology vetoes the correction.
             */
            float centerOutlierEvidence = smoothstep(0.070, 0.220, chromaDisagreement);
            float neutralConsensusEvidence = 1.0 - smoothstep(0.070, 0.160, consensusMagnitude);
            float isolatedEvidence = smoothstep(1.35, 2.75, centerToConsensusMagnitude);
            float phaseConfidence = phaseLikeEvidence * mix(0.70, 1.0, isolatedEvidence);
            float legacyFalseColorBase = centerOutlierEvidence * neutralConsensusEvidence *
                surfaceSupport * neutralSurfaceSupport * (1.0 - realColorConfidence) *
                (1.0 - measuredColorProtection);
            float legacyFalseColorScore = legacyFalseColorBase * phaseConfidence;

            /* Physical validity does not require a neutral target. A real red/blue/purple material
             * with one clipped channel is repaired toward physically valid same-surface color, not
             * toward grey. Conversely a neutral window/ceiling edge naturally has a neutral valid
             * consensus. RGB topology is deliberately not a veto on this path. */
            float physicalFalseColorScore = physicalOutlierEvidence * physicalValidityEvidence;

            vec3 legacyTargetChroma = consensusNormalizedChroma * centerScale;
            float centerMagnitude = length(centerChroma);
            float legacyTargetMagnitude = length(legacyTargetChroma);
            if (legacyTargetMagnitude > centerMagnitude && legacyTargetMagnitude > 1.0e-7) {
                legacyTargetChroma *= centerMagnitude / legacyTargetMagnitude;
                legacyTargetMagnitude = centerMagnitude;
            }

            float targetAgreement = hueAgreement(centerChroma, legacyTargetChroma);
            float targetNeutral = 1.0 - smoothstep(0.010, 0.045, legacyTargetMagnitude);
            float supportedTarget = max(targetNeutral, smoothstep(0.82, 0.94, targetAgreement));
            float legacyCorrection = smoothstep(0.72, 0.90, legacyFalseColorScore) * supportedTarget;
            vec3 legacyDesiredDelta = legacyTargetChroma - centerChroma;
            float legacyDesiredLength = length(legacyDesiredDelta);
            float legacyDecisiveNeutralCfaProof =
                smoothstep(0.92, 0.985, legacyFalseColorScore) *
                smoothstep(0.88, 0.985, phaseLikeEvidence) *
                smoothstep(0.90, 0.995, neutralSurfaceSupport) *
                smoothstep(0.90, 0.995, targetNeutral) *
                (1.0 - smoothstep(0.02, 0.12, realColorConfidence)) *
                (1.0 - measuredColorProtection);
            float legacyMaximumMove = min(0.050, 0.40 * centerMagnitude);
            float maximumMove = mix(legacyMaximumMove, legacyDesiredLength,
                legacyDecisiveNeutralCfaProof);
            float boundedScale = legacyDesiredLength > 1.0e-7
                ? min(1.0, maximumMove / legacyDesiredLength) : 0.0;
            vec3 correctedChroma = centerChroma +
                legacyDesiredDelta * boundedScale * legacyCorrection;
            if (length(correctedChroma) > centerMagnitude && length(correctedChroma) > 1.0e-7) {
                correctedChroma *= centerMagnitude / length(correctedChroma);
            }


            /* IRIS_26707_VALID_CFA_NEUTRAL_SURFACE_LEAK_REJECT
             * Radiometrically valid CFA samples do not prove that reconstructed chroma belongs to
             * the center surface. A narrow neutral conduit/wire can borrow saturated background hue
             * while every contributing source sample remains unclipped. Bypass measured-color
             * protection only for an overwhelming signal-defined case: the center is a chroma
             * outlier, its same-luma neighborhood has a strongly neutral consensus, the center hue
             * exhibits the inherited near/far CFA-phase signature, and there is no compact/chain
             * real-color topology. This path changes chroma only; center luminance/geometry are
             * unchanged, and clean lenses/scenes that lack this signature remain exact pass-through. */
            float neutralLeakOutlier = smoothstep(0.100, 0.205, chromaDisagreement);
            float neutralLeakConsensus = smoothstep(0.72, 0.96, neutralConsensusEvidence);
            float neutralLeakSurface = min(
                smoothstep(0.78, 0.97, surfaceSupport),
                smoothstep(0.82, 0.985, neutralSurfaceSupport));
            float neutralLeakPhase = smoothstep(0.76, 0.94, phaseLikeEvidence);
            float neutralLeakIsolation = smoothstep(1.55, 2.80, centerToConsensusMagnitude);
            float neutralLeakRealColorVeto = clamp(max(max(
                supportedMaterialBoundary,
                microObjectProtection),
                contourTopologyProtection * (1.0 - 0.95 * phaseLikeEvidence)), 0.0, 1.0);
            float validCfaNeutralLeakProof = min(min(neutralLeakOutlier, neutralLeakConsensus),
                min(neutralLeakSurface, neutralLeakPhase)) *
                mix(0.80, 1.0, neutralLeakIsolation) * (1.0 - neutralLeakRealColorVeto);
            float validCfaNeutralLeakAuthority = smoothstep(0.62, 0.88, validCfaNeutralLeakProof);
            float validCfaNeutralLeakDesiredLength = length(legacyDesiredDelta);
            float validCfaNeutralLeakMaximumMove = min(0.070, 0.68 * centerMagnitude);
            float validCfaNeutralLeakScale = validCfaNeutralLeakDesiredLength > 1.0e-7
                ? min(1.0, validCfaNeutralLeakMaximumMove /
                    validCfaNeutralLeakDesiredLength) : 0.0;
            vec3 validCfaNeutralLeakCandidate = centerChroma + legacyDesiredDelta *
                validCfaNeutralLeakScale;
            correctedChroma = mix(correctedChroma, validCfaNeutralLeakCandidate,
                0.92 * validCfaNeutralLeakAuthority);

            /* IRIS_26732_NEUTRAL_FINE_STRUCTURE_LOCK
             * IRIS_26734_POLARITY_INDEPENDENT_ACHROMATIC_STRUCTURE_CLEANUP
             * A thin achromatic structure bracketed by a trustworthy neutral pair remains neutral
             * regardless of polarity, font, contour, lens or zoom. Do not use coherent center hue as
             * a veto here: a reconstructed green/magenta stroke can otherwise self-protect. Genuine
             * colored micro-objects remain protected by measured material/topology/compact support. */
            if (neutralInkPairWeight > 1.0e-6) {
                vec3 neutralInkTargetNormalized = neutralInkPairChromaSum / neutralInkPairWeight;
                vec3 neutralInkTarget = neutralInkTargetNormalized * centerScale;
                /* IRIS_26741_STRONG_ACHROMATIC_FINE_STRUCTURE_AUTHORITY
                 * A physically neutral opposing pair is stronger evidence than reconstructed center hue.
                 * Lower the visible-false-chroma entry threshold and make cleanup effectively complete,
                 * while the independent physical real-color proof still protects genuine colored micro-detail. */
                float neutralInkOutlier = smoothstep(0.018, 0.090, centerNormalizedMagnitude);
                /* IRIS_26735_RECONSTRUCTED_HUE_CANNOT_SELF_VETO_ACHROMATIC_OWNER
                 * 26734 allowed reconstructed topology/micro-object color to veto neutral cleanup.
                 * The supplied 1x/2x/4.1x/7x samples prove coherent false green/magenta can therefore
                 * protect itself. Only independently CFA-valid color continuation/compact support may
                 * veto a physically bracketed neutral structure. */
                float neutralInkProof = neutralInkPairEvidence * neutralInkOutlier *
                    (1.0 - physicalRealColorVeto26735);
                float neutralInkAuthority = smoothstep(0.42, 0.76, neutralInkProof);
                float neutralSpecularAuthority26735 = smoothstep(0.55, 0.86,
                    neutralSpecularTransition26735) * neutralInkOutlier *
                    (1.0 - physicalRealColorVeto26735);
                neutralInkAuthority = max(neutralInkAuthority, 0.96 * neutralSpecularAuthority26735);
                float neutralInkTargetMagnitude = length(neutralInkTarget);
                if (neutralInkTargetMagnitude > centerMagnitude && neutralInkTargetMagnitude > 1.0e-7) {
                    neutralInkTarget *= centerMagnitude / neutralInkTargetMagnitude;
                }
                correctedChroma = mix(correctedChroma, neutralInkTarget,
                    0.995 * neutralInkAuthority);
            }

            /* The physical path may increase or decrease chroma because its target is measured
             * neighboring color with high per-channel CFA validity. Only physically invalid RGB
             * components are replaced. The candidate is then uniformly rescaled back to the center
             * luminance, so valid measured channels are never independently repainted. This is what
             * protects true colored objects: no neutral assumption and no post-RGB coherence veto. */
            float physicalAuthority = uSabreSupportValid != 0
                ? clamp(physicalFalseColorScore, 0.0, 1.0) *
                    (1.0 - measuredColorProtection)
                : 0.0;
            vec3 physicalTargetRgb=max(vec3(centerLuma)+physicalTargetChroma,vec3(0.0));
            /* Per-channel invalidity is the only component replacement mask. Do not multiply it by
             * physicalAuthority here and again below: that double attenuation was explicitly
             * rejected because it can turn strong physical evidence into another visible no-op. */
            vec3 componentRepair=clamp(channelInvalidity,vec3(0.0),vec3(1.0));
            vec3 physicalCandidateRgb=mix(center,physicalTargetRgb,componentRepair);
            float physicalCandidateLuma=luminanceOf(physicalCandidateRgb);
            if(centerLuma>1.0e-7&&physicalCandidateLuma>1.0e-7){
                physicalCandidateRgb*=centerLuma/physicalCandidateLuma;
            }
            vec3 physicalCandidateChroma=physicalCandidateRgb-vec3(centerLuma);
            correctedChroma=mix(correctedChroma,physicalCandidateChroma,physicalAuthority);

            /* IRIS_26581_GAP_BACKGROUND_CHROMA_RESTORE
             * When the strict paired-edge proof succeeds, the far samples are the actual supported
             * background owner. Restore only toward their observed chroma; never invent a hue or use
             * surrounding foreground color. This repair is independent of the false-color gate so a
             * real blue sky opening can be made uniform even though blue itself is real color. */
            if (gapBackgroundWeight > 1.0e-6) {
                vec3 gapNormalizedChroma = gapBackgroundChromaSum / gapBackgroundWeight;
                vec3 gapTargetChroma = gapNormalizedChroma * centerScale;
                float gapDisagreement = smoothstep(0.045, 0.150,
                    length(centerNormalizedChroma - gapNormalizedChroma));
                float gapOwnership = smoothstep(0.42, 0.88, gapPairEvidence) * gapDisagreement;
                correctedChroma = mix(correctedChroma, gapTargetChroma, 0.88 * gapOwnership);
            }

            /* IRIS_26732_CONNECTED_INVALID_HIGHLIGHT_CLEANUP
             * 26731 restored transport containment but its isolated fallback was too narrow for short
             * chains/plateaus of clipped highlight chroma. A physically invalid bright center now
             * inherits hue only from a symmetric pair of physically valid same-surface samples. If no
             * such pair exists and the center is nearly white, suppress unsupported chroma rather than
             * allowing a pink/green dotted highlight chain to self-protect. */
            float invalidHighlightCenter = (1.0 - measuredColorProtection) *
                smoothstep(0.58, 0.82, centerLuma);
            if (invalidHighlightPairWeight > 1.0e-6) {
                vec3 invalidHighlightTargetNormalized = invalidHighlightPairChromaSum /
                    invalidHighlightPairWeight;
                vec3 invalidHighlightTarget = invalidHighlightTargetNormalized * centerScale;
                float invalidHighlightAuthority = invalidHighlightCenter *
                    smoothstep(0.48, 0.86, invalidHighlightPairEvidence);
                correctedChroma = mix(correctedChroma, invalidHighlightTarget,
                    0.96 * invalidHighlightAuthority);
            } else {
                float unresolvedInvalidHighlight = invalidHighlightCenter *
                    smoothstep(0.84, 0.97, centerLuma) *
                    (1.0 - smoothstep(0.20, 0.55, invalidHighlightPairEvidence));
                correctedChroma *= 1.0 - 0.82 * unresolvedInvalidHighlight;
            }

            /* IRIS_26741_CLIPPED_FLATTENED_HIGHLIGHT_NEUTRAL_AUTHORITY
             * Chroma denoise is not the owner here. Once bright source information is clipped or
             * flattened, unsupported hue is physically unknowable and must fail neutral. A real
             * bright colored material may opt out only through the independent below-headroom
             * continuation proof above; reconstructed highlight hue cannot prove itself. */
            float clippedFlattenedNeutralAuthority26741 = invalidHighlightCenter *
                smoothstep(0.72, 0.90, centerLuma) *
                (1.0 - physicalHeadroomColorProof26741);
            correctedChroma *= 1.0 - 0.995 * clamp(clippedFlattenedNeutralAuthority26741, 0.0, 1.0);

            /* IRIS_26728_PHYSICALLY_SUPPORTED_CHROMA_MAGNITUDE
             * Restore only missing chroma magnitude along the already-cleaned VGN direction.
             * Pre-VGN RGB never supplies an RGB vector or hue. Strong all-channel CFA validity,
             * strong pre/clean direction agreement and coherent real-color topology are all
             * required. Existing false-color/phase/neutral-leak authorities and highlights veto.
             * Alpha carries only the proven pre-VGN magnitude for the later residual-denoise floor. */
            float protectedPreVgnMagnitude = 0.0;
            if (uPhysicalPreVgnValid != 0 && uSabreSupportValid != 0) {
                vec3 preVgnRgb = max(texelFetch(uPhysicalPreVgn, p, 0).rgb, vec3(0.0));
                float preVgnPeak = maximum3(preVgnRgb);
                float preVgnLuma = luminanceOf(preVgnRgb);
                vec3 preVgnChroma = preVgnRgb - vec3(preVgnLuma);
                float preVgnMagnitude = length(preVgnChroma);
                float cleanedMagnitude = length(correctedChroma);
                float cleanedDirectionPresent = smoothstep(0.010, 0.035, cleanedMagnitude);
                float preVgnChromaPresent = smoothstep(0.018, 0.060, preVgnMagnitude);
                float directionAgreement = hueAgreement(preVgnChroma, correctedChroma);
                float measuredProof = smoothstep(0.992, 0.9995, centerMeasuredValidity);
                float directionProof = smoothstep(0.94, 0.985, directionAgreement);
                float topologyProof = smoothstep(0.55, 0.90, realColorConfidence);
                float highlightSafe = 1.0 - smoothstep(0.78, 0.92, max(preVgnPeak, centerLuma));
                float phaseArtifactAuthority = smoothstep(0.68, 0.90,
                    phaseConfidence * neutralSurfaceSupport * (1.0 - realColorConfidence));
                /* IRIS_26733_NEUTRAL_FLOOR_VETO
                 * The residual-denoise magnitude floor must never re-amplify chroma when physically
                 * valid same-surface evidence is neutral. Tiny genuine color keeps the floor through
                 * compact/topological color proof; neutral printed strokes and neutral surfaces do not. */
                float validNeutralConsensus = 1.0 - smoothstep(0.045, 0.115,
                    length(validConsensusNormalizedChroma));
                float neutralFloorVeto = smoothstep(0.72, 0.94, neutralSurfaceSupport) *
                    validNeutralConsensus *
                    (1.0 - smoothstep(0.55, 0.88, physicalRealColorVeto26735));
                /* IRIS_26734_ACHROMATIC_PAIR_RESIDUAL_FLOOR_VETO
                 * A proven neutral pair remains authoritative after residual denoise; the protected
                 * pre-VGN magnitude floor may not repaint chroma into that neutral structure. */
                float neutralPairFloorVeto = smoothstep(0.55, 0.86, neutralInkPairEvidence) *
                    (1.0 - smoothstep(0.55, 0.88, physicalRealColorVeto26735));
                neutralFloorVeto = max(neutralFloorVeto, neutralPairFloorVeto);
                float artifactVeto = clamp(max(max(
                    smoothstep(0.65, 0.90, legacyFalseColorScore),
                    smoothstep(0.35, 0.70, physicalFalseColorScore)),
                    max(max(max(validCfaNeutralLeakAuthority, phaseArtifactAuthority), neutralFloorVeto),
                        clippedFlattenedNeutralAuthority26741)),
                    0.0, 1.0);
                float strictPhysicalProof = min(min(measuredProof, directionProof),
                    min(topologyProof, highlightSafe));
                float hardArtifactVeto = step(0.50, artifactVeto);
                float artifactPermission = (1.0 - artifactVeto) * (1.0 - hardArtifactVeto);
                float restorePermission = strictPhysicalProof * cleanedDirectionPresent *
                    preVgnChromaPresent * artifactPermission;
                float missingMagnitude = max(preVgnMagnitude - cleanedMagnitude, 0.0);
                float restoredMagnitude = min(preVgnMagnitude,
                    cleanedMagnitude + missingMagnitude * restorePermission);
                if (cleanedMagnitude > 1.0e-7 && restoredMagnitude > cleanedMagnitude) {
                    correctedChroma *= restoredMagnitude / cleanedMagnitude;
                }
                float floorPermission = smoothstep(0.78, 0.92, restorePermission);
                protectedPreVgnMagnitude = floorPermission >= 0.5 ? preVgnMagnitude : 0.0;
            }

            /* IRIS_26739_NO_POST_HOC_CFA_MOIRE_OWNER
             * CFA alias removal belongs to direct burst reconstruction.  Do not infer or erase
             * real scene color after RGB has already been reconstructed and protected. */

            vec3 correctedRgb = clamp(vec3(centerLuma) + correctedChroma, 0.0, 1.0);

            /* IRIS_26743_VISIBLE_FLATTENED_HIGHLIGHT_NEUTRAL_AUTHORITY
             * This is the final hue owner. It deliberately restores the successful 26727/26728
             * visible headroom hierarchy, but in the correct calculation-WB domain. A region whose
             * rendered/highlight luminance enters 0.72..0.92 progressively loses hue and is fully
             * neutral at the top. An immediate 8-neighbor fringe is included only when that center
             * is already in the inherited 0.58..0.72 bright-transition range. This catches the
             * cyan/magenta seam beside a flattened highlight without touching ordinary-color pixels.
             * No reconstructed hue, topology, micro-object or material owner can override this final
             * visible-highlight rule. HDR magnitude is untouched because 26611 restores it later
             * from uPhysicalPreVgn as one scalar. */
            float visibleCenterLuma26743 = visibleHighlightLuma26743(p);
            float visibleCoreAuthority26743 = smoothstep(0.72, 0.92, visibleCenterLuma26743);
            float neighboringVisibleCore26743 = 0.0;
            const ivec2 highlightNeighbors26743[8] = ivec2[8](
                ivec2(0,-1), ivec2(1,0), ivec2(0,1), ivec2(-1,0),
                ivec2(1,-1), ivec2(1,1), ivec2(-1,1), ivec2(-1,-1));
            for (int i26743 = 0; i26743 < 8; ++i26743) {
                neighboringVisibleCore26743 = max(neighboringVisibleCore26743,
                    smoothstep(0.72, 0.92,
                        visibleHighlightLuma26743(p + highlightNeighbors26743[i26743])));
            }
            float visibleFringeAuthority26743 = neighboringVisibleCore26743 *
                smoothstep(0.58, 0.72, visibleCenterLuma26743);

            /* IRIS_26745_CONNECTED_BRIGHT_FRINGE_COLOR_AUTHORITY
             * Preserve the exact successful 26743 core + immediate-neighbor rule above. The only
             * extension is one additional connected hop: a radius-two highlight core may reach this
             * center only through a radius-one bright-transition sample on the same direction. This
             * closes the multi-pixel marker-outline gap without flooding across a dark separator.
             * This never reconstructs RGB or detail. Independent physical real-color
             * continuation below highlight headroom vetoes only this new radius-two extension. */
            float connectedSecondRingCore26745 = 0.0;
            for (int i26745 = 0; i26745 < 8; ++i26745) {
                ivec2 d26745 = highlightNeighbors26743[i26745];
                float bridgeLuma26745 = visibleHighlightLuma26743(p + d26745);
                float farCore26745 = smoothstep(0.72, 0.92,
                    visibleHighlightLuma26743(p + 2 * d26745));
                float connectedBridge26745 = smoothstep(0.58, 0.72, bridgeLuma26745);
                connectedSecondRingCore26745 = max(connectedSecondRingCore26745,
                    farCore26745 * connectedBridge26745);
            }
            float physicalBrightColorVeto26745 =
                smoothstep(0.55, 0.88, physicalRealColorVeto26735) *
                physicalHeadroomColorProof26741;
            /* IRIS_26747_CONNECTED_UNRECOVERABLE_SECOND_RING_OVERRIDE
             * Keep 26745's radius-two real-color veto for recoverable highlights. If the far core
             * is in the inherited 0.72..0.92 highlight range and its all-channel CFA support is
             * physically exhausted, the 26727 highlight owner wins and the fringe cannot self-protect. */
            float connectedUnrecoverableCore26747 = 0.0;
            for (int i26747 = 0; i26747 < 8; ++i26747) {
                ivec2 d26747 = highlightNeighbors26743[i26747];
                float bridgeLuma26747 = visibleHighlightLuma26743(p + d26747);
                ivec2 farP26747 = p + 2 * d26747;
                float farLuma26747 = visibleHighlightLuma26743(farP26747);
                float farMeasured26747 = minimum3(loadSabreChannelValidity(farP26747));
                float farPhysical26747 = smoothstep(0.985, 0.9995, farMeasured26747);
                float farUnrecoverable26747 = max(
                    smoothstep(0.90, 0.92, farLuma26747),
                    smoothstep(0.72, 0.92, farLuma26747) * (1.0 - farPhysical26747));
                connectedUnrecoverableCore26747 = max(connectedUnrecoverableCore26747,
                    farUnrecoverable26747 * smoothstep(0.58, 0.72, bridgeLuma26747));
            }
            float physicalBrightColorVeto26747 = physicalBrightColorVeto26745 *
                (1.0 - connectedUnrecoverableCore26747);
            float visibleSecondRingFringe26745 = 0.85 * connectedSecondRingCore26745 *
                smoothstep(0.58, 0.72, visibleCenterLuma26743) *
                (1.0 - physicalBrightColorVeto26747);
            float visibleFringeAuthority26745 = max(visibleFringeAuthority26743,
                visibleSecondRingFringe26745);
            float visibleHighlightNeutralAuthority26745 = clamp(max(
                visibleCoreAuthority26743, visibleFringeAuthority26745), 0.0, 1.0);

            /* Neutralize hue after calculation WB, then return only the cleaned direction to camera
             * RGB. Preserve the pre-pass camera-RGB scalar so below-white brightness cannot shift;
             * above-white physical magnitude remains owned by the separate HDR scalar carrier. */
            vec3 correctedCalculationRgb26743 = max(correctedRgb * uCalculationGains, vec3(0.0));
            float correctedCalculationLuma26743 = luminanceOf(correctedCalculationRgb26743);
            vec3 correctedCalculationChroma26743 = correctedCalculationRgb26743 -
                vec3(correctedCalculationLuma26743);
            correctedCalculationChroma26743 *= 1.0 - visibleHighlightNeutralAuthority26745;
            vec3 neutralizedCalculationRgb26743 = max(vec3(correctedCalculationLuma26743) +
                correctedCalculationChroma26743, vec3(0.0));
            vec3 neutralizedCameraRgb26743 = neutralizedCalculationRgb26743 /
                max(uCalculationGains, vec3(1.0e-6));
            float originalCameraPeak26743 = maximum3(correctedRgb);
            float neutralizedCameraPeak26743 = maximum3(neutralizedCameraRgb26743);
            if (originalCameraPeak26743 > 1.0e-7 && neutralizedCameraPeak26743 > 1.0e-7) {
                neutralizedCameraRgb26743 *= originalCameraPeak26743 / neutralizedCameraPeak26743;
            }
            correctedRgb = clamp(neutralizedCameraRgb26743, 0.0, 1.0);
            protectedPreVgnMagnitude *= 1.0 - visibleHighlightNeutralAuthority26745;

            uvec3 encodedRgb = uvec3(round(correctedRgb * 65535.0));
            uint encodedProtection = uPhysicalPreVgnValid != 0
                ? uint(round(clamp(protectedPreVgnMagnitude, 0.0, 1.0) * 65535.0))
                : 65535u;
            imageStore(uDestination, p, uvec4(encodedRgb, encodedProtection));
        }
    """.trimIndent()

    val seed = """
        #version 310 es
        precision highp float;
        precision highp int;
        precision highp uimage2D;
        layout(local_size_x=8, local_size_y=8) in;
        layout(rgba16ui,binding=0) readonly uniform highp uimage2D uInput;
        layout(rgba16ui,binding=1) writeonly uniform highp uimage2D uOutput;
        uniform vec3 uCalculationGains;
        uniform float uMinimumDirectionGradient;
        $common
        /* IRIS_26730_PHYSICAL_VALIDITY_CONTAINMENT_AUTHORITY
         * The 26729 material-preservation gates may only be established by reconstructed color
         * whose consumed CFA support remains valid in every RGB channel. Clipped/invalid hue may
         * still be repaired later, but it cannot grant itself early VGN ownership. */
        uniform highp sampler2D uSabreWeightR;
        uniform highp sampler2D uSabreWeightsGb;
        uniform highp sampler2D uSabreValidWeights;
        uniform highp float uSabreValidityWeightScale;
        uniform int uSabreSupportValid;
        float physicalColorTrust(ivec2 p){
            if(uSabreSupportValid==0)return 1.0;
            ivec2 q=safePos(p);
            vec3 totalWeight=vec3(max(texelFetch(uSabreWeightR,q,0).r,0.0),max(texelFetch(uSabreWeightsGb,q,0).r,0.0),max(texelFetch(uSabreWeightsGb,q,0).g,0.0));
            vec3 validWeight=max(texelFetch(uSabreValidWeights,q,0).rgb,vec3(0.0))*max(uSabreValidityWeightScale,1.0);
            vec3 channelValidity=clamp(validWeight/max(totalWeight,vec3(1.0e-6)),vec3(0.0),vec3(1.0));
            float measured=min(channelValidity.r,min(channelValidity.g,channelValidity.b));
            return smoothstep(0.985,0.9995,measured);
        }
        vec3 calculationRgbAt(ivec2 p) {
            uvec3 e=imageLoad(uInput,safePos(p)).rgb;
            return clamp(vec3(decodeU16(e.r),decodeU16(e.g),decodeU16(e.b))*uCalculationGains,vec3(0.0),vec3(65504.0));
        }
        float yAt(ivec2 p){ return dot(calculationRgbAt(p),vec3(0.25,0.5,0.25)); }
        vec2 materialChromaAt(ivec2 p){
            vec3 rgb=calculationRgbAt(p);
            float sum=max(rgb.r+2.0*rgb.g+rgb.b,1.0);
            return (rgb.rb-vec2(rgb.g))/sum;
        }
        uint directionMaskAt(ivec2 p){
            const ivec2 d[8]=ivec2[8](ivec2(0,-1),ivec2(1,0),ivec2(0,1),ivec2(-1,0),ivec2(1,-1),ivec2(1,1),ivec2(-1,1),ivec2(-1,-1));
            float center=yAt(p); vec2 centerChroma=materialChromaAt(p);
            float centerChromaMagnitude=length(centerChroma);
            float g[8]; float chromaJump[8]; float neighborContinuation[8]; float neighborWithinDelta[8];
            float neighborNeutral[8]; float neighborY[8]; float neighborTrust26734[8];
            float neighborPhysicalColor26735[8];
            float lo=65504.0; float hi=0.0; float centerContinuation=0.0; float centerWithinDelta=65504.0;
            float brighterNeutralSupport=0.0;
            /* IRIS_26739_WRONSKI_OWNS_CFA_ALIAS_REMOVAL
             * Retire the 26737 post-reconstruction periodic-chroma classifier. CFA aliasing must
             * disappear through multi-frame RAW reconstruction, never by guessing scene color. */
            /* IRIS_26735_PHYSICAL_COLOR_CONTINUATION_VETO
             * Neutral ownership may ignore a contaminated center hue, but it must still preserve
             * genuine colored strokes whose non-neutral color is independently supported by valid
             * near/far CFA-backed samples along the material. */
            float physicalColorContinuation26735=0.0;
            float physicalHeadroomColorContinuation26741=0.0;
            float centerTrust=physicalColorTrust(p);
            /* IRIS_26747_SEED_CONNECTED_UNRECOVERABLE_HIGHLIGHT_OWNER */
            float connectedUnrecoverableHighlight26747=0.0;
            for(int i=0;i<8;++i){
                float first=yAt(p+d[i]); float second=yAt(p+d[i]*2);
                neighborY[i]=first;
                vec2 firstChroma=materialChromaAt(p+d[i]);
                vec2 secondChroma=materialChromaAt(p+d[i]*2);
                float rgbGradient=abs(center-first)+0.5*abs(first-second);
                g[i]=rgbGradient; lo=min(lo,g[i]); hi=max(hi,g[i]);
                chromaJump[i]=length(centerChroma-firstChroma);
                neighborWithinDelta[i]=length(firstChroma-secondChroma);
                neighborContinuation[i]=1.0-smoothstep(0.020,0.070,neighborWithinDelta[i]);
                neighborNeutral[i]=1.0-smoothstep(0.055,0.140,length(firstChroma));
                float relativeFirst=(first-center)/max(max(first,center),3930.0);
                float lumaCompatible=1.0-smoothstep(0.10,0.30,abs(relativeFirst));
                float neighborTrust=physicalColorTrust(p+d[i]);
                float secondTrust=physicalColorTrust(p+d[i]*2);
                float centerBrightBridge26747=smoothstep(0.58,0.72,clamp(center/65504.0,0.0,1.0));
                float firstNormalized26747=clamp(first/65504.0,0.0,1.0);
                float secondNormalized26747=clamp(second/65504.0,0.0,1.0);
                float firstUnrecoverable26747=max(
                    smoothstep(0.90,0.92,firstNormalized26747),
                    smoothstep(0.72,0.92,firstNormalized26747)*(1.0-neighborTrust));
                float secondUnrecoverable26747=max(
                    smoothstep(0.90,0.92,secondNormalized26747),
                    smoothstep(0.72,0.92,secondNormalized26747)*(1.0-secondTrust));
                connectedUnrecoverableHighlight26747=max(connectedUnrecoverableHighlight26747,
                    centerBrightBridge26747*max(firstUnrecoverable26747,secondUnrecoverable26747));
                neighborTrust26734[i]=neighborTrust;
                float firstMagnitude=length(firstChroma);
                float secondMagnitude=length(secondChroma);
                float chainHue=dot(firstChroma,secondChroma)/
                    max(firstMagnitude*secondMagnitude,1.0e-6);
                float chainLuma=1.0-smoothstep(0.10,0.30,
                    abs(first-second)/max(max(first,second),3930.0));
                float chainColor=smoothstep(0.080,0.160,min(firstMagnitude,secondMagnitude))*
                    smoothstep(0.88,0.97,chainHue)*chainLuma*min(neighborTrust,secondTrust);
                physicalColorContinuation26735=max(physicalColorContinuation26735,chainColor);
                float secondHeadroom26741=1.0-smoothstep(0.76,0.90,second/65504.0);
                physicalHeadroomColorContinuation26741=max(physicalHeadroomColorContinuation26741,
                    chainColor*secondHeadroom26741);
                neighborPhysicalColor26735[i]=neighborTrust*
                    smoothstep(0.080,0.160,firstMagnitude);
                float trustedCenterNeighbor=min(centerTrust,neighborTrust);
                brighterNeutralSupport+=neighborNeutral[i]*smoothstep(0.08,0.35,relativeFirst)*neighborTrust;
                centerWithinDelta=min(centerWithinDelta,mix(65504.0,chromaJump[i],trustedCenterNeighbor));
                centerContinuation=max(centerContinuation,lumaCompatible*(1.0-smoothstep(0.020,0.070,chromaJump[i]))*trustedCenterNeighbor);
            }
            float threshold=max(uMinimumDirectionGradient,1.5*lo+0.09375*(hi-lo));
            /* IRIS_26733_INHERITED_HIGHLIGHT_HEADROOM_OWNER
             * The successful 26727/26728 rule is authoritative before any 26729+ material gate:
             * near-white color ownership fades from 0.72..0.92 luma. A real bright colored material
             * may opt back in only with strong all-channel physical support, substantial normalized
             * chroma and coherent same-material continuation. */
            float centerNormalizedY=clamp(center/65504.0,0.0,1.0);
            float inheritedHighlightPermission=1.0-smoothstep(0.72,0.92,centerNormalizedY);
            /* IRIS_26740_BRIGHT_COLOR_REQUIRES_INDEPENDENT_PHYSICAL_CONTINUATION
             * Keep the 26729+ color gains, but do not let a coherent reconstructed highlight fringe
             * opt itself back into color ownership. Bright color may bypass the inherited 26727/26728
             * headroom veto only when valid same-material color continues independently away from
             * the center. Ordinary non-highlight color ownership is unchanged. */
            float realBrightColorProof=centerTrust*
                smoothstep(0.10,0.18,centerChromaMagnitude)*
                smoothstep(0.55,0.82,centerContinuation)*
                smoothstep(0.62,0.90,physicalColorContinuation26735)*
                smoothstep(0.50,0.82,physicalHeadroomColorContinuation26741);
            /* IRIS_26747_FULL_26727_UNRECOVERABLE_HEADROOM_VETO_SEED
             * Keep the 26745 opt-back-in proof for recoverable color, but never let a physically
             * exhausted bright core or its connected bright-transition fringe seed the 26729+
             * color-only material owners. Bit 15 freezes that local fallback for later VGN stages. */
            float centerUnrecoverableHighlight26747=max(
                smoothstep(0.90,0.92,centerNormalizedY),
                smoothstep(0.72,0.92,centerNormalizedY)*(1.0-centerTrust));
            connectedUnrecoverableHighlight26747=clamp(max(
                connectedUnrecoverableHighlight26747,centerUnrecoverableHighlight26747),0.0,1.0);
            realBrightColorProof*=1.0-connectedUnrecoverableHighlight26747;
            float highlightColorOwnershipPermission=max(inheritedHighlightPermission,realBrightColorProof);
            int highlightInvalidCleanup=(1.0-highlightColorOwnershipPermission)>0.35?1:0;
            int legacy26727HighlightMode26747=connectedUnrecoverableHighlight26747>0.35?1:0;
            /* IRIS_26733_EARLY_ACHROMATIC_STRUCTURE_OWNER
             * Dark/antialiased neutral strokes are recognized before chroma filtering from a neutral
             * center plus multiple physically trustworthy brighter neutral neighbors. This is a
             * generic structural/material rule (text, wire, mesh, line art), not OCR. */
            float neutralCenterProof=(1.0-smoothstep(0.070,0.160,centerChromaMagnitude))*centerTrust;
            float neutralDarkPermission=1.0-smoothstep(0.42,0.62,centerNormalizedY);
            float neutralLegacyProof=neutralCenterProof*neutralDarkPermission*
                smoothstep(1.25,3.00,brighterNeutralSupport);
            /* IRIS_26734_EARLY_POLARITY_INDEPENDENT_ACHROMATIC_OWNER
             * Preserve the 26733 dark-center branch, then add a strict symmetric neutral-pair proof
             * for either luma polarity. The center may contain bounded reconstructed false chroma;
             * the pair itself must be physically trusted and neutral. */
            const int pairA26734[4]=int[4](0,1,4,5);
            const int pairB26734[4]=int[4](2,3,6,7);
            float neutralOppositePair26734=0.0;
            for(int j=0;j<4;++j){
                int a=pairA26734[j],b=pairB26734[j];
                float relA=(neighborY[a]-center)/max(max(neighborY[a],center),3930.0);
                float relB=(neighborY[b]-center)/max(max(neighborY[b],center),3930.0);
                float brightPair=smoothstep(0.08,0.35,relA)*smoothstep(0.08,0.35,relB);
                float darkPair=smoothstep(0.08,0.35,-relA)*smoothstep(0.08,0.35,-relB);
                /* IRIS_26735_NEUTRAL_EDGE_BRACKET_OWNER
                 * Edge pixels of black-on-white/white-on-black structure normally have one dark
                 * and one bright side, so requiring both neighbors to share the center polarity
                 * misses exactly the colored text fringes seen in 26734. A physically trusted
                 * neutral opposing pair may therefore own the transition when its endpoints span
                 * a real luma edge. Center chroma is intentionally not a permission input. */
                float pairSpan=abs(neighborY[a]-neighborY[b])/
                    max(max(neighborY[a],neighborY[b]),3930.0);
                float edgeBracket=smoothstep(0.08,0.30,pairSpan)*
                    max(smoothstep(0.08,0.35,abs(relA)),smoothstep(0.08,0.35,abs(relB)));
                float pairNeutral=neighborNeutral[a]*neighborNeutral[b];
                float pairTrust=min(neighborTrust26734[a],neighborTrust26734[b]);
                neutralOppositePair26734=max(neutralOppositePair26734,
                    max(max(brightPair,darkPair),edgeBracket)*pairNeutral*pairTrust);
            }
            float horizontalColor26735=max(neighborPhysicalColor26735[1],neighborPhysicalColor26735[3]);
            float verticalColor26735=max(neighborPhysicalColor26735[0],neighborPhysicalColor26735[2]);
            float diagonalAColor26735=max(neighborPhysicalColor26735[4],neighborPhysicalColor26735[6]);
            float diagonalBColor26735=max(neighborPhysicalColor26735[5],neighborPhysicalColor26735[7]);
            float compactTwoAxisColor26735=max(max(horizontalColor26735*verticalColor26735,
                diagonalAColor26735*diagonalBColor26735),
                max(horizontalColor26735,verticalColor26735)*
                    max(diagonalAColor26735,diagonalBColor26735));
            float physicalCompactColorSeed26735=centerTrust*
                smoothstep(0.10,0.18,centerChromaMagnitude)*
                smoothstep(0.24,0.62,compactTwoAxisColor26735);
            /* IRIS_26735_CENTER_CHROMA_CANNOT_DISQUALIFY_NEUTRAL_STRUCTURE
             * 26734 still faded neutral ownership once reconstructed center chroma reached 0.10..0.18.
             * The two supplied 26734 sets prove that strong green/magenta contamination can exceed
             * that threshold and thereby self-protect. Neutral ownership now comes from the trusted
             * surrounding material/luma topology; only independently continued or compact physical
             * color may veto it, preserving true colored text/logos/micro-objects. */
            float physicalColorVetoSeed26735=max(physicalColorContinuation26735,
                physicalCompactColorSeed26735);
            float neutralPairProof26735=centerTrust*
                smoothstep(0.52,0.86,neutralOppositePair26734)*
                (1.0-smoothstep(0.58,0.90,physicalColorVetoSeed26735));
            float neutralStructureProof=max(neutralLegacyProof,neutralPairProof26735);
            int neutralStructure=neutralStructureProof>0.50?1:0;
            int mask=0; int count=0; int cleanupFallback=0;
            for(int i=0;i<8;++i){
                /* IRIS_26729_COLOR_MATERIAL_DIRECTION_GATE
                 * A coherent color boundary blocks chroma transport even when luma is nearly equal.
                 * Isolated false-color dots do not gain protection because the center must continue
                 * coherently in at least one other direction and the neighboring material must also
                 * continue away from the boundary. */
                float physicalTrust=min(centerTrust,min(physicalColorTrust(p+d[i]),physicalColorTrust(p+d[i]*2)));
                float withinScale=max(max(centerWithinDelta,neighborWithinDelta[i]),0.006);
                float materialStepProof=smoothstep(1.35,2.20,chromaJump[i]/withinScale);
                /* IRIS_26730_TRUE_MATERIAL_STEP_GATE: a smooth within-material hue gradient is not
                 * a boundary. Both sides must be more internally coherent than the interface jump. */
                float colorBoundary=smoothstep(0.030,0.095,chromaJump[i]) *
                    smoothstep(0.35,0.75,centerContinuation) * neighborContinuation[i] *
                    materialStepProof * physicalTrust * highlightColorOwnershipPermission *
                    (1.0-float(legacy26727HighlightMode26747));
                if(neutralStructure!=0)colorBoundary=max(colorBoundary,1.0-neighborNeutral[i]);
                if(g[i]<=threshold&&colorBoundary<0.50){ mask|=1<<i; count++; }
            }
            if(count==0){
                /* IRIS_26747_EXACT_26727_DIRECTION_FALLBACK
                 * Around a connected unrecoverable highlight, retire only the 26729 color-only
                 * all-directions-blocked behavior and restore the successful 26727 all-direction
                 * fallback. Recoverable material color keeps the modern 26745 behavior. */
                if(legacy26727HighlightMode26747!=0){mask=0xFF;count=8;cleanupFallback=0;}
                else if(centerContinuation>0.35){mask=0;count=0;}
                else{mask=0xFF;count=8;cleanupFallback=1;}
            }
            /* IRIS_26731_ISOLATED_FALSE_COLOR_CLEANUP_FLAG
             * Bit 12 distinguishes the inherited all-direction cleanup fallback from genuine
             * all-direction same-material connectivity. Downstream filters may pull trusted color
             * into this suspicious center, but trusted neighbors must never pull from it. */
            return uint(mask | (count << 8) | (cleanupFallback << 12) |
                (highlightInvalidCleanup << 13) | (neutralStructure << 14) |
                (legacy26727HighlightMode26747 << 15));
        }
        uvec4 toYccd(vec3 rgb,uint direction){
            float sum=rgb.r+2.0*rgb.g+rgb.b+1.0;
            vec2 c=(rgb.rb-vec2(rgb.g))*(32768.0/sum);
            ivec2 ci=ivec2(clamp(c,vec2(-32768.0),vec2(32767.0)));
            return uvec4(uint(clamp(0.25*(sum-1.0),0.0,65504.0)),unsignedChroma(ci.x),unsignedChroma(ci.y),direction);
        }
        void main(){ ivec2 p=ivec2(gl_GlobalInvocationID.xy); if(any(greaterThanEqual(p,uImageSize)))return; imageStore(uOutput,p,toYccd(calculationRgbAt(p),directionMaskAt(p))); }
    """.trimIndent()

    val localClamp = """
        #version 310 es
        precision highp int; precision highp uimage2D;
        layout(local_size_x=8,local_size_y=8) in;
        layout(rgba16ui,binding=0) readonly uniform highp uimage2D uInput;
        layout(rgba16ui,binding=1) writeonly uniform highp uimage2D uOutput;
        $common
        /* IRIS_26570_ONE_SIDED_EDGE_LUMA_AUTHORITY
         * VGN is a color-noise stage. A thin dark/bright structure is allowed to sit outside the
         * eight-neighbor envelope; never fill its luma from the opposite side of a boundary.
         */
        void main(){
            ivec2 p=ivec2(gl_GlobalInvocationID.xy); if(any(greaterThanEqual(p,uImageSize)))return;
            imageStore(uOutput,p,imageLoad(uInput,p));
        }
    """.trimIndent()

    val localMedian = """
        #version 310 es
        precision highp float; precision highp int; precision highp uimage2D;
        layout(local_size_x=8,local_size_y=8) in;
        layout(rgba16ui,binding=0) readonly uniform highp uimage2D uInput;
        layout(rgba16ui,binding=1) writeonly uniform highp uimage2D uOutput;
        uniform float uChromaStrength;
        $common
        /* IRIS_26730_PHYSICAL_VALIDITY_CONTAINMENT_AUTHORITY
         * The 26729 material-preservation gates may only be established by reconstructed color
         * whose consumed CFA support remains valid in every RGB channel. Clipped/invalid hue may
         * still be repaired later, but it cannot grant itself early VGN ownership. */
        uniform highp sampler2D uSabreWeightR;
        uniform highp sampler2D uSabreWeightsGb;
        uniform highp sampler2D uSabreValidWeights;
        uniform highp float uSabreValidityWeightScale;
        uniform int uSabreSupportValid;
        float physicalColorTrust(ivec2 p){
            if(uSabreSupportValid==0)return 1.0;
            ivec2 q=safePos(p);
            vec3 totalWeight=vec3(max(texelFetch(uSabreWeightR,q,0).r,0.0),max(texelFetch(uSabreWeightsGb,q,0).r,0.0),max(texelFetch(uSabreWeightsGb,q,0).g,0.0));
            vec3 validWeight=max(texelFetch(uSabreValidWeights,q,0).rgb,vec3(0.0))*max(uSabreValidityWeightScale,1.0);
            vec3 channelValidity=clamp(validWeight/max(totalWeight,vec3(1.0e-6)),vec3(0.0),vec3(1.0));
            float measured=min(channelValidity.r,min(channelValidity.g,channelValidity.b));
            return smoothstep(0.985,0.9995,measured);
        }
        ivec3 s(ivec2 p){ uvec4 v=imageLoad(uInput,safePos(p)); return ivec3(int(v.r),signedChroma(v.g),signedChroma(v.b)); }
        float chromaAgreement(vec2 a, vec2 b){return dot(a,b)/max(length(a)*length(b),1.0);}
        /* IRIS_26731_FROZEN_RECIPROCAL_MATERIAL_OWNERSHIP
         * Alpha is the 26730 validity-owned seed map. It is immutable through this stage. A
         * neighbor belongs to the same transport region only when both pixels explicitly agree. */
        bool insideImage(ivec2 q){return all(greaterThanEqual(q,ivec2(0)))&&all(lessThan(q,uImageSize));}
        int directionBitForDelta(ivec2 d){
            if(d==ivec2(0,-1))return 0; if(d==ivec2(1,0))return 1;
            if(d==ivec2(0,1))return 2; if(d==ivec2(-1,0))return 3;
            if(d==ivec2(1,-1))return 4; if(d==ivec2(1,1))return 5;
            if(d==ivec2(-1,1))return 6; if(d==ivec2(-1,-1))return 7;
            return -1;
        }
        int oppositeDirectionBit(int bit){
            if(bit==0)return 2; if(bit==1)return 3; if(bit==2)return 0; if(bit==3)return 1;
            if(bit==4)return 6; if(bit==5)return 7; if(bit==6)return 4; if(bit==7)return 5; return -1;
        }
        bool cleanupFallbackAt(ivec2 p){return (int(imageLoad(uInput,p).a)&0x1000)!=0;}
        bool highlightInvalidAt(ivec2 p){return (int(imageLoad(uInput,p).a)&0x2000)!=0;}
        bool neutralStructureAt(ivec2 p){return (int(imageLoad(uInput,p).a)&0x4000)!=0;}
        bool legacy26727HighlightAt26747(ivec2 p){return (int(imageLoad(uInput,p).a)&0x8000)!=0;}
        bool reciprocalConnected(ivec2 centerP,ivec2 delta){
            ivec2 neighborP=centerP+delta; if(!insideImage(neighborP))return false;
            int bit=directionBitForDelta(delta); int opposite=oppositeDirectionBit(bit); if(bit<0||opposite<0)return false;
            int centerMask=int(imageLoad(uInput,centerP).a)&0xFF; int neighborMask=int(imageLoad(uInput,neighborP).a)&0xFF;
            bool centerAllows=(centerMask&(1<<bit))!=0;
            bool centerNeedsCleanup=cleanupFallbackAt(centerP)||highlightInvalidAt(centerP);
            bool neighborNeedsCleanup=cleanupFallbackAt(neighborP)||highlightInvalidAt(neighborP);
            /* IRIS_26732_TRUSTED_ONE_WAY_CLEANUP_TRANSPORT
             * Suspicious/invalid centers may receive from a clean neighbor along their luma-safe
             * direction, but no trusted pixel may ever receive chroma from a suspicious center. */
            if(centerNeedsCleanup)return centerAllows&&!neighborNeedsCleanup;
            if(neighborNeedsCleanup)return false;
            return centerAllows&&(neighborMask&(1<<opposite))!=0;
        }
        void main(){
            ivec2 p=ivec2(gl_GlobalInvocationID.xy); if(any(greaterThanEqual(p,uImageSize)))return;
            ivec3 a=s(p+ivec2(-1,-1)),b=s(p+ivec2(0,-1)),c=s(p+ivec2(1,-1));
            ivec2 row=a.yz+b.yz+c.yz-min(min(a.yz,b.yz),c.yz)-max(max(a.yz,b.yz),c.yz); ivec2 mn=row,mx=row,sum=row;
            a=s(p+ivec2(-1,0));b=s(p);c=s(p+ivec2(1,0)); row=a.yz+b.yz+c.yz-min(min(a.yz,b.yz),c.yz)-max(max(a.yz,b.yz),c.yz); sum+=row; mn=min(mn,row); mx=max(mx,row);
            a=s(p+ivec2(-1,1));b=s(p+ivec2(0,1));c=s(p+ivec2(1,1)); row=a.yz+b.yz+c.yz-min(min(a.yz,b.yz),c.yz)-max(max(a.yz,b.yz),c.yz); sum+=row-min(mn,row)-max(mx,row);
            uvec4 center=imageLoad(uInput,p);
            ivec2 centerChroma=ivec2(signedChroma(center.g),signedChroma(center.b));
            float centerY=float(center.r)/65504.0;
            float maximumRelativeLumaDelta=0.0;
            float colorBoundaryProtection=0.0;
            /* IRIS_26729_COLOR_MATERIAL_MEDIAN_GATE: establish center continuity before
             * deciding which neighbors are allowed to contribute chroma. */
            float centerMaterialContinuation=0.0;
            float centerBestMaterialDelta=65504.0;
            float centerPhysicalTrust=physicalColorTrust(p);
            const ivec2 materialDirections[8]=ivec2[8](ivec2(1,0),ivec2(-1,0),ivec2(0,1),ivec2(0,-1),ivec2(1,1),ivec2(-1,-1),ivec2(1,-1),ivec2(-1,1));
            for(int i=0;i<8;++i){
                uvec4 neighbor=imageLoad(uInput,safePos(p+materialDirections[i]));
                float neighborY=float(neighbor.r)/65504.0;
                vec2 neighborC=vec2(float(signedChroma(neighbor.g)),float(signedChroma(neighbor.b)));
                float lumaDelta=abs(neighborY-centerY)/max(max(neighborY,centerY),0.060);
                float chromaScale=max(max(length(vec2(centerChroma)),length(neighborC)),512.0);
                float chromaDelta=length(vec2(centerChroma)-neighborC)/chromaScale;
                float trustedCenterNeighbor=min(centerPhysicalTrust,physicalColorTrust(p+materialDirections[i]));
                centerBestMaterialDelta=min(centerBestMaterialDelta,mix(65504.0,chromaDelta,trustedCenterNeighbor));
                centerMaterialContinuation=max(centerMaterialContinuation,
                    (1.0-smoothstep(0.10,0.30,lumaDelta))*(1.0-smoothstep(0.18,0.42,chromaDelta))*trustedCenterNeighbor);
            }
            int brighterSide=0;
            int darkerSide=0;
            vec2 brighterChromaSum=vec2(0.0);
            vec2 darkerChromaSum=vec2(0.0);
            vec2 trustedCleanupChromaSum=vec2(0.0);
            float trustedCleanupWeight=0.0;
            vec2 neutralCleanupChromaSum=vec2(0.0);
            float neutralCleanupWeight=0.0;
            bool centerCleanup=cleanupFallbackAt(p);
            bool centerHighlightInvalid=highlightInvalidAt(p);
            bool centerNeutralStructure=neutralStructureAt(p);
            bool centerLegacy26727Highlight26747=legacy26727HighlightAt26747(p);
            for(int y=-1;y<=1;++y)for(int x=-1;x<=1;++x){
                if(x==0&&y==0)continue;
                uvec4 neighbor=imageLoad(uInput,safePos(p+ivec2(x,y)));
                float neighborY=float(neighbor.r)/65504.0;
                float scale=max(max(centerY,neighborY),0.060);
                float signedDelta=(neighborY-centerY)/scale;
                maximumRelativeLumaDelta=max(maximumRelativeLumaDelta,abs(signedDelta));
                vec2 neighborChroma=vec2(float(signedChroma(neighbor.g)),float(signedChroma(neighbor.b)));
                float localChromaScale=max(max(length(vec2(centerChroma)),length(neighborChroma)),512.0);
                float localChromaJump=length(vec2(centerChroma)-neighborChroma)/localChromaScale;
                ivec2 delta=ivec2(x,y);
                if((centerCleanup||centerHighlightInvalid)&&reciprocalConnected(p,delta)){
                    float trustedNeighbor=physicalColorTrust(p+delta);
                    float sameSurface=1.0-smoothstep(0.14,0.48,abs(signedDelta));
                    float cleanupWeight=trustedNeighbor*sameSurface;
                    trustedCleanupChromaSum+=neighborChroma*cleanupWeight;
                    trustedCleanupWeight+=cleanupWeight;
                }
                if(centerNeutralStructure||centerHighlightInvalid){
                    float trustedNeighbor=physicalColorTrust(p+delta);
                    float neutralNeighbor=1.0-smoothstep(1800.0,4600.0,length(neighborChroma));
                    float neutralWeight=trustedNeighbor*neutralNeighbor;
                    neutralCleanupChromaSum+=neighborChroma*neutralWeight;
                    neutralCleanupWeight+=neutralWeight;
                }
                /* A precomputed 3x3 median is never allowed to cross a frozen ownership edge.
                 * At such pixels the median strength is forced to zero; the following directional
                 * stage can still denoise along reciprocally connected same-material directions. */
                if(!reciprocalConnected(p,delta)){colorBoundaryProtection=1.0;continue;}
                uvec4 farPixel=imageLoad(uInput,safePos(p+delta*2));
                vec2 farChroma=vec2(float(signedChroma(farPixel.g)),float(signedChroma(farPixel.b)));
                float farScale=max(max(length(neighborChroma),length(farChroma)),512.0);
                float neighborWithinDelta=length(neighborChroma-farChroma)/farScale;
                float neighborContinuation=1.0-smoothstep(0.18,0.42,neighborWithinDelta);
                float physicalTrust=min(centerPhysicalTrust,min(physicalColorTrust(p+delta),physicalColorTrust(p+delta*2)));
                float withinScale=max(max(centerBestMaterialDelta,neighborWithinDelta),0.060);
                float materialStepProof=smoothstep(1.35,2.20,localChromaJump/withinScale);
                float ownershipColorPermission=(centerHighlightInvalid||centerNeutralStructure||
                    centerLegacy26727Highlight26747)?0.0:1.0;
                float colorMaterialBoundary=smoothstep(0.35,0.70,localChromaJump)*
                    smoothstep(0.35,0.75,centerMaterialContinuation)*neighborContinuation*
                    materialStepProof*physicalTrust*ownershipColorPermission;
                colorBoundaryProtection=max(colorBoundaryProtection,colorMaterialBoundary);
                /* Cross-material neighbors do not participate in the side statistics. The final
                 * strength veto below also blocks the precomputed 3x3 median itself. */
                if(colorMaterialBoundary>0.50)continue;
                if(signedDelta>0.16){brighterSide++;brighterChromaSum+=neighborChroma;}
                if(signedDelta<-0.16){darkerSide++;darkerChromaSum+=neighborChroma;}
            }
            float oneSidedProtection=((brighterSide>=6&&darkerSide<=1)||(darkerSide>=6&&brighterSide<=1))?1.0:0.0;
            float sideCount=0.0;
            vec2 sideChroma=vec2(0.0);
            if(brighterSide>=4&&darkerSide<=1){sideCount=float(brighterSide);sideChroma=brighterChromaSum/max(sideCount,1.0);}
            if(darkerSide>=4&&brighterSide<=1){sideCount=float(darkerSide);sideChroma=darkerChromaSum/max(sideCount,1.0);}
            float sideAgreement=sideCount>0.0?clamp(chromaAgreement(vec2(centerChroma),sideChroma),-1.0,1.0):1.0;
            float highlightPreservePermission=1.0-smoothstep(0.72,0.92,centerY);
            float materialBoundary=(sideCount>0.0?1.0:0.0)*
                (1.0-smoothstep(0.72,0.92,sideAgreement))*highlightPreservePermission;
            float legacyEdge=smoothstep(0.45,0.90,maximumRelativeLumaDelta);
            float topologySupport=0.0;
            if(centerY>0.58||sideCount>0.0||legacyEdge>0.25){
                const ivec2 td[8]=ivec2[8](ivec2(1,0),ivec2(-1,0),ivec2(0,1),ivec2(0,-1),ivec2(1,1),ivec2(-1,-1),ivec2(1,-1),ivec2(-1,1));
                float centerMagnitude=max(length(vec2(centerChroma)),1.0);
                for(int i=0;i<8;++i){
                    uvec4 farPixel=imageLoad(uInput,safePos(p+td[i]*2));
                    float farY=float(farPixel.r)/65504.0;
                    float farDelta=abs(farY-centerY)/max(max(farY,centerY),0.060);
                    vec2 farChroma=vec2(float(signedChroma(farPixel.g)),float(signedChroma(farPixel.b)));
                    float farAgreement=clamp(chromaAgreement(vec2(centerChroma),farChroma),-1.0,1.0);
                    float sameLuma=1.0-smoothstep(0.10,0.26,farDelta);
                    float centerChromaPresent=smoothstep(128.0,512.0,centerMagnitude);
                    float sameHue=smoothstep(0.82,0.94,farAgreement);
                    topologySupport+=sameLuma*mix(1.0,sameHue,centerChromaPresent);
                }
            }
            float topologyProtection=smoothstep(1.25,2.75,topologySupport)*
                smoothstep(0.20,0.55,max(legacyEdge,sideCount>0.0?1.0:0.0));
            float colorOwnershipPermission=(centerHighlightInvalid||centerNeutralStructure)?0.0:1.0;
            topologyProtection*=colorOwnershipPermission;
            colorBoundaryProtection*=colorOwnershipPermission;
            float edgeProtection=max(max(max(max(oneSidedProtection,materialBoundary),legacyEdge),topologyProtection),
                smoothstep(0.35,0.65,colorBoundaryProtection));
            float strength=clamp(uChromaStrength,0.0,1.0)*(1.0-edgeProtection);
            vec2 correctedFloat=strength<=0.0001?vec2(centerChroma):mix(vec2(centerChroma),vec2(sum),strength);
            /* IRIS_26732_CLUSTER_CLEANUP_WITHOUT_COLOR_LOSS
             * 26731 intentionally blocked cross-material medians. For an explicitly suspicious or
             * physically-invalid bright center, recover cleanup only from trustworthy luma-compatible
             * neighbors. Real colored microstructure never enters this path unless its CFA support is
             * physically invalid or the inherited isolated-artifact proof already fired. */
            if(centerHighlightInvalid){
                /* IRIS_26741_INVALID_HIGHLIGHT_NEUTRAL_DONOR_ONLY
                 * A clipped/flattened highlight may borrow only already-neutral trusted chroma.
                 * Colored neighboring highlight fringes can no longer propagate through cleanup. */
                vec2 highlightNeutralTarget=neutralCleanupWeight>0.50
                    ? neutralCleanupChromaSum/max(neutralCleanupWeight,1.0e-6) : vec2(0.0);
                correctedFloat=mix(correctedFloat,highlightNeutralTarget,0.995);
            }else if(centerCleanup&&trustedCleanupWeight>0.35){
                vec2 trustedTarget=trustedCleanupChromaSum/max(trustedCleanupWeight,1.0e-6);
                correctedFloat=mix(correctedFloat,trustedTarget,0.78);
            }
            if(centerNeutralStructure){
                /* IRIS_26733_ACHROMATIC_STRUCTURE_CLEANUP
                 * Luma/shape is untouched. Only chroma moves toward trustworthy neutral neighbors;
                 * if none exist despite the seed proof, fail achromatic rather than importing color. */
                vec2 neutralTarget=neutralCleanupWeight>0.75
                    ? neutralCleanupChromaSum/max(neutralCleanupWeight,1.0e-6) : vec2(0.0);
                correctedFloat=mix(correctedFloat,neutralTarget,0.99);
            }
            ivec2 corrected=ivec2(round(correctedFloat));
            /* IRIS_26571_CROSS_EDGE_CHROMA_OWNERSHIP
             * 26570 luma pass-through is preserved. Median chroma cleanup is additionally blocked
             * at moderate one-sided material/color boundaries, preventing sky color from entering
             * foliage or any other subject edge without weakening interior surface cleanup.
             */
            imageStore(uOutput,p,uvec4(
                center.r,
                unsignedChroma(corrected.x),
                unsignedChroma(corrected.y),
                center.a
            ));
        }
    """.trimIndent()

    val directionalSmooth = """
        #version 310 es
        precision highp float; precision highp int; precision highp uimage2D;
        layout(local_size_x=8,local_size_y=8) in;
        layout(rgba16ui,binding=0) readonly uniform highp uimage2D uOriginal;
        layout(rgba16ui,binding=1) readonly uniform highp uimage2D uSmooth;
        layout(rgba16ui,binding=2) writeonly uniform highp uimage2D uOutput;
        $common
        vec3 smoothAt(ivec2 p){uvec4 v=imageLoad(uSmooth,safePos(p));return vec3(decodeU16(v.r),float(signedChroma(v.g)),float(signedChroma(v.b)));}
        float chromaAgreement(vec2 a,vec2 b){return dot(a,b)/max(length(a)*length(b),1.0);}
        bool insideImage(ivec2 q){return all(greaterThanEqual(q,ivec2(0)))&&all(lessThan(q,uImageSize));}
        bool directionBitSet(ivec2 p,int bit){return (int(imageLoad(uOriginal,p).a)&(1<<bit))!=0;}
        bool cleanupFallbackAt(ivec2 p){return (int(imageLoad(uOriginal,p).a)&0x1000)!=0;}
        bool highlightInvalidAt(ivec2 p){return (int(imageLoad(uOriginal,p).a)&0x2000)!=0;}
        bool neutralStructureAt(ivec2 p){return (int(imageLoad(uOriginal,p).a)&0x4000)!=0;}
        bool reciprocalConnected(ivec2 p,ivec2 delta,int bit,int oppositeBit){
            ivec2 q=p+delta; if(!insideImage(q))return false;
            bool centerAllows=directionBitSet(p,bit);
            bool centerNeedsCleanup=cleanupFallbackAt(p)||highlightInvalidAt(p);
            bool neighborNeedsCleanup=cleanupFallbackAt(q)||highlightInvalidAt(q);
            if(centerNeedsCleanup)return centerAllows&&!neighborNeedsCleanup;
            if(neighborNeedsCleanup)return false;
            return centerAllows&&directionBitSet(q,oppositeBit);
        }
        /* IRIS_26731_DIRECTION_PAIR_GEOMETRY
         * Seed bits are N=0,E=1,S=2,W=3,NE=4,SE=5,SW=6,NW=7. Opposite
         * geometric filters therefore are W/E=(3,1), N/S=(0,2), NE/SW=(4,6),
         * and NW/SE=(7,5). Never reinterpret adjacent bit numbers as a pair. */
        vec3 pairCandidate(ivec2 p,vec3 center,ivec2 negDelta,int negBit,int negOpp,
            ivec2 posDelta,int posBit,int posOpp,out float sampleWeight){
            bool negOk=reciprocalConnected(p,negDelta,negBit,negOpp);
            bool posOk=reciprocalConnected(p,posDelta,posBit,posOpp);
            sampleWeight=float((negOk?1:0)+(posOk?1:0));
            if(sampleWeight<0.5)return vec3(center.y,center.z,0.0);
            vec3 directional;
            if(negOk&&posOk){
                vec3 x=smoothAt(p+negDelta),y=smoothAt(p+posDelta);
                float dx=dot(abs(center-x),vec3(1.0/6.0));
                float dy=dot(abs(center-y),vec3(1.0/6.0));
                float total=dx+dy;
                directional=total!=0.0?(x*dy+y*dx)/total:(x+y)*0.5;
            }else{
                directional=smoothAt(p+(negOk?negDelta:posDelta));
            }
            float scale=min(abs(center.x-directional.x)/max(center.x+directional.x,1.0)*2.0,1.0);
            return vec3(mix(center.y,directional.y,scale),mix(center.z,directional.z,scale),scale);
        }
        vec4 filter3(uvec4 encoded,ivec2 p){
            vec3 center=vec3(decodeU16(encoded.r),float(signedChroma(encoded.g)),float(signedChroma(encoded.b)));
            vec3 selected=vec3(0.0); float totalWeight=0.0; float minActiveScale=1.0;
            float w; vec3 candidate;
            /* IRIS_26731_RECIPROCAL_ONE_SIDED_DIRECTIONAL
             * Each opposite-axis candidate consumes only sides that are reciprocally owned. If one
             * side is blocked, it contributes exactly zero; the safe side becomes a one-sided
             * estimate rather than pulling chroma through the material boundary. */
            candidate=pairCandidate(p,center,ivec2(-1,0),3,1,ivec2(1,0),1,3,w);
            if(w>0.0){selected+=candidate*w;totalWeight+=w;minActiveScale=min(minActiveScale,candidate.z);}
            candidate=pairCandidate(p,center,ivec2(0,-1),0,2,ivec2(0,1),2,0,w);
            if(w>0.0){selected+=candidate*w;totalWeight+=w;minActiveScale=min(minActiveScale,candidate.z);}
            candidate=pairCandidate(p,center,ivec2(1,-1),4,6,ivec2(-1,1),6,4,w);
            if(w>0.0){selected+=candidate*w;totalWeight+=w;minActiveScale=min(minActiveScale,candidate.z);}
            candidate=pairCandidate(p,center,ivec2(-1,-1),7,5,ivec2(1,1),5,7,w);
            if(w>0.0){selected+=candidate*w;totalWeight+=w;minActiveScale=min(minActiveScale,candidate.z);}
            if(totalWeight<=0.0)return vec4(center.x,center.y,center.z,0.0);
            selected/=totalWeight;
            float yScale=clamp(1.0-center.x/16384.0*minActiveScale,0.0,1.0);
            return vec4(center.x,yScale*selected.x,yScale*selected.y,selected.z*65504.0);
        }
        void main(){
            ivec2 p=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(p,uImageSize)))return;
            uvec4 e=imageLoad(uOriginal,p);vec4 f=vec4(decodeU16(e.r),float(signedChroma(e.g)),float(signedChroma(e.b)),0.0);
            if(e.r!=0u&&(int(e.a)&0xFF)!=0)f=filter3(e,p);
            uvec4 sm=imageLoad(uSmooth,p);
            vec2 originalChroma=vec2(float(signedChroma(e.g)),float(signedChroma(e.b)));
            vec2 smoothChroma=vec2(float(signedChroma(sm.g)),float(signedChroma(sm.b)));
            vec2 directionalChroma=f.yz;
            vec2 legacyChroma=length(smoothChroma)<length(directionalChroma)?smoothChroma:directionalChroma;

            /* IRIS_26571_DIRECTIONAL_EDGE_CHROMA_FLOOR
             * Preserve the exact 26570 lower-chroma choice in interiors. At a real non-highlight
             * directional edge, prefer the candidate whose hue agrees with the original subject
             * and prevent that candidate from collapsing below 80% of coherent center chroma.
             * The cap is the original center magnitude, so this cannot globally boost saturation.
             */
            float edgeEvidence=clamp(f.w/65504.0,0.0,1.0);
            float centerY=clamp(f.x/65504.0,0.0,1.0);
            float highlightPreservePermission=1.0-smoothstep(0.72,0.92,centerY);
            float topologySupport=0.0;
            if(centerY>0.58||edgeEvidence>0.08){
                const ivec2 td[8]=ivec2[8](ivec2(1,0),ivec2(-1,0),ivec2(0,1),ivec2(0,-1),ivec2(1,1),ivec2(-1,-1),ivec2(1,-1),ivec2(-1,1));
                float centerMagnitude=max(length(originalChroma),1.0);
                for(int i=0;i<8;++i){
                    uvec4 farPixel=imageLoad(uOriginal,safePos(p+td[i]*2));
                    float farY=decodeU16(farPixel.r)/65504.0;
                    float farDelta=abs(farY-centerY)/max(max(farY,centerY),0.060);
                    vec2 farChroma=vec2(float(signedChroma(farPixel.g)),float(signedChroma(farPixel.b)));
                    float farAgreement=clamp(chromaAgreement(originalChroma,farChroma),-1.0,1.0);
                    float sameLuma=1.0-smoothstep(0.10,0.26,farDelta);
                    float centerChromaPresent=smoothstep(128.0,512.0,centerMagnitude);
                    topologySupport+=sameLuma*mix(1.0,smoothstep(0.82,0.94,farAgreement),centerChromaPresent);
                }
            }
            float topologyProtection=smoothstep(1.25,2.75,topologySupport)*smoothstep(0.08,0.30,edgeEvidence);
            /* IRIS_26732_SUSPICIOUS_CENTER_CANNOT_SELF_PROTECT
             * A pixel explicitly marked for artifact/highlight cleanup cannot use its own reconstructed
             * hue topology to restore that hue after the trusted-neighbor cleanup stage. */
            float suspiciousCenter=(cleanupFallbackAt(p)||highlightInvalidAt(p))?1.0:0.0;
            float neutralCenter=neutralStructureAt(p)?1.0:0.0;
            float originalHuePermission=(1.0-suspiciousCenter)*(1.0-neutralCenter);
            topologyProtection*=originalHuePermission;
            float edgePreserve=max(smoothstep(0.08,0.30,edgeEvidence)*highlightPreservePermission,
                topologyProtection)*originalHuePermission;
            float smoothAgreement=clamp(chromaAgreement(originalChroma,smoothChroma),-1.0,1.0);
            float directionalAgreement=clamp(chromaAgreement(originalChroma,directionalChroma),-1.0,1.0);
            vec2 edgeCandidate=directionalAgreement>=smoothAgreement?directionalChroma:smoothChroma;
            float edgeAgreement=max(smoothAgreement,directionalAgreement);
            float originalMagnitude=length(originalChroma);
            float edgeMagnitude=length(edgeCandidate);
            if(originalMagnitude>192.0&&edgeMagnitude>1.0&&edgeAgreement>0.82&&neutralCenter<0.5){
                float protectedMagnitude=clamp(edgeMagnitude,0.80*originalMagnitude,originalMagnitude);
                edgeCandidate*=protectedMagnitude/edgeMagnitude;
            }
            float coherentEdge=smoothstep(0.72,0.92,edgeAgreement);
            vec2 selectedChroma=mix(legacyChroma,edgeCandidate,edgePreserve*coherentEdge);
            selectedChroma=mix(selectedChroma,originalChroma,0.85*topologyProtection);
            ivec2 encodedChroma=ivec2(round(selectedChroma));
            imageStore(uOutput,p,uvec4(uint(clamp(f.x,0.0,65504.0)),unsignedChroma(encodedChroma.x),unsignedChroma(encodedChroma.y),uint(clamp(f.w,0.0,65504.0))));
        }
    """.trimIndent()

    val restoreDirection = """
        #version 310 es
        precision highp int; precision highp uimage2D;
        layout(local_size_x=8,local_size_y=8) in;
        layout(rgba16ui,binding=0) readonly uniform highp uimage2D uSmooth;
        layout(rgba16ui,binding=1) readonly uniform highp uimage2D uDirectional;
        layout(rgba16ui,binding=2) writeonly uniform highp uimage2D uOutput;
        $common
        void main(){ivec2 p=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(p,uImageSize)))return;uvec4 v=imageLoad(uSmooth,p);v.a=imageLoad(uDirectional,p).a;imageStore(uOutput,p,v);}
    """.trimIndent()

    val iirRgb = """
        #version 310 es
        precision highp float; precision highp int; precision highp uimage2D;
        layout(local_size_x=1,local_size_y=1) in;
        layout(rgba16ui,binding=0) readonly uniform highp uimage2D uInput;
        layout(rgba16ui,binding=1) writeonly uniform highp uimage2D uOutput;
        layout(rgba16ui,binding=2) readonly uniform highp uimage2D uOwnership;
        uniform vec4 uA10;uniform vec4 uB10;uniform vec4 uADyn1;uniform vec4 uBDyn1;uniform vec4 uADyn2;uniform vec4 uBDyn2;uniform int uDirection;uniform int uAxis;uniform int uFilterLuma;
        $common
        /* Keep the 26730 Sabre-validity interface stable. The validity-owned seed already consumed
         * this provenance to create uOwnership before any VGN chroma filtering begins. */
        uniform highp sampler2D uSabreWeightR;
        uniform highp sampler2D uSabreWeightsGb;
        uniform highp sampler2D uSabreValidWeights;
        uniform highp float uSabreValidityWeightScale;
        uniform int uSabreSupportValid;
        struct State{float x0;float x1;float y0;float y1;};
        float apply(inout State s,float v,vec4 a,vec4 b,bool unsignedOut){float r=a[0]*v+a[1]*s.x0+a[2]*s.x1-b[1]*s.y0-b[2]*s.y1;s.x1=s.x0;s.y1=s.y0;s.x0=v;s.y0=unsignedOut?clamp(r,0.0,65504.0):r;return s.y0;}
        float steadyOutput(float v,vec4 a,vec4 b,bool u){float r=v*(a[0]+a[1]+a[2])/(1.0+b[1]+b[2]);return u?clamp(r,0.0,65504.0):r;}
        State steady(float x,float y){return State(x,x,y,y);} ivec2 pos(int inner,int outer){return uAxis==0?ivec2(inner,outer):ivec2(outer,inner);}
        bool insideImage(ivec2 q){return all(greaterThanEqual(q,ivec2(0)))&&all(lessThan(q,uImageSize));}
        int directionBitForDelta(ivec2 d){
            if(d==ivec2(0,-1))return 0; if(d==ivec2(1,0))return 1;
            if(d==ivec2(0,1))return 2; if(d==ivec2(-1,0))return 3;
            if(d==ivec2(1,-1))return 4; if(d==ivec2(1,1))return 5;
            if(d==ivec2(-1,1))return 6; if(d==ivec2(-1,-1))return 7; return -1;
        }
        int oppositeDirectionBit(int bit){
            if(bit==0)return 2; if(bit==1)return 3; if(bit==2)return 0; if(bit==3)return 1;
            if(bit==4)return 6; if(bit==5)return 7; if(bit==6)return 4; if(bit==7)return 5; return -1;
        }
        bool cleanupFallbackAt(ivec2 p){return (int(imageLoad(uOwnership,p).a)&0x1000)!=0;}
        bool highlightInvalidAt(ivec2 p){return (int(imageLoad(uOwnership,p).a)&0x2000)!=0;}
        bool transportFromPreviousAllowed(ivec2 currentP,ivec2 previousP){
            if(!insideImage(currentP)||!insideImage(previousP))return false;
            ivec2 delta=previousP-currentP; int bit=directionBitForDelta(delta); int opposite=oppositeDirectionBit(bit);
            if(bit<0||opposite<0)return false;
            int currentMask=int(imageLoad(uOwnership,currentP).a)&0xFF; int previousMask=int(imageLoad(uOwnership,previousP).a)&0xFF;
            bool currentAllows=(currentMask&(1<<bit))!=0;
            bool currentNeedsCleanup=cleanupFallbackAt(currentP)||highlightInvalidAt(currentP);
            bool previousNeedsCleanup=cleanupFallbackAt(previousP)||highlightInvalidAt(previousP);
            /* IRIS_26732_IIR_CLEANUP_IS_ONE_WAY
             * Suspicious/invalid centers may receive trusted recursive state only along an allowed
             * direction. Their state is never propagated back into a trusted neighbor. */
            if(currentNeedsCleanup)return currentAllows&&!previousNeedsCleanup;
            if(previousNeedsCleanup)return false;
            return currentAllows&&(previousMask&(1<<opposite))!=0;
        }
        void main(){
            int outer=uAxis==0?int(gl_GlobalInvocationID.y):int(gl_GlobalInvocationID.x);int outerLimit=uAxis==0?uImageSize.y:uImageSize.x;int innerSize=uAxis==0?uImageSize.x:uImageSize.y;if(outer>=outerLimit)return;
            int start=uDirection==0?0:innerSize-1;int step=uDirection==0?1:-1;uvec4 boundary=imageLoad(uInput,pos(start,outer));float by=decodeU16(boundary.r),cr=float(signedChroma(boundary.g)),cb=float(signedChroma(boundary.b));
            float sy=steadyOutput(by,uA10,uB10,true),sc1=steadyOutput(cr,uADyn1,uBDyn1,false),sb1=steadyOutput(cb,uADyn1,uBDyn1,false),sc2=steadyOutput(sc1,uADyn2,uBDyn2,false),sb2=steadyOutput(sb1,uADyn2,uBDyn2,false);
            State ys=steady(by,sy),c1=steady(cr,sc1),b1=steady(cb,sb1),c2=steady(sc1,sc2),b2=steady(sb1,sb2);float previousY=by;
            for(int i=0;i<innerSize;++i){
                ivec2 p=pos(start+i*step,outer);uvec4 px=imageLoad(uInput,p);float currentY=decodeU16(px.r);float inCr=float(signedChroma(px.g)),inCb=float(signedChroma(px.b));
                float edgeRatio=abs(currentY-previousY)/max(max(currentY,previousY),3930.0);
                bool strongLumaBoundary=edgeRatio>0.55;
                ivec2 scanStep=uAxis==0?ivec2(step,0):ivec2(0,step);
                ivec2 previousP=p-scanStep;
                /* IRIS_26731_FROZEN_IIR_MATERIAL_OWNERSHIP
                 * Never re-classify material ownership from already-filtered chroma. The exact
                 * 26730 validity-owned seed map is frozen before VGN and shared by IIR1 and IIR3.
                 * A missing reciprocal connection is a hard chroma-state boundary in either scan
                 * direction, preventing row/column-specific feedback from forming teeth or L blocks. */
                bool frozenMaterialBoundary=i>0&&!transportFromPreviousAllowed(p,previousP);
                if(i>0&&(strongLumaBoundary||frozenMaterialBoundary)){
                    if(uFilterLuma!=0){float resetY=steadyOutput(currentY,uA10,uB10,true);ys=steady(currentY,resetY);}
                    float resetCr1=steadyOutput(inCr,uADyn1,uBDyn1,false),resetCb1=steadyOutput(inCb,uADyn1,uBDyn1,false);
                    float resetCr2=steadyOutput(resetCr1,uADyn2,uBDyn2,false),resetCb2=steadyOutput(resetCb1,uADyn2,uBDyn2,false);
                    c1=steady(inCr,resetCr1);b1=steady(inCb,resetCb1);c2=steady(resetCr1,resetCr2);b2=steady(resetCb1,resetCb2);
                }
                float y=uFilterLuma!=0?apply(ys,currentY,uA10,uB10,true):currentY;
                float r=apply(c1,inCr,uADyn1,uBDyn1,false);float q=apply(b1,inCb,uADyn1,uBDyn1,false);r=apply(c2,r,uADyn2,uBDyn2,false);q=apply(b2,q,uADyn2,uBDyn2,false);
                imageStore(uOutput,p,uvec4(uint(clamp(y,0.0,65504.0)),unsignedChroma(int(r)),unsignedChroma(int(q)),px.a));previousY=currentY;
            }
        }
    """.trimIndent()

    val calculateError = """
        #version 310 es
        precision highp float; precision highp int; precision highp uimage2D;
        layout(local_size_x=8,local_size_y=8) in;
        layout(rgba16ui,binding=0) readonly uniform highp uimage2D uOriginal;
        layout(rgba16ui,binding=1) readonly uniform highp uimage2D uSmooth;
        layout(rgba16ui,binding=2) writeonly uniform highp uimage2D uOutput;
        $common
        int countDir(int e){return(e>>8)&0x0F;}
        void main(){ivec2 p=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(p,uImageSize)))return;uvec4 o=imageLoad(uOriginal,p),s=imageLoad(uSmooth,p);if(p.x==0||p.y==0||p.x+1>=uImageSize.x||p.y+1>=uImageSize.y){imageStore(uOutput,p,s);return;}const ivec2 d[8]=ivec2[8](ivec2(0,-1),ivec2(1,0),ivec2(0,1),ivec2(-1,0),ivec2(1,-1),ivec2(1,1),ivec2(-1,1),ivec2(-1,-1));int e=int(o.a),ys=0,rs=0,bs=0;for(int i=0;i<8;++i)if((e&(1<<i))!=0){uvec4 n=imageLoad(uOriginal,p+d[i]);ys+=int(o.r)-int(n.r);rs+=signedChroma(o.g)-signedChroma(n.g);bs+=signedChroma(o.b)-signedChroma(n.b);}int count=countDir(e),bits=e&0xFF;int err=(bits==0x50||bits==0xA0)?abs(rs+bs):0;if(count>0)err=(err+abs(ys))/count;float minLevel=0.05*decodeU16(s.r);s.a=uint(clamp(decodeU16(s.a)*clamp(float(err)-minLevel,0.0,1.0),0.0,65504.0));imageStore(uOutput,p,s);}
    """.trimIndent()

    val iirError = """
        #version 310 es
        precision highp float; precision highp int; precision highp uimage2D;
        layout(local_size_x=1,local_size_y=1) in;
        layout(rgba16ui,binding=0) readonly uniform highp uimage2D uInput;
        layout(rgba16ui,binding=1) writeonly uniform highp uimage2D uOutput;
        uniform vec4 uA10;uniform vec4 uB10;uniform int uDirection;uniform int uAxis;
        $common
        struct State{float x0;float x1;float y0;float y1;};
        State steadyState(float value){float y=value*(uA10[0]+uA10[1]+uA10[2])/(1.0+uB10[1]+uB10[2]);y=clamp(y,0.0,65504.0);return State(value,value,y,y);}float apply(inout State s,float v){float r=uA10[0]*v+uA10[1]*s.x0+uA10[2]*s.x1-uB10[1]*s.y0-uB10[2]*s.y1;s.x1=s.x0;s.y1=s.y0;s.x0=v;s.y0=clamp(r,0.0,65504.0);return s.y0;}ivec2 pos(int inner,int outer){return uAxis==0?ivec2(inner,outer):ivec2(outer,inner);}
        void main(){int outer=uAxis==0?int(gl_GlobalInvocationID.y):int(gl_GlobalInvocationID.x);int outerLimit=uAxis==0?uImageSize.y:uImageSize.x;int innerSize=uAxis==0?uImageSize.x:uImageSize.y;if(outer>=outerLimit)return;int start=uDirection==0?0:innerSize-1;int step=uDirection==0?1:-1;uvec4 b=imageLoad(uInput,pos(start,outer));State s=steadyState(decodeU16(b.a));for(int i=0;i<innerSize;++i){ivec2 p=pos(start+i*step,outer);uvec4 v=imageLoad(uInput,p);v.a=uint(apply(s,decodeU16(v.a)));imageStore(uOutput,p,v);}}
    """.trimIndent()

    val blendChroma = """
        #version 310 es
        precision highp float;precision highp int;precision highp uimage2D;
        layout(local_size_x=8,local_size_y=8) in;
        layout(rgba16ui,binding=0) readonly uniform highp uimage2D uOriginal;
        layout(rgba16ui,binding=1) readonly uniform highp uimage2D uSmooth;
        layout(rgba16ui,binding=2) writeonly uniform highp uimage2D uOutput;
        uniform float uChromaStrength;
        $common
        float scale(float low,float v,float high){return(clamp(v,low,high)-low)/(high-low);}
        void main(){
            ivec2 p=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(p,uImageSize)))return;uvec4 o=imageLoad(uOriginal,p),s=imageLoad(uSmooth,p);
            int cr=signedChroma(o.g),cb=signedChroma(o.b),sr=signedChroma(s.g),sb=signedChroma(s.b);float errorScale=scale(100.0,decodeU16(s.a)*0.25,300.0);float smoothSat=1.0+float(abs(sr))+float(abs(sb));float normalSat=float(abs(cr))+float(abs(cb));
            float strength=clamp(uChromaStrength,0.0,1.0);float f=errorScale*scale(0.5,normalSat/smoothSat,1.0);if(strength<0.9999)f*=strength;
            o.g=unsignedChroma(int(mix(float(cr),float(sr),f)));o.b=unsignedChroma(int(mix(float(cb),float(sb),f)));o.a=s.a;imageStore(uOutput,p,o);
        }
    """.trimIndent()

    val finalCameraRgb = """
        #version 310 es
        precision highp float;precision highp int;precision highp uimage2D;
        layout(local_size_x=8,local_size_y=8) in;
        layout(rgba16ui,binding=0) readonly uniform highp uimage2D uInput;
        layout(rgba16ui,binding=1) writeonly uniform highp uimage2D uOutput;
        uniform vec3 uCalculationGains;
        $common
        vec3 fromYccd(uvec4 e){float y=clamp(decodeU16(e.r),0.0,65504.0),cr=float(signedChroma(e.g)),cb=float(signedChroma(e.b));float r=clamp(y*(1.0+(3.0*cr-cb)/32768.0),0.0,65504.0);float b=clamp(y*(1.0+(3.0*cb-cr)/32768.0),0.0,65504.0);float g=clamp((4.0*y-r-b)*0.5,0.0,65504.0);return vec3(r,g,b);}
        void main(){ivec2 p=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(p,uImageSize)))return;vec3 cameraRgb=fromYccd(imageLoad(uInput,p))/max(uCalculationGains,vec3(1e-6));uvec4 outputPixel=uvec4(uvec3(clamp(cameraRgb,vec3(0.0),vec3(65504.0))+vec3(0.5)),65535u);imageStore(uOutput,p,outputPixel);}
    """.trimIndent()
}
