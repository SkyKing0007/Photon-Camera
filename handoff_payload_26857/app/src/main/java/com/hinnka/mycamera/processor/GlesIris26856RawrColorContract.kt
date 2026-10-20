package com.hinnka.mycamera.processor

import kotlin.math.abs

/**
 * IRIS_26856_B_ONLY_RAWR_COLOR_DOMAIN_OWNER
 *
 * Immutable Camera2 calibration for the pinned RAWR pipeline. The normalized
 * temporal CFA is sensor-neutral. Native AMaZE EXPORT ALREADY removes its
 * temporary R/G/B WB gains. Lab/FCC need those gains reapplied exactly once
 * to the sensor-neutral AMaZE output, and removed once after FCC before Iris's
 * already-calibrated * camera-RGB -> display renderer. Do NOT apply the Camera2 matrix twice.
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

    // AMaZE export has already undone temporary WB in Vulkan. Restore it only
    // for the calibrated Lab/FCC post-WB domain; preserve HDR and alpha.
    val applyAmazeWbForLabFcc = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uSensorNeutralAmazeRgb;
        uniform vec3 uAmazeWb;
        uniform ivec2 uSize;
        layout(location = 0) out vec4 oPostWbCameraRgb;
        void main() {
            ivec2 p = clamp(ivec2(gl_FragCoord.xy), ivec2(0), uSize - ivec2(1));
            vec4 source = texelFetch(uSensorNeutralAmazeRgb, p, 0);
            oPostWbCameraRgb = vec4(source.rgb * uAmazeWb, source.a);
        }
    """.trimIndent()

    // Apply only after temporary-WB Lab defringe -> FCC x2.
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
