package com.hinnka.mycamera.processor

/**
 * IRIS_26856_AMAZE_PRE_DEMOSAIC_SINGLE_OWNER_CONTRACT.
 *
 * 26855's NORMAL temporal CFA numerator is NOT raw code and is NOT a finished
 * Bayer image: it contains the already black-subtracted, exposure-normalized,
 * *sensor-neutral* weighted R/G1/G2/B values in physical 2x2 phase order.
 *
 * The only legal direct AMaZE source is each normalized site's numerator / its
 * shared, locally admitted temporal support. Do NOT invoke 26852's backwards
 * raw-code extract, the Sabre RGB merge, or MgcSabreResolver on this branch.
 * Do NOT divide by white a second time or apply temporary calculation WB.
 *
 * This is an isolated candidate-stage input contract, NOT an AMaZE backend.
 * It must remain unused until an actual numerically verified AMaZE GPU owner,
 * physical SHORT/HDR integration and safe two-image publisher are implemented.
 */
internal object GlesIris26856AmazeCfaHandoff {
    const val owner = "IRIS_26856_AMAZE_PRE_DEMOSAIC_SINGLE_OWNER_CONTRACT"

    /** The four values are sampled from the *physical* 2x2 RAW cell: TL, TR, BL, BR.
     * RAWR's packed CFA AMaZE importer REQUIRES canonical {R,G1,G2,B} channel
     * ordering and uses BayerPattern to choose which canonical component belongs
     * to each physical RAW location. The shader must explicitly remap phases.
     */
    val packedBayerShader = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uWeightedPhases;
        uniform sampler2D uSharedSupport;
        uniform sampler2D uPhaseNoiseMoments26863;
        uniform ivec2 uCellSize;
        uniform int uBayerPattern;
        layout(location=0) out vec4 oPackedSensorCfa;
        layout(location=1) out vec4 oPhysicalSupport;
        layout(location=2) out vec4 oBNoiseVariance26863;
        void main() {
            ivec2 q = clamp(ivec2(gl_FragCoord.xy), ivec2(0), uCellSize - ivec2(1));
            vec4 weighted = texelFetch(uWeightedPhases, q, 0);
            float support = texelFetch(uSharedSupport, q, 0).r;
            // Never invent valid temporal support for an unsupported output site.
            float valid = (support > 1.0e-7) ? 1.0 : 0.0;
            vec4 phase = (weighted / max(support, 1.0e-7)) * valid;
            // The source is indexed by physical site TL/TR/BL/BR, but the
            // pinned RAWR PackedCfaImageView ABI is {R,G1,G2,B}.
            vec4 canonical = phase;
            if (uBayerPattern == 1) canonical = phase.grab; // GRBG: R=TR, G1=TL, G2=BR, B=BL
            else if (uBayerPattern == 2) canonical = phase.barg; // GBRG: R=BL, G1=BR, G2=TL, B=TR
            else if (uBayerPattern == 3) canonical = phase.abgr; // BGGR: R=BR, G1=BL, G2=TR, B=TL
            // No [0,1] clipping: a future physical SHORT/extended-HDR owner
            // needs actual camera-linear radiance, not flattened highlights.
            oPackedSensorCfa = canonical;
            // The exact same admitted sum(w) normalizes both signal and variance.
            vec4 physicalVariance = (max(texelFetch(uPhaseNoiseMoments26863,q,0),vec4(0.0))/256.0) /
                max(support*support,1.0e-12) * valid;
            vec4 noiseCanonical=physicalVariance;
            if (uBayerPattern==1) noiseCanonical=physicalVariance.grab;
            else if (uBayerPattern==2) noiseCanonical=physicalVariance.barg;
            else if (uBayerPattern==3) noiseCanonical=physicalVariance.abgr;
            float sumW2=texelFetch(uSharedSupport,q,0).a;
            float effectiveN=support*support/max(sumW2,1.0e-8);
            oPhysicalSupport = vec4(support,valid,effectiveN,0.0);
            oBNoiseVariance26863=noiseCanonical;
        }
    """.trimIndent()

    /** Fail closed on every unknown geometry or CFA instead of silently
     * reindexing a colour channel or inventing a binned-sensor mapping. */
    fun verifyInput(rawWidth: Int, rawHeight: Int, pattern: Int,
                    cellWidth: Int, cellHeight: Int, normalCount: Int) {
        require(rawWidth > 0 && rawHeight > 0 && rawWidth % 2 == 0 && rawHeight % 2 == 0) {
            "26856 AMaZE input requires even physical Bayer dimensions"
        }
        require(cellWidth * 2 == rawWidth && cellHeight * 2 == rawHeight) {
            "26856 packed Bayer dimension mismatch"
        }
        require(pattern in 0..3) { "26856 AMaZE input requires exact known Bayer pattern" }
        require(normalCount >= 2) { "26856 AMaZE comparison is a multiframe path; no single-frame fallback" }
    }
}
