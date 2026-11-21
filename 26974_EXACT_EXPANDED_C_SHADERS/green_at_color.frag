#version 310 es
precision highp float;
precision highp int;
precision highp sampler2D;
precision highp isampler2D;
precision highp usampler2D;
uniform highp isampler2D uBalanced;
uniform ivec2 uPlaneSize;
layout(location = 0) out highp ivec4 oGreen;

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

// R/B sites hold the converted value, G sites the balanced green.
int at(int u, int v) { return planeAt(uBalanced, uPlaneSize, u, v); }

void main() {
    ivec2 virtualSite = ivec2(gl_FragCoord.xy) - ivec2(PLANE_PADDING);
    int u = virtualSite.x;
    int v = virtualSite.y;
    int c = at(u, v);
    if (((u + v) & 1) != 0) {
        oGreen = ivec4(c, 0, 0, 0);
        return;
    }
    int cL = at(u - 2, v);
    int cR = at(u + 2, v);
    int cU = at(u, v - 2);
    int cD = at(u, v + 2);
    int gl = at(u - 1, v);
    int gr = at(u + 1, v);
    int gu = at(u, v - 1);
    int gd = at(u, v + 1);
    int ul = at(u - 1, v - 1);
    int ur = at(u + 1, v - 1);
    int dl = at(u - 1, v + 1);
    int dr = at(u + 1, v + 1);

    int eH = srhadd(shadd(gl, gr), c);
    int eR = srhadd(shadd(c, cR), gr);
    int eL = srhadd(shadd(cL, c), gl);
    int eV = srhadd(shadd(gu, gd), c);
    int eD = srhadd(shadd(c, cD), gd);
    int eU = srhadd(shadd(cU, c), gu);

    Ig1 horizontal = makeIg1(sabd(eH, eR), sabd(eH, eL));
    int eHWeighted = blend1(horizontal, eR, eL);
    int gH = blend1(horizontal, gr, gl);
    Ig1 vertical = makeIg1(sabd(eV, eD), sabd(eV, eU));
    int eVWeighted = blend1(vertical, eD, eU);
    int gV = blend1(vertical, gd, gu);

    int cH = shadd(srhadd(gl, gr), c);
    int cV = shadd(srhadd(gu, gd), c);
    int eHUpDown = srhadd(
        shadd(srhadd(at(u - 1, v - 2), at(u + 1, v - 2)), cU),
        shadd(srhadd(at(u - 1, v + 2), at(u + 1, v + 2)), cD)
    );
    int eVLeftRight = srhadd(
        shadd(srhadd(at(u - 2, v - 1), at(u - 2, v + 1)), cL),
        shadd(srhadd(at(u + 2, v - 1), at(u + 2, v + 1)), cR)
    );
    int pl = shadd(srhadd(ul, dl), gl);
    int pr = shadd(srhadd(ur, dr), gr);
    int pu = shadd(srhadd(ul, ur), gu);
    int pd = shadd(srhadd(dl, dr), gd);
    // (|.| >> 2) * 9 is a wrapping 16-bit MUL then USHR #3; the sums are USRA mod 2^16.
    int costA = u16(
        (u16((sabd(cV, eVLeftRight) >> 2) * 9) >> 3) +
            (sabd(cV, srhadd(pl, pr)) >> 3) + (sabd(pl, pr) >> 1)
    );
    int costB = u16(
        (u16((sabd(cH, eHUpDown) >> 2) * 9) >> 3) +
            (sabd(cH, srhadd(pu, pd)) >> 3) + (sabd(pu, pd) >> 1)
    );

    int greenH = ratioCorrect(gH, eH, eHWeighted);
    int greenV = ratioCorrect(gV, eV, eVWeighted);
    oGreen = ivec4(ig2(costB, costA, greenV, greenH), 0, 0, 0);
}
