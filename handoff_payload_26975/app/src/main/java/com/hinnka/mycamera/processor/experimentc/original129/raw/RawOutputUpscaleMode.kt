package com.hinnka.mycamera.processor.experimentc.original129.raw

import com.hinnka.mycamera.processor.experimentc.original129.camera.MultiFrameConfig

enum class RawOutputUpscaleMode {
    LANCZOS3;

    fun resolveOutputScale(requestedScale: Float): Float =
        MultiFrameConfig.normalizeOutputScale(requestedScale)

    companion object {
        val DEFAULT: RawOutputUpscaleMode = LANCZOS3

        fun fromName(name: String?): RawOutputUpscaleMode =
            entries.firstOrNull { it.name == name } ?: DEFAULT
    }
}
