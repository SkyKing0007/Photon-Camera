precision highp float;
precision highp sampler2D;
uniform sampler2D InputBuffer;
uniform float exposure;
uniform float highlightExposureScale;
uniform float shadowExposureScale;
out vec4 Output;

/* Exact Wronski exposure weights: sigma=5 => sigmaSq=25, normalized per source pixel before mips. */
vec3 RRTAndODTFit(vec3 v){
    vec3 a=v*(v+0.0245786)-0.000090537;
    vec3 b=v*(0.983729*v+0.4329510)+0.238081;
    return a/b;
}
vec3 ACESFilmicToneMapping(vec3 color){
    const mat3 ACESInputMat=mat3(
        vec3(0.59719,0.07600,0.02840),vec3(0.35458,0.90834,0.13383),vec3(0.04823,0.01566,0.83777));
    const mat3 ACESOutputMat=mat3(
        vec3(1.60475,-0.10208,-0.00327),vec3(-0.53108,1.10813,-0.07276),vec3(-0.07367,-0.00605,1.07602));
    color*=1.0/0.6;color=ACESInputMat*color;color=RRTAndODTFit(color);color=ACESOutputMat*color;
    return clamp(color,vec3(0.0),vec3(1.0));
}
vec3 irisP3ToLinearSrgb(vec3 c){
    return vec3(1.22494018*c.r-0.22494018*c.g,
                -0.04205695*c.r+1.04205695*c.g,
                -0.01963755*c.r-0.07863605*c.g+1.09827360*c.b);
}
float wronskiLightness(vec3 rgb){return sqrt(dot(clamp(ACESFilmicToneMapping(rgb),vec3(0.0),vec3(1.0)),vec3(0.1,0.7,0.2)));}
float qHalf(float v){return unpackHalf2x16(packHalf2x16(vec2(v,0.0))).x;}
vec3 qHalf3(vec3 v){return vec3(qHalf(v.r),qHalf(v.g),qHalf(v.b));}
vec3 level0At(ivec2 p,ivec2 sz){
    p=clamp(p,ivec2(0),sz-ivec2(1));
    vec3 src=irisP3ToLinearSrgb(texelFetch(InputBuffer,p,0).rgb)*exposure;
    vec3 cols=vec3(wronskiLightness(src*highlightExposureScale),wronskiLightness(src),wronskiLightness(src*shadowExposureScale));
    vec3 diff=cols-vec3(0.5);vec3 weights=exp(-0.5*diff*diff*25.0);
    weights/=dot(weights,vec3(1.0))+0.00001;
    return qHalf3(weights);
}
vec3 level1At(ivec2 p,ivec2 sz){
    ivec2 q=p*2;
    vec3 v=level0At(q,sz)+level0At(q+ivec2(1,0),sz)+level0At(q+ivec2(0,1),sz)+level0At(q+ivec2(1,1),sz);
    return qHalf3(v*0.25);
}
void main(){
    /* Exact demo storage order: normalized level0 weights -> HalfFloat, linear level1 average ->
     * HalfFloat, linear level2 average -> HalfFloat output. */
    ivec2 outP=ivec2(gl_FragCoord.xy);ivec2 sz=textureSize(InputBuffer,0);ivec2 q=outP*2;
    vec3 v=level1At(q,sz)+level1At(q+ivec2(1,0),sz)+level1At(q+ivec2(0,1),sz)+level1At(q+ivec2(1,1),sz);
    Output=vec4(v*0.25,1.0);
}
