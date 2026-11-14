package com.hinnka.mycamera.processor

/** IRIS_26932_LKR_50MP_B_ON_WHITE_ONLY.
 * The exact successful Iris B/SR-OFF 26866 near-clipped shared-channel
 * white fade, independently adapted to LKR's 2x sensor-coordinate clip mask.
 * This does NOT modify the B OFF shader, source, tone, or other modes.
 * The inverse temporary-WB is fused into this final pass: NO new 50MP buffer.
 */
internal object GlesIris26932LkrSmoothWhite {
    val shader = """
        #version 300 es
        precision highp float;
        uniform sampler2D uWbRgb;
        uniform sampler2D uPreLabWbRgb;
        uniform sampler2D uNativeSensorClip;
        uniform vec3 uInverseAmazeWb;
        uniform ivec2 uSize;
        uniform vec3 uAmazeWb;
        uniform int uBayerPattern;
        layout(location=0) out vec4 oRgb;
        // The true raw CFA sample's binary mask is duplicated 2x in the
        // LKR 50MP carrier. Re-index every physical site to its actual sensor
        // coordinate, not the upsampled 50MP image phase.
        float clipAt(ivec2 p){
            ivec2 siteSize=uSize/2;
            ivec2 q=clamp(p,ivec2(0),siteSize-ivec2(1))*2;
            return clamp(texelFetch(uNativeSensorClip,q,0).r,0.0,1.0);
        }
        // The original selected Bayer RAW footprint remains BINARY. Its
        // external R16F sidecar is also used by the 26876 native true-2x
        // JPEG packer and MUST remain exactly 0/1; never encode confidence
        // in that published mask. The four CFA patterns retain their exact
        // physical R/G1/G2/B orientation from successful 26882.
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
            // Post-Lab/FCC is the final colour we correct; original camera
            // radiance evidence must NOT be sourced from the chroma that
            // Lab/FCC may already have distorted in clipped highlights.
            // This pre-Lab post-WB texture already exists for BOTH B routes;
            // the extra read introduces no new 50MP allocations.
            vec3 evidenceRgb=max(texelFetch(uPreLabWbRgb,p,0).rgb,vec3(0.0));
            vec3 rgb=max(original.rgb,vec3(0.0));
            vec3 gains=max(uAmazeWb,vec3(0.0001));
            // Temporary WB is inverted for the pre-clipping brightness
            // test on the existing BEFORE-Lab/FCC post-AMaZE RGB. This is
            // NOT an independently measured original-Bayer soft-clipping
            // sidecar; original Bayer HARD clipping remains independent and
            // strictly binary. No Wronski/HDRq reconstruction is changed.
            vec3 cameraRgb=evidenceRgb/gains;
            float wbSafe=max(min(gains.r,min(gains.g,gains.b)),0.0001);
            // RAWR OFF's shared WB-safe ceiling means a visually white
            // highlight can approach saturation BEFORE two RAW channels
            // approach sensor-white (for example high red WB gain). Test
            // visual shoulder against one shared WB ceiling; separately
            // require reconstructed pre-WB brightness for sensor plausibility.
            vec3 nearChannel=smoothstep(vec3(0.72),vec3(1.01),
                clamp(evidenceRgb/wbSafe,vec3(0.0),vec3(3.0)));
            float brightOne=max(max(rgb.r,rgb.g),rgb.b);
            float sourceOne=max(max(evidenceRgb.r,evidenceRgb.g),evidenceRgb.b);
            float sourceTwo=max(min(evidenceRgb.r,evidenceRgb.g),
                min(max(evidenceRgb.r,evidenceRgb.g),evidenceRgb.b));
            float weakestCam=min(cameraRgb.r,min(cameraRgb.g,cameraRgb.b));
            float strongestCam=max(cameraRgb.r,max(cameraRgb.g,cameraRgb.b));
            // A genuinely colored saturated source needs a third-channel
            // witness. Red/blue/yellow lamps with negligible one-channel
            // response remain unchanged even when two other channels clip.
            float sourceColorBalance=smoothstep(0.27,0.61,
                weakestCam/max(strongestCam,0.0001));
            float weakestVisible=min(evidenceRgb.r,min(evidenceRgb.g,evidenceRgb.b));
            float visibleWhiteBalance=smoothstep(0.47,0.70,
                weakestVisible/max(sourceOne,0.0001));
            // Use BOTH sensor-referenced and currently-visible evidence:
            // strong yellow/red/blue emitters cannot qualify as white just
            // because two individual camera channels approach saturation.
            float whiteWitness=sourceColorBalance*visibleWhiteBalance;
            float sensorApproach=smoothstep(0.48,0.80,strongestCam);
            // Post-WB shared safe ceiling is ONE common level for R/G/B,
            // unlike a channel-by-channel colored clamp. Output intensity
            // follows the local second-brightest/brightest signal rather
            // than a constant grey shoulder or fixed normalized plateau.
            float brightWitness=smoothstep(0.68,1.04,
                max(sourceTwo/wbSafe,weakestCam));
            // 26882 defect: an immediate clippedCoverage==0 early return
            // makes the near-clipped white shoulder completely unreachable.
            // Only this reconstructed near-headroom branch can act before
            // hard clipping; it does not touch/publish the binary RAW mask.
            float rgNear=min(nearChannel.r,nearChannel.g);
            float gbNear=min(nearChannel.g,nearChannel.b);
            float rbNear=min(nearChannel.r,nearChannel.b) *
                smoothstep(0.35,0.80,cameraRgb.g);
            float earlyWhite=max(max(rgNear,gbNear),rbNear);
            float earlyFade=smoothstep(0.06,0.89,earlyWhite) *
                whiteWitness*brightWitness*sensorApproach;
            // Preserve the full original Bayer binary check, including a
            // continuous 5-tap footprint and separately oriented CFA phases.
            // It can increase certainty for truly physically clipped whites
            // but does not gate the visually earlier near-clip shoulder.
            ivec2 sensorP=clamp(p/2,ivec2(0),uSize/2-ivec2(1));
            float clippedCoverage=(4.0*clipAt(sensorP)+
                clipAt(sensorP+ivec2(-1,0))+clipAt(sensorP+ivec2(1,0))+
                clipAt(sensorP+ivec2(0,-1))+clipAt(sensorP+ivec2(0,1)))*0.125;
            vec2 cellPosition=(vec2(p)+vec2(0.5))*0.25-vec2(0.5);
            ivec2 baseCell=ivec2(floor(cellPosition));
            vec2 blend=clamp(fract(cellPosition),vec2(0.0),vec2(1.0));
            vec3 colorClip=mix(
                mix(phaseColorClipAt(baseCell),
                    phaseColorClipAt(baseCell+ivec2(1,0)),blend.x),
                mix(phaseColorClipAt(baseCell+ivec2(0,1)),
                    phaseColorClipAt(baseCell+ivec2(1,1)),blend.x),blend.y);
            float greenCross=min(colorClip.g,max(colorClip.r,colorClip.b));
            float greenOnly=colorClip.g *
                smoothstep(0.80,0.98,min(cameraRgb.r,cameraRgb.b));
            float rbWithGreen=min(colorClip.r,colorClip.b) *
                smoothstep(0.35,0.75,cameraRgb.g);
            float allColors=min(colorClip.r,min(colorClip.g,colorClip.b));
            float sensorWhite=max(allColors,max(greenCross,max(greenOnly,rbWithGreen)));
            float sensorFade=smoothstep(0.07,0.46,
                min(clippedCoverage,sensorWhite)) *
                whiteWitness*brightWitness;
            float fade=max(earlyFade,sensorFade);
            if(fade<=0.0){oRgb=vec4(original.rgb*uInverseAmazeWb,original.a);return;}
            // Source highlight brightness remains monotone: mixing to a
            // common-white target MAXIMUM cannot darken a clipped channel.
            float neutral=max(max(brightOne,sourceOne),wbSafe);
            oRgb=vec4(mix(original.rgb,vec3(neutral),
                clamp(fade,0.0,1.0))*uInverseAmazeWb,original.a);
        }
    """.trimIndent()
}
