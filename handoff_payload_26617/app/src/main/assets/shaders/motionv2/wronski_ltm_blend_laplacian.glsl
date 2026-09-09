precision highp float;
precision highp sampler2D;
uniform sampler2D ExposuresFine;
uniform sampler2D WeightsFine;
uniform sampler2D ExposuresCoarse;
uniform sampler2D AccumCoarse;
uniform sampler2D BroadWeights;
uniform vec2 FineSize;
uniform float useBroadWeightAuthority;
out float Output;
void main(){
    vec2 uv=gl_FragCoord.xy/FineSize;
    float accumSoFar=texture(AccumCoarse,uv).r;
    vec3 laplacians=texelFetch(ExposuresFine,ivec2(gl_FragCoord.xy),0).rgb-texture(ExposuresCoarse,uv).rgb;
    vec3 fineWeights=texelFetch(WeightsFine,ivec2(gl_FragCoord.xy),0).rgb;
    vec3 broadWeights=texture(BroadWeights,uv).rgb;
    /* IRIS_26617_STRUCTURE_STABLE_EXPOSURE_AUTHORITY
     * boostLocalContrast remains false. Wronski's mip-5 exposure decision owns broad local
     * illumination; mips 4..2 reuse that decision so fine structure cannot choose a different
     * synthetic exposure on opposite sides of an edge. Branch-specific fine detail is retained. */
    fineWeights/=dot(fineWeights,vec3(1.0))+0.00001;
    broadWeights/=dot(broadWeights,vec3(1.0))+0.00001;
    vec3 weights=mix(fineWeights,broadWeights,clamp(useBroadWeightAuthority,0.0,1.0));
    Output=accumSoFar+dot(laplacians*weights,vec3(1.0));
}
