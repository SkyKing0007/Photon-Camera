#version 310 es
#line 1
precision highp float;
precision highp int;
precision mediump sampler2D;
uniform sampler2D ClassMask;
uniform sampler2D PrevConnected;
uniform int iris26799Iteration;
/* IRIS_26816_TELEMETRY_SSBO_RETIRED */
out float Output;

/* IRIS_26822_CONNECTED_FLOOD_RETIRED_PASS_THROUGH
 * Keep the inherited 26821 host allocation/pass sequence byte-contract compatible, but do not
 * propagate confidence spatially. Each of the eight inherited ping-pong passes copies the original
 * continuous classifier evidence unchanged. PrevConnected/iteration remain referenced so the
 * existing host bindings stay valid without a Java/GPU-lifetime redesign in this localized build.
 */
float fetchMask(sampler2D tex,ivec2 p){
    ivec2 sz=textureSize(tex,0);
    p=clamp(p,ivec2(0),sz-ivec2(1));
    return texelFetch(tex,p,0).r;
}
void main(){
    ivec2 p=ivec2(gl_FragCoord.xy);
    float confidence=fetchMask(ClassMask,p);
    /* Runtime iterations are 0..7. The impossible negative branch deliberately retains the
     * inherited PrevConnected binding without granting it any propagation authority. */
    if(iris26799Iteration<0){
        confidence=fetchMask(PrevConnected,p);
    }
    Output=clamp(confidence,0.0,1.0);
}
