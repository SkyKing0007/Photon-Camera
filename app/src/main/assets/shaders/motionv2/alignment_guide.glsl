#define LAYOUT //
LAYOUT
precision highp float;
precision highp sampler2D;
precision highp image2D;

uniform sampler2D InputCfa;
layout(r32f, binding=0) uniform highp writeonly image2D OutputGuide;
uniform int guideScale;
uniform float signalScale;

#ifndef CFAPATTERN
#define CFAPATTERN 0
#endif

/* IRIS_26420_V2_ALIGNMENT_GREEN_GUIDE */
/* IRIS_26421_GLES_R32F_ALIGNMENT_GUIDE */
float packedGreen(vec4 v) {
#if CFAPATTERN == 0 || CFAPATTERN == 3
    return 0.5*(v.g+v.b);
#else
    return 0.5*(v.r+v.a);
#endif
}

void main() {
    ivec2 q=ivec2(gl_GlobalInvocationID.xy);
    ivec2 outSize=imageSize(OutputGuide);
    if(any(greaterThanEqual(q,outSize))) return;

    ivec2 inSize=textureSize(InputCfa,0);
    ivec2 start=q*guideScale;
    float sum=0.0;
    float count=0.0;

    for(int y=0;y<4;y++){
        for(int x=0;x<4;x++){
            if(x>=guideScale || y>=guideScale) continue;
            ivec2 p=clamp(start+ivec2(x,y),ivec2(0),inSize-ivec2(1));
            vec4 c=max(texelFetch(InputCfa,p,0),vec4(0.0));
            sum+=packedGreen(c)/max(signalScale,1.0e-6);
            count+=1.0;
        }
    }

    imageStore(OutputGuide,q,vec4(sum/max(count,1.0),0.0,0.0,0.0));
}