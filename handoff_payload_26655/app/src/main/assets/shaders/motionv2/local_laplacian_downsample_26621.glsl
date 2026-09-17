precision highp float;
precision highp int;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
uniform int iris26655EdgeAware;
out float Output;

float irisAt(ivec2 p){
    ivec2 sz=textureSize(InputBuffer,0);
    return texelFetch(InputBuffer,clamp(p,ivec2(0),sz-ivec2(1)),0).r;
}
float irisKernel5(int o){
    int a=abs(o);
    if(a==0)return 6.0;
    if(a==1)return 4.0;
    return 1.0;
}
void main(){
    ivec2 q=ivec2(gl_FragCoord.xy);
    ivec2 center=q*2;
    if(iris26655EdgeAware==0){
        /* Exact inherited 26654 Local-Laplacian downsample path. */
        float legacySum=0.0;
        for(int oy=-2;oy<=2;oy++){
            float wy=irisKernel5(oy);
            for(int ox=-2;ox<=2;ox++){
                float wx=irisKernel5(ox);
                legacySum+=irisAt(center+ivec2(ox,oy))*(wx*wy);
            }
        }
        Output=legacySum*(1.0/256.0);
        return;
    }

    float centerValue=irisAt(center);
    float sum=0.0;
    float weightSum=0.0;
    for(int oy=-2;oy<=2;oy++){
        float wy=irisKernel5(oy);
        for(int ox=-2;ox<=2;ox++){
            float wx=irisKernel5(ox);
            float sampleValue=irisAt(center+ivec2(ox,oy));
            /* IRIS_26655_SOURCE_DOMAIN_EDGE_AWARE_DOWNSAMPLE
             * Values are log2 radiance, so the difference is directly in EV. A 0.65 EV
             * bilateral scale smooths ordinary illumination gradients while preventing a
             * bright source/material from bleeding through a strong radiometric boundary. */
            float d=(sampleValue-centerValue)/0.65;
            float rangeWeight=exp(-0.5*d*d);
            float w=wx*wy*rangeWeight;
            sum+=sampleValue*w;
            weightSum+=w;
        }
    }
    Output=sum/max(weightSum,1.0e-8);
}
