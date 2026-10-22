package com.hinnka.mycamera.processor

/**
 * IRIS_26868_B_ONLY_SABRE_FREE_SINGLE_LONG.
 * LONG is a different exposure and NEVER enters the multi-frame RAWR HDRq merge.
 * Its physical RAW16 CFA receives the same black/white/LSC normalization
 * and the existing genuine AMaZE demosaicer, then only a shadow-luma guide
 * may influence the finished NORMAL result. No LONG chroma, fusion support,
 * detail, or DNG output may be published.
 */
internal object GlesIris26868DirectLong {
    val packCalibratedLong = """
        #version 300 es
        precision highp float;
        precision highp int;
        precision highp usampler2D;
        uniform highp usampler2D uPhysicalLongRaw16;
        uniform highp sampler2D uPhysicalLensShading;
        uniform ivec2 uSensorSize;
        uniform vec4 uPhysicalBlack;
        uniform float uPhysicalWhite;
        uniform float uReferenceOverLongExposure;
        uniform int uPhysicalBayer;
        layout(location=0) out vec4 oAmazeCanonicalCfa;
        layout(location=1) out vec4 oLongClip;
        ivec2 site(ivec2 c,int ch) {
            ivec2 tl=c*2;
            if(uPhysicalBayer==0) {
                if(ch==0)return tl;
                if(ch==1)return tl+ivec2(1,0);
                if(ch==2)return tl+ivec2(0,1);
                return tl+ivec2(1,1);
            }
            if(uPhysicalBayer==1) {
                if(ch==0)return tl+ivec2(1,0);
                if(ch==1)return tl;
                if(ch==2)return tl+ivec2(1,1);
                return tl+ivec2(0,1);
            }
            if(uPhysicalBayer==2) {
                if(ch==0)return tl+ivec2(0,1);
                if(ch==1)return tl+ivec2(1,1);
                if(ch==2)return tl;
                return tl+ivec2(1,0);
            }
            if(ch==0)return tl+ivec2(1,1);
            if(ch==1)return tl+ivec2(0,1);
            if(ch==2)return tl+ivec2(1,0);
            return tl;
        }
        void main(){
            ivec2 c=clamp(ivec2(gl_FragCoord.xy),ivec2(0),uSensorSize/2-1);
            vec4 values=vec4(0.0);
            float clipped=0.0;
            for(int ch=0;ch<4;ch++){
                ivec2 p=site(c,ch);
                int phase=(p.y&1)*2+(p.x&1);
                float raw=float(texelFetch(uPhysicalLongRaw16,p,0).r);
                float black=uPhysicalBlack[phase];
                float normalized=clamp((raw-black)/max(1.0,uPhysicalWhite-black),0.0,1.0);
                // Native pinned RAWR uses the same canonical LSC ordering:
                // R,G,G,B, with the green map indexed by physical sensor row.
                // Exactly mirror the pinned native RAWR physical LSC grid:
                // map x/(sensorW-1) to [0, mapW-1] (GL_LINEAR texel centers).
                // Green-even/green-odd use PHYSICAL sensor row, not Bayer
                // channel order; both greens must not sample the same plane.
                ivec2 mapSize=textureSize(uPhysicalLensShading,0);
                vec2 sensorRange=vec2(max(uSensorSize-ivec2(1),ivec2(1)));
                vec2 mapRange=vec2(max(mapSize-ivec2(1),ivec2(0)));
                vec2 lscUv=(vec2(p)/sensorRange*mapRange+vec2(0.5))/vec2(mapSize);
                vec4 lsc=texture(uPhysicalLensShading,lscUv);
                float lensGain=ch==0?lsc.r:(ch==3?lsc.a:
                    ((p.y&1)==0?lsc.g:lsc.b));
                float v=normalized*lensGain*uReferenceOverLongExposure;
                values[ch]=max(0.0,v);
                clipped=max(clipped,step(0.985,normalized));
            }
            oAmazeCanonicalCfa=values;
            oLongClip=vec4(clipped,0.0,0.0,1.0);
        }
    """.trimIndent()

    // This is explicitly NOT a motion estimator: trust is zero when source
    // contours disagree. A single LONG cannot override a moving NORMAL edge.
    // The only permitted reduction is low-frequency shadow luminance noise.
    val trustedShadowGain = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform highp sampler2D uNormalCameraRgb;
        uniform highp sampler2D uLongCameraRgb;
        uniform highp sampler2D uLongCfaClip;
        uniform ivec2 uImageSize;
        layout(location=0) out vec4 oShadowGain;
        float lum(vec3 c){return dot(max(c,vec3(0.0)),vec3(0.25,0.5,0.25));}
        float readLum(sampler2D t,ivec2 p){
            return lum(texelFetch(t,clamp(p,ivec2(0),uImageSize-1),0).rgb);
        }
        void main(){
            ivec2 p=clamp(ivec2(gl_FragCoord.xy),ivec2(0),uImageSize-1);
            float normalNow=readLum(uNormalCameraRgb,p);
            float longNow=readLum(uLongCameraRgb,p);
            float normalLow=0.0;
            float longLow=0.0;
            for(int y=-2;y<=2;y++)for(int x=-2;x<=2;x++){
                ivec2 q=p+ivec2(x,y);
                normalLow+=readLum(uNormalCameraRgb,q);
                longLow+=readLum(uLongCameraRgb,q);
            }
            normalLow/=25.0;
            longLow/=25.0;
            // Large registration, moving subjects, edge disagreement, clipping,
            // invalid measured light, and well-exposed areas all veto LONG.
            float highNormal=normalNow-normalLow;
            float highLong=longNow-longLow;
            float structureAgreement=1.0-smoothstep(0.012,0.055,
                abs(highNormal-highLong));
            float radianceAgreement=1.0-smoothstep(0.12,0.38,
                abs(longLow-normalLow)/max(max(normalLow,longLow),0.02));
            float shadowOnly=1.0-smoothstep(0.07,0.32,normalLow);
            float clip=texelFetch(uLongCfaClip,p/2,0).r;
            // Uniform black is never a source of reliable shadow structure:
            // forbid multiplying near-black read noise or negative leakage.
            float measuredLight=smoothstep(0.008,0.035,max(longLow,normalLow));
            float valid=measuredLight*(1.0-step(0.5,clip));
            float trust=clamp(structureAgreement*radianceAgreement*
                shadowOnly*valid,0.0,1.0);
            // The detail/high-pass belongs to multi-frame NORMAL. LONG may
            // replace only a bounded fraction of the low-frequency component.
            float targetLow=mix(normalLow,longLow,trust*0.6);
            float target=max(0.0,targetLow+highNormal);
            float gain=clamp(target/max(normalNow,0.015),0.82,1.18);
            // Subpixel bias should not multiply shadow grain near black.
            gain=mix(1.0,gain,trust);
            if(isnan(gain)||isinf(gain))gain=1.0;
            oShadowGain=vec4(gain,trust,0.0,1.0);
        }
    """.trimIndent()
}
