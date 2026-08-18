#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
precision highp usampler2D;
uniform highp usampler2D referenceGray;
uniform highp sampler2D inputRejection;
layout(r32f,binding=0) uniform highp writeonly image2D outLuma;
layout(r32f,binding=1) uniform highp writeonly image2D outRejection;
uniform ivec2 inputSize;
uniform ivec2 outputSize;

float lumaLinear(vec2 coordinate) {
    vec2 shifted = coordinate - vec2(0.5);
    ivec2 p0 = ivec2(floor(shifted));
    vec2 fraction = fract(shifted);
    ivec2 maximum = inputSize - ivec2(1);
    float v00 = float(texelFetch(referenceGray, clamp(p0, ivec2(0), maximum), 0).r);
    float v10 = float(texelFetch(referenceGray, clamp(p0 + ivec2(1, 0), ivec2(0), maximum), 0).r);
    float v01 = float(texelFetch(referenceGray, clamp(p0 + ivec2(0, 1), ivec2(0), maximum), 0).r);
    float v11 = float(texelFetch(referenceGray, clamp(p0 + ivec2(1), ivec2(0), maximum), 0).r);
    return mix(mix(v00, v10, fraction.x), mix(v01, v11, fraction.x), fraction.y);
}

float rejectionLinear(vec2 coordinate) {
    vec2 shifted = coordinate - vec2(0.5);
    ivec2 p0 = ivec2(floor(shifted));
    vec2 fraction = fract(shifted);
    ivec2 maximum = inputSize - ivec2(1);
    float v00 = texelFetch(inputRejection, clamp(p0, ivec2(0), maximum), 0).r;
    float v10 = texelFetch(inputRejection, clamp(p0 + ivec2(1, 0), ivec2(0), maximum), 0).r;
    float v01 = texelFetch(inputRejection, clamp(p0 + ivec2(0, 1), ivec2(0), maximum), 0).r;
    float v11 = texelFetch(inputRejection, clamp(p0 + ivec2(1), ivec2(0), maximum), 0).r;
    return mix(mix(v00, v10, fraction.x), mix(v01, v11, fraction.x), fraction.y);
}

/* IRIS_26488_BJZHOU_REJECTION_DOWNSAMPLE_NATIVE_GRAY_EXACT */
void main() {
    ivec2 p = ivec2(gl_GlobalInvocationID.xy);
    if (any(greaterThanEqual(p, outputSize))) return;
    vec2 center = 4.0 * vec2(p) + vec2(2.0);
    center = clamp(center, vec2(2.0), vec2(inputSize) - vec2(2.0));
    float luma = 0.0;
    float rejection = 0.0;
    for (int y = -1; y <= 1; y += 2) {
        for (int x = -1; x <= 1; x += 2) {
            vec2 coordinate = center + vec2(x, y);
            luma += lumaLinear(coordinate);
            rejection += rejectionLinear(coordinate);
        }
    }
    imageStore(outLuma, p, vec4(0.25 * luma / 16383.0));
    imageStore(outRejection, p, vec4(0.25 * rejection));
}
