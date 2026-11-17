package com.hinnka.mycamera.processor

/**
 * IRIS_26952_B_ON_RAWLENS_2_3_94_TWO_RADIUS_COLOR_DIFFERENCE_MEDIAN.
 * RawLens 2.3.94 app/src/main/assets/shaders/amaze/cleanup.glsl:
 * exact 19-exchange Paeth medians at radii 1 and 2 over WB-balanced
 * (R-G, B-G); choose the smaller color-difference norm.
 * This part is adapted from RawLens GPL-3.0-or-later app shader;
 * upstream release tag 2.3.94, cleanup.glsl Git blob
 * 5f53f47c3391273739267146d61b50bf1d3a5b25.
 * This intentionally does NOT port RawLens purple-defringe because the
 * existing Iris Lab defringe is preserved by user request.
 * Native LKR has already demosaiced, and Iris's LSC/WB has already occurred.
 */
internal object GlesIris26932RawLensMedian {
    // IRIS_26939_B_ON_RAWLENS_EARLY_CAMERA_LINEAR_WHITE_WINDOW
    // Mirror the original RawLens 2.2.86 rcd_final.glsl white transition:
    // evaluate max(smoothstep(0.70, 0.99, camera-native RGB channels))
    // and interpolate toward shutter-frozen camera neutral white before Lab.
    // Iris has temporarily white-balanced this RGB for its original 19-exchange
    // RawLens median. Undo those gains for the white-window decision and
    // reapply them only to deliver the same post-WB Lab input domain.
    // Do NOT require a native Bayer clipping mask, chroma-neutral appearance,
    // or per-pixel physical evidence: those constraints caused 26937/38 pink.
    // Do NOT add a second false-color correction or late local-peak whitening.
    // The existing unused native-clip sampler remains bound by the protected
    // stacker for ABI compatibility; it is intentionally not consulted here.
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
        // Paeth's 19-comparator median network, byte-for-byte same ordering
        // as RawLens cleanup.glsl.  Only the sampling radius changes.
        highp vec2 cc_median(ivec2 p,highp vec2 center,int radius){
            highp vec2 p0=cc_diff(p+ivec2(-radius,-radius)),p1=cc_diff(p+ivec2(0,-radius));
            highp vec2 p2=cc_diff(p+ivec2(radius,-radius)),p3=cc_diff(p+ivec2(-radius,0));
            highp vec2 p4=center,p5=cc_diff(p+ivec2(radius,0));
            highp vec2 p6=cc_diff(p+ivec2(-radius,radius)),p7=cc_diff(p+ivec2(0,radius));
            highp vec2 p8=cc_diff(p+ivec2(radius,radius));
            CC_SORT(p1,p2) CC_SORT(p4,p5) CC_SORT(p7,p8) CC_SORT(p0,p1) CC_SORT(p3,p4)
            CC_SORT(p6,p7) CC_SORT(p1,p2) CC_SORT(p4,p5) CC_SORT(p7,p8) CC_SORT(p0,p3)
            CC_SORT(p5,p8) CC_SORT(p4,p7) CC_SORT(p3,p6) CC_SORT(p1,p4) CC_SORT(p2,p5)
            CC_SORT(p4,p7) CC_SORT(p4,p2) CC_SORT(p6,p4) CC_SORT(p4,p2)
            return p4;
        }
        void main(){
            ivec2 p=clamp(ivec2(gl_FragCoord.xy),ivec2(0),uSize-ivec2(1));
            vec4 original=texelFetch(uLkrPostWbRgb,p,0);
            highp vec3 c=max(original.rgb,vec3(0.0));
            // 26952 restores the *current* RawLens two-radius cleanup,
            // not a generic color desaturation or green-luma blur.  The
            // separate two rings observe the original input, not one another.
            highp vec2 m0=cc_diff(p);
            highp vec2 fine=cc_median(p,m0,1);
            highp vec2 wide=cc_median(p,m0,2);
            highp vec2 d=dot(wide,wide)<dot(fine,fine)?wide:fine;
            highp vec3 medianRgb=max(vec3(c.g+d.x,c.g,c.g+d.y),vec3(0.0));
            // RawLens rcd_final.glsl (pinned upstream) operates in camera-
            // native linear RGB, not the temporary post-WB Lab domain.
            vec3 wb=max(uAmazeWb,vec3(0.0001));
            vec3 cameraRgb=medianRgb/wb;
            // RawLens SceneLinearColorProcessor resolves as-shot neutral,
            // normalized so the largest sensor-neutral channel is 1.0.
            // Our shutter-frozen Camera2 relative gains are inverse to that
            // neutral; normalize after inversion to match its definition.
            vec3 cameraWhite=vec3(1.0)/wb;
            cameraWhite/=max(cameraWhite.r,max(cameraWhite.g,cameraWhite.b));
            // EXACT rcd_final.glsl 0.70..0.99 highlight-window response.
            // No already-clipped mask and NO near-neutral/chroma veto.
            vec3 whiteBlendRgb=smoothstep(vec3(0.70),vec3(0.99),cameraRgb);
            float whiteBlend=max(whiteBlendRgb.r,max(whiteBlendRgb.g,whiteBlendRgb.b));
            vec3 neutralCameraRgb=mix(cameraRgb,cameraWhite,whiteBlend);
            vec3 corrected=neutralCameraRgb*wb;
            oRgb=vec4(corrected,original.a);
        }
    """.trimIndent()
}
