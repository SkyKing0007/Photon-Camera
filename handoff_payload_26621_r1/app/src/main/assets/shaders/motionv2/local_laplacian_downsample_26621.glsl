precision highp float;
precision highp int;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
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
    float sum=0.0;
    for(int oy=-2;oy<=2;oy++){
        float wy=irisKernel5(oy);
        for(int ox=-2;ox<=2;ox++){
            float wx=irisKernel5(ox);
            sum+=irisAt(center+ivec2(ox,oy))*(wx*wy);
        }
    }
    Output=sum*(1.0/256.0);
}
