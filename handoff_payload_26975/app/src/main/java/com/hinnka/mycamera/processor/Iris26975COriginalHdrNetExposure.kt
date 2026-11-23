package com.hinnka.mycamera.processor

import com.hinnka.mycamera.processor.experimentc.bjzhou.raw.RawHdrReferenceMath
import kotlin.math.pow

/**
 * C-private immutable boundary for ORIGINAL, persisted donor HDRNet provenance.
 *
 * There is deliberately NO Camera2/exposure-product inference or synthetic PGTM.
 * The complete donor HDRNet generator is not yet connected. Only a caller holding
 * a real pinned-donor HDRNet PGTM and its matching original exposure metadata
 * may invoke [fromPinnedDonor]. Ordinary Camera2 captures never instantiate it.
 */
internal object Iris26975COriginalHdrNetExposure {
    internal class Frozen private constructor(
        val physicalCameraId: String,
        val referenceTimestampNs: Long,
        val hdrRatio: Float,
        val sourceToShortGain: Float,
        val postExposureEv: Float?,
        val inputExposureEv: Float?,
        val explicitEditEv: Float,
    ) {
        /** Original RawDemosaicProcessor: HDRNet long exposure, then user edit EV once. */
        fun originalSceneGain(): Float {
            val original = requireNotNull(RawHdrReferenceMath.hdrNetSceneExposureGain(
                hdrRatio, sourceToShortGain, postExposureEv, inputExposureEv,
            )) { "Pinned donor HDRNet scene exposure is invalid" }
            return (original * 2f.pow(explicitEditEv)).also { gain ->
                require(gain.isFinite() && gain > 0f) {
                    "Pinned donor HDRNet exposure after user edit is invalid"
                }
            }
        }

        fun matches(physicalCameraId: String, referenceTimestampNs: Long): Boolean =
            this.physicalCameraId == physicalCameraId &&
                this.referenceTimestampNs == referenceTimestampNs

        companion object {
            /** Only real persisted HDRNet values; all fields must refer to the same RAW. */
            fun fromPinnedDonor(
                physicalCameraId: String,
                referenceTimestampNs: Long,
                hdrRatio: Float,
                sourceToShortGain: Float,
                postExposureEv: Float?,
                inputExposureEv: Float?,
                explicitEditEv: Float,
            ): Frozen {
                require(physicalCameraId.isNotBlank() && referenceTimestampNs > 0L &&
                    hdrRatio.isFinite() && hdrRatio >= 1f &&
                    sourceToShortGain.isFinite() && sourceToShortGain > 0f &&
                    (postExposureEv == null || postExposureEv.isFinite()) &&
                    (inputExposureEv == null || inputExposureEv.isFinite()) &&
                    explicitEditEv.isFinite()) {
                    "C HDRNet requires genuine finite donor exposure and physical RAW reference"
                }
                return Frozen(physicalCameraId, referenceTimestampNs, hdrRatio,
                    sourceToShortGain, postExposureEv, inputExposureEv, explicitEditEv)
                    .also { it.originalSceneGain() }
            }
        }
    }
}
