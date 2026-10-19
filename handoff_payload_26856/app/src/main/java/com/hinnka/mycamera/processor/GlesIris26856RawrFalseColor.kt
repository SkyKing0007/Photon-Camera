package com.hinnka.mycamera.processor

/**
 * IRIS_26856_RAWR_TWO_PASS_FALSE_COLOR_SOURCE.
 *
 * Direct GLES 3.0 fragment-stage adaptation of RAWR's pinned 2026-10-18
 * `native/false_color_correction/shaders/fcc_chroma_median.comp` and
 * `fcc_reconstruct.comp` (RAWR commit ce767e80bfce2e1641abf7dad6b1bf504d844fd9).
 * RAWR in turn pins RawTherapee commit 498f623784e33fd9a7077fcd8937fe0734033366.
 * GPL-3.0-or-later; original provenance/notice must be retained upon shipping.
 *
 * One FCC STEP consists of these TWO shader invocations:
 *    linear RGB -> RG32F median YIQ chroma -> linear RGB reconstruction.
 * Apply the step twice, serially, after defringe and before tone/color output.
 * This is NOT a demosaicer and MUST NOT run through legacy VGN chroma-restoration.
 * GLSL shader compilation, Vulkan/AMaZE integration, exact numerical parity,
 * GLES full-precision intermediate and device performance remain UNTESTED.
 */
internal object GlesIris26856RawrFalseColor {
    const val owner = "IRIS_26856_RAWR_TWO_PASS_FALSE_COLOR_SOURCE"

    val medianChroma = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uRgb;
        uniform ivec2 uSize;
        uniform int uNormalizedChroma;
        layout(location=0) out vec2 oIQ;

        vec2 toIQ(vec3 c) {
            return vec2(0.596*c.r-0.275*c.g-0.321*c.b,
                        0.212*c.r-0.523*c.g+0.311*c.b);
        }
        vec2 iqAt(int x, int y) {
            vec3 c = texelFetch(uRgb, ivec2(x, y), 0).rgb;
            vec2 iq = toIQ(c);
            if (uNormalizedChroma != 0)
                iq /= max(dot(c, vec3(0.299, 0.587, 0.114)), 1.0e-4);
            return iq;
        }
        void cswap(inout vec2 a, inout vec2 b) {
            vec2 lo=min(a,b), hi=max(a,b);
            a=lo; b=hi;
        }
        void middle4of6(vec2 a0, vec2 a1, vec2 a2, vec2 a3,
                        vec2 a4, vec2 a5, out vec2 r0, out vec2 r1,
                        out vec2 r2, out vec2 r3) {
            r0=min(a1,a2);
            r1=max(a1,a2);
            vec2 left=min(a0,r1);
            r1=max(a0,r1);
            vec2 tmp=min(left,r0);
            r0=max(left,r0);
            left=tmp;
            r3=min(a4,a5);
            vec2 right=max(a4,a5);
            r2=min(a3,right);
            right=max(a3,right);
            tmp=min(r2,r3);
            r3=max(r2,r3);
            r2=max(left,tmp);
            r1=min(r1,right);
        }
        vec2 median7(vec2 a, vec2 b, vec2 c, vec2 d,
                     vec2 e, vec2 f, vec2 g) {
            vec2 v0=a,v1=b,v2=c,v3=d,v4=e,v5=f,v6=g;
            cswap(v0,v5); cswap(v0,v3); cswap(v1,v6); cswap(v2,v4);
            cswap(v0,v1); cswap(v3,v5); cswap(v2,v6); cswap(v2,v3);
            cswap(v3,v6); cswap(v4,v5); cswap(v1,v4); cswap(v1,v3);
            cswap(v3,v4);
            return v3;
        }
        void main() {
            ivec2 p=ivec2(gl_FragCoord.xy);
            int W=uSize.x, H=uSize.y;
            int x=p.x,y=p.y;
            if (y==0||y==H-1||x==0||x>=W-2) {
                oIQ=iqAt(x,y);
                return;
            }
            vec2 upL=iqAt(x-1,y-1),midL=iqAt(x-1,y),downL=iqAt(x-1,y+1);
            vec2 upC=iqAt(x,y-1),midC=iqAt(x,y),downC=iqAt(x,y+1);
            vec2 upR=iqAt(x+1,y-1),midR=iqAt(x+1,y),downR=iqAt(x+1,y+1);
            vec2 m0,m1,m2,m3;
            if ((x&1)==1) {
                middle4of6(upC,midC,downC,upR,midR,downR,m0,m1,m2,m3);
                oIQ=median7(upL,midL,downL,m0,m1,m2,m3);
            } else {
                middle4of6(upL,midL,downL,upC,midC,downC,m0,m1,m2,m3);
                oIQ=median7(upR,midR,downR,m0,m1,m2,m3);
            }
        }
    """.trimIndent()

    val reconstructChroma = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uRgb;
        uniform sampler2D uMedianIq;
        uniform ivec2 uSize;
        uniform int uNormalizedChroma;
        uniform float uEdgeSigma;
        uniform float uChromaBound;
        layout(location=0) out vec4 oRgb;

        float Yof(vec3 c) { return 0.299*c.r+0.587*c.g+0.114*c.b; }
        vec3 fromYIQ(float Y, vec2 iq) {
            return vec3(Y+0.956*iq.x+0.621*iq.y,
                        Y-0.272*iq.x-0.647*iq.y,
                        Y-1.105*iq.x+1.702*iq.y);
        }
        float boundScale(float Y, vec2 iq, float sourceMaximum) {
            float upper=max(Y,sourceMaximum)>1.0?
                1.25*max(Y,sourceMaximum):1.0;
            vec3 full=fromYIQ(Y,iq);
            if (all(greaterThanEqual(full,vec3(0.0))) &&
                all(lessThanEqual(full,vec3(upper)))) return 1.0;
            float lo=0.0,hi=1.0;
            for(int i=0;i<4;++i) {
                float mid=0.5*(lo+hi);
                vec3 c=fromYIQ(Y,mid*iq);
                if (all(greaterThanEqual(c,vec3(0.0))) &&
                    all(lessThanEqual(c,vec3(upper)))) lo=mid;
                else hi=mid;
            }
            return lo;
        }
        void main() {
            ivec2 p=ivec2(gl_FragCoord.xy);
            vec4 src=texelFetch(uRgb,p,0);
            if(p.y==0||p.y==uSize.y-1) { oRgb=src; return; }
            vec2 iq=vec2(0.0);
            if(p.x==0||p.x==uSize.x-1) {
                iq=texelFetch(uMedianIq,p,0).rg;
            } else if(uEdgeSigma>0.0) {
                float Yc=Yof(src.rgb);
                float inv2s2=1.0/max(uEdgeSigma*uEdgeSigma,1.0e-8);
                float wSum=0.0;
                for(int dy=-1;dy<=1;++dy) for(int dx=-1;dx<=1;++dx) {
                    ivec2 q=p+ivec2(dx,dy);
                    float Yn=Yof(texelFetch(uRgb,q,0).rgb);
                    float d=Yn-Yc;
                    float w=exp(-d*d*inv2s2);
                    iq+=w*texelFetch(uMedianIq,q,0).rg;
                    wSum+=w;
                }
                iq/=max(wSum,1.0e-6);
            } else {
                for(int dy=-1;dy<=1;++dy) for(int dx=-1;dx<=1;++dx)
                    iq+=texelFetch(uMedianIq,p+ivec2(dx,dy),0).rg;
                iq*=1.0/9.0;
            }
            float Y=Yof(src.rgb);
            if(uNormalizedChroma!=0) iq*=max(Y,1.0e-4);
            if(uChromaBound>0.0)
                iq*=boundScale(Y,iq,max(src.r,max(src.g,src.b)));
            oRgb=vec4(fromYIQ(Y,iq),src.a);
        }
    """.trimIndent()
}
