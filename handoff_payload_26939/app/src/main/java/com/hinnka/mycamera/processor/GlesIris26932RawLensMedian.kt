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
