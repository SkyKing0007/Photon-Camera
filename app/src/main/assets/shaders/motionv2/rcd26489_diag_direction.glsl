#define LAYOUT //
LAYOUT
precision highp float;
precision highp int;
layout(std430, binding = 6) readonly buffer PBuf {
    float pdiff[];
};
layout(std430, binding = 7) readonly buffer QBuf {
    float qdiff[];
};
layout(std430, binding = 8) buffer PqBuf {
    float pq[];
};
uniform ivec2 bandSize;
int idxAt(ivec2 p) {
    p = clamp(p, ivec2(0), bandSize - ivec2(1));
    return p.y * bandSize.x + p.x;
}
float pv(ivec2 p) { return pdiff[idxAt(p)]; }
float qv(ivec2 p) { return qdiff[idxAt(p)]; }
void main() {
    ivec2 p = ivec2(gl_GlobalInvocationID.xy);
    if (any(greaterThanEqual(p, bandSize))) return;
    float ps = pv(p+ivec2(-1,-1)) + pv(p) + pv(p+ivec2(1,1));
    float qs = qv(p+ivec2(1,-1)) + qv(p) + qv(p+ivec2(-1,1));
    ps=max(ps,1.0e-10); qs=max(qs,1.0e-10);
    pq[idxAt(p)] = ps/(ps+qs);
}
