precision highp float;
precision highp sampler2D;
uniform sampler2D Exposures;
uniform sampler2D Weights;
out float Output;
void main(){
    ivec2 p=ivec2(gl_FragCoord.xy);
    vec3 weights=texelFetch(Weights,p,0).rgb;
    vec3 exposures=texelFetch(Exposures,p,0).rgb;
    weights/=dot(weights,vec3(1.0))+0.0001;
    Output=dot(exposures*weights,vec3(1.0));
}
