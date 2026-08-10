#define LAYOUT //
LAYOUT
precision highp float;
precision highp sampler2D;
precision highp image2D;

uniform highp sampler2D flowTexture;

layout(rgba16f, binding = 0) uniform highp readonly image2D currentRgb;
layout(rgba16f, binding = 1) uniform highp readonly image2D currentSupport;
layout(rgba16f, binding = 2) uniform highp readonly image2D alterCfa;
layout(rgba16f, binding = 3) uniform highp writeonly image2D outRgb;
layout(rgba16f, binding = 4) uniform highp writeonly image2D outSupport;

uniform ivec2 rawSize;
uniform ivec2 rawHalf;
uniform int cfaPattern;
uniform float noiseS;
uniform float noiseO;
uniform float maximumSupport;
uniform float sensorClipLevel;
uniform vec3 sensorGains;

/*
 * IRIS_26426_TRUE_PER_OBSERVATION_NORMALIZED_CONVOLUTION
 *
 * This replaces the 26424/26425 "build one RGB candidate per frame, then
 * average RGB candidates" approximation.
 *
 * Each real CFA photosite is treated as a scalar observation:
 *   scalar RAW observation
 *       x structure-aware geometric kernel
 *       x alignment confidence
 *       x scalar RAW-domain robustness
 *       x saturation reliability
 *   -> per-channel numerator / denominator.
 *
 * No auxiliary frame ever becomes a completed RGB image before fusion.
 */

int componentIndex(ivec2 p) {
    return ((p.y & 1) << 1) | (p.x & 1);
}

int componentColor(int c) {
    if (cfaPattern == 0) {
        if (c == 0) return 0;
        if (c == 3) return 2;
        return 1;
    } else if (cfaPattern == 1) {
        if (c == 1) return 0;
        if (c == 2) return 2;
        return 1;
    } else if (cfaPattern == 2) {
        if (c == 2) return 0;
        if (c == 1) return 2;
        return 1;
    }
    if (c == 3) return 0;
    if (c == 0) return 2;
    return 1;
}

float physicalSample(ivec2 rawPos) {
    ivec2 p = clamp(rawPos,ivec2(0),rawSize-ivec2(1));
    vec4 v = imageLoad(alterCfa,p>>1);
    int c = componentIndex(p);
    if (c == 0) return v.r;
    if (c == 1) return v.g;
    if (c == 2) return v.b;
    return v.a;
}

float currentLuma(ivec2 p) {
    ivec2 q = clamp(p,ivec2(0),rawSize-ivec2(1));
    vec3 rgb = max(imageLoad(currentRgb,q).rgb,vec3(0.0));
    return dot(rgb,vec3(0.25,0.50,0.25));
}

void structureAt(ivec2 xy, out vec2 normal, out float edgeStrength) {
    float gx = currentLuma(xy+ivec2(1,0)) - currentLuma(xy-ivec2(1,0));
    float gy = currentLuma(xy+ivec2(0,1)) - currentLuma(xy-ivec2(0,1));
    vec2 g = vec2(gx,gy);
    float mag = length(g);
    float center = max(currentLuma(xy),0.02);
    edgeStrength = clamp(mag/(0.05+0.40*center),0.0,1.0);
    normal = mag > 1.0e-6 ? g/mag : vec2(1.0,0.0);
}

vec2 accumulateObservations(
        vec2 sourceCoord,
        int wantedColor,
        float prediction,
        vec2 normal,
        float edgeStrength,
        float alignmentConfidence) {
    ivec2 base = ivec2(floor(sourceCoord));
    vec2 tangent = vec2(-normal.y,normal.x);

    float sigmaAlong = mix(1.25,2.10,edgeStrength);
    float sigmaAcross = mix(1.25,0.44,edgeStrength);
    float invAlong2 = 1.0/max(sigmaAlong*sigmaAlong,0.04);
    float invAcross2 = 1.0/max(sigmaAcross*sigmaAcross,0.04);

    float numerator = 0.0;
    float denominator = 0.0;
    float clip = max(sensorClipLevel,1.0e-6);

    // Scalar prediction uncertainty in the canonical sensor/noise domain.
    float sigma = sqrt(max(max(prediction,0.0)*noiseS+noiseO,1.0e-8));
    float robustStart = mix(4.0,5.5,edgeStrength);
    float robustEnd = mix(9.0,12.0,edgeStrength);

    for (int oy=-3; oy<=3; oy++) {
        for (int ox=-3; ox<=3; ox++) {
            ivec2 p = base+ivec2(ox,oy);
            if (any(lessThan(p,ivec2(0))) || any(greaterThanEqual(p,rawSize))) continue;
            if (componentColor(componentIndex(p)) != wantedColor) continue;

            float value = physicalSample(p);
            vec2 d = (vec2(p)+vec2(0.5))-(sourceCoord+vec2(0.5));
            float along = dot(d,tangent);
            float across = dot(d,normal);
            float metric = along*along*invAlong2 + across*across*invAcross2;
            float spatial = exp(-0.5*metric);

            // No forced 4-8% floor: clipped samples have zero chromatic authority.
            float saturation = 1.0-smoothstep(0.930*clip,0.985*clip,value);

            // Robustness is applied to the SCALAR RAW observation, not to an
            // already-demosaiced RGB candidate.
            float z = abs(value-prediction)/max(sigma,1.0e-5);
            float robust = 1.0-smoothstep(robustStart,robustEnd,z);

            float w = spatial * alignmentConfidence * saturation * robust;
            numerator += value*w;
            denominator += w;
        }
    }
    return vec2(numerator,denominator);
}

void main() {
    ivec2 xy = ivec2(gl_GlobalInvocationID.xy);
    if (any(greaterThanEqual(xy,rawSize))) return;

    vec3 cur = max(imageLoad(currentRgb,xy).rgb,vec3(0.0));
    vec3 oldSupport = max(imageLoad(currentSupport,xy).rgb,vec3(1.0e-4));

    // MotionV2Alignment publishes flow in packed-CFA pixels.
    vec2 uv = (vec2(xy)+vec2(0.5))/vec2(max(rawSize,ivec2(1)));
    vec4 flow = texture(flowTexture,uv);
    vec2 rawFlow = flow.xy*2.0;
    float alignmentConfidence = clamp(flow.z,0.0,1.0);
    vec2 sourceCoord = vec2(xy)+rawFlow;

    vec2 normal;
    float edgeStrength;
    structureAt(xy,normal,edgeStrength);

    vec2 rObs = accumulateObservations(
            sourceCoord,0,cur.r,normal,edgeStrength,alignmentConfidence);
    vec2 gObs = accumulateObservations(
            sourceCoord,1,cur.g,normal,edgeStrength,alignmentConfidence);
    vec2 bObs = accumulateObservations(
            sourceCoord,2,cur.b,normal,edgeStrength,alignmentConfidence);

    vec3 obsNumerator = vec3(rObs.x,gObs.x,bObs.x);
    vec3 obsWeight = vec3(rObs.y,gObs.y,bObs.y);

    // currentRgb * currentSupport is the running numerator. This is
    // mathematically equivalent to normalizing only after all frames while
    // avoiding another three full-resolution sum textures.
    vec3 numerator = cur*oldSupport + obsNumerator;
    vec3 newSupport = min(vec3(maximumSupport*8.0),oldSupport+obsWeight);
    vec3 merged = numerator/max(newSupport,vec3(1.0e-5));

    imageStore(outRgb,xy,vec4(max(merged,vec3(0.0)),1.0));
    imageStore(outSupport,xy,vec4(newSupport,1.0));
}
