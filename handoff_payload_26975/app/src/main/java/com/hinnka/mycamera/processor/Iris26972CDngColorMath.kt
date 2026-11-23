package com.hinnka.mycamera.processor

/**
 * C-private Camera2-to-bjzhou DNG adapter. All matrix color science is executed by
 * the exact pinned original DngSdkColorSpec, not a local derivative solver.
 * The donor Sabre stage's final gains are provenance-checked, not applied twice.
 */
internal object Iris26972CDngColorMath {
    private const val COMPONENT = "26972 C frozen dual-illuminant color"

    internal class Inputs(
        val colorMatrix1: FloatArray,
        val colorMatrix2: FloatArray?,
        val calibrationMatrix1: FloatArray?,
        val calibrationMatrix2: FloatArray?,
        val forwardMatrix1: FloatArray?,
        val forwardMatrix2: FloatArray?,
        val neutralCamera: FloatArray,
        val appliedDonorRgbGains: FloatArray,
        /** Original DNG/EXIF illuminant tags, NOT preconverted Kelvin. */
        val illuminant1Tag: Int,
        val illuminant2Tag: Int,
    )

    internal class Solved internal constructor(
        sensorToProfile: FloatArray,
        profileToLinearSrgb: FloatArray,
        val interpolation: Double,
        cameraWhite: FloatArray,
    ) {
        private val frozenWhite = cameraWhite.copyOf()
        private val frozenSensor = sensorToProfile.copyOf()
        private val frozenDisplay = profileToLinearSrgb.copyOf()
        val cameraWhite: FloatArray get() = frozenWhite.copyOf()
        val sensorToProfile: FloatArray get() = frozenSensor.copyOf()
        val profileToLinearSrgb: FloatArray get() = frozenDisplay.copyOf()
    }

    /**
     * The only live C color solve: calls original pinned bjzhou DngSdkColorSpec
     * (Git blob d4adb57319d556f6b5a8c9aab11a13d6b2f8baa8).
     * Iris adapts physical as-shot neutral into the exact [R,Ge,Go,B] white-gain
     * domain expected by the donor. The donor solver owns all matrix math,
     * illuminant interpolation and Bradford adaptation; no copied C solver runs.
     */
    internal fun solve(input: Inputs): Solved {
        val neutral = input.neutralCamera
        require(neutral.size == 3 && neutral.all { it.isFinite() && it > 0f }) {
            "$COMPONENT requires actual shutter-frozen Camera2 neutral"
        }
        require(input.appliedDonorRgbGains.size == 3 &&
            input.appliedDonorRgbGains.all { it.isFinite() && it > 0f }) {
            "$COMPONENT requires genuine donor Resolve WB provenance"
        }
        val gains = floatArrayOf(
            neutral[1] / neutral[0], 1f, 1f, neutral[1] / neutral[2]
        )
        require(gains.all { it.isFinite() && it > 0f }) {
            "$COMPONENT non-finite as-shot Camera2 gain normalization"
        }
        val donor = com.hinnka.mycamera.processor.experimentc.bjzhou.raw.DngSdkColorSpec
        val dng = donor.computeCameraToPcsD50(
            input.colorMatrix1, input.colorMatrix2,
            input.forwardMatrix1, input.forwardMatrix2,
            input.illuminant1Tag, input.illuminant2Tag, gains,
            cameraCalibration1 = input.calibrationMatrix1,
            cameraCalibration2 = input.calibrationMatrix2,
        ) ?: throw IllegalArgumentException("$COMPONENT original DngSdk ColorSpec rejected physical calibration")
        val white = donor.computeCameraWhite(
            input.colorMatrix1, input.colorMatrix2,
            input.forwardMatrix1, input.forwardMatrix2,
            input.illuminant1Tag, input.illuminant2Tag, gains,
            cameraCalibration1 = input.calibrationMatrix1,
            cameraCalibration2 = input.calibrationMatrix2,
        ) ?: throw IllegalArgumentException("$COMPONENT original donor camera white unavailable")
        val xy = donor.computeWhiteXy(
            input.colorMatrix1, input.colorMatrix2,
            input.forwardMatrix1, input.forwardMatrix2,
            input.illuminant1Tag, input.illuminant2Tag, gains,
            cameraCalibration1 = input.calibrationMatrix1,
            cameraCalibration2 = input.calibrationMatrix2,
        ) ?: throw IllegalArgumentException("$COMPONENT original donor scene white unavailable")
        val xyzToProfile = requireNotNull(donor.computeXyzD50ToGamut(com.hinnka.mycamera.processor.experimentc.bjzhou.raw.ColorSpace.ProPhoto)) {
            "$COMPONENT original ProPhoto PCS transform unavailable"
        }
        val xyzToSrgb = requireNotNull(donor.computeXyzD50ToGamut(com.hinnka.mycamera.processor.experimentc.bjzhou.raw.ColorSpace.SRGB)) {
            "$COMPONENT original linear sRGB transform unavailable"
        }
        val profileToXyz = requireNotNull(donor.invertMatrix3x3(xyzToProfile)) {
            "$COMPONENT singular original ProPhoto PCS transform"
        }
        val sensorToProfile = donor.multiplyMatrix3x3(xyzToProfile, dng)
        val profileToLinearSrgb = donor.multiplyMatrix3x3(xyzToSrgb, profileToXyz)
        val weight = donor.hueSatWeightForWhite(input.illuminant1Tag,
            input.illuminant2Tag, xy)
        require(sensorToProfile.all(Float::isFinite) &&
            profileToLinearSrgb.all(Float::isFinite) && white.all(Float::isFinite) &&
            weight.isFinite()) {
            "$COMPONENT nonfinite exact donor color calculation"
        }
        return Solved(sensorToProfile, profileToLinearSrgb, weight.toDouble(), white)
    }
}
