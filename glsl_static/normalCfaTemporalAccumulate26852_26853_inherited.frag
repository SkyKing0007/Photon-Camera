#version 300 es
precision highp float;
precision highp int;
precision highp usampler2D;
uniform highp usampler2D uRaw;
uniform sampler2D uFlow;
uniform sampler2D uCovariance;
uniform sampler2D uRejection;
uniform vec4 uFlowScaleOffset;
uniform ivec2 uRawSize;
uniform ivec2 uQuadSize;
uniform vec4 uFrameBorderPadded;
uniform int uUseFrameWeight;
uniform vec4 uPhaseGains;
uniform vec4 uPhaseBlackTerms;
uniform float uSourceWhiteNormalized;
uniform vec4 uCovRangeRg;
uniform vec2 uCovRangeB;
uniform int uRowFlickerEnabled;
uniform int uRowFlickerHarmonic;
uniform vec2 uRowFlickerAB;
uniform float uRowFlickerStrength;
uniform float uClipZoneClipStart26834;
layout(location = 0) out vec4 oPhaseSignal;
/* x=merge-valid shared temporal support; y=pre-headroom total support;
 * z=clip-zone numerator under the existing tunable headroom remap; w reserved. */
layout(location = 1) out vec4 oSharedSupport;
/* R/G1/G2/B validity is provenance inside the SAME shared temporal admission.
 * It can protect later SHORT/fusion decisions but can never choose frames per color. */
layout(location = 2) out vec4 oPhaseValidity;
/* IRIS_26853_LOCAL_TEMPORAL_NOISE_MOMENTS
 * Shared admission stays single-owner. x accumulates sum(w^2); y accumulates the
 * weighted square of the same-frame four-phase quad mean. These are local statistics
 * only: never frame-count authority, never color selection, never global denoise strength. */
layout(location = 3) out vec2 oTemporalStats26853;

vec2 mirrorUvs(vec2 uv) {
    if (uv.x <= uFrameBorderPadded.x) uv.x = 2.0 * uFrameBorderPadded.x - uv.x;
    if (uv.y <= uFrameBorderPadded.y) uv.y = 2.0 * uFrameBorderPadded.y - uv.y;
    if (uv.x > uFrameBorderPadded.z) uv.x = 2.0 * uFrameBorderPadded.z - uv.x;
    if (uv.y > uFrameBorderPadded.w) uv.y = 2.0 * uFrameBorderPadded.w - uv.y;
    return uv;
}
int phaseAt(ivec2 p) { return ((p.y & 1) << 1) + (p.x & 1); }
ivec2 phaseOffset(int phase) { return ivec2(phase & 1, phase >> 1); }
ivec2 clampPhaseLattice(ivec2 q, int phase) {
    ivec2 off = phaseOffset(phase);
    ivec2 maximum = max((uRawSize - ivec2(1) - off) / 2, ivec2(0));
    return clamp(q, ivec2(0), maximum);
}
ivec2 pixelForPhaseLattice(ivec2 q, int phase) {
    return clampPhaseLattice(q, phase) * 2 + phaseOffset(phase);
}
float normalizedRaw(ivec2 p) {
    p = clamp(p, ivec2(0), uRawSize - ivec2(1));
    int phase = phaseAt(p);
    return float(texelFetch(uRaw, p, 0).r) * uPhaseGains[phase] + uPhaseBlackTerms[phase];
}
float headroomAt(ivec2 p) {
    float whitePoint = max(uSourceWhiteNormalized, 1.0e-5);
    float start = whitePoint * 0.9925;
    return 1.0 - smoothstep(start, max(start + 1.0e-5, whitePoint), normalizedRaw(p));
}
float kernelWeight(vec2 d, vec3 c) {
    float kd = d.x*d.x*c.x + d.y*d.y*c.y + d.x*d.y*c.z*2.0;
    return exp2(-0.5 * kd) + 0.00005;
}
vec3 unpackCovariance(vec3 packedCovariance) {
    return vec3(
        packedCovariance.x * uCovRangeRg.y + uCovRangeRg.x,
        packedCovariance.y * uCovRangeRg.w + uCovRangeRg.z,
        packedCovariance.z * uCovRangeB.y + uCovRangeB.x);
}
float rowReliability(float rowUv) {
    if (uRowFlickerEnabled == 0 || uRowFlickerHarmonic <= 0 || uRowFlickerStrength <= 0.0) return 1.0;
    float phase = 6.283185307179586 * float(uRowFlickerHarmonic) * clamp(rowUv, 0.0, 1.0);
    float logModulation = uRowFlickerAB.x * cos(phase) + uRowFlickerAB.y * sin(phase);
    float amplitude = length(uRowFlickerAB);
    float darkMagnitude = max(-logModulation, 0.0);
    float darkBand = smoothstep(0.010, max(0.030, amplitude * 0.90), darkMagnitude);
    return mix(1.0, 0.08, clamp(darkBand * clamp(uRowFlickerStrength, 0.0, 1.0), 0.0, 1.0));
}
void samplePhase(vec2 sourceCenter, int phase, vec3 covariance,
                 out float value, out float headroom) {
    ivec2 off = phaseOffset(phase);
    vec2 lattice = 0.5 * (sourceCenter - (vec2(off) + vec2(0.5)));
    ivec2 nearest = ivec2(floor(lattice + vec2(0.5)));
    vec2 nearestDelta = lattice - vec2(nearest);
    if (max(abs(nearestDelta.x), abs(nearestDelta.y)) < 1.0e-5) {
        ivec2 p = pixelForPhaseLattice(nearest, phase);
        value = normalizedRaw(p);
        headroom = headroomAt(p);
        return;
    }
    ivec2 base = ivec2(floor(lattice));
    float sum = 0.0;
    float weight = 0.0;
    headroom = 1.0;
    for (int ly = 0; ly <= 1; ++ly) {
        for (int lx = 0; lx <= 1; ++lx) {
            ivec2 q = clampPhaseLattice(base + ivec2(lx, ly), phase);
            ivec2 p = pixelForPhaseLattice(q, phase);
            vec2 center = vec2(p) + vec2(0.5);
            float w = kernelWeight(center - sourceCenter, covariance);
            sum += normalizedRaw(p) * w;
            weight += w;
            headroom = min(headroom, headroomAt(p));
        }
    }
    value = sum / max(weight, 1.0e-8);
}
float quadRejection(ivec2 quadOrigin) {
    if (uUseFrameWeight == 0) return 1.0;
    ivec2 maxPixel = uRawSize - ivec2(1);
    vec2 invRaw = 1.0 / vec2(uRawSize);
    ivec2 p00 = clamp(quadOrigin, ivec2(0), maxPixel);
    ivec2 p10 = clamp(quadOrigin + ivec2(1,0), ivec2(0), maxPixel);
    ivec2 p01 = clamp(quadOrigin + ivec2(0,1), ivec2(0), maxPixel);
    ivec2 p11 = clamp(quadOrigin + ivec2(1,1), ivec2(0), maxPixel);
    float w00 = texture(uRejection, (vec2(p00)+vec2(0.5))*invRaw).r;
    float w10 = texture(uRejection, (vec2(p10)+vec2(0.5))*invRaw).r;
    float w01 = texture(uRejection, (vec2(p01)+vec2(0.5))*invRaw).r;
    float w11 = texture(uRejection, (vec2(p11)+vec2(0.5))*invRaw).r;
    return min(min(w00,w10),min(w01,w11));
}
void main() {
    ivec2 q = clamp(ivec2(gl_FragCoord.xy), ivec2(0), uQuadSize - ivec2(1));
    ivec2 quadOrigin = q * 2;
    vec2 rawSize = vec2(uRawSize);
    vec2 referenceUv = (vec2(quadOrigin) + vec2(1.0)) / rawSize;
    vec2 flowUv = referenceUv * uFlowScaleOffset.xy + uFlowScaleOffset.zw;
    vec2 sourceUv = mirrorUvs(referenceUv + texture(uFlow, flowUv).xy);
    vec2 translation = (sourceUv - referenceUv) * rawSize;
    vec3 covariance = unpackCovariance(texture(uCovariance, sourceUv).xyz);
    vec4 phaseSignal = vec4(0.0);
    vec4 phaseHeadroom = vec4(1.0);
    float sharedHeadroom = 1.0;
    for (int phase = 0; phase < 4; ++phase) {
        float v; float h;
        vec2 targetCenter = vec2(quadOrigin + phaseOffset(phase)) + vec2(0.5) + translation;
        samplePhase(targetCenter, phase, covariance, v, h);
        phaseSignal[phase] = v;
        phaseHeadroom[phase] = h;
        sharedHeadroom = min(sharedHeadroom, h);
    }
    float baseWeight = quadRejection(quadOrigin) * rowReliability(sourceUv.y);
    float validWeight = baseWeight * (uUseFrameWeight != 0
        ? sharedHeadroom : mix(0.001, 1.0, sharedHeadroom));
    float desiredWidth = max(1.0 - clamp(uClipZoneClipStart26834, 0.97, 0.999), 1.0e-4);
    float remapExponent = desiredWidth / 0.0075;
    float clipConfidence = pow(clamp(sharedHeadroom, 0.0, 1.0), remapExponent);
    float quadMean26853 = dot(phaseSignal, vec4(0.25));
    oPhaseSignal = phaseSignal * validWeight;
    oSharedSupport = vec4(validWeight, baseWeight, baseWeight * clipConfidence, 0.0);
    oPhaseValidity = phaseHeadroom * validWeight;
    oTemporalStats26853 = vec2(validWeight * validWeight,
        quadMean26853 * quadMean26853 * validWeight);
}
