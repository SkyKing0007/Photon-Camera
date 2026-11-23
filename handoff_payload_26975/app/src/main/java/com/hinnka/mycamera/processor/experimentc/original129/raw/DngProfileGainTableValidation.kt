package com.hinnka.mycamera.processor.experimentc.original129.raw

/** Validates large PGTM gain arrays outside Kotlin's per-element hot loop. */
internal object DngProfileGainTableValidation {
    private val nativeAvailable = runCatching {
        com.hinnka.mycamera.processor.experimentc.Iris26975COriginalNative.ensureLoaded()
    }.isSuccess

    fun validate(gains: FloatArray, minimum: Float, maximum: Float): Boolean {
        if (gains.isEmpty() || !minimum.isFinite() || !maximum.isFinite() || maximum < minimum) {
            return false
        }
        if (nativeAvailable) {
            val nativeResult = runCatching {
                validateGainsNative(gains, minimum, maximum)
            }.getOrNull()
            if (nativeResult != null) return nativeResult
        }
        // Local JVM tests do not load the Android native library. Keep an allocation-free
        // reference fallback; production reaches the OpenMP implementation above.
        for (index in gains.indices) {
            val value = gains[index]
            if (!value.isFinite() || value < minimum || value > maximum) return false
        }
        return true
    }

    private external fun validateGainsNative(
        gains: FloatArray,
        minimum: Float,
        maximum: Float,
    ): Boolean
}
