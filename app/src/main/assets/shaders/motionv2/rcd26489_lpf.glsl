#define LAYOUT //
LAYOUT
precision highp float;
precision highp int;
layout(std430, binding = 0) readonly buffer CfaBuf {
    float cfa[];
};
layout(std430, binding = 5) buffer LpfBuf {
    float lpf[];
};
uniform ivec2 bandSize;
int idxAt(ivec2 p) {
    p = clamp(p, ivec2(0), bandSize - ivec2(1));
    return p.y * bandSize.x + p.x;
}
float raw(ivec2 p) { return cfa[idxAt(p)]; }
void main() {
    ivec2 p = ivec2(gl_GlobalInvocationID.xy);
    if (any(greaterThanEqual(p, bandSize))) return;
    float v = raw(p)
        + 0.5 * (raw(p + ivec2(-1,0)) + raw(p + ivec2(1,0))
               + raw(p + ivec2(0,-1)) + raw(p + ivec2(0,1)))
        + 0.25 * (raw(p + ivec2(-1,-1)) + raw(p + ivec2(1,-1))
                + raw(p + ivec2(-1,1)) + raw(p + ivec2(1,1)));
    lpf[idxAt(p)] = v;
}
