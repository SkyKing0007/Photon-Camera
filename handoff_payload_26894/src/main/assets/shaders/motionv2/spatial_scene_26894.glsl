precision highp float;
precision highp int;
precision mediump sampler2D;
uniform sampler2D InputBuffer;
uniform ivec2 iris26894SceneGridSize;
out vec2 Output;
float iris26894GuideAt(ivec2 pixel) {
    ivec2 sz=textureSize(InputBuffer,0);
    vec3 rgb=max(texelFetch(InputBuffer,clamp(pixel,ivec2(0),sz-ivec2(1)),0).rgb,vec3(0.0));
    float lum=dot(rgb,vec3(0.22897456,0.69173852,0.07928691));
    return max(lum,max(rgb.r,max(rgb.g,rgb.b)));
}
void main(){
    /* IRIS_26894_B_OFF_SPATIALLY_RESOLVED_ILLUMINATION: 4x4 stratified
     * source-domain samples per ~32x32 cell, no CPU/GPU readback or stalls.
     * R=regional mean, G=regional standard deviation. RGB/white/clipping
     * owners are immutable. Grid never changes exposure or temporal fusion.
     */
    ivec2 sz=textureSize(InputBuffer,0);
    vec2 grid=vec2(max(iris26894SceneGridSize,ivec2(1)));
    vec2 corner=(gl_FragCoord.xy-vec2(0.5))/grid*vec2(sz);
    vec2 span=vec2(sz)/grid;
    float sumY=0.0;float sumY2=0.0;
    for(int yy=0;yy<4;yy++){
        for(int xx=0;xx<4;xx++){
            vec2 q=corner+(vec2(float(xx),float(yy))+vec2(0.5))*(span*0.25);
            float guide=min(iris26894GuideAt(ivec2(q)),8.0);
            sumY+=guide;sumY2+=guide*guide;
        }
    }
    float avg=sumY*(1.0/16.0);
    float variance=max(sumY2*(1.0/16.0)-avg*avg,0.0);
    Output=vec2(avg,sqrt(variance));
}
