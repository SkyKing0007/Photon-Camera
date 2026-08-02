#define LAYOUT //
LAYOUT
precision highp float;
precision highp sampler2D;
//uniform highp usampler2D alterTexture;
uniform highp usampler2D inTex;
layout(rgba16f, binding = 0) uniform highp readonly image2D inTexture;
layout(rgba16f, binding = 1) uniform highp readonly image2D diffTexture;
layout(rgba16f, binding = 2) uniform highp writeonly image2D outTexture;
layout(rgba16f, binding = 3) uniform highp readonly image2D diffOrTexture;
layout(r32f, binding = 4) uniform highp image2D contributionTexture;

/*
 * Build 26228:
 * Motion-only temporal chroma-impulse statistics. Each correction is one
 * individual CFA channel, not a spatial blur or whole-pixel replacement.
 * Index 0 = total, 1 = R, 2 = G1, 3 = G2, 4 = B.
 */
layout(std430, binding = 5) buffer TemporalImpulseStats {
    uint impulseStats[];
};
#define TILE 2
#define CONCAT 1
uniform float weight;
uniform float weight2;
uniform float exposure;
uniform float noiseS;
uniform float noiseO;
uniform int motionEqualStack;
uniform float motionNoiseAllowance;
uniform float motionNoiseRecoveryStrength;
uniform float motionNoiseRecoveryGate;
uniform float contributionIncrement;
uniform float whiteLevel;
uniform vec4 blackLevel;
uniform vec4 analogBalance;
uniform int cfaPattern;
#import median
uint getBayer(ivec2 coords, highp usampler2D tex){
    return texelFetch(tex,coords,0).r;
}

vec4 getBayerVec(ivec2 coords, highp usampler2D tex){
    vec4 c0 = vec4(getBayer(coords,tex),getBayer(coords+ivec2(1,0),tex),getBayer(coords+ivec2(0,1),tex),getBayer(coords+ivec2(1,1),tex));
    return clamp((c0 - blackLevel)/(vec4(whiteLevel)-blackLevel), 0.0, 1.0);
}

vec4 robustWeight(vec4 w){
    return vec4(min(w.r, min(w.g, min(w.b, w.a))));
}

void recordTemporalImpulse(int channel) {
    atomicAdd(impulseStats[0], 1u);
    atomicAdd(impulseStats[channel + 1], 1u);
}

#define EPS 1e-6
void main() {
    ivec2 xy = ivec2(gl_GlobalInvocationID.xy);
    vec4 base = imageLoad(inTexture, xy);
    vec4 noise = sqrt(max(base * noiseS + noiseO,EPS));
    vec4 diff = imageLoad(diffTexture, xy);
    vec4 bayer = getBayerVec(xy*2, inTex);
    vec4 mean = vec4(0.0);
    vec4 medians[9];
    for (int i = -1; i <= 1; i++) {
        for (int j = -1; j <= 1; j++) {
            vec4 diff = getBayerVec((xy+ivec2(i, j))*2, inTex);
            //mean += diff;
            medians[(i+1)*3+(j+1)] = diff;
        }
    }
    //mean /= 9.0;
    mean = median9(medians);
    vec4 variance = vec4(0.0);
    for (int i = -1; i <= 1; i++) {
        for (int j = -1; j <= 1; j++) {
            vec4 diff = getBayerVec((xy+ivec2(i, j))*2, inTex);
            variance = max(((diff-mean)*(diff-mean)), variance);
        }
    }
    //variance /= 8.0;
    /*if(length(diff) > 0.1){
        diff = vec4(0.0);
    }*/
    //diff *= robustWeight(sqrt(vec4(1.0) - ((diff*diff)/(noise*noise*1.0 + diff*diff))));
    //float cexp = max(base.r, max(base.g, max(base.b, base.a)));
    /*if(cexp < exposure*0.7){
        diff*=weight;
    } else {
        diff*=weight2;
    }*/
    //vec4 alter = getBayerVec(xy*2, alterTexture);
    //vec4 alterFiltered = base + diff;
    //float d1 = length(alterFiltered - alter) + EPS;
    //float d2 = length(alterFiltered - base) + EPS;
    //alterFiltered = mix(alter, base, d1/(d1+d2));
    //alterFiltered = clamp(alterFiltered, min(alter, base), max(alter, base));
    //diff = alterFiltered - base;
    //vec4 diffOrigin = alter*vec4(exposure) - base;
    vec4 diffOrigin = imageLoad(diffOrTexture, xy);
    //if(dot(alter, vec4(0.25)) > exposure || dot(base, vec4(0.25)) > exposure) {
    //    diffOrigin = vec4(0.0);
    //}
    //diff = diffOrigin * (diff.x / (dot(diffOrigin, vec4(0.25)) + EPS));
    //diff = clamp(diff, min(diffOrigin, vec4(0.0)), max(diffOrigin, vec4(0.0)));
    //diff *= ((((noise*noise)/(noise*noise + diff*diff))));
    float localDifferenceCap =
            sqrt(length(variance)*1.4826 + EPS);

    float predictedNoiseCap =
            length(noise) * motionNoiseAllowance;

    /*
     * Build 26221:
     * Remove the ineffective texture-cap experiment from 26219/26220.
     * Keep the established noise-safe difference floor while the confirmed
     * post-demosaic ESD double-pass and forced downscale are corrected.
     */
    localDifferenceCap =
            max(
                    localDifferenceCap,
                    predictedNoiseCap
            );

    float reconstructedDifference =
            length(diff);

    float originDifference =
            length(diffOrigin);

    float lDiff =
            clamp(
                    reconstructedDifference,
                    EPS,
                    localDifferenceCap
            );

    float recoveryOuter =
            max(
                    predictedNoiseCap
                            * max(
                                    motionNoiseRecoveryGate,
                                    1.0
                            ),
                    predictedNoiseCap + EPS
            );

    float noiseConsistent =
            originDifference > EPS
                    ? 1.0
                            - smoothstep(
                                    predictedNoiseCap,
                                    recoveryOuter,
                                    originDifference
                            )
                    : 1.0;

    float recoveryApplied =
            clamp(
                    motionNoiseRecoveryStrength
                            * noiseConsistent,
                    0.0,
                    1.0
            );

    if (originDifference > EPS) {
        /*
         * Build 26172:
         *
         * The existing pyramid reconstruction can suppress an alternate
         * frame's independent sensor-noise difference and then rebuild that
         * alternate from the fixed reference Bayer sample. Repeating that
         * process carries reference-frame noise through the nominal stack.
         *
         * Restore the aligned alternate difference only when it remains
         * inside the predicted noise-consistent gate. Larger differences,
         * likely caused by scene motion or alignment error, keep the robust
         * pyramid result.
         */
        lDiff =
                min(
                        originDifference,
                        mix(
                                min(
                                        lDiff,
                                        originDifference
                                ),
                                originDifference,
                                recoveryApplied
                        )
                );
    }

    float preservedIndependentFraction =
            originDifference <= EPS
                    ? 1.0
                    : clamp(
                            lDiff
                                    / originDifference,
                            0.0,
                            1.0
                    );

    //float lDiff = length(diff);
    diff = diffOrigin / (originDifference + EPS) * lDiff;
    //diff *= ((((noise*noise)/(noise*noise + diff*diff))));

    float previousContribution =
            imageLoad(
                    contributionTexture,
                    xy
            ).r;

    imageStore(
            contributionTexture,
            xy,
            vec4(
                    clamp(
                            previousContribution
                                    + contributionIncrement
                                            * preservedIndependentFraction,
                            0.0,
                            1.0
                    ),
                    0.0,
                    0.0,
                    1.0
            )
    );

    /*
     * Build 26228 — conservative temporal chroma-impulse rejection.
     *
     * The aligned alternate candidate is already represented by
     * diff / analogBalance + bayer. Compare it with:
     *   1. the running temporal base,
     *   2. the same-CFA 3x3 spatial median,
     *   3. the modeled per-channel noise.
     *
     * A channel is corrected only when it is a strong positive impulse,
     * spatially unsupported, temporally unsupported, and substantially more
     * abnormal than the other three CFA channels. This avoids treating hair,
     * fabric, foliage, text edges, or ordinary luminance detail as defects.
     */
    vec4 correctedBase = base;
    vec4 correctedCandidate = diff / analogBalance + bayer;

    if (motionEqualStack == 1) {
        vec4 spatialDeviation =
                sqrt(
                        max(
                                variance,
                                vec4(EPS)
                        )
                );

        vec4 impulseThreshold =
                max(
                        noise * 8.0,
                        max(
                                spatialDeviation * 2.75,
                                vec4(0.025)
                        )
                );

        vec4 candidateResidual =
                correctedCandidate
                        - max(
                                correctedBase,
                                mean
                        );

        vec4 baseResidual =
                correctedBase
                        - max(
                                correctedCandidate,
                                mean
                        );

        float candidateOtherR = max(max(candidateResidual.g, candidateResidual.b), candidateResidual.a);
        float candidateOtherG1 = max(max(candidateResidual.r, candidateResidual.b), candidateResidual.a);
        float candidateOtherG2 = max(max(candidateResidual.r, candidateResidual.g), candidateResidual.a);
        float candidateOtherB = max(max(candidateResidual.r, candidateResidual.g), candidateResidual.b);

        float baseOtherR = max(max(baseResidual.g, baseResidual.b), baseResidual.a);
        float baseOtherG1 = max(max(baseResidual.r, baseResidual.b), baseResidual.a);
        float baseOtherG2 = max(max(baseResidual.r, baseResidual.g), baseResidual.a);
        float baseOtherB = max(max(baseResidual.r, baseResidual.g), baseResidual.b);

        if (
                candidateResidual.r > impulseThreshold.r
                        && candidateResidual.r
                                > max(candidateOtherR, 0.0) * 1.35
                                        + noise.r * 2.0
        ) {
            correctedCandidate.r =
                    clamp(
                            mix(correctedBase.r, mean.r, 0.20),
                            0.0,
                            1.0
                    );
            recordTemporalImpulse(0);
        } else if (
                baseResidual.r > impulseThreshold.r
                        && baseResidual.r
                                > max(baseOtherR, 0.0) * 1.35
                                        + noise.r * 2.0
        ) {
            correctedBase.r =
                    clamp(
                            mix(correctedCandidate.r, mean.r, 0.20),
                            0.0,
                            1.0
                    );
            recordTemporalImpulse(0);
        }

        if (
                candidateResidual.g > impulseThreshold.g
                        && candidateResidual.g
                                > max(candidateOtherG1, 0.0) * 1.35
                                        + noise.g * 2.0
        ) {
            correctedCandidate.g =
                    clamp(
                            mix(correctedBase.g, mean.g, 0.20),
                            0.0,
                            1.0
                    );
            recordTemporalImpulse(1);
        } else if (
                baseResidual.g > impulseThreshold.g
                        && baseResidual.g
                                > max(baseOtherG1, 0.0) * 1.35
                                        + noise.g * 2.0
        ) {
            correctedBase.g =
                    clamp(
                            mix(correctedCandidate.g, mean.g, 0.20),
                            0.0,
                            1.0
                    );
            recordTemporalImpulse(1);
        }

        if (
                candidateResidual.b > impulseThreshold.b
                        && candidateResidual.b
                                > max(candidateOtherG2, 0.0) * 1.35
                                        + noise.b * 2.0
        ) {
            correctedCandidate.b =
                    clamp(
                            mix(correctedBase.b, mean.b, 0.20),
                            0.0,
                            1.0
                    );
            recordTemporalImpulse(2);
        } else if (
                baseResidual.b > impulseThreshold.b
                        && baseResidual.b
                                > max(baseOtherG2, 0.0) * 1.35
                                        + noise.b * 2.0
        ) {
            correctedBase.b =
                    clamp(
                            mix(correctedCandidate.b, mean.b, 0.20),
                            0.0,
                            1.0
                    );
            recordTemporalImpulse(2);
        }

        if (
                candidateResidual.a > impulseThreshold.a
                        && candidateResidual.a
                                > max(candidateOtherB, 0.0) * 1.35
                                        + noise.a * 2.0
        ) {
            correctedCandidate.a =
                    clamp(
                            mix(correctedBase.a, mean.a, 0.20),
                            0.0,
                            1.0
                    );
            recordTemporalImpulse(3);
        } else if (
                baseResidual.a > impulseThreshold.a
                        && baseResidual.a
                                > max(baseOtherB, 0.0) * 1.35
                                        + noise.a * 2.0
        ) {
            correctedBase.a =
                    clamp(
                            mix(correctedCandidate.a, mean.a, 0.20),
                            0.0,
                            1.0
                    );
            recordTemporalImpulse(3);
        }
    }

    imageStore(
            outTexture,
            xy,
            mix(
                    correctedBase,
                    correctedCandidate,
                    weight
            )
    );
    //imageStore(outTexture, xy, diff);
}
