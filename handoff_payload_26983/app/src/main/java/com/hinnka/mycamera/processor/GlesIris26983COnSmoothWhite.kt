package com.hinnka.mycamera.processor

/** IRIS_26937_B_ON_POST_LAB_CLIPPED_NEUTRAL_RECONCILIATION.
 * The actual clipped-white blend is owned by RawLens-median-before-Lab.
 * This final stage only rejects NEW chroma excursions introduced by Lab
 * inside an already neutral, brightly clipped input. It preserves luminance,
 * exact original inverse-WB ownership, and unmasked colour/alpha unchanged.
 */
internal object GlesIris26983COnSmoothWhite {
    val shader = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uWbRgb;
        uniform sampler2D uPreLabWbRgb;
        uniform vec3 uInverseAmazeWb;
        uniform ivec2 uSize;
        layout(location=0) out vec4 oRgb;
        void main(){
            ivec2 p=clamp(ivec2(gl_FragCoord.xy),ivec2(0),uSize-ivec2(1));
            vec4 original=texelFetch(uWbRgb,p,0);
            vec3 before=max(texelFetch(uPreLabWbRgb,p,0).rgb,vec3(0.0));
            vec3 after=max(original.rgb,vec3(0.0));
            float bMax=max(before.r,max(before.g,before.b));
            float bMin=min(before.r,min(before.g,before.b));
            float aMax=max(after.r,max(after.g,after.b));
            float aMin=min(after.r,min(after.g,after.b));
            float beforeChroma=bMax-bMin;
            float afterChroma=aMax-aMin;
            // Only a BRIGHT, ALREADY-neutral pre-Lab pixel can veto a NEW
            // Lab chroma excursion. This cannot whiten a genuine yellow leaf
            // that the physical clipping witness left uncorrected.
            float neutral=smoothstep(0.90,0.995,bMin/max(bMax,0.0001));
            float bright=smoothstep(0.95,1.35,bMax);
            float newFalseColor=smoothstep(0.015,0.20,
                max(afterChroma-beforeChroma,0.0));
            float fade=neutral*bright*newFalseColor;
            // Match after-Lab brightness; never insert a dark outline when
            // restoring the pre-Lab neutral chroma. No global tone change.
            float afterLuma=dot(after,vec3(0.25,0.50,0.25));
            float beforeLuma=dot(before,vec3(0.25,0.50,0.25));
            vec3 neutralAtLuma=before+vec3(afterLuma-beforeLuma);
            vec3 corrected=mix(original.rgb,neutralAtLuma,fade);
            oRgb=vec4(corrected*uInverseAmazeWb,original.a);
        }
    """.trimIndent()
}
