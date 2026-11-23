package com.hinnka.mycamera.processor.experimentc.bjzhou.raw

/** Copied unchanged from pinned donor DcpProfile.kt, apart from isolated package. */
enum class DcpDefaultBlackRender(val tagValue: Int) {
    Auto(0),
    None(1);

    companion object {
        fun fromTagValue(tagValue: Int?): DcpDefaultBlackRender {
            return values().firstOrNull { it.tagValue == tagValue } ?: Auto
        }
    }
}
