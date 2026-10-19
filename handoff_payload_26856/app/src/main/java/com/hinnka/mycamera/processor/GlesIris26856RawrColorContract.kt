package com.hinnka.mycamera.processor

import kotlin.math.abs

/**
 * IRIS_26856_B_ONLY_RAWR_COLOR_DOMAIN_OWNER
 *
 * Immutable Camera2 calibration for the pinned RAWR pipeline. The normalized
 * temporal CFA is sensor-neutral. AMaZE applies relative R/G/B white balance
 * exactly once, Lab and FCC process that post-WB camera-linear image, and the
 * final RGB carrier must undo those gains before Iris's already-calibrated
 * camera-RGB -> display renderer. Do NOT apply the Camera2 matrix twice.
 *
 * Rejected calibration never silently becomes identity. Experiment A never
 * constructs this object and uses the historical 26850 path verbatim.
 */
internal object GlesIris26856RawrColorContract {
    data class Snapshot private constructor(
        val amazeWhiteBalance: FloatArray,
        val inverseWhiteBalance: FloatArray,
        val postWbCameraToSrgb: FloatArray,
    ) {
        fun cloneForCapture(): Snapshot = Snapshot(
            amazeWhiteBalance.copyOf(), inverseWhiteBalance.copyOf(), postWbCameraToSrgb.copyOf(),
        )
        companion object {
            fun create(wb: FloatArray, inverse: FloatArray, ccm: FloatArray) =
                Snapshot(wb.copyOf(), inverse.copyOf(), ccm.copyOf())
        }
    }

    fun freeze(colorGainsRggb: FloatArray, transform: FloatArray,
               directColorValid: Boolean): Snapshot {
        require(directColorValid) { "26856 B requires valid shutter-frozen Camera2 color transform" }
        require(colorGainsRggb.size >= 4 && colorGainsRggb.take(4).all {
            it.isFinite() && it > 0f
        }) { "26856 B invalid Camera2 RGGB white-balance gains" }
        require(transform.size == 9 && transform.all { it.isFinite() }) {
            "26856 B requires finite 3x3 Camera2 post-WB RGB-to-sRGB matrix"
        }
        val green = (colorGainsRggb[1].toDouble() + colorGainsRggb[2].toDouble()) / 2.0
        require(green.isFinite() && green > 0.0)
        val wb = floatArrayOf((colorGainsRggb[0] / green).toFloat(), 1f,
            (colorGainsRggb[3] / green).toFloat())
        require(wb.all { it.isFinite() && it > 0f && it <= 64f }) {
            "26856 B cannot reproduce unsupported relative AMaZE white balance"
        }
        val m = transform
        val determinant = m[0].toDouble() * (m[4].toDouble() * m[8] - m[5].toDouble() * m[7]) -
            m[1].toDouble() * (m[3].toDouble() * m[8] - m[5].toDouble() * m[6]) +
            m[2].toDouble() * (m[3].toDouble() * m[7] - m[4].toDouble() * m[6])
        require(determinant.isFinite() && abs(determinant) > 1e-10) {
            "26856 B singular Camera2 RGB calibration; no identity fallback"
        }
        return Snapshot.create(wb, floatArrayOf(1f / wb[0], 1f, 1f / wb[2]), transform)
    }

    // Apply only after RAWR AMaZE -> calibrated Lab defringe -> FCC x2.
    // No luminance compression, RGB clipping, gamma or second matrix.
    val undoAmazeWbToIrisSensorNeutral = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uPostRawrRgb;
        uniform vec3 uInverseAmazeWb;
        uniform ivec2 uSize;
        layout(location = 0) out vec4 oIrisSensorNeutralRgb;
        void main() {
            ivec2 p = clamp(ivec2(gl_FragCoord.xy), ivec2(0), uSize - ivec2(1));
            vec4 source = texelFetch(uPostRawrRgb, p, 0);
            oIrisSensorNeutralRgb = vec4(source.rgb * uInverseAmazeWb, source.a);
        }
    """.trimIndent()
}
