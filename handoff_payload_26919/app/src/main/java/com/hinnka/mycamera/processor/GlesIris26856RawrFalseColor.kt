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
        // IRIS_26919_B_OFF_CLIPPED_COLOR_BOUNDARY: original physical CFA
        // clipping is 1.0 in R16F for a clipped sensor site (not RGB alpha).
        // Enabled only for B Photo SR OFF. Unclipped and all other routes
        // retain the original RAWR FCC median mathematics exactly.
        uniform sampler2D uOriginalSensorClip26919;
        uniform int uClipAwareBOff26919;
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
        bool nearOriginalClipping(ivec2 p) {
            // No reads outside physical sensor; the successful 26917 AMaZE
            // edge/halo implementation is frozen and this guard avoids
            // changing the outer four pixels at all.
            const ivec2 taps[13]=ivec2[13](
                ivec2(0,0),ivec2(1,0),ivec2(-1,0),ivec2(0,1),ivec2(0,-1),
                ivec2(1,1),ivec2(1,-1),ivec2(-1,1),ivec2(-1,-1),
                ivec2(2,0),ivec2(-2,0),ivec2(0,2),ivec2(0,-2));
            for(int i=0;i<13;++i)
                if(texelFetch(uOriginalSensorClip26919,p+taps[i],0).r>0.5)
                    return true;
            return false;
        }
        void main() {
            ivec2 p=ivec2(gl_FragCoord.xy);
            int W=uSize.x, H=uSize.y;
            int x=p.x,y=p.y;
            if (y==0||y==H-1||x==0||x>=W-2) {
                oIQ=iqAt(x,y);
                return;
            }
            // A clipped sensor-site chroma is not a trustworthy donor.
            // Keep the center's actual chroma, rather than allowing the
            // neighborhood median to propagate a clipped lamp's hue.
            // The later reconstruction also rejects clipped neighbor donors.
            if (uClipAwareBOff26919!=0 &&
                x>=4 && x<W-4 && y>=4 && y<H-4 &&
                nearOriginalClipping(p)) {
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
        uniform sampler2D uOriginalSensorClip26919;
        uniform int uClipAwareBOff26919;
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
            // Leave the original physical border alone; guard only an actual
            // sensor-clipped area and only on independent B Photo SR OFF.
            bool gate=uClipAwareBOff26919!=0 &&
                p.x>=4 && p.y>=4 && p.x<uSize.x-4 && p.y<uSize.y-4;
            bool clippedCenter=false, nearClip=false;
            if(gate) {
                clippedCenter=texelFetch(uOriginalSensorClip26919,p,0).r>0.5;
                if(clippedCenter){oRgb=src;return;} // Preserve existing white fade.
                const ivec2 nearTaps[12]=ivec2[12](
                    ivec2(1,0),ivec2(-1,0),ivec2(0,1),ivec2(0,-1),
                    ivec2(1,1),ivec2(-1,1),ivec2(1,-1),ivec2(-1,-1),
                    ivec2(2,0),ivec2(-2,0),ivec2(0,2),ivec2(0,-2));
                for(int i=0;i<12;++i){
                    if(texelFetch(uOriginalSensorClip26919,p+nearTaps[i],0).r>0.5){
                        nearClip=true;break;
                    }
                }
            }
            vec2 iq=vec2(0.0);
            if(p.x==0||p.x==uSize.x-1) {
                iq=texelFetch(uMedianIq,p,0).rg;
            } else if(nearClip) {
                // Original CFA clipping, not RGB saturation inference, owns
                // this boundary. Keep color evidence on the same luminance
                // side and NEVER import chroma from an actually clipped site.
                // Distant clean ceiling and non-B routes remain exact RAWR.
                float Yc=Yof(src.rgb);
                float sigma=max(0.018,0.22*max(Yc,0.025));
                float inv2s2=1.0/(sigma*sigma);
                float wSum=0.0;
                for(int dy=-1;dy<=1;++dy) for(int dx=-1;dx<=1;++dx) {
                    ivec2 q=p+ivec2(dx,dy);
                    if(texelFetch(uOriginalSensorClip26919,q,0).r>0.5) continue;
                    float Yn=Yof(texelFetch(uRgb,q,0).rgb);
                    float d=Yn-Yc;
                    float w=exp(-d*d*inv2s2);
                    iq+=w*texelFetch(uMedianIq,q,0).rg;
                    wSum+=w;
                }
                if(wSum<=1.0e-6){oRgb=src;return;}
                iq/=wSum;
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
