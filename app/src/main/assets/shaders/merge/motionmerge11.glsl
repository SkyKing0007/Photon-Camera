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
layout(r32f, binding = 6) uniform highp readonly image2D warpConfidenceTexture;
layout(rgba32f, binding = 7) uniform highp writeonly image2D mergeDecisionDiagnosticTexture;

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
uniform float motionTemporalConfidence;
uniform int motionMergeOrdinal;
uniform highp sampler2D motionAlignmentTexture;
uniform ivec2 motionAlignmentShift;
uniform ivec2 motionAlignmentSize;
uniform ivec2 motionRawHalf;
uniform int motionAlignmentTile;
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
vec2 decodeAlignmentVector(vec4 packed) {
    return packed.xy * vec2(motionRawHalf) + packed.zw;
}
float geometricAlignmentConfidence(ivec2 xy) {
    ivec2 tileCoord = clamp(xy / max(1, motionAlignmentTile / 2), ivec2(0), motionAlignmentSize - ivec2(1));
    ivec2 atlasCoord = motionAlignmentShift + tileCoord;
    ivec2 atlasMin = motionAlignmentShift;
    ivec2 atlasMax = motionAlignmentShift + motionAlignmentSize - ivec2(1);
    vec2 c = decodeAlignmentVector(texelFetch(motionAlignmentTexture, clamp(atlasCoord, atlasMin, atlasMax), 0));
    vec2 l = decodeAlignmentVector(texelFetch(motionAlignmentTexture, clamp(atlasCoord + ivec2(-1,0), atlasMin, atlasMax), 0));
    vec2 r = decodeAlignmentVector(texelFetch(motionAlignmentTexture, clamp(atlasCoord + ivec2(1,0), atlasMin, atlasMax), 0));
    vec2 u = decodeAlignmentVector(texelFetch(motionAlignmentTexture, clamp(atlasCoord + ivec2(0,-1), atlasMin, atlasMax), 0));
    vec2 d = decodeAlignmentVector(texelFetch(motionAlignmentTexture, clamp(atlasCoord + ivec2(0,1), atlasMin, atlasMax), 0));
    vec2 m = 0.25 * (l+r+u+d);
    float outlier = length(c-m) + 0.125*(length(l-m)+length(r-m)+length(u-m)+length(d-m));
    return 1.0 - smoothstep(0.35, 2.20, outlier);
}
float expandedOcclusionDisagreement(ivec2 xy) {
    float mx = 0.0;
    for (int oy=-1; oy<=1; oy++) {
        for (int ox=-1; ox<=1; ox++) {
            ivec2 p = clamp(
                    xy + ivec2(ox,oy),
                    ivec2(0),
                    imageSize(diffOrTexture)-ivec2(1));
            vec4 residual = abs(imageLoad(diffOrTexture,p));
            float scalarResidual = max(
                    max(residual.r, residual.g),
                    max(residual.b, residual.a));
            mx = max(mx, scalarResidual);
        }
    }
    return mx;
}
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

    /*
     * Build 26252:
     * Local temporal-retention guard for disagreement-prone structural edges.
     *
     * A globally healthy stack can still contain a small region where the
     * aligned alternate disagrees with both the running base and the same-CFA
     * spatial neighborhood. That produced the translucent/doubled speaker
     * edge in the supplied artifact sample.
     *
     * The guard stays neutral in stable regions. It reduces temporal
     * retention only when:
     * 1. candidate/base disagreement exceeds modeled noise;
     * 2. the candidate is less spatially consistent than the running base;
     * 3. meaningful local edge structure is present.
     */
    vec4 mergeCandidate =
            bayer
                    + diff
                    / max(
                            analogBalance,
                            vec4(EPS)
                    );

    vec4 candidateBaseResidual =
            mergeCandidate
                    - base;

    vec4 candidateReferenceResidual =
            mergeCandidate
                    - bayer;

    float temporalDisagreement =
            max(
                    length(candidateBaseResidual),
                    max(
                            max(
                                    abs(candidateBaseResidual.r),
                                    abs(candidateBaseResidual.g)
                            ),
                            max(
                                    abs(candidateBaseResidual.b),
                                    abs(candidateBaseResidual.a)
                            )
                    ) * 2.0
            );

    /*
     * Build 26256:
     * Compare every reconstructed candidate against both the recursive merge
     * and the immutable Bayer reference. The recursive base may already carry
     * sub-pixel blur, so agreement with it alone cannot prove that fine text
     * or a dark structural edge is correctly aligned.
     */
    float immutableReferenceDisagreement =
            max(
                    length(candidateReferenceResidual),
                    max(
                            max(
                                    abs(candidateReferenceResidual.r),
                                    abs(candidateReferenceResidual.g)
                            ),
                            max(
                                    abs(candidateReferenceResidual.b),
                                    abs(candidateReferenceResidual.a)
                            )
                    ) * 2.0
            );

    float baseSpatialError =
            length(
                    base
                            - mean
            );

    float immutableReferenceEdge =
            length(
                    bayer
                            - mean
            );

    float candidateSpatialError =
            length(
                    mergeCandidate
                            - mean
            );

    float modeledNoiseMagnitude =
            max(
                    length(noise),
                    EPS
            );

    float localEdgeStrength =
            max(
                    baseSpatialError,
                    sqrt(length(variance) + EPS)
            );

    /*
     * Build 26254:
     * The first local guard still allowed fine lettering to soften because
     * three gates were multiplied together. A weak value from any one gate
     * could hide real temporal disagreement at a small structural edge.
     *
     * Treat temporal disagreement and spatial inconsistency as alternative
     * evidence, while still requiring local edge support. Thresholds begin
     * closer to modeled noise so lettering and grille perforations are
     * protected before they become visibly doubled.
     */
    float temporalDisagreementGate =
            smoothstep(
                    modeledNoiseMagnitude * 0.75,
                    modeledNoiseMagnitude * 2.20
                            + 0.006,
                    temporalDisagreement
            );

    float spatialConsistencyGate =
            smoothstep(
                    modeledNoiseMagnitude * 0.35,
                    modeledNoiseMagnitude * 2.00
                            + 0.006,
                    candidateSpatialError
                            - baseSpatialError
            );

    float edgeSupportGate =
            smoothstep(
                    modeledNoiseMagnitude * 0.30,
                    modeledNoiseMagnitude * 2.25
                            + 0.007,
                    localEdgeStrength
            );

    float temporalEdgeDisagreement =
            temporalDisagreementGate
                    * edgeSupportGate;

    float spatialEdgeDisagreement =
            spatialConsistencyGate
                    * edgeSupportGate;

    /*
     * Dark lettering and upholstery seams can have low absolute signal while
     * still containing a real edge. Normalize candidate/reference mismatch by
     * modeled noise and require support from the immutable reference edge.
     */
    float immutableReferenceMismatchGate =
            smoothstep(
                    modeledNoiseMagnitude * 0.60,
                    modeledNoiseMagnitude * 1.85
                            + 0.004,
                    immutableReferenceDisagreement
            );

    float immutableReferenceEdgeGate =
            smoothstep(
                    modeledNoiseMagnitude * 0.20,
                    modeledNoiseMagnitude * 1.60
                            + 0.003,
                    immutableReferenceEdge
            );

    float immutableReferenceEdgeDisagreement =
            immutableReferenceMismatchGate
                    * immutableReferenceEdgeGate;

    float localMergeDisagreement =
            clamp(
                    max(
                            max(
                                    temporalEdgeDisagreement,
                                    spatialEdgeDisagreement
                            ),
                            immutableReferenceEdgeDisagreement
                    ),
                    0.0,
                    1.0
            );

    /*
     * A clearly inconsistent structural pixel falls fully back to the running
     * reference. Stable pixels retain confidence 1.0 and therefore preserve
     * the existing full-stack denoise.
     */
    float localMergeConfidence =
            1.0 - smoothstep(0.035, 0.30, localMergeDisagreement);

    /*
     * Build 26274:
     * Consume merge0's exact geometric decision instead of reconstructing a
     * second, conflicting confidence from neighboring vectors.
     */
    float persistentWarpConfidence =
            clamp(
                    imageLoad(warpConfidenceTexture, xy).r,
                    0.0,
                    1.0
            );

    float occlusionDisagreement = expandedOcclusionDisagreement(xy);
    float occlusionConfidence = 1.0 - smoothstep(
            predictedNoiseCap * 2.0 + 0.01,
            predictedNoiseCap * 7.0 + 0.08,
            occlusionDisagreement);
    float accumulatedAgreement = clamp(
            imageLoad(contributionTexture, xy).r,
            0.0,
            1.0);
    float consensusConfidence = smoothstep(
            contributionIncrement * 0.50,
            contributionIncrement * 2.25,
            accumulatedAgreement);

    /*
     * Keep consensus active, but avoid the cold-start feedback loop where an
     * initially empty contribution map prevents otherwise valid frames from
     * ever establishing consensus.
     */
    float consensusGate =
            mix(
                    0.68,
                    1.0,
                    consensusConfidence
            );

    float structuralConfidence = clamp(
            min(
                    occlusionConfidence,
                    localMergeConfidence
                            * motionTemporalConfidence
                            * consensusGate
            ),
            0.0,
            1.0
    );

    /*
     * Persistent warp confidence is a strict upper bound. Later stages may
     * reduce a geometrically valid contribution, but cannot override or
     * recreate the alignment decision.
     */
    float trustedMergeConfidence =
            min(
                    persistentWarpConfidence,
                    structuralConfidence
            );

    if (persistentWarpConfidence < 0.05
            || occlusionConfidence < 0.10
            || localMergeConfidence < 0.05) {
        trustedMergeConfidence = 0.0;
    }

    /*
     * Build 26276 diagnostic only:
     * R=persistentWarpConfidence
     * G=localMergeConfidence
     * B=occlusionConfidence
     * A=trustedMergeConfidence
     */
    imageStore(
            mergeDecisionDiagnosticTexture,
            xy,
            vec4(
                    persistentWarpConfidence,
                    localMergeConfidence,
                    occlusionConfidence,
                    trustedMergeConfidence
            )
    );

    lDiff *= trustedMergeConfidence;
    preservedIndependentFraction *= trustedMergeConfidence;

    // Reconstruct from the original temporal direction after local gating.
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
                                            * preservedIndependentFraction
                                            * nativeSrScalarConfidence,
                            0.0,
                            1.0
                    ),
                    0.0,
                    0.0,
                    1.0
            )
    );

    /*
     * Build 26232:
     * The iterative merge-time impulse detector was retired after runtime
     * counters remained zero despite visible randomized defects. Correction
     * now occurs once on the stable merged CFA texture immediately before
     * demosaic.
     */
    vec4 correctedBase = base;
    vec4 correctedCandidate = diff / analogBalance + bayer;

    /*
     * Build 26281 native-resolution robust CFA accumulator.
     *
     * Photon already aligns every alternate into the four-channel rawHalf CFA
     * domain. Keep the same binned output geometry, but weight each CFA plane
     * independently so one bad or saturated channel cannot contaminate all
     * channels in the texel.
     *
     * This is reference anchored: only the already-aligned candidate is used,
     * and trustedMergeConfidence remains the geometric/occlusion upper bound.
     */
    vec4 nativeSrNoiseScale =
            max(
                    noise * 2.75 + vec4(0.004),
                    vec4(EPS)
            );

    vec4 nativeSrNormalizedResidual =
            abs(correctedCandidate - correctedBase)
                    / nativeSrNoiseScale;

    vec4 nativeSrRobustConfidence =
            vec4(1.0)
                    / (
                            vec4(1.0)
                                    + nativeSrNormalizedResidual
                                            * nativeSrNormalizedResidual
                    );

    vec4 nativeSrSignalPeak =
            max(
                    max(correctedCandidate, correctedBase),
                    bayer
            );

    vec4 nativeSrSaturationConfidence =
            vec4(1.0)
                    - smoothstep(
                            vec4(0.94),
                            vec4(0.995),
                            nativeSrSignalPeak
                    );

    vec4 nativeSrChannelConfidence =
            clamp(
                    vec4(trustedMergeConfidence)
                            * nativeSrRobustConfidence
                            * nativeSrSaturationConfidence,
                    vec4(0.0),
                    vec4(1.0)
            );

    float nativeSrScalarConfidence =
            dot(
                    nativeSrChannelConfidence,
                    vec4(0.25)
            );
    /*
     * Build 26255:
     * Reference-detail lock for fine static structure.
     *
     * 26254 reduced the candidate blend, but repeated sub-pixel averaging
     * could still soften lettering and upholstery seams. Preserve the current
     * reference detail whenever local temporal disagreement overlaps real
     * structural detail, while still allowing low-frequency temporal denoise.
     *
     * The local median is used only as a low-frequency anchor. High-frequency
     * content from correctedBase is retained progressively as confidence
     * falls. Stable regions keep the original temporal blend.
     */
    vec4 finalMergeWeight =
            clamp(
                    vec4(weight)
                            * nativeSrChannelConfidence,
                    vec4(0.0),
                    vec4(1.0)
            );

    vec4 temporallyMerged =
            mix(
                    correctedBase,
                    correctedCandidate,
                    finalMergeWeight
            );

    /*
     * Build 26256:
     * Use true immutable reference detail. 26255 mistakenly derived
     * "reference" high frequency from correctedBase, which is the recursive
     * accumulation and can already contain the ghost contour we are trying to
     * remove.
     */
    vec4 immutableReferenceHighFrequency =
            bayer
                    - mean;

    vec4 accumulatedHighFrequency =
            correctedBase
                    - mean;

    float referenceDetailMagnitude =
            length(immutableReferenceHighFrequency);

    float fineStructureGate =
            smoothstep(
                    modeledNoiseMagnitude * 0.15,
                    modeledNoiseMagnitude * 1.45
                            + 0.003,
                    referenceDetailMagnitude
            );

    float confidenceDrivenReferenceLock =
            clamp(
                    fineStructureGate
                            * (
                                    1.0
                                            - trustedMergeConfidence
                            ),
                    0.0,
                    1.0
            );

    /*
     * Build 26257:
     * 26256 produced no visible change, proving the mismatch-driven confidence
     * rarely crossed its threshold in the affected dark structures.
     *
     * Use the immutable reference neighborhood itself to identify dark
     * structural detail. This does not classify every dark pixel as unsafe:
     * smooth dark surfaces keep fineStructureGate near zero. A dark
     * neighborhood with a real edge, lettering, grille opening, or upholstery
     * seam receives a direct reference-detail lock independent of the
     * post-warp mismatch score.
     */
    float immutableNeighborhoodLuma =
            dot(
                    mean,
                    vec4(0.25)
            );

    float darkNeighborhoodGate =
            1.0
                    - smoothstep(
                            0.16,
                            0.38,
                            immutableNeighborhoodLuma
                    );

    float referenceStructureSupport =
            max(
                    referenceDetailMagnitude,
                    sqrt(
                            length(variance)
                                    + EPS
                    )
            );

    float darkStructureEdgeGate =
            smoothstep(
                    modeledNoiseMagnitude * 0.10,
                    modeledNoiseMagnitude * 1.15
                            + 0.002,
                    referenceStructureSupport
            );

    float hardDarkStructureReferenceLock =
            clamp(
                    darkNeighborhoodGate
                            * darkStructureEdgeGate
                            * 0.96,
                    0.0,
                    0.96
            );

    float referenceDetailLock =
            max(
                    confidenceDrivenReferenceLock,
                    hardDarkStructureReferenceLock
            );

    /*
     * Preserve the temporally merged low-frequency result, but replace the
     * suspect accumulated high-frequency component with the immutable Bayer
     * reference component. The forced path is limited to dark structural
     * detail; smooth shadows retain the temporal stack.
     */
    vec4 referenceDetailCorrection =
            immutableReferenceHighFrequency
                    - accumulatedHighFrequency;

    vec4 finalOutput =
            temporallyMerged
                    + referenceDetailCorrection
                    * referenceDetailLock;

    imageStore(
            outTexture,
            xy,
            clamp(
                    finalOutput,
                    0.0,
                    1.0
            )
    );
    //imageStore(outTexture, xy, diff);
}
