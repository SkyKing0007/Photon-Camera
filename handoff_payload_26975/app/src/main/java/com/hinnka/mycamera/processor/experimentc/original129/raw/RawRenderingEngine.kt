package com.hinnka.mycamera.processor.experimentc.original129.raw

const val RAW_RENDERING_ENGINE_DEFAULT_EXPOSURE_EV = 0.7f

enum class RawExposureCompensationDomain {
    Curve,
    Linear
}

enum class RawRenderingEngine(
    val shaderId: Int,
    val workingColorSpace: ColorSpace,
    val defaultExposureCompensationEv: Float,
    val exposureCompensationDomain: RawExposureCompensationDomain
) {
    AdobeCurve(
        shaderId = 0,
        workingColorSpace = ColorSpace.ProPhoto,
        defaultExposureCompensationEv = 0f,
        exposureCompensationDomain = RawExposureCompensationDomain.Curve
    ),
    ;

    companion object {
        fun fromPersistedName(
            value: String?,
            fallback: RawRenderingEngine = AdobeCurve
        ): RawRenderingEngine {
            return entries.firstOrNull { it.name.equals(value, ignoreCase = true) } ?: fallback
        }
    }
}
