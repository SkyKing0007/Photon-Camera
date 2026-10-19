package com.hinnka.mycamera.processor

/**
 * IRIS_26856_B_PHYSICAL_SHORT_SCALAR_RADIANCE_TRANSFER
 *
 * B uses RAWR AMaZE/Lab/FCC for its independent chroma and structure.
 * The existing 26651 *pre-VGN* NORMAL/SHORT fusion supplies only the already-
 * vetted physical radiance increment: no Sabre RGB/chroma is substituted for B,
 * no second SHORT alignment or source-admission policy is invented, and no
 * post-VGN color is sampled. Identity for every absent/rejected SHORT sample.
 *
 * Trusted three-channel SHORT chroma restoration is enabled ONLY under the
 * existing 26651 full-NORMAL-color-loss + spatial consensus + SHORT agreement
 * proof, never by geometric proximity, extra demosaic or a guessed hue.
 * Production B/A+B publication remains separately guarded.
 */
internal object GlesIris26856ShortHdrTransfer {
    val scalarRadianceShader = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform highp sampler2D uBNormalSensorRgb;
        uniform highp sampler2D uNormalPreVgnMaster;
        uniform highp sampler2D uFusedPreVgnMaster;
        uniform highp sampler2D uShortDecision;
        uniform highp sampler2D uShortColorValidity;
        uniform ivec2 uSize;
        uniform float uPhysicalShortExposureRatio;
        layout(location = 0) out vec4 oBExtendedSensorRgb;

        float radiance(vec3 rgb) {
            // Exactly the scalar 26651 NORMAL/SHORT owner's luma weights.
            return dot(max(rgb, vec3(0.0)), vec3(0.25, 0.50, 0.25));
        }
        void main() {
            ivec2 p = clamp(ivec2(gl_FragCoord.xy), ivec2(0), uSize - ivec2(1));
            vec4 b = texelFetch(uBNormalSensorRgb, p, 0);
            int packed = int(floor(texelFetch(uShortDecision, p, 0).r * 255.0 + 0.5));
            // 192..255 mean geometry/source/SNR rejection in the exact 26651 owner.
            // 0..191 encode four color states x 48 physical radiance levels.
            // State 3 is reserved for agreeing, locally-consensual SHORT chroma;
            // state 2 explicitly rejects discordant cyan/magenta SHORT chroma.
            if (packed > 191 || packed < 0 || packed % 48 == 0) {
                oBExtendedSensorRgb = b;
                return;
            }
            float normalY = radiance(texelFetch(uNormalPreVgnMaster, p, 0).rgb);
            float fusedY = radiance(texelFetch(uFusedPreVgnMaster, p, 0).rgb);
            if (normalY < 0.05 || fusedY <= normalY || !(uPhysicalShortExposureRatio > 1.0)) {
                oBExtendedSensorRgb = b;
                return;
            }
            float gain = fusedY / normalY;
            if (isnan(gain) || isinf(gain)) {
                oBExtendedSensorRgb = b;
                return;
            }
            // The physical exposure ratio is an upper sanity bound, NOT a
            // display shoulder, clipping threshold, or new tone operator.
            gain = clamp(gain, 1.0, uPhysicalShortExposureRatio);
            vec3 bRadiance = b.rgb * gain;

            /* IRIS_26856_B_TRUSTED_SHORT_CHROMA_DIFFERENCE
             * The 26651 physical SHORT owner already proved three-channel NORMAL
             * CFA loss, neighborhood consensus and agreement with aligned SHORT
             * chromaticity before emitting colorState=3. Only in that state may
             * B inherit the color DIFFERENCE inferred from the verified pre-VGN
             * NORMAL->SHORT comparison. Never replace B with Sabre color, never
             * consume VGN color, and never use color state 1 or 2 as evidence.
             * The continuous validity gate excludes unstable or barely accepted
             * estimates. Normal-only, rejected, outlier and absent SHORT inputs
             * remain exactly B (or B with its already authorized scalar gain).
             */
            int colorState = packed / 48;
            if (colorState == 3) {
                float evidence = texelFetch(uShortColorValidity, p, 0).r;
                if (evidence > 0.03 && normalY > 0.05 && fusedY > 0.05) {
                    vec3 n = max(texelFetch(uNormalPreVgnMaster, p, 0).rgb, vec3(0.0));
                    vec3 f = max(texelFetch(uFusedPreVgnMaster, p, 0).rgb, vec3(0.0));
                    // Relative chromaticity is radiometrically invariant. Transfer
                    // the delta only: the baseline hue/structure stays RAWR-owned.
                    vec3 delta = f / fusedY - n / normalY;
                    float trust = smoothstep(0.03, 0.35, evidence);
                    // Reject exceptionally large chromaticity excursions instead
                    // of manufacturing a hard cyan/magenta transition at clipping.
                    float magnitude = max(max(abs(delta.r), abs(delta.g)), abs(delta.b));
                    trust *= 1.0 - smoothstep(0.25, 0.50, magnitude);
                    vec3 candidate = bRadiance + (radiance(bRadiance) * trust) * delta;
                    if (!any(isnan(candidate)) && !any(isinf(candidate))) {
                        // The color difference has mathematically zero luma;
                        // correct half-float rounding to preserve scalar HDR.
                        float candidateY = radiance(candidate);
                        if (candidateY > 1.0e-5) {
                            bRadiance = candidate * (radiance(bRadiance) / candidateY);
                        }
                    }
                }
            }
            oBExtendedSensorRgb = vec4(bRadiance, b.a);
        }
    """.trimIndent()
}
