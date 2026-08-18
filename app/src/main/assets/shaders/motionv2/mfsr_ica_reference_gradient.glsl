#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D ReferenceGuide;
layout(rgba32f,binding=0) uniform highp writeonly image2D OutputGradient;
uniform ivec2 levelSize;

/*
 * IRIS_26475_IPOL_ICA_REFERENCE_GRADIENT_PREP_ONCE
 * IRIS_26476_ADRENO_RGBA32F_GRADIENT_CARRIER_RG_ONLY
 * Same centered finite-difference gradient used by 26473 ICA, but computed
 * once for the immutable reference instead of once per auxiliary/iteration.
 */
float refCircular(ivec2 p) {
    ivec2 q=ivec2((p.x%levelSize.x+levelSize.x)%levelSize.x,
                  (p.y%levelSize.y+levelSize.y)%levelSize.y);
    return texelFetch(ReferenceGuide,q,0).r;
}
void main(){
    ivec2 p=ivec2(gl_GlobalInvocationID.xy);
    if(any(greaterThanEqual(p,levelSize))) return;
    vec2 g=vec2(
        refCircular(p+ivec2(1,0))-refCircular(p-ivec2(1,0)),
        refCircular(p+ivec2(0,1))-refCircular(p-ivec2(0,1)));
    imageStore(OutputGradient,p,vec4(g,0.0,0.0));
}

