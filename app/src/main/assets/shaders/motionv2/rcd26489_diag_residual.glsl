#define LAYOUT //
LAYOUT
precision highp float;
precision highp int;
layout(std430, binding = 0) readonly buffer CfaBuf {
    float cfa[];
};
layout(std430, binding = 6) buffer PBuf {
    float pdiff[];
};
layout(std430, binding = 7) buffer QBuf {
    float qdiff[];
};
uniform ivec2 bandSize;
int idxAt(ivec2 p) {
    p = clamp(p, ivec2(0), bandSize - ivec2(1));
    return p.y * bandSize.x + p.x;
}
float raw(ivec2 p) { return cfa[idxAt(p)]; }
float sq(float v) { return v*v; }
void main() {
    ivec2 p = ivec2(gl_GlobalInvocationID.xy);
    if (any(greaterThanEqual(p, bandSize))) return;
    int i = idxAt(p);
    if (p.x < 4 || p.y < 4 || p.x + 4 >= bandSize.x || p.y + 4 >= bandSize.y) {
        pdiff[i] = qdiff[i] = 1.0e-10;
        return;
    }
    float a = raw(p+ivec2(-3,-3)) - raw(p+ivec2(-1,-1)) - raw(p+ivec2(1,1)) + raw(p+ivec2(3,3))
        - 3.0*(raw(p+ivec2(-2,-2))+raw(p+ivec2(2,2))) + 6.0*raw(p);
    float b = raw(p+ivec2(3,-3)) - raw(p+ivec2(1,-1)) - raw(p+ivec2(-1,1)) + raw(p+ivec2(-3,3))
        - 3.0*(raw(p+ivec2(2,-2))+raw(p+ivec2(-2,2))) + 6.0*raw(p);
    pdiff[i] = max(sq(a), 1.0e-10);
    qdiff[i] = max(sq(b), 1.0e-10);
}
