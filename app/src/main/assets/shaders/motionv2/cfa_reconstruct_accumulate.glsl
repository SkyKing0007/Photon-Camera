#define LAYOUT //
LAYOUT
precision highp float;
precision highp sampler2D;
precision highp image2D;

uniform highp sampler2D flowTexture;
layout(rgba16f, binding = 0) uniform highp readonly image2D referenceTexture;
layout(rgba16f, binding = 1) uniform highp readonly image2D currentTexture;
layout(rgba16f, binding = 2) uniform highp readonly image2D alterTexture;
layout(r32f, binding = 3) uniform highp readonly image2D currentSupport;
layout(rgba16f, binding = 4) uniform highp writeonly image2D outTexture;
layout(r32f, binding = 5) uniform highp writeonly image2D outSupport;

uniform ivec2 rawSize;
uniform ivec2 rawHalf;
uniform int cfaPattern;
uniform float noiseS;
uniform float noiseO;
uniform float maximumSupport;
uniform float sensorClipLevel;
uniform float temporalDistanceMs;

/*
 * IRIS_26452_PHASE_AWARE_CFA_RECONSTRUCTION
 *
 * Packed RGBA is storage only: each component remains a physical Bayer site.
 * Flow is produced in packed-CFA pixels and converted exactly once to raw-pixel
 * displacement before any auxiliary observation is reconstructed.
 *
 * Spatial kernel support and temporal frame support are different units.
 * Each auxiliary frame produces one normalized physical-CFA observation and can
 * contribute at most one confidence-weighted frame equivalent.
 */

int componentIndex(ivec2 p) {
    return ((p.y & 1) << 1) | (p.x & 1);
}

int componentColor(int c) {
    if (cfaPattern == 0) {        // RGGB
        if (c == 0) return 0;
        if (c == 3) return 2;
        return 1;
    } else if (cfaPattern == 1) { // GRBG
        if (c == 1) return 0;
        if (c == 2) return 2;
        return 1;
    } else if (cfaPattern == 2) { // GBRG
        if (c == 2) return 0;
        if (c == 1) return 2;
        return 1;
    }                             // BGGR
    if (c == 3) return 0;
    if (c == 0) return 2;
    return 1;
}

ivec2 componentOffset(int c) {
    if (c == 0) return ivec2(0,0);
    if (c == 1) return ivec2(1,0);
    if (c == 2) return ivec2(0,1);
    return ivec2(1,1);
}

float getComponent(vec4 v, int c) {
    if (c == 0) return v.r;
    if (c == 1) return v.g;
    if (c == 2) return v.b;
    return v.a;
}

void setComponent(inout vec4 v, int c, float x) {
    if (c == 0) v.r=x;
    else if (c == 1) v.g=x;
    else if (c == 2) v.b=x;
    else v.a=x;
}

float physicalSampleAlter(ivec2 rawPos) {
    ivec2 p=clamp(rawPos,ivec2(0),rawSize-ivec2(1));
    vec4 cell=imageLoad(alterTexture,p>>1);
    return getComponent(cell,componentIndex(p));
}

float physicalSampleReference(ivec2 rawPos) {
    ivec2 p=clamp(rawPos,ivec2(0),rawSize-ivec2(1));
    vec4 cell=imageLoad(referenceTexture,p>>1);
    return getComponent(cell,componentIndex(p));
}

float packedGreen(vec4 v) {
    if (cfaPattern == 0 || cfaPattern == 3) {
        return 0.5*(v.g+v.b);
    }
    return 0.5*(v.r+v.a);
}

float referenceGreenCell(ivec2 packedPos) {
    ivec2 p=clamp(packedPos,ivec2(0),rawHalf-ivec2(1));
    return max(packedGreen(imageLoad(referenceTexture,p)),0.0);
}

float alterGreenRaw(ivec2 rawPos) {
    ivec2 p=clamp(rawPos,ivec2(0),rawSize-ivec2(1));
    ivec2 q=p>>1;
    return max(packedGreen(imageLoad(alterTexture,q)),0.0);
}

float currentGreenCell(ivec2 packedPos) {
    ivec2 p=clamp(packedPos,ivec2(0),rawHalf-ivec2(1));
    return max(packedGreen(imageLoad(currentTexture,p)),0.0);
}

float tukeyWeight(float x) {
    float a=abs(x);
    if(a>=1.0) return 0.0;
    float t=1.0-a*a;
    return t*t;
}

float cellWhiteLossReference(ivec2 packedPos) {
    ivec2 p=clamp(packedPos,ivec2(0),rawHalf-ivec2(1));
    vec4 v=max(imageLoad(referenceTexture,p),vec4(0.0));
    float peak=max(max(v.r,v.g),max(v.b,v.a));
    float clip=max(sensorClipLevel,1.0e-6);
    return smoothstep(0.840*clip,0.970*clip,peak);
}

float cellWhiteLossAlterRaw(ivec2 rawPos) {
    ivec2 p=clamp(rawPos,ivec2(0),rawSize-ivec2(1));
    vec4 v=max(imageLoad(alterTexture,p>>1),vec4(0.0));
    float peak=max(max(v.r,v.g),max(v.b,v.a));
    float clip=max(sensorClipLevel,1.0e-6);
    return smoothstep(0.840*clip,0.970*clip,peak);
}

void structureAtPacked(ivec2 xy, out vec2 normal, out float edgeStrength) {
    ivec2 l=xy-ivec2(1,0);
    ivec2 r=xy+ivec2(1,0);
    ivec2 u=xy-ivec2(0,1);
    ivec2 d=xy+ivec2(0,1);
    float gx=referenceGreenCell(r)-referenceGreenCell(l);
    float gy=referenceGreenCell(d)-referenceGreenCell(u);
    vec2 g=vec2(gx,gy);
    float mag=length(g);
    float center=max(referenceGreenCell(xy),0.02);
    edgeStrength=clamp(mag/(0.08+0.45*center),0.0,1.0);
    normal=mag>1.0e-6 ? normalize(g) : vec2(1.0,0.0);
}

float referenceLocalStd5(ivec2 xy) {
    float sum=0.0;
    float sum2=0.0;
    float count=0.0;
    for(int oy=-2;oy<=2;oy++){
        for(int ox=-2;ox<=2;ox++){
            float v=referenceGreenCell(xy+ivec2(ox,oy));
            sum+=v;
            sum2+=v*v;
            count+=1.0;
        }
    }
    float mean=sum/max(count,1.0);
    return sqrt(max(sum2/max(count,1.0)-mean*mean,0.0));
}

float flowContinuity(vec2 uv) {
    ivec2 fs=textureSize(flowTexture,0);
    vec2 texel=1.0/vec2(max(fs,ivec2(1)));
    vec2 c=texture(flowTexture,uv).xy;
    vec2 l=texture(flowTexture,uv-vec2(texel.x,0.0)).xy;
    vec2 r=texture(flowTexture,uv+vec2(texel.x,0.0)).xy;
    vec2 u=texture(flowTexture,uv-vec2(0.0,texel.y)).xy;
    vec2 d=texture(flowTexture,uv+vec2(0.0,texel.y)).xy;
    float span=max(max(length(l-c),length(r-c)),
                   max(length(u-c),length(d-c)));
    return 1.0-smoothstep(0.55,2.10,span);
}

float flowSpan(vec2 uv) {
    ivec2 fs=textureSize(flowTexture,0);
    vec2 texel=1.0/vec2(max(fs,ivec2(1)));
    vec2 c=texture(flowTexture,uv).xy;
    float s=0.0;
    for(int oy=-1;oy<=1;oy++){
        for(int ox=-1;ox<=1;ox++){
            vec2 f=texture(flowTexture,uv+vec2(float(ox),float(oy))*texel).xy;
            s=max(s,length(f-c));
        }
    }
    return s;
}

/*
 * Returns:
 *   x = normalized same-color physical CFA observation
 *   y = usable kernel coverage in [0,1]
 *
 * The numerator/denominator are normalized INSIDE this one frame. Therefore
 * the number of spatial samples never becomes temporal frame support.
 */
vec2 gatherObservation(
        vec2 sourceCoord,
        int wantedColor,
        vec2 normal,
        float edgeStrength) {
    ivec2 base=ivec2(floor(sourceCoord));
    vec2 tangent=vec2(-normal.y,normal.x);

    float sigmaAlong=mix(1.30,2.40,edgeStrength);
    float sigmaAcross=mix(1.30,0.72,edgeStrength);
    float invAlong2=1.0/max(sigmaAlong*sigmaAlong,0.04);
    float invAcross2=1.0/max(sigmaAcross*sigmaAcross,0.04);

    float numerator=0.0;
    float denominator=0.0;
    float geometricMass=0.0;
    float clip=max(sensorClipLevel,1.0e-6);

    for(int oy=-3;oy<=3;oy++){
        for(int ox=-3;ox<=3;ox++){
            ivec2 p=base+ivec2(ox,oy);
            if(any(lessThan(p,ivec2(0))) ||
               any(greaterThanEqual(p,rawSize))) continue;
            if(componentColor(componentIndex(p))!=wantedColor) continue;

            vec2 delta=(vec2(p)+vec2(0.5))-(sourceCoord+vec2(0.5));
            float along=dot(delta,tangent);
            float across=dot(delta,normal);
            float metric=along*along*invAlong2+across*across*invAcross2;
            float spatial=exp(-0.5*metric);
            geometricMass+=spatial;

            float value=max(physicalSampleAlter(p),0.0);
            float relative=value/clip;
            float saturationTrust=1.0-smoothstep(0.940,0.992,relative);
            float w=spatial*saturationTrust;
            numerator+=value*w;
            denominator+=w;
        }
    }

    if(denominator<=1.0e-7 || geometricMass<=1.0e-7) {
        return vec2(0.0,0.0);
    }
    return vec2(
            numerator/denominator,
            clamp(denominator/geometricMass,0.0,1.0));
}

void main() {
    ivec2 xy=ivec2(gl_GlobalInvocationID.xy);
    if(any(greaterThanEqual(xy,rawHalf))) return;

    vec4 currentValue=imageLoad(currentTexture,xy);
    float oldFrameSupport=clamp(
            imageLoad(currentSupport,xy).r,
            1.0,
            max(maximumSupport,1.0));

    vec2 uv=(vec2(xy)+vec2(0.5))/vec2(max(rawHalf,ivec2(1)));
    vec4 flow=texture(flowTexture,uv);

    /*
     * IRIS_26452_PACKED_TO_RAW_FLOW_CONTRACT
     * MotionV2Alignment publishes packed-CFA displacement. A packed texel spans
     * exactly two raw pixels on each axis, so multiply by two exactly once.
     */
    vec2 rawFlow=flow.xy*2.0;
    vec2 rawCellCenter=vec2(xy*2)+vec2(0.5,0.5);
    vec2 sourceCellCenter=rawCellCenter+rawFlow;

    vec2 normal;
    float edgeStrength;
    structureAtPacked(xy,normal,edgeStrength);

    float referenceCenter=referenceGreenCell(xy);
    float auxiliaryCenter=alterGreenRaw(ivec2(round(sourceCellCenter)));
    float currentCenter=currentGreenCell(xy);

    /*
     * IRIS_26452_CANONICAL_NOISE_ROBUSTNESS
     * noiseS/noiseO are already transformed by MotionV2CfaReconstruction:
     * y=g*x => Var(y)=(g*S)*y + g^2*O.
     */
    float fallbackSigmaReference=
            0.018+0.065*sqrt(max(referenceCenter,0.0))
            +0.010*referenceCenter;
    float fallbackSigmaAuxiliary=
            0.018+0.065*sqrt(max(auxiliaryCenter,0.0))
            +0.010*auxiliaryCenter;

    float modeledSigmaReference=sqrt(max(
            referenceCenter*max(noiseS,0.0)+max(noiseO,0.0),1.0e-8));
    float modeledSigmaAuxiliary=sqrt(max(
            auxiliaryCenter*max(noiseS,0.0)+max(noiseO,0.0),1.0e-8));

    float sigmaReference=clamp(
            modeledSigmaReference,
            0.70*fallbackSigmaReference,
            2.25*fallbackSigmaReference);
    float sigmaAuxiliary=clamp(
            modeledSigmaAuxiliary,
            0.70*fallbackSigmaAuxiliary,
            2.25*fallbackSigmaAuxiliary);

    float alignmentSigma=
            0.35*sigmaReference
            *clamp(max(flow.w,0.0)/0.070,0.0,2.0);

    float structureAllowance=min(
            referenceLocalStd5(xy),
            2.0*max(sigmaReference,sigmaAuxiliary));

    float combinedSigma=sqrt(
            sigmaReference*sigmaReference
            +sigmaAuxiliary*sigmaAuxiliary
            +alignmentSigma*alignmentSigma
            +0.25*structureAllowance*structureAllowance
            +1.0e-8);

    float immutableResidualSigma=
            abs(auxiliaryCenter-referenceCenter)
            /max(combinedSigma,1.0e-5);

    /*
     * Current temporal consensus is a weak consistency signal only. The
     * immutable physical reference remains the decisive ownership authority.
     */
    float consensusSigma=sqrt(
            combinedSigma*combinedSigma
            +max(sigmaAuxiliary*sigmaAuxiliary,1.0e-8));
    float temporalResidualSigma=
            abs(auxiliaryCenter-currentCenter)
            /max(consensusSigma,1.0e-5);

    float alignmentTrust=clamp(flow.z,0.0,1.0);
    float alignmentResidualTrust=
            1.0-smoothstep(0.025,0.070,max(flow.w,0.0));
    float immutableReferenceTrust=tukeyWeight(immutableResidualSigma/2.80);
    float temporalTrust=tukeyWeight(temporalResidualSigma/3.20);
    float continuityTrust=flowContinuity(uv);
    float localSpan=flowSpan(uv);
    float localFlowTrust=1.0-smoothstep(0.55,2.10,localSpan);

    float ageRisk=smoothstep(160.0,450.0,max(temporalDistanceMs,0.0));
    float weakAgePrior=mix(1.0,0.88,ageRisk);

    float referenceWhiteLoss=cellWhiteLossReference(xy);
    float sourceWhiteLoss=
            cellWhiteLossAlterRaw(ivec2(round(sourceCellCenter)));
    float specularRisk=max(referenceWhiteLoss,sourceWhiteLoss);
    float specularAuthority=
            mix(1.0,0.82,smoothstep(0.12,0.58,specularRisk));

    vec4 observation=vec4(0.0);
    vec4 coverage=vec4(0.0);

    for(int c=0;c<4;c++){
        ivec2 rawOut=xy*2+componentOffset(c);
        vec2 sourceCoord=vec2(rawOut)+rawFlow;
        int wantedColor=componentColor(c);
        vec2 obs=gatherObservation(
                sourceCoord,wantedColor,normal,edgeStrength);
        setComponent(observation,c,obs.x);
        setComponent(coverage,c,obs.y);
    }

    /*
     * IRIS_26452_SHARED_COLOR_OBSERVATION_COHERENCE
     * Convert the four physical Bayer-site coverages into R/G/B frame evidence.
     * Green has two physical phases, so use their mean rather than double-counting.
     */
    float rCoverage=0.0;
    float gCoverage=0.0;
    float bCoverage=0.0;
    float gCount=0.0;
    for(int c=0;c<4;c++){
        int color=componentColor(c);
        float cv=getComponent(coverage,c);
        if(color==0) rCoverage=cv;
        else if(color==2) bCoverage=cv;
        else { gCoverage+=cv; gCount+=1.0; }
    }
    gCoverage/=max(gCount,1.0);

    float strongestCoverage=max(rCoverage,max(gCoverage,bCoverage));
    float weakestCoverage=min(rCoverage,min(gCoverage,bCoverage));
    float channelCoverageRatio=
            weakestCoverage/max(strongestCoverage,1.0e-5);

    float sharedChannelValidity=smoothstep(
            mix(0.10,0.16,specularRisk),
            mix(0.38,0.50,specularRisk),
            channelCoverageRatio);

    /*
     * Ratio alone is insufficient when every channel is unsupported (e.g. all
     * clipped). Require real absolute same-color evidence too.
     */
    float absoluteCoverageAuthority=
            smoothstep(0.05,0.25,weakestCoverage);

    float sharedConfidence=clamp(
            alignmentTrust
            *alignmentResidualTrust
            *immutableReferenceTrust
            *mix(0.92,1.0,temporalTrust)
            *continuityTrust
            *localFlowTrust
            *weakAgePrior
            *specularAuthority
            *sharedChannelValidity
            *absoluteCoverageAuthority,
            0.0,1.0);

    /*
     * IRIS_26452_DECISIVE_REFERENCE_FALLBACK
     * Unsafe or ambiguous auxiliary evidence contributes zero. There is never
     * an unaligned auxiliary fallback.
     */
    bool temporalConflict=temporalResidualSigma>4.20;
    bool immutableReferenceConflict=immutableResidualSigma>3.10;
    bool alignmentConflict=
            alignmentTrust<0.06 || alignmentResidualTrust<0.18;
    bool occlusionConflict=continuityTrust<0.12;
    bool localFlowConflict=localSpan>2.35;
    bool colorCoverageConflict=weakestCoverage<0.025;

    if(temporalConflict || immutableReferenceConflict ||
       alignmentConflict || occlusionConflict ||
       localFlowConflict || colorCoverageConflict) {
        sharedConfidence=0.0;
    }

    /*
     * IRIS_26452_TRUE_FRAME_EQUIVALENT_CFA_SUPPORT
     * One auxiliary can add at most one frame equivalent, independent of how
     * many spatial CFA samples were used to reconstruct its normalized observation.
     */
    float remaining=max(maximumSupport-oldFrameSupport,0.0);
    float frameContribution=min(sharedConfidence,remaining);
    float newFrameSupport=oldFrameSupport+frameContribution;

    vec4 merged=currentValue;
    if(frameContribution>0.0){
        merged=
                (currentValue*oldFrameSupport
                 +observation*frameContribution)
                /max(newFrameSupport,1.0e-6);
    }

    imageStore(outTexture,xy,max(merged,vec4(0.0)));
    imageStore(outSupport,xy,vec4(newFrameSupport));
}