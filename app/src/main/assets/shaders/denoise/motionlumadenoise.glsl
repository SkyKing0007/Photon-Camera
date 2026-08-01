precision highp float;
precision highp sampler2D;

uniform sampler2D InputBuffer;
uniform sampler2D GuideBuffer;
uniform int yOffset;

out vec4 Output;

#define DIRECTION 0
#define KSIZE 3
#define STRENGTH 0.0
#define NOISEGAIN 1.35
#define NOISES 0.0
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

    float guideLuma =
            lumaValue(
                    guideCenter
            );

    float inputLuma =
            lumaValue(
                    inputCenter
            );

    vec2 originalChroma =
            opponentChroma(
                    guideCenter
            );

    float noiseSigma =
            sqrt(
                    max(
                            NOISES
                                    * max(guideLuma, 0.0)
                                    + NOISEO,
                            0.000001
                    )
            )
                    * NOISEGAIN;

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
                                localLuma - guideLuma
                        )
                );
    }

    ivec2 direction =
            DIRECTION == 0
                    ? ivec2(1, 0)
                    : ivec2(0, 1);

    float accumulatedLuma =
            0.0;

    float accumulatedWeight =
            0.0;

    float guideSigma =
            max(
                    0.025,
                    noiseSigma * 4.0
            );

    for (int offsetIndex = -KSIZE;
         offsetIndex <= KSIZE;
         offsetIndex++) {

        ivec2 sampleCoordinate =
                clamp(
                        xy
                                + direction
                                * offsetIndex,
                        ivec2(0),
                        maximumCoordinate
                );

        float sampleGuideLuma =
                lumaValue(
                        texelFetch(
                                GuideBuffer,
                                sampleCoordinate,
                                0
                        ).rgb
                );

        float sampleInputLuma =
                lumaValue(
                        texelFetch(
                                InputBuffer,
                                sampleCoordinate,
                                0
                        ).rgb
                );

        float spatialWeight =
                gaussianWeight(
                        float(offsetIndex),
                        1.65
                );

        float guideWeight =
                gaussianWeight(
                        sampleGuideLuma - guideLuma,
                        guideSigma
                );

        float sampleWeight =
                spatialWeight
                        * guideWeight;

        accumulatedLuma +=
                sampleInputLuma
                        * sampleWeight;

        accumulatedWeight +=
                sampleWeight;
    }

    float filteredLuma =
            accumulatedWeight > 0.000001
                    ? accumulatedLuma
                            / accumulatedWeight
                    : inputLuma;

    float residual =
            abs(
                    inputLuma - filteredLuma
            );

    /*
     * Residuals inside the modeled-noise range are cleaned. Larger residuals
     * are treated as genuine structure, preventing general softness.
     */
    float noiseResidualMask =
            1.0
                    - smoothstep(
                            noiseSigma * 1.25,
                            noiseSigma * 4.50,
                            residual
                    );

    float flatMask =
            1.0
                    - smoothstep(
                            max(
                                    0.020,
                                    noiseSigma * 1.20
                            ),
                            max(
                                    0.085,
                                    noiseSigma * 4.50
                            ),
                            localGradient
                    );

    float darkMask =
            1.0
                    - smoothstep(
                            0.50,
                            0.90,
                            guideLuma
                    );

    float blend =
            clamp(
                    STRENGTH
                            * noiseResidualMask
                            * flatMask
                            * darkMask,
                    0.0,
                    1.0
            );

    float outputLuma =
            mix(
                    inputLuma,
                    filteredLuma,
                    blend
            );

    vec3 outputRgb =
            reconstructFromLumaChroma(
                    outputLuma,
                    originalChroma
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
