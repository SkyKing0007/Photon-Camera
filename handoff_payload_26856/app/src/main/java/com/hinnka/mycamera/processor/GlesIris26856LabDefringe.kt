package com.hinnka.mycamera.processor

import android.content.res.AssetManager
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.abs

/**
 * IRIS_26856_RAWR_PINNED_LAB_DEFRINGE_GLES_PORT.
 * Mathematical operations, Gaussian stencil, purple-object veto, and the
 * packed R32UI half-score + SSBO-reduction sequence follow RAWR
 * ce767e80bfce2e1641abf7dad6b1bf504d844fd9 exactly.
 * The sole API adaptation is Vulkan push constants -> GLES3.1 std140 UBO.
 * A is never a consumer; caller owns all GL resources and synchronizes passes.
 */
internal object GlesIris26856LabDefringe {
    const val OWNER = "IRIS_26856_RAWR_PINNED_LAB_DEFRINGE_GLES_PORT"
    const val PARAM_BYTES = 128
    private const val DIR = "iris26856/rawr/lab/"
    private const val INCLUDE = "#include \"lab_defringe_common.glsl\""

    fun expandedShader(assets: AssetManager, name: String): String {
        require(name == "lab_defringe_prepare.comp" || name == "lab_defringe_reduce.comp" ||
                name == "lab_defringe_reconstruct.comp") { "26856 unknown pinned Lab shader" }
        val shader = assets.open(DIR + name).bufferedReader(Charsets.UTF_8).use { it.readText() }
        val common = assets.open(DIR + "lab_defringe_common.glsl")
            .bufferedReader(Charsets.UTF_8).use { it.readText() }
        require(shader.indexOf(INCLUDE) > 0 && shader.indexOf(INCLUDE) == shader.lastIndexOf(INCLUDE)) {
            "26856 pinned Lab include count must be exactly one"
        }
        return shader.replace(INCLUDE, common)
    }

    /** Original RAWR calibrated camera RGB -> D50 Lab model, row major. */
    fun parameters(width: Int, height: Int, strength: Float, cameraToSrgb: FloatArray): ByteBuffer {
        require(width > 0 && height > 0 && width <= 16384 && height <= 16384)
        require(strength.isFinite() && strength in 0f..1f)
        require(cameraToSrgb.size == 9 && cameraToSrgb.all { it.isFinite() }) {
            "26856 Lab requires finite camera-to-sRGB 3x3 calibration"
        }
        val srgbToD50 = doubleArrayOf(
            .4360747, .3850649, .1430804,
            .2225045, .7168786, .0606169,
            .0139322, .0971045, .7141733,
        )
        val forward = DoubleArray(9)
        for (row in 0..2) for (column in 0..2) for (k in 0..2)
            forward[row * 3 + column] += srgbToD50[row * 3 + k] * cameraToSrgb[k * 3 + column]
        val inverse = doubleArrayOf(
            forward[4] * forward[8] - forward[5] * forward[7],
            forward[2] * forward[7] - forward[1] * forward[8],
            forward[1] * forward[5] - forward[2] * forward[4],
            forward[5] * forward[6] - forward[3] * forward[8],
            forward[0] * forward[8] - forward[2] * forward[6],
            forward[2] * forward[3] - forward[0] * forward[5],
            forward[3] * forward[7] - forward[4] * forward[6],
            forward[1] * forward[6] - forward[0] * forward[7],
            forward[0] * forward[4] - forward[1] * forward[3],
        )
        val determinant = forward[0] * inverse[0] + forward[1] * inverse[3] + forward[2] * inverse[6]
        require(determinant.isFinite() && abs(determinant) >= 1.0e-10) {
            "26856 Lab calibration is singular"
        }
        val output = ByteBuffer.allocateDirect(PARAM_BYTES).order(ByteOrder.nativeOrder())
        output.putInt(width).putInt(height)
        output.putFloat(strength).putFloat(13f)
        output.putFloat(1f)
        repeat(3) { output.putInt(0) }
        for (row in 0..2) {
            for (col in 0..2) output.putFloat(forward[row * 3 + col].toFloat())
            output.putFloat(0f)
        }
        for (row in 0..2) {
            for (col in 0..2) output.putFloat((inverse[row * 3 + col] / determinant).toFloat())
            output.putFloat(0f)
        }
        check(output.position() == PARAM_BYTES)
        output.rewind()
        return output
    }
}
