package com.hinnka.mycamera.processor

import android.opengl.EGL14
import android.opengl.EGLContext
import android.opengl.GLES30
import com.hinnka.mycamera.processor.experimentc.bjzhou.raw.DngBaselineExposure
import java.nio.ByteBuffer
import java.nio.ByteOrder

/**
 * C-private, explicitly provenance-bound DNG ProfileGainTableMap2 -> original bjzhou GLSL ABI.
 * This is an adapter for a REAL DNG 52525/52544 asset, not a PGTM generator. Camera2 alone
 * cannot supply it. No default/identity or synthetic HDRNet table is ever manufactured.
 * Field order, flattened R32F layout, baseline coordinate and uniforms are the pinned donor's
 * RawDemosaicProcessor.bindProfileGainTableMap/ensureProfileGainTableTexture contract.
 */
internal class Iris26975COriginalPgtmBinding(private val map: Frozen?) : AutoCloseable {
    internal class Frozen private constructor(
        val mapPointsV: Int, val mapPointsH: Int,
        val mapSpacingV: Double, val mapSpacingH: Double,
        val mapOriginV: Double, val mapOriginH: Double,
        val mapPointsN: Int, private val immutableWeights: FloatArray,
        val gamma: Float, private val immutableGains: FloatArray,
        val sourceTag: Int, val totalBaselineExposureEv: Float,
    ) {
        fun weights(): FloatArray = immutableWeights.copyOf()
        fun gains(): FloatArray = immutableGains.copyOf()
        val textureWidth get() = mapPointsN
        val textureHeight get() = Math.multiplyExact(mapPointsH, mapPointsV)

        companion object {
            /** DNG tag provenance must be supplied by an actual DNG tag reader. */
            fun fromDng(
                mapPointsV: Int, mapPointsH: Int,
                mapSpacingV: Double, mapSpacingH: Double,
                mapOriginV: Double, mapOriginH: Double,
                mapPointsN: Int, mapInputWeights: FloatArray,
                gamma: Float, gains: FloatArray,
                sourceTag: Int,
                dngBaselineExposureEv: Float,
                dcpBaselineExposureOffsetEv: Float,
            ): Frozen {
                require(sourceTag == 52525 || sourceTag == 52544) {
                    "Original PGTM requires actual DNG tag 52525 or 52544"
                }
                val count = mapPointsV.toLong() * mapPointsH.toLong() * mapPointsN.toLong()
                require(mapPointsV > 0 && mapPointsH > 0 && mapPointsN > 0 &&
                    count in 1 until 16_777_216L && gains.size.toLong() == count &&
                    mapPointsH.toLong() * mapPointsV <= Int.MAX_VALUE &&
                    mapInputWeights.size == 5 && mapInputWeights.all(Float::isFinite) &&
                    mapSpacingV.isFinite() && mapSpacingV > 0.0 &&
                    mapSpacingH.isFinite() && mapSpacingH > 0.0 &&
                    mapOriginV.isFinite() && mapOriginH.isFinite() &&
                    gamma.isFinite() && gamma in 0.125f..8f &&
                    gains.all { it.isFinite() && it in 0.000244140625f..4096f } &&
                    dngBaselineExposureEv.isFinite() &&
                    dcpBaselineExposureOffsetEv.isFinite()) {
                    "Invalid authentic DNG ProfileGainTableMap metadata"
                }
                val baseline = DngBaselineExposure.sanitize(dngBaselineExposureEv) +
                    dcpBaselineExposureOffsetEv
                require(baseline.isFinite() && DngBaselineExposure.exactGain(baseline).isFinite()) {
                    "Invalid DNG total baseline exposure"
                }
                return Frozen(mapPointsV, mapPointsH, mapSpacingV, mapSpacingH,
                    mapOriginV, mapOriginH, mapPointsN, mapInputWeights.copyOf(),
                    gamma, gains.copyOf(), sourceTag, baseline)
            }
        }
    }

    private val gpu = Iris26972CDonorSabreGpuMerge
    private val owner: EGLContext = EGL14.eglGetCurrentContext()
    private var texture = 0
    private var closed = false

    /** Set every donor PGTM uniform, including the original 257-wide R32F upload semantics. */
    fun bind(program: Int, disabledFallbackTexture: Int) {
        check(!closed && owner != EGL14.EGL_NO_CONTEXT && EGL14.eglGetCurrentContext() == owner) {
            "C original DNG PGTM GL owner mismatch"
        }
        require(program > 0 && disabledFallbackTexture > 0)
        fun location(name: String) = GLES30.glGetUniformLocation(program, name)
        GLES30.glActiveTexture(GLES30.GL_TEXTURE0 + 7)
        if (map == null) {
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, disabledFallbackTexture)
            GLES30.glUniform1i(location("uProfileGainTableMap"), 7)
            GLES30.glUniform1i(location("uProfileGainEnabled"), 0)
            return
        }
        if (texture == 0) upload(map)
        GLES30.glActiveTexture(GLES30.GL_TEXTURE0 + 7)
        GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, texture)
        GLES30.glUniform1i(location("uProfileGainTableMap"), 7)
        GLES30.glUniform1i(location("uProfileGainEnabled"), 1)
        GLES30.glUniform3i(location("uProfileGainTableSize"),
            map.mapPointsH, map.mapPointsV, map.mapPointsN)
        GLES30.glUniform4f(location("uProfileGainGrid"),
            map.mapOriginH.toFloat(), map.mapOriginV.toFloat(),
            map.mapSpacingH.toFloat(), map.mapSpacingV.toFloat())
        val w = map.weights()
        GLES30.glUniform4f(location("uProfileGainWeights0"), w[0], w[1], w[2], w[3])
        GLES30.glUniform1f(location("uProfileGainWeightMax"), w[4])
        GLES30.glUniform1f(location("uProfileGainGamma"), map.gamma)
        GLES30.glUniform1f(location("uProfileGainBaselineGain"),
            DngBaselineExposure.exactGain(map.totalBaselineExposureEv))
    }

    private fun upload(map: Frozen) {
        val maxTexture = gpu.glInt(GLES30.GL_MAX_TEXTURE_SIZE)
        require(map.textureWidth <= maxTexture && map.textureHeight <= maxTexture) {
            "Authentic DNG PGTM exceeds supported texture bounds"
        }
        val oldActive = gpu.glInt(GLES30.GL_ACTIVE_TEXTURE)
        val oldPbo = gpu.glInt(GLES30.GL_PIXEL_UNPACK_BUFFER_BINDING)
        val oldAlignment = gpu.glInt(GLES30.GL_UNPACK_ALIGNMENT)
        val oldRowLength = gpu.glInt(GLES30.GL_UNPACK_ROW_LENGTH)
        GLES30.glActiveTexture(GLES30.GL_TEXTURE0 + 7)
        val oldTexture = gpu.glInt(GLES30.GL_TEXTURE_BINDING_2D)
        val ids = IntArray(1)
        try {
            GLES30.glGenTextures(1, ids, 0)
            check(ids[0] > 0) { "Original PGTM R32F allocation failed" }
            GLES30.glBindBuffer(GLES30.GL_PIXEL_UNPACK_BUFFER, 0)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_ROW_LENGTH, 0)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_ALIGNMENT, 1)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, ids[0])
            val gains = map.gains()
            val buffer = ByteBuffer.allocateDirect(Math.multiplyExact(gains.size, 4))
                .order(ByteOrder.nativeOrder()).asFloatBuffer()
            buffer.put(gains).position(0)
            GLES30.glTexImage2D(GLES30.GL_TEXTURE_2D, 0, GLES30.GL_R32F,
                map.textureWidth, map.textureHeight, 0,
                GLES30.GL_RED, GLES30.GL_FLOAT, buffer)
            GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_MIN_FILTER, GLES30.GL_NEAREST)
            GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_MAG_FILTER, GLES30.GL_NEAREST)
            GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_WRAP_S, GLES30.GL_CLAMP_TO_EDGE)
            GLES30.glTexParameteri(GLES30.GL_TEXTURE_2D, GLES30.GL_TEXTURE_WRAP_T, GLES30.GL_CLAMP_TO_EDGE)
            check(GLES30.glGetError() == GLES30.GL_NO_ERROR) { "Original DNG PGTM GPU upload failed" }
            texture = ids[0]
        } finally {
            GLES30.glBindBuffer(GLES30.GL_PIXEL_UNPACK_BUFFER, oldPbo)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_ROW_LENGTH, oldRowLength)
            GLES30.glPixelStorei(GLES30.GL_UNPACK_ALIGNMENT, oldAlignment)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, oldTexture)
            GLES30.glActiveTexture(oldActive)
            if (texture == 0 && ids[0] > 0) GLES30.glDeleteTextures(1, ids, 0)
        }
    }

    override fun close() {
        if (closed) return
        check(owner != EGL14.EGL_NO_CONTEXT && EGL14.eglGetCurrentContext() == owner)
        if (texture != 0) GLES30.glDeleteTextures(1, intArrayOf(texture), 0)
        texture = 0
        closed = true
    }
}
