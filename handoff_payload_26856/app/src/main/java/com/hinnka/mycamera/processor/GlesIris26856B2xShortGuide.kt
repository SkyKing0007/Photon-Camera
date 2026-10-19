package com.hinnka.mycamera.processor

/**
 * IRIS_26856_B_TRUE2X_VERIFIED_SHORT_SCALAR_ONLY
 *
 * The 26651 physical SHORT decision is already embedded in B's own 1x RAWR
 * after-image. Store its *scalar* radiance ratio as a compact GL_R16F guide
 * and apply it only AFTER independent NORMAL CFA -> AMaZE -> Lab/FCC 2x.
 * No extra SHORT reconstruction, Sabre/VGN color, demosaic or spatial RGB
 * fallback is authorized here; absent/rejected SHORT produces gain=1.
 * This does not repair totally missing 2x CFA support at saturated sites:
 * that case must still reject capture before AMaZE rather than fake detail.
 */
internal object GlesIris26856B2xShortGuide {
    const val owner = "IRIS_26856_B_TRUE2X_VERIFIED_SHORT_SCALAR_ONLY"
    val extractGain = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform highp sampler2D uBNormal;
        uniform highp sampler2D uBPhysicalShort;
        uniform ivec2 uNativeSize;
        uniform float uPhysicalRatio;
        layout(location=0) out vec4 oGain;
        float radiance(vec3 c) {
            return dot(max(c,vec3(0.0)),vec3(0.25,0.50,0.25));
        }
        void main() {
            ivec2 p = clamp(ivec2(gl_FragCoord.xy),ivec2(0),uNativeSize-ivec2(1));
            float prior = radiance(texelFetch(uBNormal,p,0).rgb);
            float afterShort = radiance(texelFetch(uBPhysicalShort,p,0).rgb);
            float g = 1.0;
            if (prior >= 0.05 && afterShort > prior &&
                !isnan(prior) && !isnan(afterShort) &&
                !isinf(prior) && !isinf(afterShort) && uPhysicalRatio > 1.0) {
                g = clamp(afterShort/prior,1.0,uPhysicalRatio);
            }
            oGain = vec4(g,0.0,0.0,1.0);
        }
    """.trimIndent()

    val applyGain = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform highp sampler2D uIndependentB2xRgb;
        uniform highp sampler2D uVerifiedShortGain;
        uniform ivec2 uExpandedOrigin;
        uniform ivec2 uNativeSize;
        layout(location=0) out vec4 oExtendedB2xRgb;
        void main() {
            ivec2 local=ivec2(gl_FragCoord.xy);
            ivec2 nativeP=clamp((uExpandedOrigin+local)/2,
                ivec2(0),uNativeSize-ivec2(1));
            vec4 c=texelFetch(uIndependentB2xRgb,local,0);
            float g=texelFetch(uVerifiedShortGain,nativeP,0).r;
            // Rejected and missing physical SHORT are exact identity. The
            // guide carries only the bounded accepted 26651 scalar, never
            // a lower-resolution RGB/chroma replacement or an SDR clamp.
            if (isnan(g) || isinf(g) || g<1.0) g=1.0;
            oExtendedB2xRgb=vec4(c.rgb*g,c.a);
        }
    """.trimIndent()
    /* IRIS_26856_B_LONG_LUMA_SHARED_SCALAR_ONLY
     * Consume the existing 26845 native-resolution LONG gain/trust product
     * only AFTER independent B AMaZE/Lab/FCC; native B uses output scale 1,
     * streamed true-2x B uses scale 2 and the exact expanded tile origin.
     * Native-resolution gain is smoothly sampled in the doubled lattice;
     * B RGB hue/chroma ratios and genuine reconstructed 2x detail remain
     * exclusively NORMAL-owned. LONG does not enter CFA support, alignment,
     * reconstruction, VGN, SHORT or DNG.
     */
    val applyVerifiedLongLuma26856 = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform highp sampler2D uIndependentBRgb;
        uniform highp sampler2D uVerifiedLongLuma;
        uniform ivec2 uExpandedOrigin;
        uniform ivec2 uNativeSize;
        uniform int uOutputScale;
        layout(location=0) out vec4 oIndependentB;
        vec2 verifiedGain(ivec2 p) {
            return max(texelFetch(uVerifiedLongLuma,
                clamp(p,ivec2(0),uNativeSize-ivec2(1)),0).rg,vec2(0.0));
        }
        void main() {
            ivec2 local=ivec2(gl_FragCoord.xy);
            vec4 rgb=texelFetch(uIndependentBRgb,local,0);
            vec2 mapped=(vec2(uExpandedOrigin+local)+vec2(0.5))/float(uOutputScale)-vec2(0.5);
            ivec2 base=ivec2(floor(mapped));
            vec2 fractPart=fract(mapped);
            float g00=verifiedGain(base).r;
            float g10=verifiedGain(base+ivec2(1,0)).r;
            float g01=verifiedGain(base+ivec2(0,1)).r;
            float g11=verifiedGain(base+ivec2(1,1)).r;
            float gain=mix(mix(g00,g10,fractPart.x),mix(g01,g11,fractPart.x),fractPart.y);
            // A native 26845 gain product is identity for rejected LONG support.
            // No extra blur or shadow detail substitution belongs to independent B.
            if (isnan(gain) || isinf(gain)) gain=1.0;
            gain=clamp(gain,0.78,1.42);
            oIndependentB=vec4(rgb.rgb*gain,rgb.a);
        }
    """.trimIndent()
}
