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
float gainFor(int c){ return c==0?wbR:(c==2?wbB:wbG); }

/* IRIS_26463_WRONSKI_PUBLIC_RAW_WB_DOMAIN
 * Public loader normalizes each CFA sample then multiplies by camera WB
 * normalized to green before the Wronski core.
 */
void main(){
    ivec2 p=ivec2(gl_GlobalInvocationID.xy);
    ivec2 sz=imageSize(outputCfa);
    if(any(greaterThanEqual(p,sz))) return;
    vec4 v=imageLoad(inputCfa,p);
    vec4 o;
    o.r=v.r*gainFor(componentColor(0));
    o.g=v.g*gainFor(componentColor(1));
    o.b=v.b*gainFor(componentColor(2));
    o.a=v.a*gainFor(componentColor(3));
    imageStore(outputCfa,p,o);
}
