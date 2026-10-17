#version 300 es
precision highp float;
precision highp int;
precision highp usampler2D;
uniform highp usampler2D uResolvedR;
uniform highp usampler2D uResolvedG;
uniform highp usampler2D uResolvedB;
uniform sampler2D uLensShading;
uniform ivec2 uOutputSize;
uniform int uUseLensShading;
uniform vec3 uFinalBlackLevel;
uniform float uDemosaicWhiteLevel;
uniform float uOutputExposureScale;

vec3 transformOutput(ivec2 p) {
    uvec3 encoded = uvec3(
        texelFetch(uResolvedR, p, 0).r,
        texelFetch(uResolvedG, p, 0).r,
        texelFetch(uResolvedB, p, 0).r
    );
    // ResolveSabre emits camera RGB in its RAW14 domain and deliberately retains the
    // per-channel final black level. Convert that native result to the black-free,
    // normalized camera domain expected by Photon's linear-RGB pipeline.
    vec3 resolved = max(vec3(encoded) - uFinalBlackLevel, vec3(0.0)) /
        max(vec3(uDemosaicWhiteLevel) - uFinalBlackLevel, vec3(1.0));
    if (uUseLensShading != 0) {
        vec2 uv = (vec2(p) + vec2(0.5)) / vec2(uOutputSize);
        vec4 shading = texture(uLensShading, uv);
        resolved *= vec3(shading.r, 0.5 * (shading.g + shading.b), shading.a);
    }
    return max(
        resolved * uOutputExposureScale,
        vec3(0.0)
    );
}
layout(location = 0) out highp uvec4 oResolved;
float max3(vec3 v) { return max(v.r, max(v.g, v.b)); }
void main() {
    ivec2 p = ivec2(gl_FragCoord.xy);
    vec3 physical = max(transformOutput(p), vec3(0.0));
    float magnitude = max(max3(physical), 1.0);
    vec3 directionDomain = clamp(physical / magnitude, 0.0, 1.0);
    oResolved = uvec4(uvec3(round(directionDomain * 65535.0)), 65535u);
}
