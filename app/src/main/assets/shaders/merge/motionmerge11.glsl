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
     * Build 26220: normalized texture-aware reference retention.
     *
     * 26219 compared two vector-length expressions whose practical scales
     * were not guaranteed to match, so the retention mask could remain nearly
     * inactive. 26220 converts both local Bayer variation and predicted sensor
     * noise to comparable per-channel RMS amplitudes before forming the ratio.
     *
     * Flat/noisy regions keep temporal averaging. Fine structure rising above
     * predicted noise strongly limits repeated updates, retaining more of the
     * first/reference-derived foliage, fur, fabric, hair and text detail.
     */
    float localTextureRms =
            sqrt(
                    max(
                            dot(
                                    variance,
                                    vec4(0.25)
                            ),
                            EPS
                    )
            );

    float predictedNoiseRms =
            sqrt(
                    max(
                            dot(
                                    noise * noise,
                                    vec4(0.25)
                            ),
                            EPS
                    )
            );

    float textureToNoiseRatio =
            localTextureRms
                    / max(
                            predictedNoiseRms,
                            EPS
                    );

    float textureConfidence =
            smoothstep(
                    1.05,
                    2.50,
                    textureToNoiseRatio
            );

    float localContribution =
            clamp(
                    imageLoad(
                            contributionTexture,
                            xy
                    ).r,
                    0.0,
                    1.0
            );

    float uncertainContribution =
            1.0
                    - smoothstep(
                            0.30,
                            0.80,
                            localContribution
                    );

    float referenceRetention =
            clamp(
                    textureConfidence
                            * mix(
                                    0.78,
                                    1.0,
                                    uncertainContribution
                            ),
                    0.0,
                    1.0
            );

    float temporalUpdateScale =
            mix(
                    1.0,
                    0.18,
                    referenceRetention
            );

    localDifferenceCap *= temporalUpdateScale;

    localDifferenceCap =
            max(
                    localDifferenceCap,
                    predictedNoiseCap * 0.30
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

    imageStore(outTexture, xy, mix(base, diff/analogBalance+bayer, weight));
    //imageStore(outTexture, xy, diff);
}
