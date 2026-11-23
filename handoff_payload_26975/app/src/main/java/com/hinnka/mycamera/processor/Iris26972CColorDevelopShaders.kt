package com.hinnka.mycamera.processor

/**
 * 26972 C-only genuine cameraRGB RAW color developer. Input is the donor's pre-clamp
 * floating ResolveSabre output, NOT its already-clipped U16 output. Filmic/Adobe
 * processing must not overwrite the separate scene-linear HDR output.
 *
 * DCP HSV interpolation and max/mid/min Adobe tone follow donor mechanics; default
 * ACR3 samples are copied separately from pinned bjzhou's table. This is a C-owned
 * path and deliberately does not import any A/B renderer or shader.
 */
internal object Iris26972CColorDevelopShaders {
    /** Pinned RawEngineTonePass HDR neutral-sample pass, Adobe/no-DCP branch.
     * Output is GPU-measured RGBA16F, not a Float32 CPU interpolation. */
    val donorAdobeNeutralMeasure = """
        #version 300 es
        precision highp float;
        precision highp sampler2D;
        uniform sampler2D uNeutralAcr3;
        uniform int uNeutralToneEnabled;
        uniform float uNeutralToneSlope;
        uniform float uNeutralToneA;
        uniform float uNeutralToneB;
        uniform float uNeutralToneC;
        uniform vec3 uNeutralOutputRow0;
        uniform vec3 uNeutralOutputRow1;
        uniform vec3 uNeutralOutputRow2;
        layout(location=0) out vec4 fragColor;
        float sampleAdobeCurve(float value) {
            value=clamp(value,0.0,1.0);
            const float size=1025.0;
            float coord=value*((size-1.0)/size)+(0.5/size);
            return texture(uNeutralAcr3,vec2(coord,0.5)).r;
        }
        float applyNegativeExposureTone(float value) {
            if (uNeutralToneEnabled==0) return value;
            if (value<=0.25) return value*uNeutralToneSlope;
            return (uNeutralToneA*value+uNeutralToneB)*value+uNeutralToneC;
        }
        void main() {
            // Exactly the donor neutral HDR sample position: floor(gl_FragCoord.x).
            float x=floor(gl_FragCoord.x)/1023.0;
            float tone=sampleAdobeCurve(applyNegativeExposureTone(x));
            vec3 engine=vec3(tone);
            vec3 outputLinear=vec3(dot(uNeutralOutputRow0,engine),
                dot(uNeutralOutputRow1,engine),dot(uNeutralOutputRow2,engine));
            float response=max(dot(outputLinear,vec3(0.2126,0.7152,0.0722)),0.0);
            fragColor=vec4(response,0.0,0.0,1.0);
        }
    """.trimIndent()

    val color = """
        #version 300 es
        precision highp float;
        precision highp sampler2D;
        precision highp int;
        uniform highp sampler2D uExtendedCameraRgb;
        uniform sampler2D uHueSatMap;
        uniform sampler2D uLookMap;
        uniform sampler2D uAdobeAcr3;
        uniform sampler2D uHdrNeutralCurve;
        uniform int uAcr3Size;
        uniform float uHdrJoinInput;
        uniform float uHdrJoinOutput;
        uniform float uHdrJoinSlope;
        uniform float uHdrQuadratic;
        uniform float uHdrWhiteOutput;
        uniform float uHdrWhiteSlope;
        uniform int uHdrExtendsBase;
        // Original donor RawProfileExposureGl: Adobe Camera2 default uses
        // Auto black rendering followed by the profile exposure ramp.
        uniform float uProfileRampSlope;
        uniform float uProfileRampBlack;
        uniform float uProfileRampRadius;
        uniform float uProfileRampQScale;
        uniform bool uProfileToneEnabled;
        uniform float uProfileToneSlope;
        uniform float uProfileToneA;
        uniform float uProfileToneB;
        uniform float uProfileToneC;
        uniform bool uHueSatEnabled;
        uniform bool uLookEnabled;
        uniform ivec3 uHueSatDims;
        uniform ivec3 uLookDims;
        uniform vec3 uSensorToProfile0;
        uniform vec3 uSensorToProfile1;
        uniform vec3 uSensorToProfile2;
        uniform vec3 uProfileToLinearSrgb0;
        uniform vec3 uProfileToLinearSrgb1;
        uniform vec3 uProfileToLinearSrgb2;
        uniform vec3 uCameraWhite;
        layout(location=0) out highp vec4 oEncodedSdr;
        layout(location=1) out highp vec4 oDonorHdrRatio;

        vec3 matSensorToProfile(vec3 c) {
            return vec3(dot(uSensorToProfile0,c), dot(uSensorToProfile1,c),
                dot(uSensorToProfile2,c));
        }
        vec3 matProfileToLinearSrgb(vec3 c) {
            return vec3(dot(uProfileToLinearSrgb0,c),dot(uProfileToLinearSrgb1,c),
                dot(uProfileToLinearSrgb2,c));
        }
        vec3 rgbToHsv(vec3 rgb) {
            float hi=max(rgb.r,max(rgb.g,rgb.b));
            float lo=min(rgb.r,min(rgb.g,rgb.b));
            float delta=hi-lo;
            float hue=0.0;
            if(delta>1e-6) {
                if(hi==rgb.r) hue=mod((rgb.g-rgb.b)/delta,6.0);
                else if(hi==rgb.g) hue=(rgb.b-rgb.r)/delta+2.0;
                else hue=(rgb.r-rgb.g)/delta+4.0;
            }
            return vec3(hue,hi>1e-6?delta/hi:0.0,hi);
        }
        vec3 hsvToRgb(vec3 hsv) {
            float hue=mod(hsv.x,6.0);
            float sat=max(hsv.y,0.0), val=max(hsv.z,0.0);
            float chroma=val*sat;
            float x=chroma*(1.0-abs(mod(hue,2.0)-1.0));
            vec3 p;
            if(hue<1.0) p=vec3(chroma,x,0.0);
            else if(hue<2.0) p=vec3(x,chroma,0.0);
            else if(hue<3.0) p=vec3(0.0,chroma,x);
            else if(hue<4.0) p=vec3(0.0,x,chroma);
            else if(hue<5.0) p=vec3(x,0.0,chroma);
            else p=vec3(chroma,0.0,x);
            return p+vec3(val-chroma);
        }
        vec3 tableAt(sampler2D tex, int s,int h,int v,int hd) {
            return texelFetch(tex,ivec2(s,v*hd+h),0).rgb;
        }
        vec3 profileMap(vec3 c,sampler2D tex,ivec3 dims) {
            // A DCP table is defined on the nonnegative profile domain; preserve
            // real negative excursions until one common neutral-axis gamut shift.
            if(min(c.r,min(c.g,c.b))<0.0) return c;
            int hd=dims.x,sd=dims.y,vd=dims.z;
            vec3 hsv=rgbToHsv(c);
            float hs=hsv.x*float(hd)/6.0;
            float ss=clamp(hsv.y,0.0,1.0)*float(max(sd-1,0));
            float vs=clamp(hsv.z,0.0,1.0)*float(max(vd-1,0));
            int h0=min(int(floor(hs)),hd-1), h1=(h0+1)%hd;
            int s0=min(int(floor(ss)),max(sd-2,0)),s1=min(s0+1,sd-1);
            int v0=min(int(floor(vs)),max(vd-2,0)),v1=min(v0+1,vd-1);
            float hf=clamp(hs-float(h0),0.0,1.0),sf=clamp(ss-float(s0),0.0,1.0);
            float vf=clamp(vs-float(v0),0.0,1.0);
            vec3 a=mix(tableAt(tex,s0,h0,v0,hd),tableAt(tex,s0,h0,v1,hd),vf);
            vec3 b=mix(tableAt(tex,s0,h1,v0,hd),tableAt(tex,s0,h1,v1,hd),vf);
            vec3 d=mix(tableAt(tex,s1,h0,v0,hd),tableAt(tex,s1,h0,v1,hd),vf);
            vec3 e=mix(tableAt(tex,s1,h1,v0,hd),tableAt(tex,s1,h1,v1,hd),vf);
            vec3 adjust=mix(mix(a,b,hf),mix(d,e,hf),sf);
            hsv.x=mod(hsv.x+adjust.x/60.0,6.0);
            hsv.y=clamp(hsv.y*adjust.y,0.0,1.0);
            // True scene-linear overrange survives DCP value scaling. Lookup
            // coords clamp but the actual scene signal is never clamped to [0,1].
            hsv.z=max(hsv.z*adjust.z,0.0);
            return hsvToRgb(hsv);
        }
        float donorProfileExposureRampValue(float value, bool preserveHighlights) {
            float black=uProfileRampBlack;
            float radius=uProfileRampRadius;
            if(value<=black-radius) return 0.0;
            if(value>=black+radius) {
                float ramped=max((value-black)*uProfileRampSlope,0.0);
                return preserveHighlights ? ramped : min(ramped,1.0);
            }
            float y=value-(black-radius);
            return uProfileRampQScale*y*y;
        }
        vec3 donorProfileExposureRamp(vec3 color, bool preserveHighlights) {
            return vec3(donorProfileExposureRampValue(color.r,preserveHighlights),
                donorProfileExposureRampValue(color.g,preserveHighlights),
                donorProfileExposureRampValue(color.b,preserveHighlights));
        }
        float hdrCurveSample(float x) {
            float pos=clamp(x,0.0,1.0)*1023.0;
            int lo=int(floor(pos));int hi=min(lo+1,1023);
            return mix(texelFetch(uHdrNeutralCurve,ivec2(lo,0),0).r,
                texelFetch(uHdrNeutralCurve,ivec2(hi,0),0).r,fract(pos));
        }
        float donorHdrExtendedCurve(float x) {
            float value=max(x,0.0);
            if(value<=uHdrJoinInput) return hdrCurveSample(value);
            if(value<=1.0) {
                float d=value-uHdrJoinInput;
                return uHdrExtendsBase != 0 ?
                    hdrCurveSample(value)+uHdrQuadratic*d*d :
                    uHdrJoinOutput+uHdrJoinSlope*d+uHdrQuadratic*d*d;
            }
            return uHdrWhiteOutput+uHdrWhiteSlope*(value-1.0);
        }
        float curveAt(float x) {
            float bounded=clamp(x,0.0,1.0)*float(uAcr3Size-1);
            int lo=int(floor(bounded));int hi=min(lo+1,uAcr3Size-1);
            return mix(texelFetch(uAdobeAcr3,ivec2(lo,0),0).r,
                texelFetch(uAdobeAcr3,ivec2(hi,0),0).r,fract(bounded));
        }
        float donorProfileExposureToneValue(float x) {
            if(!uProfileToneEnabled) return x;
            if(x<=0.25) return x*uProfileToneSlope;
            return (uProfileToneA*x+uProfileToneB)*x+uProfileToneC;
        }
        float adobeCurve(float x) {
            // Pinned AdobeCurveToneShader.sampleProfileToneCurve: negative
            // exposure's monotone hybrid is applied BEFORE ACR3 lookup.
            if(x<0.0)return x;
            if(x<=1.0)return curveAt(donorProfileExposureToneValue(x));
            const float step=0.001;
            return curveAt(donorProfileExposureToneValue(1.0))+
                (curveAt(donorProfileExposureToneValue(1.0))-
                 curveAt(donorProfileExposureToneValue(1.0-step)))*(x-1.0)/step;
        }
        void adobeOrdered(inout float hi,inout float mid,inout float low) {
            float h=hi,m=mid,l=low;
            hi=adobeCurve(h);low=adobeCurve(l);
            mid=abs(h-l)<1e-6?low:low+(hi-low)*(m-l)/(h-l);
        }
        vec3 adobeRgb(vec3 value) {
            // Pinned donor default: supportOverrange=false. Its Adobe curve
            // clamps profile RGB to [0,1] before ordered max/mid/min tone.
            value=clamp(value,vec3(0.0),vec3(1.0));
            float r=value.r,g=value.g,b=value.b;
            if(r>=g) {
                if(g>b) adobeOrdered(r,g,b);
                else if(b>r) adobeOrdered(b,r,g);
                else if(b>g) adobeOrdered(r,b,g);
                else {r=adobeCurve(r);g=adobeCurve(g);b=g;}
            } else {
                if(r>=b) adobeOrdered(g,r,b);
                else if(b>g) adobeOrdered(b,g,r);
                else adobeOrdered(g,b,r);
            }
            return vec3(r,g,b);
        }
        vec3 srgbEncode(vec3 c) {
            c=clamp(c,0.0,1.0);
            return vec3(
                c.r<=0.0031308 ? 12.92*c.r : 1.055*pow(c.r,1.0/2.4)-0.055,
                c.g<=0.0031308 ? 12.92*c.g : 1.055*pow(c.g,1.0/2.4)-0.055,
                c.b<=0.0031308 ? 12.92*c.b : 1.055*pow(c.b,1.0/2.4)-0.055);
        }
        void main() {
            ivec2 pixel=ivec2(gl_FragCoord.xy);
            // NO synthetic input and NO reconstruction from clipped SDR U16.
            vec3 cameraRgb=texelFetch(uExtendedCameraRgb,pixel,0).rgb;
            // Original donor RawLinearRcdPass clamps camera RGB to the
            // calibrated white vector, then clamps profile RGB to [0,1]
            // before Adobe's exposure/ramp/tone stage. The HDR branch below
            // deliberately keeps original pre-clamp source samples so the
            // separate Iris highlight extension never invents lost headroom.
            // Pinned RawDemosaicProcessor sets clampProfileRgb=true for
            // AdobeCurve; the HDR reference consumes the SAME LinearRcdPass
            // profile texture, not a separate unclipped cameraRGB developer.
            vec3 donorCamera=min(cameraRgb,max(uCameraWhite,vec3(0.001)));
            vec3 profile=clamp(matSensorToProfile(donorCamera),0.0,1.0);
            vec3 profileBeforeRamp=profile;
            if(uHueSatEnabled)profile=profileMap(profile,uHueSatMap,uHueSatDims);
            // The original donor Adobe profile order is HueSat -> exposure
            // ramp -> DCP Look. This ramp was previously missing entirely.
            profile=donorProfileExposureRamp(profile,false);
            if(uLookEnabled)profile=profileMap(profile,uLookMap,uLookDims);
            // Keep the genuine pre-tone source for Iris's permitted HDR
            // highlight extension, independently from the donor SDR curve.
            // Original bjzhou RawSrgbPass independently clips negative display
            // primaries; it does NOT add a common RGB offset (which would
            // introduce fabricated white and alter the donor's chroma).
            vec3 hdrForRatio=donorProfileExposureRamp(profileBeforeRamp,true);
            // Pinned RawEngineTonePass.renderHdrReference returns ONE scalar
            // gain ratio from a 1024-sample neutral engine curve, not a second
            // independently colored HDR image. With accepted no-DCP settings,
            // the profile exposure ramp is the only input adjustment.
            float sdrInput=max(profile.r,max(profile.g,profile.b));
            float hdrInput=max(hdrForRatio.r,max(hdrForRatio.g,hdrForRatio.b));
            float base=max(hdrCurveSample(sdrInput),0.000001);
            float extended=max(donorHdrExtendedCurve(hdrInput),base);
            float ratio=extended/base;
            vec3 rendered=matProfileToLinearSrgb(adobeRgb(profile));
            oDonorHdrRatio=vec4(vec3(ratio),1.0);
            oEncodedSdr=vec4(srgbEncode(rendered),1.0);
        }
    """.trimIndent()
}
