precision highp float;
precision highp sampler2D;
uniform sampler2D ExposuresFine;
uniform sampler2D WeightsFine;
uniform sampler2D ExposuresCoarse;
uniform sampler2D AccumCoarse;
uniform vec2 FineSize;
out float Output;
void main(){
    vec2 uv=gl_FragCoord.xy/FineSize;
    float accumSoFar=texture(AccumCoarse,uv).r;
    vec3 laplacians=texelFetch(ExposuresFine,ivec2(gl_FragCoord.xy),0).rgb-texture(ExposuresCoarse,uv).rgb;
    vec3 weights=texelFetch(WeightsFine,ivec2(gl_FragCoord.xy),0).rgb;
    /* Exact linked-demo default: boostLocalContrast=false, so no abs(laplacian) reweighting. */
    weights/=dot(weights,vec3(1.0))+0.00001;
    Output=accumSoFar+dot(laplacians*weights,vec3(1.0));
}
