#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;

layout(rgba16f, binding = 0) uniform highp readonly image2D currentRgb;
layout(rgba16f, binding = 1) uniform highp readonly image2D currentFrameSupport;
layout(rgba16f, binding = 2) uniform highp writeonly image2D outRgb;

/*
 * IRIS_26455_RGB_IDENTITY_FRAME_SUPPORT_FINALIZER
 * RGB identity only. No demosaic. No chroma filtering. No luma filtering.
 * Alpha receives local true frame-equivalent support.
 */
void main() {
    ivec2 xy = ivec2(gl_GlobalInvocationID.xy);
    ivec2 sz = imageSize(outRgb);
    if (any(greaterThanEqual(xy, sz))) return;

    vec4 rgb = imageLoad(currentRgb, xy);
    float frameSupport = max(imageLoad(currentFrameSupport, xy).r, 1.0);
    imageStore(outRgb, xy, vec4(rgb.rgb, frameSupport));
}