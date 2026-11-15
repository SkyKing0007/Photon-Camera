package com.hinnka.mycamera.processor

/** IRIS_26936_B_SRON_SENSOR_GUIDED_WHITE_ROLLOFF.
 * LKR B/ON finishing only. Keep original reference Bayer clipping binary;
 * blend to neutral for plausible near-white or independently multi-channel
 * clipped cores, but do not erase highly saturated yellow/orange materials.
 * Preserve all native LKR math and downstream color-space ownership.
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

            /* IRIS_26936_B_ON_COLOR_PRESERVING_WHITE_ROLLOFF
             * 26934's max-of-three-channel 0.70..0.99 trigger turned yellow
             * leaves into white before the sensor had clipped their blue
             * channel. The smoothness of a scalar curve does not establish
             * spatially correct material boundaries. Preserve real hue when
             * the third channel witnesses a saturated COLOR, not white.
             * These samples are already in the temporary WB domain; our
             * shared neutral and the existing inverse WB remain paired. */
            vec3 gains=max(uAmazeWb,vec3(0.0001));
            float sharedWhite=max(min(gains.r,min(gains.g,gains.b)),0.0001);
            vec3 visualRgb=max(preLab,postLab)/sharedWhite;
            float peak=max(visualRgb.r,max(visualRgb.g,visualRgb.b));
            float second=max(min(visualRgb.r,visualRgb.g),
                min(max(visualRgb.r,visualRgb.g),visualRgb.b));
            float third=min(visualRgb.r,min(visualRgb.g,visualRgb.b));
            float balanced=smoothstep(0.42,0.72,third/max(peak,0.0001));
            float visibleShoulder=smoothstep(0.72,1.02,second) *
                smoothstep(0.74,1.08,peak) * balanced;

            /* Native LKR selected-reference clipping remains the original
             * BINARY R16F mask. Sample ORIGINAL physical CFA sites (not
             * pseudo-CFA at 50 MP), interpolate only clipping confidence,
             * and require independent chromatic support before neutralizing.
             * Fully clipped R/G/B physically has no usable color: it may
             * fade to white even when the solved RGB is falsely magenta. */
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
            float allColors=min(phaseSupport.r,min(phaseSupport.g,phaseSupport.b));
            float greenAndColor=min(phaseSupport.g,max(phaseSupport.r,phaseSupport.b));
            float physicalWhite=max(smoothstep(0.12,0.70,allColors),
                0.65*balanced*smoothstep(0.20,0.82,greenAndColor));
            float sensorFade=smoothstep(0.12,0.82,coverage)*physicalWhite*
                smoothstep(0.60,0.94,peak);
            float fade=clamp(max(visibleShoulder,sensorFade),0.0,1.0);

            /* Never darken original luminance at the color/white boundary.
             * Remove the forced constant sharedWhite plateau of 26934:
             * only blend channels toward the local observed bright channel. */
            float localPeak=max(max(preLab.r,max(preLab.g,preLab.b)),
                max(postLab.r,max(postLab.g,postLab.b)));
            vec3 corrected=mix(original.rgb,vec3(localPeak),fade);
            oRgb=vec4(corrected*uInverseAmazeWb,original.a);
        }
    """.trimIndent()
}
