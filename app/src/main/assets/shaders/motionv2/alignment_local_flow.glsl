#define LAYOUT //
LAYOUT
precision highp float;
precision highp sampler2D;
precision highp image2D;

uniform sampler2D ReferenceGuide;
uniform sampler2D AlterGuide;
layout(rgba16f, binding=0) uniform highp writeonly image2D OutputFlow;
uniform ivec2 globalShiftGuide;
uniform float guideScale;

float patchCost(ivec2 p, ivec2 candidateShift) {
    ivec2 sz=textureSize(ReferenceGuide,0);
    float sum=0.0;
    float count=0.0;
    for(int y=-1;y<=1;y++){
        for(int x=-1;x<=1;x++){
            ivec2 r=clamp(p+ivec2(x,y),ivec2(0),sz-ivec2(1));
            ivec2 a=clamp(r+candidateShift,ivec2(0),sz-ivec2(1));
            float rv=texelFetch(ReferenceGuide,r,0).r;
            float av=texelFetch(AlterGuide,a,0).r;
            sum+=min(abs(rv-av),0.10);
            count+=1.0;
        }
    }
    return sum/max(count,1.0);
}

/*
 * IRIS_26420_V2_CONTINUOUS_LOCAL_FLOW
 *
 * The global search owns capture range. A dense soft 3x3 local search then
 * produces fractional residual displacement. The texture is sampled LINEAR by
 * reconstruction, so the final field is continuous rather than tile-owned.
 */
void main() {
    ivec2 p=ivec2(gl_GlobalInvocationID.xy);
    ivec2 sz=imageSize(OutputFlow);
    if(any(greaterThanEqual(p,sz))) return;

    float costs[9];
    float best=1.0e9;
    float secondBest=1.0e9;
    int k=0;

    for(int dy=-1;dy<=1;dy++){
        for(int dx=-1;dx<=1;dx++){
            float c=patchCost(p,globalShiftGuide+ivec2(dx,dy));
            costs[k++]=c;
            if(c<best){
                secondBest=best;
                best=c;
            } else if(c<secondBest){
                secondBest=c;
            }
        }
    }

    float temperature=max(0.004,0.55*best+0.002);
    vec2 residual=vec2(0.0);
    float wsum=0.0;
    k=0;
    for(int dy=-1;dy<=1;dy++){
        for(int dx=-1;dx<=1;dx++){
            float w=exp(-(costs[k++]-best)/temperature);
            residual+=w*vec2(dx,dy);
            wsum+=w;
        }
    }
    residual/=max(wsum,1.0e-6);

    ivec2 l=max(p-ivec2(1,0),ivec2(0));
    ivec2 r=min(p+ivec2(1,0),sz-ivec2(1));
    ivec2 u=max(p-ivec2(0,1),ivec2(0));
    ivec2 d=min(p+ivec2(0,1),sz-ivec2(1));
    float center=texelFetch(ReferenceGuide,p,0).r;
    float structure=max(
            abs(texelFetch(ReferenceGuide,l,0).r-
                texelFetch(ReferenceGuide,r,0).r),
            abs(texelFetch(ReferenceGuide,u,0).r-
                texelFetch(ReferenceGuide,d,0).r));

    float photometric=1.0-smoothstep(0.020,0.105,best);
    float uniqueness=smoothstep(
            0.0015,
            0.020,
            max(secondBest-best,0.0));
    float structureTrust=smoothstep(0.001,0.018,structure);

    /*
     * Flat regions may legitimately align from the global estimate, so they
     * retain a conservative confidence floor instead of becoming holes.
     */
    float confidence=photometric
            * mix(0.48,1.0,max(uniqueness,structureTrust));
    confidence=clamp(confidence,0.0,1.0);

    vec2 flowPacked=
            (vec2(globalShiftGuide)+residual)*guideScale;

    imageStore(OutputFlow,p,vec4(flowPacked,confidence,best));
}