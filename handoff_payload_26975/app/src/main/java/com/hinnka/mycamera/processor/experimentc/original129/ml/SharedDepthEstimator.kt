package com.hinnka.mycamera.processor.experimentc.original129.ml

import android.content.Context

/** Optional donor depth-model prewarming. Pro Sabre 1x does not enable depth ML.
 * No alternate ML renderer may silently enter Experiment C. */
internal object SharedDepthEstimator {
    suspend fun prewarm(context: Context): Nothing =
        throw IllegalStateException("Experiment C Pro Sabre forbids an unverified depth model")
}
