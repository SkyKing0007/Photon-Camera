package com.hinnka.mycamera.processor

/**
 * IRIS_26932_LKR_ONLY_RAWLENS_2_2_86_FALSE_COLOR_MEDIAN.
 * RawLens 2.2.86 app/src/main/assets/shaders/amaze/cleanup.glsl:
 * exact 19-exchange Paeth median-of-9 over WB-balanced (R-G, B-G).
 * This part is adapted from RawLens GPL-3.0-or-later app shader;
 * upstream commit 36e5141df568e74e2708dd4f50413b3aa51dab20.
 * This intentionally does NOT port RawLens purple-defringe because the
 * existing Iris Lab defringe is preserved by user request.
 * Native LKR has already demosaiced, and Iris's LSC/WB has already occurred.
 */
internal object GlesIris26932RawLensMedian {
    // IRIS_26938_B_ON_SINGLE_CAMERA_LINEAR_WHITE_OWNER
    // RawLens's sensor-domain near-white response belongs AFTER its unchanged
    // one-pass WB-space chroma median, BEFORE Iris Lab/CCM. A fixed camera
    // white, not per-pixel max-white, defines neutral hue. Scale that neutral
    // by the input's WB-space luminance, so the blend cannot produce a dark
    // or bright ring at a changing clipping boundary. Unlike raw RawLens's
    // unrestricted all-bright-channel rule, its near-white shoulder is gated
    // by original Bayer clipping + WB-space hue: genuine bright yellow stays.
    // No second YIQ false-colour correction, no extra post-Lab repaint.
    val shader = """#version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uLkrPostWbRgb;
        uniform sampler2D uNativeSensorClip;
        uniform ivec2 uSize;
        uniform vec3 uAmazeWb;
        uniform int uBayerPattern;
        layout(location=0) out vec4 oRgb;
        #define CC_SORT(a,b) { highp vec2 t_=min(a,b); b=max(a,b); a=t_; }
        highp vec2 cc_diff(ivec2 pixel){
            highp vec3 c=max(texelFetch(uLkrPostWbRgb,
                clamp(pixel,ivec2(0),uSize-ivec2(1)),0).rgb,vec3(0.0));
            return c.rb-c.g;
        }
        // LKR 2x clip texture repeats each ORIGINAL RAW sample into a 2x2
        // output region. Recover the four independent physical Bayer phases.
        float originalClip(ivec2 site){
            ivec2 n=max(uSize/2,ivec2(1));
            return clamp(texelFetch(uNativeSensorClip,
                2*clamp(site,ivec2(0),n-ivec2(1)),0).r,0.0,1.0);
        }
        vec3 phaseClip(ivec2 cell){
            ivec2 n=max((uSize/2-ivec2(1))/2,ivec2(0));
            ivec2 b=2*clamp(cell,ivec2(0),n);
            float a=originalClip(b);
            float x=originalClip(b+ivec2(1,0));
            float y=originalClip(b+ivec2(0,1));
            float z=originalClip(b+ivec2(1,1));
            int r=clamp(uBayerPattern,0,3);
            int blue=3-r;
            // For 0/3 red phase, green phases are 1/2; for 1/2, 0/3.
            float red=(r==0)?a:(r==1)?x:(r==2)?y:z;
            float blu=(blue==0)?a:(blue==1)?x:(blue==2)?y:z;
            float green=(r==0||r==3)?0.5*(x+y):0.5*(a+z);
            return vec3(red,green,blu);
        }
        void main(){
            ivec2 p=clamp(ivec2(gl_FragCoord.xy),ivec2(0),uSize-ivec2(1));
            vec4 original=texelFetch(uLkrPostWbRgb,p,0);
            highp vec3 c=max(original.rgb,vec3(0.0));
            highp vec2 p0=cc_diff(p+ivec2(-1,-1)),p1=cc_diff(p+ivec2(0,-1));
            highp vec2 p2=cc_diff(p+ivec2(1,-1)),p3=cc_diff(p+ivec2(-1,0));
            highp vec2 p4=c.rb-c.g,p5=cc_diff(p+ivec2(1,0));
            highp vec2 p6=cc_diff(p+ivec2(-1,1)),p7=cc_diff(p+ivec2(0,1));
            highp vec2 p8=cc_diff(p+ivec2(1,1));
            CC_SORT(p1,p2) CC_SORT(p4,p5) CC_SORT(p7,p8) CC_SORT(p0,p1) CC_SORT(p3,p4)
            CC_SORT(p6,p7) CC_SORT(p1,p2) CC_SORT(p4,p5) CC_SORT(p7,p8) CC_SORT(p0,p3)
            CC_SORT(p5,p8) CC_SORT(p4,p7) CC_SORT(p3,p6) CC_SORT(p1,p4) CC_SORT(p2,p5)
            CC_SORT(p4,p7) CC_SORT(p4,p2) CC_SORT(p6,p4) CC_SORT(p4,p2)
            highp vec3 medianRgb=max(vec3(c.g+p4.x,c.g,c.g+p4.y),vec3(0.0));
            // Bilinear ORIGINAL-CFA phase support: smooth pixel transitions,
            // no upsampled pseudo-Bayer classification or hard square blocks.
            vec2 pos=(vec2(p)+vec2(0.5))*0.25-vec2(0.5);
            ivec2 cell=ivec2(floor(pos));
            vec2 f=clamp(fract(pos),vec2(0.0),vec2(1.0));
            vec3 phases=mix(mix(phaseClip(cell),phaseClip(cell+ivec2(1,0)),f.x),
                mix(phaseClip(cell+ivec2(0,1)),phaseClip(cell+ivec2(1,1)),f.x),f.y);
            // RawLens 2.2.86 rcd_final.glsl: clip response in native
            // camera-linear RGB BEFORE the calibrated colour matrix.
            // WB factors were applied solely for median/Lab; undo them here
            // to measure actual sensor-domain brightness (not multiplied WB).
            vec3 wb=max(uAmazeWb,vec3(0.0001));
            vec3 sensorRgb=medianRgb/wb;
            vec3 whiteCurve=smoothstep(vec3(0.70),vec3(0.99),sensorRgb);
            float rawLensWhite=max(whiteCurve.r,max(whiteCurve.g,whiteCurve.b));

            // Two independent physical witnesses determine whether abnormal
            // RB-vs-G chroma can be a clipped neutral glint. In particular,
            // green-only and R+B clips must not fail as in 26937.
            float allClip=min(phases.r,min(phases.g,phases.b));
            float rbClip=min(phases.r,phases.b);
            float peak=max(medianRgb.r,max(medianRgb.g,medianRgb.b));
            float minimum=min(medianRgb.r,min(medianRgb.g,medianRgb.b));
            float chromaSpan=(peak-minimum)/max(peak,0.0001);
            float magenta=(min(medianRgb.r,medianRgb.b)-medianRgb.g)/max(peak,0.0001);
            float wrongMagenta=smoothstep(0.03,0.14,magenta);
            float rbEvidence=smoothstep(0.07,0.80,rbClip);
            float greenEvidence=smoothstep(0.07,0.80,phases.g);
            float allEvidence=smoothstep(0.07,0.80,allClip);
            float clippedPink=wrongMagenta*max(rbEvidence,greenEvidence);

            // Near-neutral whites use RawLens's gradual 0.70..0.99 curve.
            // High-chroma genuine yellow/red/cyan cannot be declared white
            // by brightness alone; physically clipped pink cores remain safe.
            float nearNeutral=1.0-smoothstep(0.11,0.29,chromaSpan);
            float fade=clamp(max(allEvidence,clippedPink,
                nearNeutral*rawLensWhite),0.0,1.0);

            // Camera's measured neutral-white direction is (1/WB.r,
            // 1/WB.g,1/WB.b). Use its common post-WB axis and KEEP original
            // weighted luminance; unlike 26934's local max or RawLens's
            // constant unit target, no spatially varying brightness jump.
            float luma=dot(medianRgb,vec3(0.25,0.50,0.25));
            vec3 corrected=mix(medianRgb,vec3(luma),fade);
            oRgb=vec4(corrected,original.a);
        }
    """.trimIndent()
}
