#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;

layout(r32f,binding=0) uniform highp writeonly image2D accumulatorNumerator;
layout(r32f,binding=1) uniform highp writeonly image2D accumulatorDenominator;
layout(r32f,binding=2) uniform highp writeonly image2D accumulatorFrameSupport;
uniform ivec2 accumulatorSize;

/*
 * IRIS_26489_V3_R32F_PERSISTENT_ACCUMULATOR_CLEAR
 *
 * GLES 3.1 requires non-r32 image variables to be readonly or writeonly. The persistent
 * burst accumulators need true read/write access in the accumulate pass, so each four-phase
 * vec4 cell is stored as four adjacent R32F texels. This clear pass owns that scalar storage.
 */
void main() {
    ivec2 p = ivec2(gl_GlobalInvocationID.xy);
    if (any(greaterThanEqual(p, accumulatorSize))) return;
    imageStore(accumulatorNumerator, p, vec4(0.0));
    imageStore(accumulatorDenominator, p, vec4(0.0));
    imageStore(accumulatorFrameSupport, p, vec4(0.0));
}
