#define LAYOUT //
LAYOUT
precision highp float;
precision highp int;
layout(std430, binding = 0) readonly buffer CfaBuf {
    float cfa[];
};
layout(std430, binding = 2) buffer GreenBuf {
    float green[];
};
layout(std430, binding = 4) readonly buffer VhBuf {
    float vh[];
};
layout(std430, binding = 5) readonly buffer LpfBuf {
    float lpf[];
};
uniform ivec2 bandSize;
uniform int bandOriginY;
uniform int cfaPattern;

int idxAt(ivec2 p) {
    p = clamp(p, ivec2(0), bandSize - ivec2(1));
    return p.y * bandSize.x + p.x;
}
float raw(ivec2 p) { return cfa[idxAt(p)]; }
float low(ivec2 p) { return lpf[idxAt(p)]; }
int phaseAt(ivec2 p) {
    ivec2 gp = ivec2(p.x, bandOriginY + p.y);
    return (gp.x & 1) | ((gp.y & 1) << 1);
}
int colorAt(ivec2 p) {
    int q = phaseAt(p);
    if (cfaPattern == 0) return q == 0 ? 0 : (q == 3 ? 2 : 1);
    if (cfaPattern == 1) return q == 1 ? 0 : (q == 2 ? 2 : 1);
    if (cfaPattern == 2) return q == 2 ? 0 : (q == 1 ? 2 : 1);
    return q == 3 ? 0 : (q == 0 ? 2 : 1);
}
void main() {
    ivec2 p = ivec2(gl_GlobalInvocationID.xy);
    if (any(greaterThanEqual(p, bandSize))) return;
    int i = idxAt(p);
    if (colorAt(p) == 1 || p.x < 5 || p.y < 5 || p.x + 5 >= bandSize.x || p.y + 5 >= bandSize.y) {
        if (colorAt(p) == 1) green[i] = raw(p);
        return;
    }
    const float e = 1.0e-5;
    float c = raw(p);
    float ng = e + abs(raw(p+ivec2(0,-1))-raw(p+ivec2(0,1)))
        + abs(c-raw(p+ivec2(0,-2))) + abs(raw(p+ivec2(0,-1))-raw(p+ivec2(0,-3)))
        + abs(raw(p+ivec2(0,-2))-raw(p+ivec2(0,-4)));
    float sg = e + abs(raw(p+ivec2(0,1))-raw(p+ivec2(0,-1)))
        + abs(c-raw(p+ivec2(0,2))) + abs(raw(p+ivec2(0,1))-raw(p+ivec2(0,3)))
        + abs(raw(p+ivec2(0,2))-raw(p+ivec2(0,4)));
    float wg = e + abs(raw(p+ivec2(-1,0))-raw(p+ivec2(1,0)))
        + abs(c-raw(p+ivec2(-2,0))) + abs(raw(p+ivec2(-1,0))-raw(p+ivec2(-3,0)))
        + abs(raw(p+ivec2(-2,0))-raw(p+ivec2(-4,0)));
    float eg = e + abs(raw(p+ivec2(1,0))-raw(p+ivec2(-1,0)))
        + abs(c-raw(p+ivec2(2,0))) + abs(raw(p+ivec2(1,0))-raw(p+ivec2(3,0)))
        + abs(raw(p+ivec2(2,0))-raw(p+ivec2(4,0)));
    float lc = low(p);
    float n = raw(p+ivec2(0,-1)) * (2.0*lc) / (e + lc + low(p+ivec2(0,-1)));
    float s = raw(p+ivec2(0,1)) * (2.0*lc) / (e + lc + low(p+ivec2(0,1)));
    float w = raw(p+ivec2(-1,0)) * (2.0*lc) / (e + lc + low(p+ivec2(-1,0)));
    float ee = raw(p+ivec2(1,0)) * (2.0*lc) / (e + lc + low(p+ivec2(1,0)));
    float v = (sg*n + ng*s) / (ng + sg);
    float h = (wg*ee + eg*w) / (eg + wg);
    green[i] = mix(v, h, clamp(vh[i], 0.0, 1.0));
}
