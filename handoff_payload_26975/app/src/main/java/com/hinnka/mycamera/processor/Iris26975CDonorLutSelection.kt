package com.hinnka.mycamera.processor

/**
 * Experiment C LUT ownership, matching the donor's explicit `none` choice.
 *
 * The user chose the donor's NO LUT look as Experiment C's default. This does
 * not disable the AdobeCurve RAW profile/exposure/tone path, MGC finishing, or
 * the UHDR reference/gainmap. It only avoids applying an additional creative
 * LUT or RAW baseline LUT unless explicitly selected for this C capture.
 *
 * The donor always derives the UHDR luminance sidecar from its actual before-
 * and after-LUT SDR buffers. Even when the two layers are `none`, do not fake
 * or omit that measured sidecar during future live UHDR integration.
 *
 * This C-only selection policy does not read or modify A/B preferences.
 */
internal object Iris26975CDonorLutSelection {
    const val NONE = "none"
    const val DEFAULT_BASELINE_ID = NONE
    const val DEFAULT_CREATIVE_ID = NONE

    data class Frozen(val baselineId: String, val creativeId: String) {
        val hasBaseline: Boolean get() = baselineId != NONE
        val hasCreative: Boolean get() = creativeId != NONE
        val isNoLut: Boolean get() = !hasBaseline && !hasCreative
    }

    /** `null`/blank means the experiment default, not the donor APK's Standard preset. */
    fun freeze(baselineId: String? = null, creativeId: String? = null): Frozen = Frozen(
        baselineId = baselineId?.trim()?.takeIf { it.isNotEmpty() } ?: DEFAULT_BASELINE_ID,
        creativeId = creativeId?.trim()?.takeIf { it.isNotEmpty() } ?: DEFAULT_CREATIVE_ID,
    )
}
