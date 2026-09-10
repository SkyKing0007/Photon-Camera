precision highp float;
precision highp int;
precision mediump sampler2D;

uniform sampler2D InputPyramid;
out vec2 Output;

/* IRIS_26620_LOCAL_LAPLACIAN_GAUSSIAN_DOWNSAMPLE
 * Centered 5x5 binomial Gaussian reduction before every 2:1 pyramid step.
 * R/G remain source/global log-guide pairs at identical spatial phases. */
vec2 pairAt(ivec2 p){
    ivec2 sz=textureSize(InputPyramid,0);
    return texelFetch(InputPyramid,clamp(p,ivec2(0),sz-ivec2(1)),0).rg;
}

float kernel5(int o){
    int a=abs(o);
    if(a==0)return 6.0;
    if(a==1)return 4.0;
    return 1.0;
}

void main(){
    ivec2 q=ivec2(gl_FragCoord.xy);
    ivec2 center=q*2;
    vec2 sum=vec2(0.0);
    for(int oy=-2;oy<=2;oy++){
        float wy=kernel5(oy);
        for(int ox=-2;ox<=2;ox++){
            float wx=kernel5(ox);
            sum+=pairAt(center+ivec2(ox,oy))*(wx*wy);
        }
    }
    Output=sum*(1.0/256.0);
}
