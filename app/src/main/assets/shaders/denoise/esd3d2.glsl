precision highp float;
precision highp sampler2D;
uniform sampler2D InputBuffer;
#define IRIS_LOCAL_SUPPORT_26383 0
#if IRIS_LOCAL_SUPPORT_26383 == 1
uniform sampler2D MotionLocalSupportMap;
#define IRIS_LOCAL_SUPPORT_RETAINED_26383 1.0
#endif
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

/*
 * IRIS_26373_SIGNAL_AWARE_LUMA_CHROMA
 *
 * Motion-only residual cleanup:
 * - local luma filtering follows actual signal/noise confidence;
 * - fine luma grain/detail is retained when SNR is healthy;
 * - chroma is cleaned independently on a broader support;
 * - flat low-SNR hue wandering is pulled toward the local base hue;
 * - structured/color-edge regions are protected.
 */
#define IRIS_MOTION_26373 0
#define IRIS_STACK_QUALITY_26373 0.0
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

#if IRIS_LOCAL_SUPPORT_26383 == 1
    /* IRIS_26383_LOCAL_TEMPORAL_SUPPORT */
    vec2 iris26383SupportUv =
            (vec2(xy) + vec2(0.5)) / vec2(textureSize(InputBuffer,0));
    float iris26383LocalFrames =
            texture(MotionLocalSupportMap, iris26383SupportUv).r;
    float iris26383LocalSupport =
            clamp(
                    iris26383LocalFrames
                            / max(1.0, float(IRIS_LOCAL_SUPPORT_RETAINED_26383)),
                    1.0 / max(1.0, float(IRIS_LOCAL_SUPPORT_RETAINED_26383)),
                    1.0);
#else
    float iris26383LocalSupport = 1.0;
#endif
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
    float sigY = max(NOISES*noisefactor + NOISEO, 0.0000001);
    //float sigY = max(NOISES*noisefactor + NOISES*NOISES * 3.0/8.0 + NOISEO, 0.0000001);
    vec3 chromaDiff = (abs(cavg-cinX)+abs(cavg-cinY)+abs(cavg-cinXY)+abs(cavg-cin))/4.0;
    //chromaDiff *= (length(chromaDiff)/(length(chromaDiff)+sigY*64.0));
    chromaDiff *= max(abs(xDelta),abs(yDelta));
    float chromaNoise = max(chromaDiff.r,max(chromaDiff.g,chromaDiff.b))-min(chromaDiff.r,min(chromaDiff.g,chromaDiff.b));
    float sigZ = max(sigY,min(abs(chromaNoise)*MOIRE,0.2));
    //sigY += min(abs(chromaNoise)/32.0,0.2);
    float Z = 0.01f;
    float Z2 = 0.01f;
    final_colour += cin*Z;
    final_colour2 += cin*Z;
    //sigY /= 25.0;
    // Use hybrid SNN filtering to denoise the image
    //vec3 cc[4];
    for (int i=0; i <= KSIZE; ++i)
    {
        for (int j=0; j <= KSIZE; ++j)
        {
            ivec2 pos = ivec2(i,j);
            ivec2 pos2 = ivec2(-i,-j);
            ivec2 pos3 = ivec2(i,-j);
            ivec2 pos4 = ivec2(-i,j);
            vec3 cc0 = vec3(texelFetch(InputBuffer, xy+pos, 0).rgb);
            vec3 cc1 = vec3(texelFetch(InputBuffer, xy+pos2, 0).rgb);
            vec3 cc2 = vec3(texelFetch(InputBuffer, xy+pos3, 0).rgb);
            vec3 cc3 = vec3(texelFetch(InputBuffer, xy+pos4, 0).rgb);
            // Compute the weights
            vec4 d = vec4(length(abs(cc0-cin)),length(abs(cc1-cin)),length(abs(cc2-cin)),length(abs(cc3-cin)));
            vec4 w = (1.0-d*d/(d*d + sigY));
            vec4 w2 = (1.0-d*d/(d*d + sigZ));
            float wm = min(min(min(w[0],w[1]),w[2]),w[3])*1.0;
            vec4 ws = w - wm;
            ws /= length(ws) + 0.000001;
            vec4 w2s = w2 - wm;
            w2s /= length(w2s) + 0.000001;
            w *= ws;
            w2 *= w2s;
            float f1 = normpdf(float(i),KERNELSIZE)*normpdf(float(j),KERNELSIZE);
            final_colour += f1*mat4x3(cc0,cc1,cc2,cc3)*w;
            final_colour2 += f1*mat4x3(cc0,cc1,cc2,cc3)*w2;
            Z += dot(vec4(f1),w);
            Z2 += dot(vec4(f1),w2);
        }
    }

    //if (Z <= 0.002f) {
    //    Output = vec4(cin,1.0);
    //} else {
    float irisInputLuma = dot(cin,vec3(0.25,0.5,0.25));
    float irisFilteredLuma =
            dot(final_colour/Z,vec3(0.25,0.5,0.25));

    /*
     * Residual SNR proxy. This uses the same modeled residual noise that
     * reaches ESD, but compares it against the ACTUAL local image signal.
     *
     * High local signal / low residual noise -> protect luma texture.
     * Near-black / low-SNR signal           -> allow more luma cleanup.
     */
    float irisNoiseSigma =
            sqrt(max(NOISES*max(irisInputLuma,0.0) + NOISEO,1e-8));
    float irisLocalSnr =
            max(irisInputLuma,0.0) / max(irisNoiseSigma,1e-5);

    float irisSnrClean =
            smoothstep(2.0,7.0,irisLocalSnr);

    /*
     * 3x3 luma structure detector. Fine structure raises this gate and
     * suppresses luma replacement even when the signal is dark.
     */
    float irisLumaMin = irisInputLuma;
    float irisLumaMax = irisInputLuma;

    /*
     * IRIS_26374_TEXTURE_PROTECTION
     *
     * Directional 3-pixel averages provide a conservative coherent
     * structure signal for CHROMA protection only.  Denim weave, stitching,
     * foliage, bark, grass, hair and text should make broad chroma cleanup
     * back off.  This does not alter the 26373 luma/SNR decision.
     */
    float irisLeftLuma = 0.0;
    float irisRightLuma = 0.0;
    float irisTopLuma = 0.0;
    float irisBottomLuma = 0.0;

    for (int irisY=-1; irisY<=1; ++irisY) {
        for (int irisX=-1; irisX<=1; ++irisX) {
            vec3 irisN =
                    vec3(texelFetch(
                            InputBuffer,
                            xy+ivec2(irisX,irisY),
                            0).rgb);
            float irisNL =
                    dot(irisN,vec3(0.25,0.5,0.25));
            irisLumaMin = min(irisLumaMin,irisNL);
            irisLumaMax = max(irisLumaMax,irisNL);

            if (irisX == -1) irisLeftLuma += irisNL;
            if (irisX ==  1) irisRightLuma += irisNL;
            if (irisY == -1) irisTopLuma += irisNL;
            if (irisY ==  1) irisBottomLuma += irisNL;
        }
    }

    irisLeftLuma /= 3.0;
    irisRightLuma /= 3.0;
    irisTopLuma /= 3.0;
    irisBottomLuma /= 3.0;

    float irisLocalRange =
            max(irisLumaMax-irisLumaMin,0.0);
    float irisStructure =
            smoothstep(
                    irisNoiseSigma*1.25,
                    irisNoiseSigma*4.0 + 0.003,
                    irisLocalRange);

    float irisAppliedLuma = LUMA;
#if IRIS_MOTION_26373 == 1
    /*
     * A healthy temporal stack and high local SNR can drive broad luma
     * replacement almost completely away.  We deliberately retain a tiny
     * floor rather than mathematically disabling the node.
     */
    float irisTemporalClean =
            clamp(IRIS_STACK_QUALITY_26373,0.0,1.0);

    float irisDetailConfidence =
            max(irisSnrClean,irisStructure);

    float irisLumaKeep =
            clamp(
                    0.85*irisDetailConfidence
                    + 0.15*irisTemporalClean,
                    0.0,
                    1.0);

    irisAppliedLuma =
            mix(
                    LUMA,
                    min(LUMA,0.06),
                    irisLumaKeep);
#endif

    float br =
            mix(
                    irisInputLuma,
                    irisFilteredLuma,
                    irisAppliedLuma);

    vec3 resColour = final_colour2/Z2;
    resColour /=
            max(
                    1e-6,
                    dot(resColour,vec3(0.25,0.5,0.25)));

#if IRIS_MOTION_26373 == 1
    /*
     * IRIS_26377_ROSE_BLOOM_SAFE_CHROMA_ROLLBACK
     *
     * Restore the conservative 26374 opponent-color reconstruction.
     * The 26375 +/-24 px field is retired because it can spread saturated
     * flower/object color and suppress legitimate low-light clothing color.
     *
     * This is deliberately a safe rollback, not the final wall-mottle
     * solution. The future low-frequency chroma pass will be architecturally
     * separated from high-resolution object color.
     */
    vec3 irisCenterOpponent =
            cin - vec3(irisInputLuma);

    float irisDirectionalStructure =
            max(
                    abs(irisLeftLuma-irisRightLuma),
                    abs(irisTopLuma-irisBottomLuma));

    float irisChromaTextureProtect =
            smoothstep(
                    irisNoiseSigma*0.45 + 0.0015,
                    irisNoiseSigma*1.60 + 0.0080,
                    irisDirectionalStructure);

    float irisChromaFineProtect =
            smoothstep(
                    irisNoiseSigma*0.75 + 0.0020,
                    irisNoiseSigma*2.20 + 0.0100,
                    irisLocalRange);

    float irisTextureProtect =
            clamp(
                    max(
                            irisChromaTextureProtect,
                            irisChromaFineProtect),
                    0.0,
                    1.0);

    vec3 irisOpponentSum = vec3(0.0);
    float irisOpponentWeight = 0.0;

    float irisChromaSigma =
            max(
                    0.018,
                    0.012 + irisNoiseSigma*2.8);

    float irisLumaSigma =
            max(
                    0.018,
                    0.018 + irisNoiseSigma*5.0);

    for (int irisGY=-3; irisGY<=3; ++irisGY) {
        for (int irisGX=-3; irisGX<=3; ++irisGX) {
            ivec2 irisOffset =
                    ivec2(irisGX*2,irisGY*2);

            vec3 irisN =
                    vec3(texelFetch(
                            InputBuffer,
                            xy+irisOffset,
                            0).rgb);

            float irisNL =
                    dot(irisN,vec3(0.25,0.5,0.25));

            vec3 irisNOpponent =
                    irisN - vec3(irisNL);

            float irisDist2 =
                    float(
                            irisOffset.x*irisOffset.x
                            + irisOffset.y*irisOffset.y);

            float irisSpatialW =
                    exp(-irisDist2/28.0);

            float irisLumaW =
                    exp(
                            -abs(irisNL-irisInputLuma)
                            / irisLumaSigma);

            float irisColorDistance =
                    length(
                            irisNOpponent
                            - irisCenterOpponent);

            float irisColorW =
                    exp(
                            -irisColorDistance
                            / irisChromaSigma);

            float irisW =
                    irisSpatialW
                    * irisLumaW
                    * irisColorW;

            irisOpponentSum += irisNOpponent*irisW;
            irisOpponentWeight += irisW;
        }
    }

    vec3 irisBaseOpponent =
            irisOpponentSum
            / max(irisOpponentWeight,1e-5);

    vec3 irisTargetRgb =
            vec3(irisInputLuma)
            + irisBaseOpponent;

    float irisTargetLuma =
            max(
                    dot(
                            irisTargetRgb,
                            vec3(0.25,0.5,0.25)),
                    1e-5);

    vec3 irisTargetChromaticity =
            irisTargetRgb / irisTargetLuma;

    float irisLowSnr =
            1.0-irisSnrClean;

    float irisFlatConfidence =
            1.0-clamp(
                    max(irisStructure,irisTextureProtect),
                    0.0,
                    1.0);

    float irisChromaBlend =
            clamp(
                    0.04
                    + 0.86
                    * irisLowSnr
                    * irisFlatConfidence,
                    0.0,
                    0.90);

    float irisSupportConfidence =
            smoothstep(
                    3.0,
                    14.0,
                    irisOpponentWeight);

    irisChromaBlend *= irisSupportConfidence;

    resColour =
            mix(
                    resColour,
                    irisTargetChromaticity,
                    irisChromaBlend);
#endif

#if IRIS_MOTION_26373 == 1
    /*
     * IRIS_26382_LOW_FREQUENCY_OPPONENT_CHROMA
     *
     * Broad chroma mottling is lower-frequency than the successful 26377
     * full-resolution color protection. Estimate only a sparse opponent-
     * chroma field and correct a bounded residual while preserving the
     * original center luminance. This is intentionally NOT the retired
     * 26375 +/-24 full-resolution reconstruction.
     */
    vec3 iris26382Center = resColour;
    float iris26382Y = dot(iris26382Center,vec3(0.25,0.5,0.25));
    vec3 iris26382CenterOpp = iris26382Center - vec3(iris26382Y);

    vec3 iris26382BroadOpp = vec3(0.0);
    float iris26382W = 0.0;
    const int iris26382R1 = 16;
    const int iris26382R2 = 32;
    ivec2 iris26382Off[8] = ivec2[8](
            ivec2( iris26382R1,0), ivec2(-iris26382R1,0),
            ivec2(0, iris26382R1), ivec2(0,-iris26382R1),
            ivec2( iris26382R2,0), ivec2(-iris26382R2,0),
            ivec2(0, iris26382R2), ivec2(0,-iris26382R2));

    for (int iris26382I=0; iris26382I<8; ++iris26382I) {
        ivec2 iris26382P =
                clamp(
                        xy + iris26382Off[iris26382I],
                        ivec2(0),
                        textureSize(InputBuffer,0)-ivec2(1));
        vec3 iris26382N = vec3(texelFetch(InputBuffer,iris26382P,0).rgb);
        float iris26382NY = dot(iris26382N,vec3(0.25,0.5,0.25));
        vec3 iris26382NOpp = iris26382N - vec3(iris26382NY);
        float iris26382LumaSim =
                exp(-abs(iris26382NY-iris26382Y)/max(0.018,3.0*irisNoiseSigma));
        float iris26382ChromaDist = length(iris26382NOpp-iris26382CenterOpp);
        float iris26382ChromaCompat =
                exp(-iris26382ChromaDist/max(0.030,4.0*irisNoiseSigma));
        float iris26382Weight = iris26382LumaSim * iris26382ChromaCompat;
        iris26382BroadOpp += iris26382NOpp * iris26382Weight;
        iris26382W += iris26382Weight;
    }

    iris26382BroadOpp /= max(iris26382W,0.0001);
    vec3 iris26382Residual = iris26382CenterOpp - iris26382BroadOpp;

    float iris26382Flat = 1.0 - clamp(irisStructure,0.0,1.0);
    float iris26382DarkNeed =
            1.0 - smoothstep(0.08,0.30,iris26382Y);
    float iris26382LowSnr =
            1.0 - clamp(irisLocalSnr/4.0,0.0,1.0);
    float iris26382Support = clamp(iris26382W/5.0,0.0,1.0);
    float iris26382Need =
            iris26382Flat
                    * iris26382DarkNeed
                    * iris26382LowSnr
                    * iris26382Support;

    float iris26382ResidualMag = length(iris26382Residual);
    float iris26382BoundedResidual =
            smoothstep(0.010,0.055,iris26382ResidualMag);
    /*
     * IRIS_26383_SUPPORT_GOVERNED_CHROMA
     * High local support preserves source color; weak support permits only
     * a modest bounded increase in the existing 26382 cleanup.
     */
    float iris26383WeakSupport = 1.0 - iris26383LocalSupport;
    float iris26383ChromaStrength =
            mix(0.30, 0.50, iris26383WeakSupport);
    float iris26382Blend =
            iris26383ChromaStrength
                    * iris26382Need
                    * iris26382BoundedResidual;

    vec3 iris26382Correction =
            clamp(iris26382Residual,vec3(-0.028),vec3(0.028));
    vec3 iris26382Clean =
            iris26382Center - iris26382Blend * iris26382Correction;
    float iris26382CleanY = dot(iris26382Clean,vec3(0.25,0.5,0.25));
    iris26382Clean += vec3(iris26382Y - iris26382CleanY);

    resColour = mix(iris26382Center,iris26382Clean,iris26382Flat);
#endif


    resColour =
            clamp(resColour*br,0.0,1.0);
    Output = vec4(resColour,1.0);
    //Output = vec4(final_colour/Z,1.0);
    //}
}
