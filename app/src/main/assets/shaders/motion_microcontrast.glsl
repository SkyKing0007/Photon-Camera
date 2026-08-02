precision highp float;
precision highp sampler2D;

uniform sampler2D InputBuffer;
uniform int yOffset;

out vec4 Output;

#define MICROSTRENGTH 0.0
#define NOISES 0.0
#define NOISEO 0.0

float lumaValue(vec3 rgb) {
    return dot(
            rgb,
            vec3(0.25, 0.50, 0.25)
    );
}

void main() {
    ivec2 xy =
            ivec2(gl_FragCoord.xy)
                    + ivec2(0, yOffset);

    ivec2 size =
            textureSize(
                    InputBuffer,
                    0
            );

    ivec2 clamped =
            clamp(
                    xy,
                    ivec2(1),
                    size - ivec2(2)
            );

    vec4 center =
            texelFetch(
                    InputBuffer,
                    clamped,
                    0
            );

    vec3 left =
            texelFetch(
                    InputBuffer,
                    clamped + ivec2(-1, 0),
                    0
            ).rgb;

    vec3 right =
            texelFetch(
                    InputBuffer,
                    clamped + ivec2(1, 0),
                    0
            ).rgb;

    vec3 top =
            texelFetch(
                    InputBuffer,
                    clamped + ivec2(0, -1),
                    0
            ).rgb;

    vec3 bottom =
            texelFetch(
                    InputBuffer,
                    clamped + ivec2(0, 1),
                    0
            ).rgb;

    vec3 diagonalAverage =
            0.25 * (
                    texelFetch(
                            InputBuffer,
                            clamped + ivec2(-1, -1),
                            0
                    ).rgb
                    + texelFetch(
                            InputBuffer,
                            clamped + ivec2(1, -1),
                            0
                    ).rgb
                    + texelFetch(
                            InputBuffer,
                            clamped + ivec2(-1, 1),
                            0
                    ).rgb
                    + texelFetch(
                            InputBuffer,
                            clamped + ivec2(1, 1),
                            0
                    ).rgb
            );

    vec3 narrowBlur =
            0.34 * center.rgb
                    + 0.115 * (
                            left
                                    + right
                                    + top
                                    + bottom
                    )
                    + 0.20 * diagonalAverage;

    float centerLuma =
            lumaValue(center.rgb);

    float blurLuma =
            lumaValue(narrowBlur);

    float residual =
            centerLuma - blurLuma;

    float gradientSupport =
            max(
                    min(
                            abs(centerLuma - lumaValue(left)),
                            abs(centerLuma - lumaValue(right))
                    ),
                    min(
                            abs(centerLuma - lumaValue(top)),
                            abs(centerLuma - lumaValue(bottom))
                    )
            );

    float modeledNoise =
            sqrt(
                    max(
                            centerLuma * NOISES + NOISEO,
                            0.000001
                    )
            );

    float edgeGate =
            smoothstep(
                    modeledNoise * 1.10 + 0.003,
                    modeledNoise * 2.40 + 0.016,
                    gradientSupport
            );

    float flatNoiseGate =
            1.0
                    - smoothstep(
                            0.0,
                            modeledNoise * 1.25 + 0.005,
                            abs(residual)
                    );

    float validStructure =
            edgeGate
                    * (1.0 - 0.65 * flatNoiseGate);

    float highlightGate =
            1.0
                    - smoothstep(
                            0.88,
                            0.99,
                            centerLuma
                    );

    float deepShadowGate =
            smoothstep(
                    0.012,
                    0.055,
                    centerLuma
            );

    float chromaRange =
            max(
                    center.r,
                    max(center.g, center.b)
            )
                    - min(
                        center.r,
                        min(center.g, center.b)
                    );

    float chromaGate =
            1.0
                    - 0.45
                    * smoothstep(
                            0.12,
                            0.38,
                            chromaRange
                    );

    float localGain =
            MICROSTRENGTH
                    * validStructure
                    * highlightGate
                    * deepShadowGate
                    * chromaGate;

    float limitedResidual =
            clamp(
                    residual,
                    -0.018,
                    0.018
            );

    float enhancedLuma =
            centerLuma
                    + limitedResidual * localGain;

    float scale =
            enhancedLuma
                    / max(
                        centerLuma,
                        0.0001
                    );

    vec3 result =
            center.rgb * scale;

    Output =
            vec4(
                    clamp(result, 0.0, 1.0),
                    center.a
            );
}