#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D InputGuide;
layout(r32f,binding=0) uniform highp writeonly image2D OutputGuide;
uniform int factor;
uniform int direction;

/*
 * IRIS_26473_IPOL_FACTOR_DEPENDENT_GAUSSIAN_PYRAMID
 * Public cuda_downsample(): sigma=factor*0.5, radius=round(4*sigma).
 */
float sampleCircular(ivec2 p){
    ivec2 s=textureSize(InputGuide,0);
    ivec2 q=ivec2((p.x%s.x+s.x)%s.x,(p.y%s.y+s.y)%s.y);
    return texelFetch(InputGuide,q,0).r;
}
void main(){
    ivec2 p=ivec2(gl_GlobalInvocationID.xy);
    ivec2 os=imageSize(OutputGuide);
    if(any(greaterThanEqual(p,os))) return;

    int f=max(factor,1);
    float sigma=max(0.5*float(f),0.5);
    int radius=min(8,int(floor(4.0*sigma+0.5)));
    ivec2 center=direction==0?p:p*f;

    float sum=0.0,ws=0.0;
    for(int i=-8;i<=8;i++){
        if(abs(i)>radius) continue;
        float w=exp(-float(i*i)/(2.0*sigma*sigma));
        ivec2 q=center+(direction==0?ivec2(i,0):ivec2(0,i));
        sum+=w*sampleCircular(q);
        ws+=w;
    }
    imageStore(OutputGuide,p,vec4(sum/max(ws,1.0e-8),0.0,0.0,0.0));
}
