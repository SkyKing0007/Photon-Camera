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
 * Iris-owned rewrite of the post-fusion Spatial-RGB chroma stage. bjzhou c317/MGC is used only as
 * a pinned semantic reference for equations, coefficients, coordinate domains, and stage ordering.
 * This owner is intentionally integrated around Iris' existing Spatial-RGB accumulator, texture
 * lifecycle, diagnostics, Motion ownership, and GPU export path rather than vendoring bjzhou code.
 *
 * Input is one full contiguous RGBA16UI camera-RGB image. RGB contains normalized camera color;
 * alpha contains the packed fused-green doubled-angle direction moment produced by the Iris merge.
 * All directional and recursive filtering runs in global image coordinates so processing bands can
 * never become visible tile boundaries.
 */
internal class GlesIris26529SpatialRgbChromaPostprocessor(
    private val imageWidth: Int,
    private val imageHeight: Int,
    calculationWbGains: FloatArray,
    outputScale: Float,
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
    private val coefficients = Iris26529SpatialRgbIirCoefficients.forOutputScale(
        outputScale.takeIf { it.isFinite() && it > 0f } ?: 1f,
    )
    private val passWindow = GlesGpuScheduler.PassWindow("Iris26529SpatialRgbChroma", 2)

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
    ): Result {
        check(assembledRgb != 0)
        check(writtenBands == bands.size) {
            "Iris 26529 chroma input incomplete: $writtenBands/${bands.size} bands"
        }
        workA = allocate("YCCD A")
        workB = allocate("YCCD B")
        val chromaStart = System.nanoTime()

        // Keep the c317/MGC stage domains but use Iris-owned storage rotation:
        // workA = seed YCCD, workB = local-clamped YCCD, assembledRgb = median YCCD,
        // then workA = directional YCCD and assembledRgb = restored-direction YCCD.
        dispatchSeed(assembledRgb, workA)
        dispatchLocal(localClampProgram, workA, workB, "local clamp")
        dispatchLocal(localMedianProgram, workB, assembledRgb, "local median")
        dispatchDirectional(workB, assembledRgb, workA)
        dispatchRestoreDirection(workA, workB, assembledRgb)

        // Preserve the restored-direction YCCD as the original reference until the final blend.
        // This rotation mirrors the reference stage ownership without copying its host structure.
        val originalYccd = assembledRgb
        var smoothYccd = workA
        var scratchYccd = workB
        runIirRgb(smoothYccd, scratchYccd, coefficients.pass1, filterLuma = true, "IIR1").also {
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
        runIirRgb(filteredYccd, finalScratch, coefficients.pass3, filterLuma = false, "IIR3").also {
            filteredYccd = it.first
            finalScratch = it.second
        }
        val chromaMs = (System.nanoTime() - chromaStart) / 1_000_000L

        val finalStart = System.nanoTime()
        dispatchFinal(filteredYccd, originalYccd)
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

    private fun dispatchSeed(source: Int, destination: Int) {
        GLES31.glUseProgram(seedProgram)
        setImageSize(seedProgram)
        GLES31.glUniform3fv(host.uniformLocation(seedProgram, "uCalculationGains"), 1, calculationRgbGains, 0)
        GLES31.glUniform1f(host.uniformLocation(seedProgram, "uMinimumDirectionGradient"), 8f)
        dispatch2d(seedProgram, intArrayOf(source), destination, "seed")
    }

    private fun dispatchLocal(program: Int, source: Int, destination: Int, label: String) {
        GLES31.glUseProgram(program)
        setImageSize(program)
        dispatch2d(program, intArrayOf(source), destination, label)
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
        pass: Iris26529SpatialRgbIirCoefficients.Pass,
        filterLuma: Boolean,
        label: String,
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
            trackedIirDispatch(d[1], "$label/$index", input, output)
            clearImages()
            input = output.also { output = input }
        }
        return input to output
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

    private fun trackedIirDispatch(axis: Int, label: String, read: Int, write: Int) {
        passWindow.beginPass(
            label,
            reads = longArrayOf(GlesGpuScheduler.textureResource(read)),
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
 * Iris-owned GLSL translation of the c317/MGC Spatial-RGB post-fusion behavior.
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
        vec3 calculationRgbAt(ivec2 p) {
            uvec3 e=imageLoad(uInput,safePos(p)).rgb;
            return clamp(vec3(decodeU16(e.r),decodeU16(e.g),decodeU16(e.b))*uCalculationGains,vec3(0.0),vec3(65504.0));
        }
        float yAt(ivec2 p){ return dot(calculationRgbAt(p),vec3(0.25,0.5,0.25)); }
        float snorm8(uint x){ int v=int(x&255u); if(v>127)v-=256; return clamp(float(v)/127.0,-1.0,1.0); }
        vec2 directionMomentAt(ivec2 p){ uint a=imageLoad(uInput,safePos(p)).a; return vec2(snorm8(a),snorm8(a>>8u)); }
        uint directionMaskAt(ivec2 p){
            const ivec2 d[8]=ivec2[8](ivec2(0,-1),ivec2(1,0),ivec2(0,1),ivec2(-1,0),ivec2(1,-1),ivec2(1,1),ivec2(-1,1),ivec2(-1,-1));
            const vec2 axis2[8]=vec2[8](vec2(-1,0),vec2(1,0),vec2(-1,0),vec2(1,0),vec2(0,-1),vec2(0,1),vec2(0,-1),vec2(0,1));
            float center=yAt(p); vec2 moment=directionMomentAt(p); float g[8]; float lo=65504.0; float hi=0.0;
            for(int i=0;i<8;++i){
                float first=yAt(p+d[i]); float second=yAt(p+d[i]*2);
                float rgbGradient=abs(center-first)+0.5*abs(first-second);
                float structureScale=clamp(1.0+0.5*dot(moment,axis2[i]),0.5,1.5);
                g[i]=rgbGradient*structureScale; lo=min(lo,g[i]); hi=max(hi,g[i]);
            }
            float threshold=max(uMinimumDirectionGradient,1.5*lo+0.09375*(hi-lo));
            int mask=0; int count=0;
            for(int i=0;i<8;++i){ if(g[i]<=threshold){ mask|=1<<i; count++; } }
            if(count==0){ mask=0xFF; count=8; }
            return uint(mask | (count << 8));
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
        uint yAt(ivec2 p){ return imageLoad(uInput,safePos(p)).r; }
        void main(){
            ivec2 p=ivec2(gl_GlobalInvocationID.xy); if(any(greaterThanEqual(p,uImageSize)))return;
            uvec4 r=imageLoad(uInput,p); uint lo=65535u; uint hi=0u;
            for(int y=-1;y<=1;++y)for(int x=-1;x<=1;++x){ if(x==0&&y==0)continue; uint v=yAt(p+ivec2(x,y)); lo=min(lo,v); hi=max(hi,v); }
            r.r=clamp(r.r,lo,hi); imageStore(uOutput,p,r);
        }
    """.trimIndent()

    val localMedian = """
        #version 310 es
        precision highp int; precision highp uimage2D;
        layout(local_size_x=8,local_size_y=8) in;
        layout(rgba16ui,binding=0) readonly uniform highp uimage2D uInput;
        layout(rgba16ui,binding=1) writeonly uniform highp uimage2D uOutput;
        $common
        ivec3 s(ivec2 p){ uvec4 v=imageLoad(uInput,safePos(p)); return ivec3(int(v.r),signedChroma(v.g),signedChroma(v.b)); }
        void main(){
            ivec2 p=ivec2(gl_GlobalInvocationID.xy); if(any(greaterThanEqual(p,uImageSize)))return;
            ivec3 a=s(p+ivec2(-1,-1)),b=s(p+ivec2(0,-1)),c=s(p+ivec2(1,-1));
            ivec2 row=a.yz+b.yz+c.yz-min(min(a.yz,b.yz),c.yz)-max(max(a.yz,b.yz),c.yz); ivec2 mn=row,mx=row,sum=row; int ysum=a.x+2*b.x+c.x;
            a=s(p+ivec2(-1,0));b=s(p);c=s(p+ivec2(1,0)); row=a.yz+b.yz+c.yz-min(min(a.yz,b.yz),c.yz)-max(max(a.yz,b.yz),c.yz); sum+=row; mn=min(mn,row); mx=max(mx,row); ysum+=2*a.x+4*b.x+2*c.x;
            a=s(p+ivec2(-1,1));b=s(p+ivec2(0,1));c=s(p+ivec2(1,1)); row=a.yz+b.yz+c.yz-min(min(a.yz,b.yz),c.yz)-max(max(a.yz,b.yz),c.yz); sum+=row-min(mn,row)-max(mx,row); ysum+=a.x+2*b.x+c.x;
            uvec4 center=imageLoad(uInput,p); imageStore(uOutput,p,uvec4(uint(max(ysum/16,0)),unsignedChroma(sum.x),unsignedChroma(sum.y),center.a));
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
        vec4 filter3(uvec4 encoded,ivec2 p){
            vec3 neg[4]; vec3 pos[4];
            neg[0]=smoothAt(p+ivec2(-1,0));pos[0]=smoothAt(p+ivec2(1,0));neg[1]=smoothAt(p+ivec2(0,-1));pos[1]=smoothAt(p+ivec2(0,1));neg[2]=smoothAt(p+ivec2(1,-1));pos[2]=smoothAt(p+ivec2(-1,1));neg[3]=smoothAt(p+ivec2(-1,-1));pos[3]=smoothAt(p+ivec2(1,1));
            vec3 center=vec3(decodeU16(encoded.r),float(signedChroma(encoded.g)),float(signedChroma(encoded.b))); vec4 cr;vec4 cb;vec4 scale;
            for(int i=0;i<4;++i){vec3 a=neg[i],b=pos[i];float da=dot(abs(center-a),vec3(1.0/6.0));float db=dot(abs(center-b),vec3(1.0/6.0));float total=da+db;vec3 d=total!=0.0?(a*db+b*da)/total:(a+b)*0.5;scale[i]=min(abs(center.x-d.x)/max(center.x+d.x,1.0)*2.0,1.0);cr[i]=mix(center.y,d.y,scale[i]);cb[i]=mix(center.z,d.z,scale[i]);}
            vec3 selected=vec3(0.0);int count=0;int direction=int(encoded.a);
            if((direction&(1<<0))!=0){selected+=vec3(cr[0],cb[0],scale[0]);count++;} if((direction&(1<<1))!=0){selected+=vec3(cr[0],cb[0],scale[0]);count++;}
            if((direction&(1<<2))!=0){selected+=vec3(cr[1],cb[1],scale[1]);count++;} if((direction&(1<<3))!=0){selected+=vec3(cr[1],cb[1],scale[1]);count++;}
            if((direction&(1<<4))!=0){selected+=vec3(cr[2],cb[2],scale[2]);count++;} if((direction&(1<<5))!=0){selected+=vec3(cr[2],cb[2],scale[2]);count++;}
            if((direction&(1<<6))!=0){selected+=vec3(cr[3],cb[3],scale[3]);count++;} if((direction&(1<<7))!=0){selected+=vec3(cr[3],cb[3],scale[3]);count++;}
            if(count>0)selected/=float(count); float minScale=min(min(scale.x,scale.y),min(scale.z,scale.w)); float yScale=clamp(1.0-center.x/16384.0*minScale,0.0,1.0); return vec4(center.x,yScale*selected.x,yScale*selected.y,selected.z*65504.0);
        }
        void main(){ivec2 p=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(p,uImageSize)))return;uvec4 e=imageLoad(uOriginal,p);vec4 f=vec4(decodeU16(e.r),float(signedChroma(e.g)),float(signedChroma(e.b)),0.0);if(e.r!=0u&&e.a!=0u)f=filter3(e,p);uvec4 sm=imageLoad(uSmooth,p);ivec2 sc=ivec2(signedChroma(sm.g),signedChroma(sm.b));ivec2 fc=ivec2(f.yz);if(abs(sc.x)+abs(sc.y)<abs(fc.x)+abs(fc.y))fc=sc;imageStore(uOutput,p,uvec4(uint(clamp(f.x,0.0,65504.0)),unsignedChroma(fc.x),unsignedChroma(fc.y),uint(clamp(f.w,0.0,65504.0))));}
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
        uniform vec4 uA10;uniform vec4 uB10;uniform vec4 uADyn1;uniform vec4 uBDyn1;uniform vec4 uADyn2;uniform vec4 uBDyn2;uniform int uDirection;uniform int uAxis;uniform int uFilterLuma;
        $common
        struct State{float x0;float x1;float y0;float y1;};
        float apply(inout State s,float v,vec4 a,vec4 b,bool unsignedOut){float r=a[0]*v+a[1]*s.x0+a[2]*s.x1-b[1]*s.y0-b[2]*s.y1;s.x1=s.x0;s.y1=s.y0;s.x0=v;s.y0=unsignedOut?clamp(r,0.0,65504.0):r;return s.y0;}
        float steadyOutput(float v,vec4 a,vec4 b,bool u){float r=v*(a[0]+a[1]+a[2])/(1.0+b[1]+b[2]);return u?clamp(r,0.0,65504.0):r;}
        State steady(float x,float y){return State(x,x,y,y);} ivec2 pos(int inner,int outer){return uAxis==0?ivec2(inner,outer):ivec2(outer,inner);}
        void main(){int outer=uAxis==0?int(gl_GlobalInvocationID.y):int(gl_GlobalInvocationID.x);int outerLimit=uAxis==0?uImageSize.y:uImageSize.x;int innerSize=uAxis==0?uImageSize.x:uImageSize.y;if(outer>=outerLimit)return;int start=uDirection==0?0:innerSize-1;int step=uDirection==0?1:-1;uvec4 b=imageLoad(uInput,pos(start,outer));float by=decodeU16(b.r),cr=float(signedChroma(b.g)),cb=float(signedChroma(b.b));float sy=steadyOutput(by,uA10,uB10,true),sc1=steadyOutput(cr,uADyn1,uBDyn1,false),sb1=steadyOutput(cb,uADyn1,uBDyn1,false),sc2=steadyOutput(sc1,uADyn2,uBDyn2,false),sb2=steadyOutput(sb1,uADyn2,uBDyn2,false);State ys=steady(by,sy),c1=steady(cr,sc1),b1=steady(cb,sb1),c2=steady(sc1,sc2),b2=steady(sb1,sb2);for(int i=0;i<innerSize;++i){ivec2 p=pos(start+i*step,outer);uvec4 px=imageLoad(uInput,p);float y=uFilterLuma!=0?apply(ys,decodeU16(px.r),uA10,uB10,true):decodeU16(px.r);float r=apply(c1,float(signedChroma(px.g)),uADyn1,uBDyn1,false);float q=apply(b1,float(signedChroma(px.b)),uADyn1,uBDyn1,false);r=apply(c2,r,uADyn2,uBDyn2,false);q=apply(b2,q,uADyn2,uBDyn2,false);imageStore(uOutput,p,uvec4(uint(clamp(y,0.0,65504.0)),unsignedChroma(int(r)),unsignedChroma(int(q)),px.a));}}
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
        $common
        float scale(float low,float v,float high){return(clamp(v,low,high)-low)/(high-low);}
        void main(){ivec2 p=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(p,uImageSize)))return;uvec4 o=imageLoad(uOriginal,p),s=imageLoad(uSmooth,p);int cr=signedChroma(o.g),cb=signedChroma(o.b),sr=signedChroma(s.g),sb=signedChroma(s.b);float errorScale=scale(100.0,decodeU16(s.a)*0.25,300.0);float smoothSat=1.0+float(abs(sr))+float(abs(sb));float normalSat=float(abs(cr))+float(abs(cb));float f=errorScale*scale(0.5,normalSat/smoothSat,1.0);o.g=unsignedChroma(int(mix(float(cr),float(sr),f)));o.b=unsignedChroma(int(mix(float(cb),float(sb),f)));o.a=s.a;imageStore(uOutput,p,o);}
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
