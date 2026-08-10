#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;

layout(rgba16f, binding = 0) uniform highp readonly image2D referenceCfa;
layout(rgba16f, binding = 1) uniform highp writeonly image2D outRgb;
layout(rgba16f, binding = 2) uniform highp writeonly image2D outSupport;

uniform ivec2 rawSize;
uniform int cfaPattern;
uniform float sensorClipLevel;
uniform vec3 sensorGains;

/*
 * IRIS_26426_TRUE_NORMALIZED_CONVOLUTION_INIT
 *
 * The reference frame initializes a native-resolution camera-RGB estimate and
 * per-channel support from REAL CFA observations. No named demosaic stage and
 * no completed RGB candidate from an auxiliary frame exists.
 *
 * Structure-aware geometry:
 *   - estimate a local edge direction from real green CFA observations;
 *   - elongate the kernel along an edge;
 *   - contract it across the edge.
 *
 * Saturated photosites carry zero chromatic authority. If a channel has no
 * trustworthy local photosite, use a sensor-neutral green-derived fallback.
 */

int componentIndex(ivec2 p) {
    return ((p.y & 1) << 1) | (p.x & 1);
}

int componentColor(int c) {
    if (cfaPattern == 0) {          // RGGB
        if (c == 0) return 0;
        if (c == 3) return 2;
        return 1;
    } else if (cfaPattern == 1) {   // GRBG
        if (c == 1) return 0;
        if (c == 2) return 2;
        return 1;
    } else if (cfaPattern == 2) {   // GBRG
        if (c == 2) return 0;
        if (c == 1) return 2;
        return 1;
    }                               // BGGR
    if (c == 3) return 0;
    if (c == 0) return 2;
    return 1;
}

float physicalSample(ivec2 rawPos) {
    ivec2 p = clamp(rawPos, ivec2(0), rawSize - ivec2(1));
    vec4 v = imageLoad(referenceCfa, p >> 1);
    int c = componentIndex(p);
    if (c == 0) return v.r;
    if (c == 1) return v.g;
    if (c == 2) return v.b;
    return v.a;
}

float greenNear(ivec2 center) {
    float sum = 0.0;
    float wsum = 0.0;
    for (int oy=-2; oy<=2; oy++) {
        for (int ox=-2; ox<=2; ox++) {
            ivec2 p = center + ivec2(ox,oy);
            if (any(lessThan(p,ivec2(0))) || any(greaterThanEqual(p,rawSize))) continue;
            if (componentColor(componentIndex(p)) != 1) continue;
            float d2 = float(ox*ox + oy*oy);
            float w = 1.0 / (0.5 + d2);
            sum += physicalSample(p) * w;
            wsum += w;
        }
    }
    return wsum > 1.0e-6 ? sum/wsum : 0.0;
}

void structureAt(ivec2 xy, out vec2 normal, out float edgeStrength) {
    float gx = greenNear(xy + ivec2(2,0)) - greenNear(xy - ivec2(2,0));
    float gy = greenNear(xy + ivec2(0,2)) - greenNear(xy - ivec2(0,2));
    vec2 g = vec2(gx,gy);
    float mag = length(g);
    float center = max(greenNear(xy), 0.02);
    edgeStrength = clamp(mag / (0.08 + 0.45*center), 0.0, 1.0);
    normal = mag > 1.0e-6 ? g/mag : vec2(1.0,0.0);
}

vec2 accumulateChannel(
        vec2 target,
        int wantedColor,
        vec2 normal,
        float edgeStrength) {
    ivec2 base = ivec2(floor(target));
    vec2 tangent = vec2(-normal.y, normal.x);

    float sigmaAlong = mix(1.20, 2.00, edgeStrength);
    float sigmaAcross = mix(1.20, 0.48, edgeStrength);
    float invAlong2 = 1.0 / max(sigmaAlong*sigmaAlong, 0.04);
    float invAcross2 = 1.0 / max(sigmaAcross*sigmaAcross, 0.04);

    float sum = 0.0;
    float weight = 0.0;
    float clip = max(sensorClipLevel, 1.0e-6);

    for (int oy=-3; oy<=3; oy++) {
        for (int ox=-3; ox<=3; ox++) {
            ivec2 p = base + ivec2(ox,oy);
            if (any(lessThan(p,ivec2(0))) || any(greaterThanEqual(p,rawSize))) continue;
            if (componentColor(componentIndex(p)) != wantedColor) continue;

            float value = physicalSample(p);
            vec2 d = (vec2(p)+vec2(0.5)) - (target+vec2(0.5));
            float along = dot(d,tangent);
            float across = dot(d,normal);
            float metric = along*along*invAlong2 + across*across*invAcross2;
            float spatial = exp(-0.5*metric);

            // Once a CFA channel clips, it is no longer valid chromatic evidence.
            float saturation = 1.0 - smoothstep(0.930*clip, 0.985*clip, value);
            float w = spatial * saturation;

            sum += value*w;
            weight += w;
        }
    }
    return vec2(sum,weight);
}

float neutralFromGreen(float green, int wantedColor) {
    vec3 gains = max(sensorGains, vec3(1.0e-6));
    float greenGain = gains.g;
    if (wantedColor == 0) return green * greenGain / gains.r;
    if (wantedColor == 2) return green * greenGain / gains.b;
    return green;
}

void main() {
    ivec2 xy = ivec2(gl_GlobalInvocationID.xy);
    if (any(greaterThanEqual(xy,rawSize))) return;

    vec2 normal;
    float edgeStrength;
    structureAt(xy,normal,edgeStrength);

    vec2 gAcc = accumulateChannel(vec2(xy),1,normal,edgeStrength);
    float g = gAcc.y > 1.0e-5 ? gAcc.x/gAcc.y : greenNear(xy);

    vec2 rAcc = accumulateChannel(vec2(xy),0,normal,edgeStrength);
    vec2 bAcc = accumulateChannel(vec2(xy),2,normal,edgeStrength);

    float r = rAcc.y > 1.0e-5 ? rAcc.x/rAcc.y : neutralFromGreen(g,0);
    float b = bAcc.y > 1.0e-5 ? bAcc.x/bAcc.y : neutralFromGreen(g,2);

    // Support is true accumulated kernel weight, independently per channel.
    vec3 support = vec3(rAcc.y, gAcc.y, bAcc.y);
    imageStore(outRgb,xy,vec4(max(vec3(r,g,b),vec3(0.0)),1.0));
    imageStore(outSupport,xy,vec4(max(support,vec3(1.0e-4)),1.0));
}
