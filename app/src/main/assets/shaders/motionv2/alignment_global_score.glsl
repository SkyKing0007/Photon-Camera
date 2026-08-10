#define LAYOUT //
LAYOUT
precision highp float;
precision highp sampler2D;
precision highp image2D;

uniform sampler2D ReferenceGuide;
uniform sampler2D AlterGuide;
layout(r32f, binding=0) uniform highp writeonly image2D OutputScore;
uniform int searchRadius;

/*
 * IRIS_26420_V2_GLOBAL_TRANSLATION_SEARCH
 * Large-range robust search on the V2-owned low-resolution green guide.
 * Each output pixel is one candidate displacement.
 */
void main() {
    ivec2 c=ivec2(gl_GlobalInvocationID.xy);
    ivec2 scoreSize=imageSize(OutputScore);
    if(any(greaterThanEqual(c,scoreSize))) return;

    ivec2 shift=c-ivec2(searchRadius);
    ivec2 sz=textureSize(ReferenceGuide,0);

    float sum=0.0;
    float count=0.0;
    for(int y=8;y<sz.y-8;y+=8){
        for(int x=8;x<sz.x-8;x+=8){
            ivec2 p=ivec2(x,y);
            ivec2 q=p+shift;
            if(any(lessThan(q,ivec2(1))) ||
               any(greaterThanEqual(q,sz-ivec2(1)))) continue;
            float a=texelFetch(ReferenceGuide,p,0).r;
            float b=texelFetch(AlterGuide,q,0).r;
            float d=abs(a-b);
            sum+=min(d,0.12);
            count+=1.0;
        }
    }
    float score=count>16.0 ? sum/count : 1.0e6;
    imageStore(OutputScore,c,vec4(score,0.0,0.0,0.0));
}