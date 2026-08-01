precision highp float;
precision highp sampler2D;

uniform sampler2D InputBuffer;
uniform sampler2D GuideBuffer;
uniform int yOffset;

out vec4 Output;

#define DIRECTION 0
#define KSIZE 4
#define SAMPLESTEP 6
#define CHROMASTRENGTH 0.0
#define GUIDESIGMA 0.08
#define NOISES 0.0
#define SHADOWNEUTRALIZATION 0.0
#define NOISEO 0.0

float lumaValue(vec3 rgb) {
    return dot(
            rgb,
            vec3(0.25, 0.50, 0.25)
    );
}

vec2 opponentChroma(vec3 rgb) {
    return vec2(
            rgb.r - rgb.g,
            rgb.b - rgb.g
    );
}

vec3 reconstructFromLumaChroma(
        float y,
        vec2 uv
) {
    float r =
            y + 0.75 * uv.x - 0.25 * uv.y;

    float g =
            y - 0.25 * uv.x - 0.25 * uv.y;

    float b =
            y - 0.25 * uv.x + 0.75 * uv.y;

    return vec3(r, g, b);
}

float gaussianWeight(
        float value,
        float sigma
) {
    float safeSigma =
            max(
                    sigma,
                    0.0001
            );

    float normalized =
            value / safeSigma;

    return exp(
            -0.5 * normalized * normalized
    );
}

void main() {
    ivec2 xy =
            ivec2(gl_FragCoord.xy)
                    + ivec2(0, yOffset);

    ivec2 imageSize =
            textureSize(
                    GuideBuffer,
                    0
            );

    ivec2 maximumCoordinate =
            imageSize - ivec2(1);

    vec3 guideCenter =
            texelFetch(
                    GuideBuffer,
                    xy,
                    0
            ).rgb;

    vec3 inputCenter =
            texelFetch(
                    InputBuffer,
                    xy,
                    0
            ).rgb;

    float centerLuma =
            lumaValue(
                    guideCenter
            );

    vec2 centerChroma =
            opponentChroma(
                    inputCenter
            );

    float noiseSigma =
            sqrt(
                    max(
                            NOISES
                                    * max(centerLuma, 0.0)
                                    + NOISEO,
                            0.000001
                    )
            );

    float localGradient =
            0.0;

    const ivec2 localOffsets[4] =
            ivec2[4](
                    ivec2(-1, 0),
                    ivec2(1, 0),
                    ivec2(0, -1),
                    ivec2(0, 1)
            );

    for (int index = 0; index < 4; index++) {
        ivec2 localCoordinate =
                clamp(
                        xy + localOffsets[index],
                        ivec2(0),
                        maximumCoordinate
                );

        float localLuma =
                lumaValue(
                        texelFetch(
                                GuideBuffer,
                                localCoordinate,
                                0
                        ).rgb
                );

        localGradient =
                max(
                        localGradient,
                        abs(
                                localLuma - centerLuma
                        )
                );
    }

    float flatThresholdLow =
            max(
                    0.025,
                    noiseSigma * 1.5
            );

    float flatThresholdHigh =
            max(
                    0.100,
                    noiseSigma * 5.0
            );

    float flatMask =
            1.0
                    - smoothstep(
                            flatThresholdLow,
                            flatThresholdHigh,
                            localGradient
                    );

    float darkMask =
            1.0
                    - smoothstep(
                            0.58,
                            0.92,
                            centerLuma
                    );

    float centerSaturation =
            length(
                    opponentChroma(
                            guideCenter
                    )
            );

    float saturatedCenterProtection =
            1.0
                    - smoothstep(
                            0.45,
                            0.75,
                            centerSaturation
                    );

    vec2 accumulatedChroma =
            vec2(0.0);

    float accumulatedWeight =
            0.0;

    ivec2 direction =
            DIRECTION == 0
                    ? ivec2(1, 0)
                    : ivec2(0, 1);

    for (int offsetIndex = -KSIZE;
         offsetIndex <= KSIZE;
         offsetIndex++) {

        ivec2 sampleCoordinate =
                clamp(
                        xy
                                + direction
                                * offsetIndex
                                * SAMPLESTEP,
                        ivec2(0),
                        maximumCoordinate
                );

        vec3 sampleGuide =
                texelFetch(
                        GuideBuffer,
                        sampleCoordinate,
                        0
                ).rgb;

        vec3 sampleInput =
                texelFetch(
                        InputBuffer,
                        sampleCoordinate,
                        0
                ).rgb;

        float sampleLuma =
                lumaValue(
                        sampleGuide
                );

        vec2 sampleChroma =
                opponentChroma(
                        sampleInput
                );

        float spatialWeight =
                gaussianWeight(
                        float(offsetIndex),
                        3.5
                );

        float lumaGuideWeight =
                gaussianWeight(
                        sampleLuma - centerLuma,
                        GUIDESIGMA
                );

        /*
         * Do not compare sample chroma with the center chroma. The 26169
         * comparison caused pixels inside a colored cloud to reinforce that
         * same cloud. Only strongly saturated real colors are downweighted.
         */
        float sampleSaturation =
                length(
                        opponentChroma(
                                sampleGuide
                        )
                );

        float sampleColorProtection =
                1.0
                        - smoothstep(
                                0.45,
                                0.85,
                                sampleSaturation
                        );

        float sampleWeight =
                spatialWeight
                        * lumaGuideWeight
                        * mix(
                                0.15,
                                1.0,
                                sampleColorProtection
                          );

        accumulatedChroma +=
                sampleChroma
                        * sampleWeight;

        accumulatedWeight +=
                sampleWeight;
    }

    vec2 filteredChroma =
            accumulatedWeight > 0.000001
                    ? accumulatedChroma
                            / accumulatedWeight
                    : centerChroma;

    float blend =
            clamp(
                    CHROMASTRENGTH
                            * flatMask
                            * darkMask
                            * saturatedCenterProtection,
                    0.0,
                    1.0
            );

    vec2 outputChroma =
            mix(
                    centerChroma,
                    filteredChroma,
                    blend
            );

    /*
     * Equal per-channel black levels were validated in the supplied session.
     * Instead of inventing a black offset, gently reduce only residual
     * chroma in the deepest, flat, high-ISO shadows.
     */
    float deepestShadowMask =
            1.0
                    - smoothstep(
                            0.10,
                            0.32,
                            centerLuma
                    );

    float neutralityStrength =
            SHADOWNEUTRALIZATION
                    * CHROMASTRENGTH
                    * flatMask
                    * deepestShadowMask
                    * saturatedCenterProtection;

    outputChroma *=
            1.0
                    - clamp(
                            neutralityStrength,
                            0.0,
                            SHADOWNEUTRALIZATION
                    );

    vec3 outputRgb =
            reconstructFromLumaChroma(
                    centerLuma,
                    outputChroma
            );

    Output =
            vec4(
                    clamp(
                            outputRgb,
                            0.0,
                            1.0
                    ),
                    1.0
            );
}
