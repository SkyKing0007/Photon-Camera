package com.hinnka.mycamera.processor.experimentc.original129.hdr

interface GainmapProducer {
    suspend fun build(
        source: GainmapSourceSet,
        strength: Float = HdrGainmapStrength.DEFAULT
    ): GainmapResult?
}
