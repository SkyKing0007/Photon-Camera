precision highp float;
uniform sampler2D InputBuffer;
out float Output;
const vec3 IRIS_P3_LUMA=vec3(0.22897456,0.69173852,0.07928691);
void main(){
    ivec2 p=ivec2(gl_FragCoord.xy);
    vec3 rgb=clamp(texelFetch(InputBuffer,p,0).rgb,vec3(0.0),vec3(1.0));
    float y=max(dot(rgb,IRIS_P3_LUMA),exp2(-12.0));
    Output=clamp(log2(y),-12.0,0.0);
}
