#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D highlightProvenance;
layout(rgba32f,binding=0) uniform highp writeonly image2D outWeight;
uniform ivec2 packedSize;

/* IRIS_26501_SHORT_VALIDATED_SEMANTIC_PHASE_WEIGHT
 * Preserve the existing Short-A validator phase by phase. Each packed texel stores
 * R/G1/G2/B authority independently; a validated red phase can never authorize a
 * neighbouring green or blue phase. Native short RAW is still the only color source.
 */
float phaseDivisor(int q){return q==0?1.0:(q==1?3.0:(q==2?9.0:27.0));}
void main(){
    ivec2 p=ivec2(gl_GlobalInvocationID.xy);
    if(any(greaterThanEqual(p,packedSize)))return;
    float code=texelFetch(highlightProvenance,p,0).r;
    vec4 weight=vec4(0.0);
    for(int q=0;q<4;++q){
        float state=mod(floor(code/phaseDivisor(q)),3.0);
        weight[q]=abs(state-2.0)<0.25?1.0:0.0;
    }
    imageStore(outWeight,p,weight);
}
