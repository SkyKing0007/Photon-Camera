package com.hinnka.mycamera.processor

/** IRIS_26934_B_SRON_RAWLENS_VISUAL_WHITE_FADE.
 * LKR-only (Experiment B, Super Res ON) finishing shader.
 * RawLens 2.2.86 rcd_final.glsl uses a per-channel 0.70..0.99 smoothstep,
 * whose MAX drives the fade to camera neutral. Unlike rejected 26932/26933
 * probes, never veto a visibly clipped highlight due to its distorted color.
 * The shared WB-safe scale maps that rule into Iris's TEMPORARY WB domain;
 * the existing inverse-WB is fused after the single neutralization.
 * The original binary Bayer clipping texture is independent, never modified,
 * and may only accelerate the fade in reconstructed/near-clipped cores.
 * No LKR, Lab, B-OFF, gainmap, tone, DNG, Night, or A-mode changes.
 */
internal object GlesIris26932LkrSmoothWhite {
    val shader = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uWbRgb;
        uniform sampler2D uPreLabWbRgb;
        uniform sampler2D uNativeSensorClip;
        uniform vec3 uInverseAmazeWb;
        uniform ivec2 uSize;
        uniform vec3 uAmazeWb;
        uniform int uBayerPattern;
        layout(location=0) out vec4 oRgb;

        // LKR output is 2x physical RAW dimensions; original Bayer clipping
        // is binary and copied into each 2x2 output block. Do NOT infer
        // sensor phase from the upsampled 50MP grid.
        float clipAt(ivec2 site){
            ivec2 sourceSize=max(uSize/2,ivec2(1));
            ivec2 q=2*clamp(site,ivec2(0),sourceSize-ivec2(1));
            return clamp(texelFetch(uNativeSensorClip,q,0).r,0.0,1.0);
        }
        vec3 phaseColorClipAt(ivec2 cell){
            ivec2 cellMax=max((uSize/2-ivec2(1))/2,ivec2(0));
            ivec2 base=2*clamp(cell,ivec2(0),cellMax);
            float phase[4]=float[4](clipAt(base),clipAt(base+ivec2(1,0)),
                clipAt(base+ivec2(0,1)),clipAt(base+ivec2(1,1)));
            int r=clamp(uBayerPattern,0,3);
            int b=3-r;
            int g0=(r==0||r==3)?1:0;
            int g1=3-g0;
            return vec3(phase[r],0.5*(phase[g0]+phase[g1]),phase[b]);
        }
        void main(){
            ivec2 p=clamp(ivec2(gl_FragCoord.xy),ivec2(0),uSize-ivec2(1));
            vec4 original=texelFetch(uWbRgb,p,0);
            vec3 preLab=max(texelFetch(uPreLabWbRgb,p,0).rgb,vec3(0.0));
            vec3 postLab=max(original.rgb,vec3(0.0));

            // RawLens's actual finishing rule: ANY channel approaching the
            // white ceiling can start the 0.70..0.99 fade. A pink/magenta
            // clipped highlight has no trustworthy chromaticity: do not
            // multiply by minimum-channel, neutral-ratio, or third-channel
            // tests, which kept those very pixels pink in 26932/26933.
            vec3 gains=max(uAmazeWb,vec3(0.0001));
            float sharedWhite=max(min(gains.r,min(gains.g,gains.b)),0.0001);
            vec3 visualRgb=max(preLab,postLab)/sharedWhite;
            vec3 whiteCurve=smoothstep(vec3(0.70),vec3(0.99),visualRgb);
            float visualFade=max(whiteCurve.r,max(whiteCurve.g,whiteCurve.b));

            // Native selected-reference hard-clip evidence also protects
            // LKR cores whose solved radiance fell below the visual ceiling.
            // It never GATES the smooth shoulder and never changes the mask.
            ivec2 sensorP=clamp(p/2,ivec2(0),uSize/2-ivec2(1));
            float coverage=(4.0*clipAt(sensorP)+
                clipAt(sensorP+ivec2(-1,0))+clipAt(sensorP+ivec2(1,0))+
                clipAt(sensorP+ivec2(0,-1))+clipAt(sensorP+ivec2(0,1)))*0.125;
            vec2 cellPosition=(vec2(p)+vec2(0.5))*0.25-vec2(0.5);
            ivec2 cell=ivec2(floor(cellPosition));
            vec2 t=clamp(fract(cellPosition),vec2(0.0),vec2(1.0));
            vec3 phaseSupport=mix(
                mix(phaseColorClipAt(cell),phaseColorClipAt(cell+ivec2(1,0)),t.x),
                mix(phaseColorClipAt(cell+ivec2(0,1)),phaseColorClipAt(cell+ivec2(1,1)),t.x),t.y);
            float physicalEvidence=max(phaseSupport.r,max(phaseSupport.g,phaseSupport.b));
            float peak=max(visualRgb.r,max(visualRgb.g,visualRgb.b));
            float clipFade=smoothstep(0.08,0.26,min(coverage,max(physicalEvidence,coverage))) *
                smoothstep(0.55,0.78,peak);
            float fade=clamp(max(visualFade,clipFade),0.0,1.0);

            // Use one achromatic value in temporary WB RGB, then invert WB
            // once so Iris's calibrated camera-to-display transform retains
            // its white point. Never repaint individual channels separately.
            float peakWb=max(max(preLab.r,max(preLab.g,preLab.b)),
                max(postLab.r,max(postLab.g,postLab.b)));
            float whiteTarget=max(peakWb,sharedWhite);
            vec3 corrected=mix(original.rgb,vec3(whiteTarget),fade);
            oRgb=vec4(corrected*uInverseAmazeWb,original.a);
        }
    """.trimIndent()
}
