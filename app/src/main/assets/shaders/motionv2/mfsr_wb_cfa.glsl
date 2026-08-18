#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
layout(rgba16f,binding=0) uniform highp readonly image2D inputCfa;
layout(rgba16f,binding=1) uniform highp writeonly image2D outputCfa;
uniform int cfaPattern;
uniform float wbR;
uniform float wbG;
uniform float wbB;
int componentColor(int c){
    if(cfaPattern==0){if(c==0)return 0;if(c==3)return 2;return 1;}
    if(cfaPattern==1){if(c==1)return 0;if(c==2)return 2;return 1;}
    if(cfaPattern==2){if(c==2)return 0;if(c==1)return 2;return 1;}
    if(c==3)return 0;if(c==0)return 2;return 1;
}
float gainForColor(int c){return c==0?wbR:(c==2?wbB:wbG);}
/* IRIS_26487_SINGLE_CLIPPING_AUTHORITY_WB_ONLY
 * Calculation-domain WB is a linear scale only. No clipped CFA sample is
 * synthesized or hue-repaired here. Physical clipping is carried separately
 * from pre-WB CFA and treated as censored evidence by merge/recovery stages.
 */
void main(){
    ivec2 q=ivec2(gl_GlobalInvocationID.xy);
    ivec2 sz=imageSize(outputCfa);
    if(any(greaterThanEqual(q,sz))) return;
    vec4 camera=max(imageLoad(inputCfa,q),vec4(0.0));
    vec4 gains=vec4(
        gainForColor(componentColor(0)),
        gainForColor(componentColor(1)),
        gainForColor(componentColor(2)),
        gainForColor(componentColor(3)));
    imageStore(outputCfa,q,camera*max(gains,vec4(1.0e-6)));
}
