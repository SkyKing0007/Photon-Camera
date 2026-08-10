#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;

layout(rgba16f, binding = 0) uniform highp readonly image2D referenceTexture;
layout(rgba16f, binding = 1) uniform highp writeonly image2D outTexture;
layout(r32f, binding = 2) uniform highp writeonly image2D outSupport;

/* IRIS_26413_V2_REFERENCE_SUPPORT_INITIALIZATION */
void main() {
    ivec2 xy = ivec2(gl_GlobalInvocationID.xy);
    vec4 referenceValue = imageLoad(referenceTexture, xy);
    imageStore(outTexture, xy, referenceValue);
    imageStore(outSupport, xy, vec4(1.0));
}