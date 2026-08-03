precision highp float;
precision highp sampler2D;
uniform sampler2D InputBuffer;
uniform sampler2D GradBuffer;
uniform sampler2D NoiseMap;
uniform ivec2 size;
uniform vec2 mapsize;
uniform int yOffset;
uniform float noiseS;
uniform float noiseO;
out vec4 Output;

#define SIGMA 10.0
#define BSIGMA 0.1
#define KERNELSIZE 3.5
#define MSIZE 15
#define KSIZE (MSIZE-1)/2
#define KSIZE_SMALL 3
#define KSIZE_TEXTURE 2
#define KSIZE_STRONG_TEXTURE 1
#define TRANSPOSE 1
#define INSIZE 1,1
#define NRcancell (0.90)
#define NRshift (+0.6)
#define maxNR (7.)
#define minNR (0.2)
#define NOISES 0.0
#define NOISEO 0.0
#define INTENSE 1.0
#define MOIRE 1.0
#define LUMA 0.0
#define TEXTUREPRESERVATION 1.0
#define SHADOWBOOST 0.5
#define CHROMASTRENGTH 1.0
#define MOTIONNOISEBLEND 0.0
#define MOTIONSTABLEWEIGHTS 0.0
#define MOTIONLOWLIGHTSCENE 0.0
#define MOTIONEDGECONFIDENCE 0.0
#define PI 3.1415926535897932384626433832795

float normpdf(in float x, in float sigma)
{
return 0.39894*exp(-0.5*x*x/(sigma*sigma))/sigma;
}
float normpdf3(in vec3 v, in float sigma)
{
return 0.39894*exp(-0.5*dot(v,v)/(sigma*sigma))/sigma;
}
float normpdf2(in vec2 v, in float sigma)
{
return 0.39894*exp(-0.5*dot(v,v)/(sigma*sigma))/sigma;
}

float lum(in vec4 color) {
    return length(color.xyz);
}

float atan2(in float y, in float x) {
bool s = (abs(x) > abs(y));
return mix(PI/2.0 - atan(x,y+0.00001), atan(y,x+0.00001), s);
}

void main() {
    ivec2 xy = ivec2(gl_FragCoord.xy);
    xy+=ivec2(0,yOffset);
    vec3 cin = vec3(texelFetch(InputBuffer, xy, 0).rgb);
    vec3 cinX = vec3(texelFetch(InputBuffer, xy+ivec2(1,0), 0).rgb);
    vec3 cinY = vec3(texelFetch(InputBuffer, xy+ivec2(0,1), 0).rgb);
    vec3 cinXY = vec3(texelFetch(InputBuffer, xy+ivec2(1,1), 0).rgb);
    vec3 cavg = (cin+cinX+cinY+cinXY)/4.0;
    float noisefactor = dot(cin,vec3(0.25,0.5,0.25));
    float xDelta = 0.0;
    float yDelta = 0.0;
    for (int i=-1; i <= 1; ++i) {
        for (int j=-1; j <= 1; ++j) {
            xDelta += float(i) * length(texelFetch(GradBuffer, xy + ivec2(i, j), 0).rgb);
            yDelta += float(j) * length(texelFetch(GradBuffer, xy + ivec2(i, j), 0).rgb);
        }
    }
    xDelta /= 3.0;
    yDelta /= 3.0;
    // calculate chromatic noise percentage
    vec3 final_colour = vec3(0.0);
    vec3 final_colour2 = vec3(0.0);
    float sigX = 2.5;
    //float sigY = (noisefactor*noisefactor*NOISES + NOISEO + 0.0000001);
    /*
     * Build 26167:
     * ESD3D2Run supplies modeled read noise through the NOISEO define.
     * The former lowercase noiseO uniform was unset here, suppressing
     * read-noise protection in deep shadows.
     */
    float sigY = max(
            NOISES*noisefactor
                    + NOISES*NOISES * 3.0/8.0
                    + NOISEO,
            0.0000001
    );
    // Shadow boost: inflate sigY in deep shadows where tonemap will later lift
    float shadowFactor = 1.0 + SHADOWBOOST * clamp(1.0 - noisefactor * 2.0, 0.0, 1.0);
    sigY *= shadowFactor;
    vec3 chromaDiff = (abs(cavg-cinX)+abs(cavg-cinY)+abs(cavg-cinXY)+abs(cavg-cin))/4.0;
    //chromaDiff *= (length(chromaDiff)/(length(chromaDiff)+sigY*64.0));
    chromaDiff *= max(abs(xDelta),abs(yDelta));
    float chromaNoise = max(chromaDiff.r,max(chromaDiff.g,chromaDiff.b))-min(chromaDiff.r,min(chromaDiff.g,chromaDiff.b));
    float sigZ = max(sigY,min(abs(chromaNoise)*MOIRE,0.2)) * CHROMASTRENGTH;
    //sigY += min(abs(chromaNoise)/32.0,0.2);

    // === Edge-aware adaptive kernel ===
    // Pre-scan: check the perimeter of the kernel for color boundaries.
    // If any perimeter pixel has RGB distance > threshold from center,
    // shrink the kernel to KSIZE_SMALL to preserve the color edge.
    // Noise-adaptive threshold: 3x the noise level
    float edgeThreshold =
            max(
                    sqrt(sigY)
                            * mix(
                                    3.0,
                                    5.0,
                                    MOTIONNOISEBLEND
                            ),
                    mix(
                            0.05,
                            0.08,
                            MOTIONNOISEBLEND
                    )
            );

    int effectiveKSIZE = KSIZE;
    bool edgeDetected = false;

    /*
     * Build 26222:
     * Dense low-contrast texture such as foliage, grass, fur and shingles
     * can evade the old perimeter-only edge test. Measure local 3x3 luma
     * structure relative to modeled noise and reduce only spatial support,
     * without changing the established LUMA strength.
     */
    float localLumaMinimum = 10000.0;
    float localLumaMaximum = -10000.0;

    for (int localY = -1; localY <= 1; localY++) {
        for (int localX = -1; localX <= 1; localX++) {
            float localLuma =
                    dot(
                            texelFetch(
                                    InputBuffer,
                                    xy + ivec2(localX, localY),
                                    0
                            ).rgb,
                            vec3(0.25, 0.5, 0.25)
                    );

            localLumaMinimum = min(localLumaMinimum, localLuma);
            localLumaMaximum = max(localLumaMaximum, localLuma);
        }
    }

    float localTextureRange = localLumaMaximum - localLumaMinimum;
    /*
     * Build 26247:
     * SHADOWBOOST should strengthen actual denoise in deep shadows, but it
     * must not also raise the threshold used to decide whether real local
     * structure exists. Use the pre-shadow noise estimate for texture
     * classification while retaining boosted sigY for the SNN filter itself.
     */
    float textureClassifierNoise =
            sigY / max(shadowFactor, 1.0);

    float modeledNoiseAmplitude =
            sqrt(max(textureClassifierNoise, 0.0000001));

    float safeTexturePreservation =
            max(
                    TEXTUREPRESERVATION,
                    0.25
            );

    float moderateTextureThreshold =
            max(
                    0.018 / safeTexturePreservation,
                    modeledNoiseAmplitude
                            * 1.35
                            / safeTexturePreservation
            );

    float strongTextureThreshold =
            max(
                    0.035 / safeTexturePreservation,
                    modeledNoiseAmplitude
                            * 2.40
                            / safeTexturePreservation
            );

    /*
     * Build 26224:
     * Keep the configured ESD luma value as the maximum for flat/noisy
     * regions. In locally structured texture, retain more of the original
     * luminance while leaving chroma filtering fully independent.
     *
     * With configured LUMA=0.8:
     * - flat/noisy area: 0.80
     * - moderate texture: 0.656
     * - strong texture: 0.56
     *
     * If Java lowers LUMA for HDR conditions, these factors scale that
     * already-reduced value rather than replacing it.
     */
    float textureAwareLuma = LUMA;

    /*
     * Build 26230:
     * Temporal stack confidence is global, but the adjustment is spatially
     * local. Only pixels already classified as real fine structure receive up
     * to five percent less ESD luma smoothing. Flat/noisy regions are unchanged.
     */
    /*
     * Build 26231:
     * Refine fine-text rendering without sharpening. Thin text strokes and
     * repeated line structure are identified by directional luma gradients,
     * while isolated single-pixel noise is rejected by requiring support on
     * opposing sides of the center.
     */
    float centerLuma3 =
            dot(
                    cin,
                    vec3(0.25, 0.5, 0.25)
            );

    float leftLuma =
            dot(
                    texelFetch(InputBuffer, xy + ivec2(-1, 0), 0).rgb,
                    vec3(0.25, 0.5, 0.25)
            );

    float rightLuma =
            dot(
                    texelFetch(InputBuffer, xy + ivec2(1, 0), 0).rgb,
                    vec3(0.25, 0.5, 0.25)
            );

    float topLuma =
            dot(
                    texelFetch(InputBuffer, xy + ivec2(0, -1), 0).rgb,
                    vec3(0.25, 0.5, 0.25)
            );

    float bottomLuma =
            dot(
                    texelFetch(InputBuffer, xy + ivec2(0, 1), 0).rgb,
                    vec3(0.25, 0.5, 0.25)
            );

    float horizontalStroke =
            min(
                    abs(centerLuma3 - leftLuma),
                    abs(centerLuma3 - rightLuma)
            );

    float verticalStroke =
            min(
                    abs(centerLuma3 - topLuma),
                    abs(centerLuma3 - bottomLuma)
            );

    float supportedDirectionalStroke =
            max(
                    horizontalStroke,
                    verticalStroke
            );

    /*
     * Build 26248:
     * Tune from the versus_3 closet fabric example, not from a fixed ISO
     * range. The opposing-side requirement remains, so isolated one-sided
     * noise does not automatically qualify as fabric structure.
     *
     * Lower the structure threshold enough to recognize faint repeated weave
     * and fibers while keeping modeled noise in the decision.
     */
    float directionalThreshold =
            max(
                    modeledNoiseAmplitude * 0.90,
                    0.0075 / safeTexturePreservation
            );

    float directionalTextConfidence =
            smoothstep(
                    directionalThreshold,
                    directionalThreshold * 1.85,
                    supportedDirectionalStroke
            );

    float localFineEdgeStrength =
            max(
                    smoothstep(
                            moderateTextureThreshold,
                            max(
                                    strongTextureThreshold,
                                    moderateTextureThreshold + 0.000001
                            ),
                            localTextureRange
                    ),
                    directionalTextConfidence
            );

    /*
     * Build 26247:
     * The previous equation multiplied by MOTIONLOWLIGHTSCENE, which made
     * the additional texture protection exactly zero in bright and normal
     * indoor scenes. Local structure is now the primary gate.
     *
     * Contribution confidence is a modest bonus, not a requirement.
     * Extreme low light tapers the protection to avoid retaining flat noise.
     */
    float sceneTextureAllowance =
            mix(
                    1.0,
                    0.45,
                    MOTIONLOWLIGHTSCENE
            );

    float confidenceBonus =
            mix(
                    0.75,
                    1.0,
                    MOTIONEDGECONFIDENCE
            );

    float localEdgeAgreement =
            localFineEdgeStrength
                    * sceneTextureAllowance
                    * confidenceBonus;

    float localSmoothingScale =
            1.0 - 0.30 * localEdgeAgreement;

    if (localTextureRange >= strongTextureThreshold) {
        effectiveKSIZE = min(effectiveKSIZE, KSIZE_STRONG_TEXTURE);
        textureAwareLuma =
                LUMA * 0.58 * localSmoothingScale;
    } else if (
            localTextureRange >= moderateTextureThreshold
                    || directionalTextConfidence > 0.22
    ) {
        effectiveKSIZE = min(effectiveKSIZE, KSIZE_TEXTURE);
        textureAwareLuma =
                LUMA * 0.76 * localSmoothingScale;
    }

    // Check perimeter pixels at KSIZE distance (top, bottom, left, right, diagonals)
    for (int i = -KSIZE; i <= KSIZE; i += max(KSIZE, 1)) {
        for (int j = -KSIZE; j <= KSIZE; j += max(KSIZE, 1)) {
            if (i == 0 && j == 0) continue;
            vec3 neighbor = texelFetch(InputBuffer, xy + ivec2(i, j), 0).rgb;

            float rgbDistance =
                    length(
                            abs(
                                    neighbor - cin
                            )
                    );

            float neighborLuma =
                    dot(
                            neighbor,
                            vec3(0.25, 0.5, 0.25)
                    );

            float centerLuma =
                    dot(
                            cin,
                            vec3(0.25, 0.5, 0.25)
                    );

            float lumaDistance =
                    abs(
                            neighborLuma - centerLuma
                    );

            /*
             * At high ISO, chroma speckles must not masquerade as hard color
             * boundaries and collapse the denoise support to KSIZE_SMALL.
             */
            float dist =
                    mix(
                            rgbDistance,
                            lumaDistance,
                            MOTIONNOISEBLEND
                    );

            if (dist > edgeThreshold) {
                edgeDetected = true;
                break;
            }
        }
        if (edgeDetected) break;
    }

    if (edgeDetected) {
        effectiveKSIZE = min(effectiveKSIZE, KSIZE_SMALL);
    }

    float Z = 0.01f;
    float Z2 = 0.01f;
    final_colour += cin*Z;
    final_colour2 += cin*Z;

    // SNN filtering with adaptive kernel size
    for (int i=0; i <= effectiveKSIZE; ++i)
    {
        for (int j=0; j <= effectiveKSIZE; ++j)
        {
            ivec2 pos = ivec2(i,j);
            ivec2 pos2 = ivec2(-i,-j);
            ivec2 pos3 = ivec2(i,-j);
            ivec2 pos4 = ivec2(-i,j);
            vec3 cc0 = vec3(texelFetch(InputBuffer, xy+pos, 0).rgb);
            vec3 cc1 = vec3(texelFetch(InputBuffer, xy+pos2, 0).rgb);
            vec3 cc2 = vec3(texelFetch(InputBuffer, xy+pos3, 0).rgb);
            vec3 cc3 = vec3(texelFetch(InputBuffer, xy+pos4, 0).rgb);
            // Compute the weights - full RGB distance (preserves color boundaries)
            vec4 d = vec4(length(abs(cc0-cin)),length(abs(cc1-cin)),length(abs(cc2-cin)),length(abs(cc3-cin)));
            vec4 w = (1.0-d*d/(d*d + sigY));
            vec4 w2 = (1.0-d*d/(d*d + sigZ));

            vec4 stableW =
                    max(
                            w,
                            vec4(0.0)
                    );

            vec4 stableW2 =
                    max(
                            w2,
                            vec4(0.0)
                    );

            float wm =
                    min(
                            min(
                                    min(w[0], w[1]),
                                    w[2]
                            ),
                            w[3]
                    );

            float wm2 =
                    min(
                            min(
                                    min(w2[0], w2[1]),
                                    w2[2]
                            ),
                            w2[3]
                    );

            vec4 ws =
                    w - wm;

            ws /=
                    length(ws)
                            + 0.000001;

            vec4 w2s =
                    w2 - wm2;

            w2s /=
                    length(w2s)
                            + 0.000001;

            vec4 sparseW =
                    w * ws;

            vec4 sparseW2 =
                    w2 * w2s;

            /*
             * The original sparse SNN weights can connect random residual
             * noise into worms. Blend toward ordinary bilateral weights only
             * for noisy Motion captures.
             */
            w =
                    mix(
                            sparseW,
                            stableW,
                            MOTIONSTABLEWEIGHTS
                    );

            w2 =
                    mix(
                            sparseW2,
                            stableW2,
                            MOTIONSTABLEWEIGHTS
                    );

            float f1 = normpdf(float(i),KERNELSIZE)*normpdf(float(j),KERNELSIZE);
            final_colour += f1*mat4x3(cc0,cc1,cc2,cc3)*w;
            final_colour2 += f1*mat4x3(cc0,cc1,cc2,cc3)*w2;
            Z += dot(vec4(f1),w);
            Z2 += dot(vec4(f1),w2);
        }
    }

    float br = dot(final_colour/Z,vec3(0.25,0.5,0.25));
    br = mix(dot(cin,vec3(0.25,0.5,0.25)),br,textureAwareLuma);
    vec3 resColour = final_colour2/Z2;
    resColour /= max(1e-6,dot(resColour,vec3(0.25,0.5,0.25)));
    resColour = clamp(resColour*br,0.0,1.0);
    Output = vec4(resColour,1.0);
}
