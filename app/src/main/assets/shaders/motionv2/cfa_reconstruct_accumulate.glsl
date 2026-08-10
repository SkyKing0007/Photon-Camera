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

uniform ivec2 rawHalf;
uniform float noiseS;
uniform float noiseO;
uniform float maximumSupport;
uniform float sensorClipLevel;

/*
 * IRIS_26420_V2_OWNED_CONTINUOUS_FLOW_CONSUMER
 * IRIS_26423_TEMPORAL_IMPULSE_RESCUE
 */
vec4 sampleAlterLinear(vec2 coords) {
    ivec2 size=imageSize(alterTexture);
    vec2 safe=clamp(coords,vec2(0.0),vec2(size-ivec2(1)));
    ivec2 p0=ivec2(floor(safe));
    ivec2 p1=min(p0+ivec2(1),size-ivec2(1));
    vec2 f=fract(safe);
    vec4 a=imageLoad(alterTexture,p0);
    vec4 b=imageLoad(alterTexture,ivec2(p1.x,p0.y));
    vec4 c=imageLoad(alterTexture,ivec2(p0.x,p1.y));
    vec4 d=imageLoad(alterTexture,p1);
    return mix(mix(a,b,f.x),mix(c,d,f.x),f.y);
}
float max4(vec4 x){ return max(max(x.x,x.y),max(x.z,x.w)); }

void main(){
    ivec2 xy=ivec2(gl_GlobalInvocationID.xy);
    ivec2 outSize=imageSize(outTexture);
    if(any(greaterThanEqual(xy,outSize))) return;

    vec4 referenceValue=imageLoad(referenceTexture,xy);
    vec4 currentValue=imageLoad(currentTexture,xy);
    float support=max(imageLoad(currentSupport,xy).r,1.0);

    vec2 uv=(vec2(xy)+vec2(0.5))/vec2(max(rawHalf,ivec2(1)));
    vec4 flowSample=texture(flowTexture,uv);
    vec2 sharedFlow=flowSample.xy;
    float flowConfidence=clamp(flowSample.z,0.0,1.0);

    vec4 aligned=sampleAlterLinear(vec2(xy)+sharedFlow);
    vec4 unwarped=imageLoad(alterTexture,xy);

    ivec2 left=max(xy-ivec2(1,0),ivec2(0));
    ivec2 right=min(xy+ivec2(1,0),outSize-ivec2(1));
    ivec2 up=max(xy-ivec2(0,1),ivec2(0));
    ivec2 down=min(xy+ivec2(0,1),outSize-ivec2(1));

    vec4 localMean=0.25*(
            imageLoad(referenceTexture,left)
            +imageLoad(referenceTexture,right)
            +imageLoad(referenceTexture,up)
            +imageLoad(referenceTexture,down));

    vec4 localSigma=sqrt(max(
            max(localMean,vec4(0.0))*vec4(noiseS)+vec4(noiseO),
            vec4(1.0e-8)));

    vec4 positiveReferenceOutlier=
            (referenceValue-localMean)/max(localSigma,vec4(1.0e-5));
    vec4 alterToLocal=
            abs(aligned-localMean)/max(localSigma,vec4(1.0e-5));

    vec4 referenceImpulseMask=
            step(vec4(7.0),positiveReferenceOutlier)
            *(vec4(1.0)-step(vec4(3.2),alterToLocal))
            *step(vec4(0.18),vec4(flowConfidence));

    vec4 trustedReference=mix(referenceValue,localMean,referenceImpulseMask);

    vec4 sigma=sqrt(max(
            max(trustedReference,vec4(0.0))*vec4(noiseS)+vec4(noiseO),
            vec4(1.0e-8)));

    vec4 rawResidual=
            abs(aligned-trustedReference)/max(sigma,vec4(1.0e-5));
    vec4 auxiliaryImpulseMask=
            step(vec4(8.0),rawResidual)
            *(vec4(1.0)-referenceImpulseMask);
    float auxiliaryValidFraction=
            clamp(1.0-dot(auxiliaryImpulseMask,vec4(0.25)),0.0,1.0);

    vec4 robustAligned=mix(aligned,currentValue,auxiliaryImpulseMask);

    vec4 residualSigma=
            abs(robustAligned-trustedReference)/max(sigma,vec4(1.0e-5));
    float residualWorst=max4(residualSigma);
    float residualConfidence=1.0-smoothstep(2.4,6.5,residualWorst);

    float alignedError=dot(abs(robustAligned-trustedReference),vec4(0.25));
    float unwarpedError=dot(abs(unwarped-trustedReference),vec4(0.25));
    float meanSigma=max(dot(sigma,vec4(0.25)),1.0e-5);

    float warpRegression=max(alignedError-unwarpedError,0.0)/meanSigma;
    float warpPreference=1.0-smoothstep(1.5,5.0,warpRegression);

    float structure=max4(abs(trustedReference-localMean))/meanSigma;
    float strongReferenceStructure=smoothstep(3.0,8.0,structure);
    float structureProtection=mix(1.0,0.32,strongReferenceStructure);

    float clip=max(sensorClipLevel,1.0e-6);
    float referenceHighlight=max4(trustedReference);
    float alignedHighlight=max4(robustAligned);
    float highlightReliability=
            1.0-smoothstep(
                    0.965*clip,
                    0.998*clip,
                    max(referenceHighlight,alignedHighlight));

    float confidence=clamp(
            flowConfidence
            *residualConfidence
            *warpPreference
            *structureProtection
            *highlightReliability
            *auxiliaryValidFraction,
            0.0,1.0);

    if(flowConfidence<0.06
            || residualWorst>8.0
            || warpRegression>7.0
            || auxiliaryValidFraction<0.24){
        confidence=0.0;
    }

    vec4 mergeBase=mix(currentValue,robustAligned,referenceImpulseMask);

    float newSupport=min(maximumSupport,support+confidence);
    vec4 merged=confidence>0.0
            ? (mergeBase*support+robustAligned*confidence)
                    /max(newSupport,1.0e-6)
            : mergeBase;

    imageStore(outTexture,xy,merged);
    imageStore(outSupport,xy,vec4(newSupport));
}