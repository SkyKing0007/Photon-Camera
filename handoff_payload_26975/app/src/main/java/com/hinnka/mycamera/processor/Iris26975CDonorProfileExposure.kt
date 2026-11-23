package com.hinnka.mycamera.processor

import com.hinnka.mycamera.processor.experimentc.original129.raw.DcpDefaultBlackRender
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawProfileExposureGl

/**
 * Experiment C's immutable parameterization of the ORIGINAL bjzhou/PhotonCamera
 * 1.29.0 RawProfileExposureGl Adobe branch. The default native-camera profile
 * has Auto black rendering and a profile ramp, even when there is no DCP.
 *
 * A Camera2 RAW capture with no embedded DNG baseline/profile gets the original
 * donor defaults (baseline EV 0, shadow scale 1), not a guessed per-device EV.
 * The metadata source is kept explicit so these values cannot be silently
 * mistaken for an imported DNG profile's actual values.
 */
internal object Iris26975CDonorProfileExposure {
    internal data class Frozen(
        val exposureEv: Float,
        val linearGain: Float,
        val slope: Float,
        val black: Float,
        val radius: Float,
        val qScale: Float,
        val supportOverrange: Boolean,
        val toneEnabled: Boolean,
        val toneSlope: Float,
        val toneA: Float,
        val toneB: Float,
        val toneC: Float,
    ) {
        fun validate() {
            require(exposureEv.isFinite() && linearGain.isFinite() && linearGain > 0f &&
                slope.isFinite() && slope > 0f && black.isFinite() && black >= 0f &&
                radius.isFinite() && radius >= 0f && qScale.isFinite() && qScale >= 0f &&
                toneSlope.isFinite() && toneSlope > 0f && toneA.isFinite() &&
                toneB.isFinite() && toneC.isFinite()) {
                "26975 C donor profile exposure is nonfinite"
            }
        }
    }
    /** Original RawProfileExposureGl.compute: defaultBlackRender=Auto, useRamp=true. */
    fun originalAdobeCameraDefault(
        explicitExposureEv: Float = 0f,
        dngBaselineExposureEv: Float = 0f,
        shadowScale: Float = 1f,
    ): Frozen {
        require(explicitExposureEv.isFinite() && dngBaselineExposureEv.isFinite()) {
            "26975 C donor profile exposure requires real finite inputs"
        }
        // The original pinned donor code computes these uniform values. This
        // C-only boundary keeps the established Frozen API, but no longer owns
        // an independent approximation of Adobe profile exposure or Auto black.
        val donor = RawProfileExposureGl.compute(
            profileExposureCompensation = explicitExposureEv,
            dngBaselineExposure = dngBaselineExposureEv,
            defaultBlackRender = DcpDefaultBlackRender.Auto,
            shadowScale = shadowScale,
            supportOverrange = false,
            useRamp = true,
        )
        return Frozen(
            exposureEv = donor.exposureEv,
            linearGain = donor.linearGain,
            slope = donor.rampSlope,
            black = donor.rampBlack,
            radius = donor.rampRadius,
            qScale = donor.rampQScale,
            supportOverrange = donor.supportOverrange,
            toneEnabled = donor.toneEnabled,
            toneSlope = donor.toneSlope,
            toneA = donor.toneA,
            toneB = donor.toneB,
            toneC = donor.toneC,
        ).also(Frozen::validate)
    }
}
