#version 310 es
precision highp float;
precision highp int;
precision highp sampler2D;
precision highp isampler2D;
precision highp usampler2D;
uniform highp isampler2D uConverted;
uniform ivec2 uPlaneSize;
uniform int uGreenImbalanceRetention;
layout(location = 0) out highp ivec4 oBalanced;

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

int converted(int u, int v) { return planeAt(uConverted, uPlaneSize, u, v); }

void main() {
    ivec2 virtualSite = ivec2(gl_FragCoord.xy) - ivec2(PLANE_PADDING);
    int u = virtualSite.x;
    int v = virtualSite.y;
    int g = converted(u, v);
    if (((u + v) & 1) == 0) {
        oBalanced = ivec4(g, 0, 0, 0);
        return;
    }
    int total = 4 * g + converted(u - 1, v - 1) + converted(u + 1, v - 1) +
        converted(u - 1, v + 1) + converted(u + 1, v + 1);
    int blur = s16((total + 4) >> 3);
    int difference = s16(g - blur);
    int correction = s16(
        int(uint(difference * uGreenImbalanceRetention) + 0x8000u) >> 16
    );
    oBalanced = ivec4(s16(correction + blur), 0, 0, 0);
}
