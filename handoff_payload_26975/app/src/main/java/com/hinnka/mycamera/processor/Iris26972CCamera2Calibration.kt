package com.hinnka.mycamera.processor

import android.hardware.camera2.CameraCharacteristics
import android.hardware.camera2.CameraMetadata
import android.hardware.camera2.CameraManager
import android.hardware.camera2.TotalCaptureResult
import android.os.Build
import android.hardware.camera2.CaptureResult
import android.hardware.camera2.params.ColorSpaceTransform
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawCameraCalibration

/**
 * Experiment C-only: freeze a REAL physical Camera2 reference's dual-illuminant
 * DNG matrices, timestamp, neutral and the donor Resolve's actually applied WB.
 * No fallback to fabricated identity, preview/global camera matrices, or A/B state.
 * Caller must obtain [characteristics] for [physicalCameraId], and supply the
 * matching PHYSICAL capture result (not logical camera metadata) when applicable.
 * The isolated capture owner is source-wired but not Android build- or device-proven.
 */
internal object Iris26972CCamera2Calibration {
    private const val COMPONENT = "26972 C physical Camera2 color freeze"
    private const val PROVENANCE = "CAMERA2_DNG_POST_DONOR_WB_ONCE"

    internal class Frozen private constructor(
        val physicalCameraId: String,
        val referenceTimestampNs: Long,
        val interpolation: Double,
        appliedDonorGains: FloatArray,
        sensorToProfile: FloatArray,
        profileToLinearSrgb: FloatArray,
        cameraWhite: FloatArray,
    ) {
        private val frozenGains = appliedDonorGains.copyOf()
        private val frozenCameraMatrix = sensorToProfile.copyOf()
        private val frozenDisplayMatrix = profileToLinearSrgb.copyOf()
        private val frozenCameraWhite = cameraWhite.copyOf()

        /** C-only physical RAW identity. Independent of the old custom color developer. */
        internal fun requireMatches(burst: Iris26972CDonorSabreGpuBurst.Plan) {
            require(burst.frozenReferenceTimestampNs == referenceTimestampNs &&
                burst.frozenFrames.first().physicalCameraId == physicalCameraId &&
                burst.resolve.finalCameraRgbGains.contentEquals(frozenGains)) {
                "$COMPONENT frozen RAW reference / lens / applied WB changed"
            }
        }

        internal fun colorPlan(
            width: Int,
            height: Int,
            burst: Iris26972CDonorSabreGpuBurst.Plan,
        ): Iris26972CColorDeveloper.Plan {
            requireMatches(burst)
            val result = Iris26972CColorDeveloper.Plan(width, height,
                frozenCameraMatrix.copyOf(), frozenDisplayMatrix.copyOf(),
                physicalCameraId, PROVENANCE,frozenCameraWhite.copyOf(),
                referenceTimestampNs = referenceTimestampNs)
            Iris26972CColorDeveloper.validate(result)
            return result
        }

        companion object {
            internal fun of(physical: String, timestamp: Long,
                gains: FloatArray, solved: Iris26972CDngColorMath.Solved): Frozen =
                Frozen(physical, timestamp, solved.interpolation, gains,
                    solved.sensorToProfile, solved.profileToLinearSrgb,
                    solved.cameraWhite)
        }
    }

    private fun matrixOrNull(transform: ColorSpaceTransform?, name: String): FloatArray? {
        if (transform == null) return null
        // Camera2 getElement(column,row) corresponds to DNG row-major matrix.
        val data = FloatArray(9) { i ->
            transform.getElement(i % 3, i / 3).toFloat()
        }
        require(data.all { it.isFinite() }) { "$COMPONENT nonfinite $name" }
        return data
    }
    private fun requiredMatrix(transform: ColorSpaceTransform?, name: String): FloatArray =
        matrixOrNull(transform,name)
            ?: throw IllegalArgumentException("$COMPONENT missing physical $name")

    /**
     * Entry for a real Camera2 capture owner. Never pair a logical camera's
     * neutral/matrices with a physical RAW. For a logical multi-camera session,
     * require the explicit physical result and retrieve that lens's own
     * characteristics. Missing maps/IDs fail; never substitute the logical
     * result or currently selected preview lens.
     */
    internal fun freezeFromTotalCaptureResult(
        cameraManager: CameraManager,
        logicalCameraId: String,
        physicalCameraId: String,
        total: TotalCaptureResult,
        frozenReferenceTimestampNs: Long,
        actualResolveGains: FloatArray,
    ): Frozen {
        require(logicalCameraId.isNotBlank() && physicalCameraId.isNotBlank()) {
            "$COMPONENT missing Camera2 logical/physical identity"
        }
        val physicalResult: CaptureResult = if (logicalCameraId == physicalCameraId) {
            total
        } else {
            require(Build.VERSION.SDK_INT >= 28) {
                "$COMPONENT physical capture metadata unavailable below Android 9"
            }
            total.physicalCameraResults[physicalCameraId]
                ?: throw IllegalArgumentException(
                    "$COMPONENT missing actual physical RAW result for $physicalCameraId"
                )
        }
        // CameraManager consults characteristics by this actual physical ID.
        val physicalCharacteristics = cameraManager.getCameraCharacteristics(physicalCameraId)
        return freeze(physicalCameraId, physicalCameraId, physicalCameraId,
            physicalCharacteristics, physicalResult,
            frozenReferenceTimestampNs, actualResolveGains)
    }

    internal fun freeze(
        physicalCameraId: String,
        actualResultPhysicalCameraId: String,
        characteristicsPhysicalCameraId: String,
        characteristics: CameraCharacteristics,
        physicalReference: CaptureResult,
        frozenReferenceTimestampNs: Long,
        /** These MUST be the exact frozen [Resolve.Plan.finalCameraRgbGains]. */
        appliedDonorRgbGains: FloatArray,
    ): Frozen {
        require(physicalCameraId.isNotBlank() &&
            physicalCameraId == actualResultPhysicalCameraId &&
            physicalCameraId == characteristicsPhysicalCameraId &&
            frozenReferenceTimestampNs > 0L &&
            physicalReference.get(CaptureResult.SENSOR_TIMESTAMP) == frozenReferenceTimestampNs) {
            "$COMPONENT mismatched physical camera or actual RAW timestamp"
        }
        val neutral = physicalReference.get(CaptureResult.SENSOR_NEUTRAL_COLOR_POINT)
            ?: throw IllegalArgumentException("$COMPONENT missing frozen DNG neutral")
        require(neutral.size == 3) { "$COMPONENT invalid physical DNG neutral" }
        val first = characteristics.get(CameraCharacteristics.SENSOR_REFERENCE_ILLUMINANT1)
        val second = characteristics.get(CameraCharacteristics.SENSOR_REFERENCE_ILLUMINANT2)?.toInt()
        // Use the *actual original donor* fixed-calibration domain and defensive
        // deep-copy semantics before handing immutable physical matrices to the
        // pre-existing C color solver.  This does not imply that the C solver is
        // already DngSdkColorSpec, or that RAW/tone parity has been achieved.
        val fixed = RawCameraCalibration(
            colorMatrix1 = requiredMatrix(characteristics.get(CameraCharacteristics.SENSOR_COLOR_TRANSFORM1), "ColorMatrix1"),
            colorMatrix2 = matrixOrNull(characteristics.get(CameraCharacteristics.SENSOR_COLOR_TRANSFORM2), "ColorMatrix2"),
            calibrationIlluminant1 = first ?: 0,
            calibrationIlluminant2 = second ?: 0,
            cameraCalibration1 = matrixOrNull(characteristics.get(CameraCharacteristics.SENSOR_CALIBRATION_TRANSFORM1), "CalibrationMatrix1"),
            cameraCalibration2 = matrixOrNull(characteristics.get(CameraCharacteristics.SENSOR_CALIBRATION_TRANSFORM2), "CalibrationMatrix2"),
            forwardMatrix1 = matrixOrNull(characteristics.get(CameraCharacteristics.SENSOR_FORWARD_MATRIX1), "ForwardMatrix1"),
            forwardMatrix2 = matrixOrNull(characteristics.get(CameraCharacteristics.SENSOR_FORWARD_MATRIX2), "ForwardMatrix2"),
        )
        val solved = Iris26972CDngColorMath.solve(Iris26972CDngColorMath.Inputs(
            requireNotNull(fixed.colorMatrix1), fixed.colorMatrix2,
            fixed.cameraCalibration1, fixed.cameraCalibration2,
            fixed.forwardMatrix1, fixed.forwardMatrix2,
            FloatArray(3) { neutral[it].toFloat() },
            appliedDonorRgbGains.copyOf(),
            first ?: 0,
            second ?: 0,
        ))
        return Frozen.of(physicalCameraId, frozenReferenceTimestampNs,
            appliedDonorRgbGains.copyOf(), solved)
    }
}
