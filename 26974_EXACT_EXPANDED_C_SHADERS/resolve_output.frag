#version 310 es
precision highp float;
precision highp int;
precision highp sampler2D;
precision highp isampler2D;
precision highp usampler2D;
uniform highp sampler2D uAccumulated;
uniform highp isampler2D uBalanced;
uniform highp isampler2D uGreen;
uniform ivec2 uImageSize;
uniform ivec2 uPlaneSize;
uniform ivec2 uRedSite;
uniform float uBlendBias;
uniform float uBlendScale;
uniform float uInverseQuantizationScale;
uniform vec3 uFinalGains;
// RGGB gains of the lens shading map; a 1x1 map of ones when the capture has none.
uniform highp sampler2D uLensShading;
layout(location = 0) out highp uvec4 oResolved;

const int PLANE_PADDING = 4;

int s16(int v) { return (v << 16) >> 16; }
int u16(int v) { return v & 0xffff; }
// findMSB never receives 0: Adreno lowers `x == 0u ? 32 : 31 - findMSB(x)` to a
// count-leading-zeros whose zero result is 0, folding the guard away (see
// docs/gles-driver-compatibility.md). x | 1 keeps the leading one of every non-zero x,
// and the zero case adds the missing bit position explicitly.
int clz16(int x) { return 15 - findMSB(x | 1) + (x == 0 ? 1 : 0); }
int clz32(uint x) { return 31 - findMSB(x | 1u) + (x == 0u ? 1 : 0); }

// SSHL .8h: the shift is the signed low byte of the lane; negative shifts are arithmetic.
int sshl16(int x, int lane) {
    int s = ((lane & 0xff) << 24) >> 24;
    if (s >= 0) return s >= 16 ? 0 : s16(x << s);
    if (s <= -16) return x < 0 ? -1 : 0;
    return x >> (-s);
}
int shadd(int a, int b) { return (a + b) >> 1; }
int srhadd(int a, int b) { return (a + b + 1) >> 1; }
int sabd(int a, int b) { return abs(a - b); }
int urhadd(int a, int b) { return (a + b + 1) >> 1; }
int sqadd(int a, int b) { return clamp(a + b, -32768, 32767); }
int sqsub(int a, int b) { return clamp(a - b, -32768, 32767); }

// Inverse-gradient pair blend. Candidate A has error dA, candidate B has error dB.
struct Ig1 {
    bool aIsNear;
    int shift;
};
Ig1 makeIg1(int dA, int dB) {
    int hA = dA >> 1;
    int hB = dB >> 1;
    int total = max(u16(hA + hB), 1);
    return Ig1(hB > hA, clz16(total) - clz16(min(hA, hB)));
}
int blend1(Ig1 g, int xA, int xB) {
    int nearValue = g.aIsNear ? xA : xB;
    int farValue = g.aIsNear ? xB : xA;
    return s16(nearValue + sshl16(s16(farValue - nearValue), g.shift));
}

// Inverse-squared-cost blend; X has cost cX and Y has cost cY.
int ig2(int cX, int cY, int x, int y) {
    uint sX = (uint(cX) * uint(cX)) >> 1;
    uint sY = (uint(cY) * uint(cY)) >> 1;
    bool xIsNear = sY > sX;
    int nearValue = xIsNear ? x : y;
    int farValue = xIsNear ? y : x;
    uint total = max(sX + sY, 1u);
    int shift = clamp(s16(clz32(total) - clz32(min(sX, sY))), -15, 15);
    return s16(nearValue + sshl16(s16(farValue - nearValue), shift));
}

// Bit below the leading one: the half-step fraction of log2(x).
int log2Fraction(int x) { return sshl16(x, clz16(u16(x)) - 14) & 1; }

// Log-domain ratio correction: xWeighted * g / gWeighted in half-step powers of two.
int ratioCorrect(int xWeighted, int g, int gWeighted) {
    int xp = max(xWeighted, 0);
    int m = max(xp, max(gWeighted, g));
    int l = s16(
        log2Fraction(xp) - 2 * clz16(u16(xp)) + 2 * clz16(u16(m)) - log2Fraction(m)
    );
    int t = sshl16(sqsub(g, gWeighted), max(s16(l >> 1), -15));
    int odd = (l & 1) != 0 ? t >> 1 : 0;
    return sqadd(xWeighted, s16(odd + t));
}

int planeAt(isampler2D plane, ivec2 planeSize, int u, int v) {
    ivec2 p = clamp(
        ivec2(u + PLANE_PADDING, v + PLANE_PADDING),
        ivec2(0),
        planeSize - ivec2(1)
    );
    return texelFetch(plane, p, 0).r;
}

// Converted value; only read at R/B sites, where pass 2 kept it.
int converted(int u, int v) { return planeAt(uBalanced, uPlaneSize, u, v); }
int green(int u, int v) { return planeAt(uGreen, uPlaneSize, u, v); }

// Chroma of colour `wantBlue ? B : R` at a site whose native colour differs.
int chroma(int u, int v, bool wantBlue) {
    int nativeOffset = wantBlue ? 1 : 0;
    bool sameRow = ((v - nativeOffset) & 1) == 0;
    bool sameColumn = ((u - nativeOffset) & 1) == 0;
    int gc = green(u, v);
    if (sameRow && !sameColumn) {
        Ig1 g = makeIg1(sabd(gc, green(u + 1, v)), sabd(gc, green(u - 1, v)));
        int xWeighted = blend1(g, converted(u + 1, v), converted(u - 1, v));
        int gWeighted = blend1(g, green(u + 1, v), green(u - 1, v));
        return ratioCorrect(xWeighted, gc, gWeighted);
    }
    if (!sameRow && sameColumn) {
        Ig1 g = makeIg1(sabd(gc, green(u, v + 1)), sabd(gc, green(u, v - 1)));
        int xWeighted = blend1(g, converted(u, v + 1), converted(u, v - 1));
        int gWeighted = blend1(g, green(u, v + 1), green(u, v - 1));
        return ratioCorrect(xWeighted, gc, gWeighted);
    }
    int center = converted(u, v);
    int topLeft = converted(u - 1, v - 1);
    int topRight = converted(u + 1, v - 1);
    int bottomLeft = converted(u - 1, v + 1);
    int bottomRight = converted(u + 1, v + 1);
    Ig1 g1 = makeIg1(sabd(gc, green(u + 1, v - 1)), sabd(gc, green(u - 1, v + 1)));
    int x1 = ratioCorrect(
        blend1(g1, topRight, bottomLeft),
        gc,
        blend1(g1, green(u + 1, v - 1), green(u - 1, v + 1))
    );
    Ig1 g2 = makeIg1(sabd(gc, green(u + 1, v + 1)), sabd(gc, green(u - 1, v - 1)));
    int x2 = ratioCorrect(
        blend1(g2, bottomRight, topLeft),
        gc,
        blend1(g2, green(u + 1, v + 1), green(u - 1, v - 1))
    );
    int cost2 = urhadd(sabd(center, topLeft), sabd(center, bottomRight));
    int cost1 = urhadd(sabd(center, bottomLeft), sabd(center, topRight));
    return ig2(cost2, cost1, x2, x1);
}

void main() {
    ivec2 site = ivec2(gl_FragCoord.xy);
    int u = site.x;
    int v = site.y;
    int cfaColor = (u & 1) + (v & 1);
    int demosaicedRed = cfaColor == 0 ? converted(u, v) : chroma(u, v, false);
    int demosaicedGreen = green(u, v);
    int demosaicedBlue = cfaColor == 2 ? converted(u, v) : chroma(u, v, true);
    vec3 demosaiced = vec3(demosaicedRed, demosaicedGreen, demosaicedBlue) *
        uInverseQuantizationScale;

    ivec2 source = clamp(site + uRedSite, ivec2(0), uImageSize - ivec2(1));
    vec4 color = texelFetch(uAccumulated, source, 0);
    float weight = clamp(uBlendBias + color.a * uBlendScale, 0.0, 1.0);
    vec4 shading = texture(uLensShading, (vec2(site) + 0.5) / vec2(uImageSize));
    vec3 gains = uFinalGains * vec3(shading.r, 0.5 * (shading.g + shading.b), shading.a);
    vec3 resolved = clamp(mix(color.rgb, demosaiced, weight) * gains, 0.0, 1.0);
    oResolved = uvec4(uvec3(round(resolved * 65535.0)), 65535u);
}
