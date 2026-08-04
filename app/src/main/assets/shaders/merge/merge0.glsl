#define LAYOUT //
LAYOUT
precision highp float;
precision highp sampler2D;
precision highp image2D;
uniform highp usampler2D inTexture;
uniform highp sampler2D alignmentTexture;
//layout(r16ui, binding = 0) uniform highp readonly uimage2D inTexture;
layout(rgba16f, binding = 0) uniform highp readonly image2D avrTexture;
layout(rgba8, binding = 1) uniform highp readonly image2D hotPixTexture;
layout(rgba16f, binding = 2) uniform highp readonly image2D baseTexture;
layout(rgba16f, binding = 3) uniform highp writeonly image2D outTexture;
layout(rgba16f, binding = 4) uniform highp readonly image2D alterTexture;
layout(r32f, binding = 5) uniform highp writeonly image2D warpConfidenceTexture;
layout(rgba32f, binding = 6) uniform highp writeonly image2D mergeConfidenceDiagnosticTexture;
layout(rgba32f, binding = 7) uniform highp writeonly image2D mergeValidityDiagnosticTexture;

uniform float minLevel;
uniform float whiteLevel;
uniform vec4 blackLevel;
uniform float exposure;
uniform float exposureLow;
uniform bool createDiff;
uniform float noiseS;
uniform float noiseO;
uniform int motionEqualExposureStack;
uniform ivec2 border;
uniform ivec2 shift;
uniform ivec2 alignmentSize;
uniform ivec2 rawHalf;
uniform vec4 analogBalance;
#define TILE 2
#define CONCAT 1
#define M_PI 3.1415926535897932384626433832795
#define TILE_AL 16

uint getBayer(ivec2 coords, highp usampler2D tex){
    return texelFetch(tex,coords,0).r;
}

vec4 getBayerVec(ivec2 coords, highp usampler2D tex){
    vec4 c0 = vec4(getBayer(coords,tex),getBayer(coords+ivec2(1,0),tex),getBayer(coords+ivec2(0,1),tex),getBayer(coords+ivec2(1,1),tex));
    return clamp((c0 - blackLevel)/(vec4(whiteLevel)-blackLevel), 0.0, 1.0);
}

float window(float x){
    return 0.5f - 0.5f * cos(2.f * M_PI * ((0.5f * (x + 0.5f) / float(TILE_AL))));
}

float windowxy(ivec2 xy){
    return window(float(xy.x)) * window(float(xy.y));
}

vec4 windowxy4(ivec2 xy){
    return vec4(window(float(xy.x)) * window(float(xy.y)),
                window(float(xy.x+1)) * window(float(xy.y)),
                window(float(xy.x)) * window(float(xy.y+1)),
                window(float(xy.x+1)) * window(float(xy.y+1)));
}
/*
vec4 robustWeight(vec4 w){
    float mv = min(w.r, min(w.g, min(w.b, w.a)));
    //mv = smoothstep(0.1, 0.9, mv);
    return vec4(mv);
}*/
vec4 robustWeight(vec4 w){
    return vec4(w.r * 2.0 + w.g + w.a,
    w.g * 2.0 + w.b + w.r,
    w.b * 2.0 + w.a + w.g,
    w.a * 2.0 + w.r + w.b) / 4.0;
}

vec2 vec4ToAlignment(vec4 alignment) {
    vec2 converted = vec2(alignment.x * float(rawHalf.x), alignment.y * float(rawHalf.y));
    converted.xy += alignment.zw;
    return converted;
}

/*
 * Build 26259:
 * Sample the half-resolution RGGB-vector texture at a floating coordinate.
 * Each vec4 component remains in its own CFA plane.
 */
vec4 sampleAlterLinear(vec2 coords) {
    ivec2 size = imageSize(alterTexture);
    vec2 safe = clamp(
            coords,
            vec2(0.0),
            vec2(size - ivec2(1))
    );

    ivec2 p0 = ivec2(floor(safe));
    ivec2 p1 = min(p0 + ivec2(1), size - ivec2(1));
    vec2 f = fract(safe);

    vec4 a = imageLoad(alterTexture, p0);
    vec4 b = imageLoad(alterTexture, ivec2(p1.x, p0.y));
    vec4 c = imageLoad(alterTexture, ivec2(p0.x, p1.y));
    vec4 d = imageLoad(alterTexture, p1);

    return mix(
            mix(a, b, f.x),
            mix(c, d, f.x),
            f.y
    );
}
vec2 hash22(vec2 p)
{
    vec3 p3 = fract(vec3(p.xyx) * vec3(.1031, .1030, .0973));
    p3 += dot(p3, p3.yzx+33.33);
    return fract((p3.xx+p3.yz)*p3.zy);
}
void main() {
    ivec2 xy = ivec2(gl_GlobalInvocationID.xy);
    ivec2 outSize = imageSize(outTexture);
    vec2 uvScale = vec2(outSize-border);
    vec2 uv = vec2(xy)/uvScale + vec2(0.5)/uvScale;
    vec4 bayerBase = imageLoad(baseTexture,xy);
    vec4 bayer = getBayerVec(xy*TILE, inTexture);
    //vec4 hp = imageLoad(hotPixTexture, xy);
    //bayer = bayer * vec4(1.0-hp) + imageLoad(avrTexture, xy) * hp;
    vec4 noise = vec4(max(sqrt(max(bayer * noiseS + noiseO, 1e-6)), vec4(minLevel)));
    vec4 w[4];
    w[3] = windowxy4((TILE*xy)%TILE_AL);
    w[2] = windowxy4((TILE*xy)%TILE_AL + ivec2(TILE_AL,0));
    w[1] = windowxy4((TILE*xy)%TILE_AL + ivec2(0,TILE_AL));
    w[0] = windowxy4((TILE*xy)%TILE_AL + ivec2(TILE_AL));
            vec4 alignedSum = vec4(0.0);
    vec4 bayerNone = imageLoad(alterTexture, xy);

    /*
     * Build 26260:
     * Safe alignment-grid mapping.
     *
     * The previous warp could clamp a base grid coordinate, add shift later,
     * then fetch outside the valid alignment texture. It also clamped invalid
     * warped image coordinates, turning bad vectors into repeated columns or
     * large smeared regions.
     *
     * This path:
     * 1. derives one explicit grid coordinate from the half-resolution Bayer
     *    texel domain;
     * 2. adds shift before validation;
     * 3. requires the complete 2x2 tile neighborhood to be valid;
     * 4. uses one shared bilinear flow for the entire RGGB-vector texel;
     * 5. rejects excessive or inconsistent vectors;
     * 6. rejects warped coordinates that leave the image;
     * 7. rejects uncertain warps to zero alternate contribution.
     */

    vec2 gridPosition =
            (vec2(xy) * float(TILE))
                    / float(TILE_AL);

    ivec2 gridBase = ivec2(floor(gridPosition));
    vec2 gridFraction = fract(gridPosition);

    /*
     * Build 26278 coordinate-space repair:
     *
     * localGridCoords are coordinates inside the logical alignment result for
     * this frame and are validated only against alignmentSize.
     *
     * atlasGridCoords are the shifted physical texture addresses and are
     * validated only against textureSize(alignmentTexture, 0).
     *
     * Alignment vectors continue to be fetched from atlasGridCoords. Invalid
     * local tiles or invalid atlas addresses still receive zero alternate
     * contribution. The 12-pixel flow limit remains unchanged.
     */
    ivec2 localGridCoords[4];
    localGridCoords[0] = gridBase + ivec2(0, 0);
    localGridCoords[1] = gridBase + ivec2(1, 0);
    localGridCoords[2] = gridBase + ivec2(0, 1);
    localGridCoords[3] = gridBase + ivec2(1, 1);

    ivec2 atlasGridCoords[4];
    atlasGridCoords[0] = localGridCoords[0] + shift;
    atlasGridCoords[1] = localGridCoords[1] + shift;
    atlasGridCoords[2] = localGridCoords[2] + shift;
    atlasGridCoords[3] = localGridCoords[3] + shift;

    ivec2 alignmentAtlasSize = textureSize(alignmentTexture, 0);
    bool validLocalGridNeighborhood = true;
    bool validAtlasNeighborhood = true;

    for (int i = 0; i < 4; i++) {
        validLocalGridNeighborhood =
                validLocalGridNeighborhood
                        && all(
                                greaterThanEqual(
                                        localGridCoords[i],
                                        ivec2(0)
                                )
                        )
                        && all(
                                lessThan(
                                        localGridCoords[i],
                                        alignmentSize
                                )
                        );

        validAtlasNeighborhood =
                validAtlasNeighborhood
                        && all(
                                greaterThanEqual(
                                        atlasGridCoords[i],
                                        ivec2(0)
                                )
                        )
                        && all(
                                lessThan(
                                        atlasGridCoords[i],
                                        alignmentAtlasSize
                                )
                        );
    }

    bool validGridNeighborhood =
            validLocalGridNeighborhood
                    && validAtlasNeighborhood;

    float bilinearWeights[4];
    bilinearWeights[0] =
            (1.0 - gridFraction.x)
                    * (1.0 - gridFraction.y);
    bilinearWeights[1] =
            gridFraction.x
                    * (1.0 - gridFraction.y);
    bilinearWeights[2] =
            (1.0 - gridFraction.x)
                    * gridFraction.y;
    bilinearWeights[3] =
            gridFraction.x
                    * gridFraction.y;

    vec2 sharedFlow = vec2(0.0);
    vec2 tileFlows[4];

    if (validGridNeighborhood) {
        for (int i = 0; i < 4; i++) {
            vec4 alignLoad =
                    texelFetch(
                            alignmentTexture,
                            atlasGridCoords[i],
                            0
                    );

            tileFlows[i] = vec4ToAlignment(alignLoad);
            sharedFlow += tileFlows[i] * bilinearWeights[i];
        }
    } else {
        for (int i = 0; i < 4; i++) {
            tileFlows[i] = vec2(0.0);
        }
    }

    float maximumFlowDisagreement = 0.0;

    for (int i = 0; i < 4; i++) {
        maximumFlowDisagreement =
                max(
                        maximumFlowDisagreement,
                        length(tileFlows[i] - sharedFlow)
                );
    }

    float flowMagnitude = length(sharedFlow);

    /*
     * Conservative limits prevent one bad tile or corrupt decode from
     * displacing a large image region. Values are in half-resolution
     * RGGB-vector texel units.
     */
    float vectorConsistency =
            1.0
                    - smoothstep(
                            0.40,
                            1.20,
                            maximumFlowDisagreement
                    );

    float magnitudeConfidence =
            1.0
                    - smoothstep(
                            6.0,
                            12.0,
                            flowMagnitude
                    );

    vec2 warpedCoordinate =
            vec2(xy) + sharedFlow;

    ivec2 alterSize = imageSize(alterTexture);

    bool validWarpCoordinate =
            all(
                    greaterThanEqual(
                            warpedCoordinate,
                            vec2(0.0)
                    )
            )
                    && all(
                            lessThanEqual(
                                    warpedCoordinate,
                                    vec2(alterSize - ivec2(1))
                            )
                    );

    vec4 bayerAligned = bayerNone;

    if (
        validGridNeighborhood
                && validWarpCoordinate
                && flowMagnitude < 12.0
    ) {
        bayerAligned =
                sampleAlterLinear(
                        warpedCoordinate
                );
    }

    vec4 alignedErrorChannels =
            abs(
                    bayerAligned * vec4(exposure)
                            - bayerBase
            );

    vec4 unwarpedErrorChannels =
            abs(
                    bayerNone * vec4(exposure)
                            - bayerBase
            );

    float alignedError =
            dot(
                    alignedErrorChannels,
                    vec4(0.25)
            );

    float unwarpedError =
            dot(
                    unwarpedErrorChannels,
                    vec4(0.25)
            );

    float photometricAdvantage =
            (unwarpedError - alignedError)
                    / (
                            unwarpedError
                                    + alignedError
                                    + 1.0e-6
                    );

    float photometricConfidence =
            smoothstep(
                    0.015,
                    0.080,
                    photometricAdvantage
            );

    /*
     * Build 26275:
     * Equal-exposure Motion accepts stable aligned frames when their residual
     * is compatible with the expected sensor noise. This avoids rejecting
     * static regions merely because the warped and unwarped errors are both
     * already small.
     */
    float expectedNoise =
            max(
                    dot(noise, vec4(0.25)),
                    1.0e-4
            );

    float normalizedAlignedResidual =
            alignedError / expectedNoise;

    float residualConfidence =
            1.0
                    - smoothstep(
                            1.25,
                            4.00,
                            normalizedAlignedResidual
                    );

    float motionPhotometricConfidence =
            clamp(
                    residualConfidence
                            + 0.20
                                    * photometricConfidence
                                    * (1.0 - residualConfidence),
                    0.0,
                    1.0
            );

    float confidenceSource =
            motionEqualExposureStack != 0
                    ? motionPhotometricConfidence
                    : photometricConfidence;

    float validityConfidence =
            validGridNeighborhood && validWarpCoordinate
                    ? 1.0
                    : 0.0;

    /*
     * Build 26279:
     * The 26278 capture proved that local/atlas addressing, warp bounds, and
     * residual agreement are valid across almost the whole frame, while
     * vectorConsistency still has a zero median. That made the multiplicative
     * confidence below discard noise-compatible aligned RAW samples.
     *
     * For equal-exposure Motion only, allow exceptionally strong residual
     * agreement to recover vector confidence. This recovery:
     *   - uses only the already-warped alternate;
     *   - remains bounded by magnitudeConfidence;
     *   - remains bounded by validityConfidence;
     *   - cannot bypass the unchanged 12-pixel hard limit below;
     *   - remains subject to downstream local/occlusion confidence.
     *
     * Non-Motion behavior preserves the original vector-confidence path.
     */
    float residualSupportedVectorConfidence =
            motionEqualExposureStack != 0
                    ? 0.72
                            * smoothstep(
                                    0.96,
                                    0.995,
                                    residualConfidence
                            )
                            * magnitudeConfidence
                    : 0.0;

    float effectiveVectorConfidence =
            motionEqualExposureStack != 0
                    ? max(
                            vectorConsistency,
                            residualSupportedVectorConfidence
                    )
                    : vectorConsistency;

    float warpConfidence =
            confidenceSource
                    * effectiveVectorConfidence
                    * magnitudeConfidence
                    * validityConfidence;

    /*
     * Build 26273:
     * Keep the verified 26260 grid mapping and subpixel sampler unchanged.
     * A geometrically uncertain alternate must not fall back to its unwarped
     * position because that produces a temporal double image.
     *
     * Only a strongly accepted warp may contribute. Otherwise reconstruct a
     * zero alternate difference from the immutable reference Bayer sample.
     */
    /*
     * Build 26274:
     * merge0 exclusively owns geometric warp confidence. Unsafe warps remain
     * reference-only. Plausible warps may contribute gradually, but only from
     * the aligned alternate; the unwarped alternate is never restored.
     */
    float gradedWarpAcceptance =
            smoothstep(
                    0.28,
                    0.72,
                    warpConfidence
            );

    if (!validGridNeighborhood
            || !validWarpCoordinate
            || flowMagnitude >= 12.0
            || warpConfidence < 0.28) {
        gradedWarpAcceptance = 0.0;
    }

    imageStore(
            warpConfidenceTexture,
            xy,
            vec4(gradedWarpAcceptance, 0.0, 0.0, 1.0)
    );

    /*
     * Build 26276 diagnostic only:
     * R=residualConfidence
     * G=vectorConsistency
     * B=warpConfidence before grading
     * A=gradedWarpAcceptance
     */
    imageStore(
            mergeConfidenceDiagnosticTexture,
            xy,
            vec4(
                    residualConfidence,
                    vectorConsistency,
                    warpConfidence,
                    gradedWarpAcceptance
            )
    );

    /*
     * Build 26277 diagnostic only:
     * R=validGridNeighborhood
     * G=validWarpCoordinate
     * B=flowMagnitude normalized to the 12-pixel hard limit
     * A=magnitudeConfidence
     */
    imageStore(
            mergeValidityDiagnosticTexture,
            xy,
            vec4(
                    validGridNeighborhood ? 1.0 : 0.0,
                    validWarpCoordinate ? 1.0 : 0.0,
                    clamp(flowMagnitude / 12.0, 0.0, 1.0),
                    magnitudeConfidence
            )
    );

    alignedSum =
            mix(
                    bayer,
                    bayerAligned,
                    gradedWarpAcceptance
            );

    alignedSum =
            clamp(
                    alignedSum,
                    vec4(0.0),
                    vec4(1.0)
            );
    alignedSum *= vec4(exposure);
    float target = 1.0;
    if(exposure <= 0.9){
        target = 0.8;
    }
    /*if(any(greaterThan(alignedSum, vec4(target*exposure))) || any(greaterThan(bayerBase, vec4(target*exposure)))){
        alignedSum = bayerBase;
    }*/
    float ma = max(max(max(alignedSum.r, alignedSum.g), alignedSum.b), alignedSum.a);
    float mb = max(max(max(bayerBase.r, bayerBase.g), bayerBase.b), bayerBase.a);
    float mixf = clamp(max((ma-target*exposure),(mb-target*exposure))/(max(0.01,exposure-target*exposure)),0.0,1.0);
    float mixf2 = clamp(max((target*exposureLow-ma),(target*exposureLow-mb))/(max(0.01,exposureLow-target*exposureLow)),0.0,1.0);
    vec4 bbDiff = bayerBase - bayer;
    vec4 bbDiffm = max(abs(bbDiff) - noise, vec4(0.0));
    bbDiff *= (((noise*noise*8.0)/(noise*noise*8.0 + bbDiffm*bbDiffm)));

    //vec4 denoised = mix(bayer+bbDiff, bayer, clamp(mb,0.0,1.0));
    vec4 denoised = bayer+bbDiff;
    //alignedSum = mix(alignedSum, bayer, clamp(mixf+mixf2, 0.0,1.0));
    alignedSum -= bayer;
    alignedSum *= analogBalance;
    /*if(any(greaterThan(abs(alignedSum), vec4(target*exposure)))) {
        alignedSum = vec4(0.0);
    }*/
    vec4 an = max(abs(alignedSum) - noise, vec4(0.0));
    //alignedSum *= (((noise*noise*4.0)/(noise*noise*4.0 + an*an)));
    imageStore(outTexture, xy, clamp(alignedSum, vec4(-1.0), vec4(1.0)));
}
