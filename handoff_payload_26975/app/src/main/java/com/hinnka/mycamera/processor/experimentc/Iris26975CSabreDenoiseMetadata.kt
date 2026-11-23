package com.hinnka.mycamera.processor.experimentc

/**
 * Experiment C-owned immutable Sabre -> native denoise transfer.
 * Neither the A/B RawMetadata class nor its Spatial/retuned-residual models are available
 * at this boundary. All coefficients come from the actual merged donor Sabre noise model.
 * This is only an Iris/PhotonCamera ABI adapter, NOT a replacement denoise algorithm.
 */
internal class Iris26975CSabreDenoiseMetadata(
    val cfaPattern: Int,
    whiteBalanceGains: FloatArray,
    lensShadingMap: FloatArray?,
    val lensShadingMapWidth: Int,
    val lensShadingMapHeight: Int,
    mgcDenoiseReadNoise: FloatArray,
    mgcDenoiseShotNoise: FloatArray,
    mgcDenoiseCorrelation: FloatArray,
) {
    val whiteBalanceGains: FloatArray = whiteBalanceGains.copyOf()
    val lensShadingMap: FloatArray? = lensShadingMap?.copyOf()
    val mgcDenoiseReadNoise: FloatArray = mgcDenoiseReadNoise.copyOf()
    val mgcDenoiseShotNoise: FloatArray = mgcDenoiseShotNoise.copyOf()
    val mgcDenoiseCorrelation: FloatArray = mgcDenoiseCorrelation.copyOf()

    init {
        require(cfaPattern in 0..3) { "C Sabre requires a standard Bayer phase" }
        require(this.whiteBalanceGains.size == 4 &&
            this.whiteBalanceGains.all { it.isFinite() && it > 0f }) {
            "C Sabre requires the real four-channel physical white balance"
        }
        require(this.mgcDenoiseReadNoise.size == 3 &&
            this.mgcDenoiseShotNoise.size == 3 &&
            this.mgcDenoiseCorrelation.size == 128 &&
            this.mgcDenoiseReadNoise.all { it.isFinite() && it >= 0f } &&
            this.mgcDenoiseShotNoise.all { it.isFinite() && it >= 0f } &&
            this.mgcDenoiseCorrelation.all { it.isFinite() && it >= 0f } &&
            (this.mgcDenoiseReadNoise.any { it > 0f } ||
                this.mgcDenoiseShotNoise.any { it > 0f })) {
            "C Sabre requires authentic nonempty donor merged noise"
        }
        val map = this.lensShadingMap
        if (map == null) {
            require(lensShadingMapWidth == 0 && lensShadingMapHeight == 0) {
                "C Sabre cannot invent an absent physical lens-shading map"
            }
        } else {
            val expected = lensShadingMapWidth.toLong() * lensShadingMapHeight.toLong() * 4L
            require(lensShadingMapWidth > 0 && lensShadingMapHeight > 0 &&
                expected in 1L..Int.MAX_VALUE.toLong() && map.size == expected.toInt() &&
                map.all { it.isFinite() && it > 0f }) {
                "C Sabre requires a valid actual physical lens-shading map"
            }
        }
    }
}
