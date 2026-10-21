package com.hinnka.mycamera.processor

/**
 * IRIS_26863_B_MEASURED_NOISE_POST_LSC_OWNER.
 * Measured per-phase RAW variance travels through both B CFA routes to this
 * *post physical-LSC* camera-linear RGB residual pass. This is NOT the A 26853
 * spatial smoother, an assumed Camera2 noise profile, or a second WB stage.
 * Demosaic correlations preclude claiming exact RGB covariance; use a bounded
 * conservative envelope. Neither detail/luma nor the calibrated renderer is
 * allowed to change. Source remains exposed as a sealed GLSL ES 300 string
 * for exact compiled runtime expansion and unit-contract checks.
 */
internal object GlesIris26863BNoiseContinuity {
    const val owner = "IRIS_26863_B_MEASURED_NOISE_POST_LSC_OWNER"
    val residualChroma = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uPostLensSensorRgb;
        uniform sampler2D uPackedMeasuredNoise;
        uniform sampler2D uActualTemporalSupport;
        uniform sampler2D uPhysicalLensShading;
        uniform ivec2 uSize;
        uniform ivec2 uOrigin;
        uniform ivec2 uNativeSize;
        uniform int uExpandedScale;
        uniform int uUsePhysicalLsc;
        layout(location=0) out vec4 oSensorRgb;
        vec3 cameraLsc(ivec2 p) {
            vec2 uv=(vec2(uOrigin+p)+vec2(0.5))/
                (vec2(uNativeSize)*float(uExpandedScale));
            if(uUsePhysicalLsc == 0) return vec3(1.0);
            vec4 v=texture(uPhysicalLensShading,uv);
            return vec3(v.r,0.5*(v.g+v.b),v.a);
        }
        vec4 noiseAt(ivec2 p) {
            ivec2 s=textureSize(uPackedMeasuredNoise,0);
            return max(texelFetch(uPackedMeasuredNoise,clamp(p/2,ivec2(0),s-ivec2(1)),0),vec4(0.0));
        }
        float luma(vec3 c){return dot(c,vec3(0.25,0.50,0.25));}
        void main() {
            ivec2 p=clamp(ivec2(gl_FragCoord.xy),ivec2(0),uSize-ivec2(1));
            vec4 center=texelFetch(uPostLensSensorRgb,p,0);
            vec2 sup=texelFetch(uActualTemporalSupport,p/2,0).yz;
            if(sup.x<0.5 || sup.y<1.01){oSensorRgb=center;return;}
            vec4 phases=noiseAt(p);
            vec3 gain=cameraLsc(p);
            // G1 and G2 are correlated after demosaic. Their maximum is a
            // conservative local camera-green uncertainty envelope, not a
            // fabricated exact post-AMaZE covariance matrix.
            vec3 variance=vec3(phases.r,max(phases.g,phases.b),phases.a)*gain*gain;
            float luminanceSigma=sqrt(max(dot(variance,vec3(0.25,0.50,0.25)),1.0e-12));
            vec2 chromaSigma=sqrt(max(vec2(variance.r+variance.g,
                variance.b+variance.g),vec2(1.0e-12)));
            float sigma=max(chromaSigma.x,chromaSigma.y);
            if(sigma<0.0025 || sigma>0.8){oSensorRgb=center;return;}
            float y=luma(center.rgb);
            vec2 c0=vec2(center.r-center.g,center.b-center.g);
            vec2 sumC=c0;
            float sumW=1.0;
            float maxGradient=0.0;
            float maxChromaGradient=0.0;
            for(int dy=-1;dy<=1;++dy) for(int dx=-1;dx<=1;++dx){
                if(dx==0 && dy==0) continue;
                ivec2 q=clamp(p+ivec2(dx,dy),ivec2(0),uSize-ivec2(1));
                vec3 neighbor=texelFetch(uPostLensSensorRgb,q,0).rgb;
                float grad=abs(luma(neighbor)-y);
                maxGradient=max(maxGradient,grad);
                vec2 nc=vec2(neighbor.r-neighbor.g,neighbor.b-neighbor.g);
                vec2 dc=nc-c0;
                maxChromaGradient=max(maxChromaGradient,length(dc));
                float yNorm=grad*grad/max(4.0*luminanceSigma*luminanceSigma,0.000004);
                float cNorm=dot(dc*dc,1.0/max(4.0*chromaSigma*chromaSigma,vec2(0.000002)));
                float w=exp(-min(16.0,yNorm+cNorm));
                sumC+=nc*w;sumW+=w;
            }
            // Universal structural veto (fabric/foliage/hair/text/mesh alike).
            // Spatially coherent high-frequency signal remains untouched.
            float structure=1.0-smoothstep(1.5,4.0,
                max(maxGradient/max(luminanceSigma,0.001),
                    maxChromaGradient/max(sigma,0.001)));
            float noiseGate=smoothstep(0.0025,0.024,sigma);
            float supportGate=clamp((sup.y-1.0)/3.0,0.15,1.0);
            float influence=0.45*structure*noiseGate*supportGate;
            vec2 proposed=(sumC/max(sumW,1.0)-c0)*influence;
            vec2 bounded=clamp(proposed,-1.25*chromaSigma,1.25*chromaSigma);
            vec3 rgbDelta=vec3(bounded.x,0.0,bounded.y);
            // Zero luma residual prevents broad shadow/luma denoise and blur.
            rgbDelta-=vec3(luma(rgbDelta));
            oSensorRgb=vec4(center.rgb+rgbDelta,center.a);
        }
    """.trimIndent()
}
