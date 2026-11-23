package com.hinnka.mycamera.processor

/**
 * C-only reproduction of the pinned bjzhou AdobeCurve/no-DCP selected branch.
 * Original source: RawLinearRcdPass, AdobeCurveToneAlgorithm, RawEngineTonePass,
 * RawSrgbPass at donor revision 0a8a11defe7d932d8c8a729120a4d5f159e9d677.
 *
 * These are independent, individually verifiable GLES 3.0 shader stages.
 * They are NOT wired to C's active color owner: donor GuidedUpsample requires
 * that the true low-resolution `cameraTexture` pass through *both* linear and
 * profile stages, with actual camera/profile matrices and exposure metadata.
 * Do NOT connect only the resulting tone to the current approximate HDR path.
 * All inputs/outputs are linear RGB except the final explicit display encoding.
 */
internal object Iris26975CDonorAdobeV25Shaders {
    val linearRcdNoDcp = """
        #version 300 es
        precision highp float;
        precision highp sampler2D;
        in vec2 vTexCoord;
        layout(location=0) out vec4 fragColor;
        uniform sampler2D uDemosaickedTexture;
        uniform mat3 uColorCorrectionMatrix;
        uniform vec3 uCameraWhite;
        uniform float uExposureGain;
        void main() {
            vec3 rgb=texture(uDemosaickedTexture,vTexCoord).rgb;
            rgb=min(rgb,max(uCameraWhite,vec3(0.001)));
            rgb=uColorCorrectionMatrix*rgb;
            rgb=clamp(rgb,vec3(0.0),vec3(1.0));
            rgb*=uExposureGain;
            fragColor=vec4(rgb,1.0);
        }
    """.trimIndent()

    // AdobeCurveToneShader selected no-DCP profile branch. The math and order
    // below are from the pinned donor; do not apply Iris custom gamut shifts,
    // post-tone boost or independent highlight rebuilding here.
    val adobeProfileAndToneNoDcp = """
        #version 300 es
        precision highp float;
        precision highp sampler2D;
        in vec2 vTexCoord;
        layout(location=0) out vec4 fragColor;
        uniform sampler2D uInputTexture;
        uniform sampler2D uCurveTexture;
        uniform mat3 uProfileToEngineTransform;
        uniform mat3 uOutputTransform;
        uniform float uCurveSize;
        uniform bool uCurveEnabled;
        uniform float uProfileExposureLinearGain;
        uniform bool uProfileExposureRampEnabled;
        uniform float uProfileExposureRampSlope;
        uniform float uProfileExposureRampBlack;
        uniform float uProfileExposureRampRadius;
        uniform float uProfileExposureRampQScale;
        uniform bool uProfileExposureSupportOverrange;
        uniform bool uProfileExposureToneEnabled;
        uniform float uProfileExposureToneSlope;
        uniform float uProfileExposureToneA;
        uniform float uProfileExposureToneB;
        uniform float uProfileExposureToneC;
        float sampleBaseCurve(float value) {
            if (!uCurveEnabled || uCurveSize <= 1.0) return value;
            value=clamp(value,0.0,1.0);
            float coordX=value*((uCurveSize-1.0)/uCurveSize)+(0.5/uCurveSize);
            return texture(uCurveTexture,vec2(coordX,0.5)).r;
        }
        float applyProfileExposureToneValue(float value) {
            if (!uProfileExposureToneEnabled) return value;
            if (value<=0.25) return value*uProfileExposureToneSlope;
            return (uProfileExposureToneA*value+uProfileExposureToneB)*value+uProfileExposureToneC;
        }
        float sampleProfileToneCurve(float value) {
            value=clamp(value,0.0,1.0);
            return sampleBaseCurve(applyProfileExposureToneValue(value));
        }
        float sampleProfileToneCurveOverrange(float value) {
            if (!(value>1.0)) return sampleProfileToneCurve(max(value,0.0));
            const float dx=0.001;
            float y1=sampleProfileToneCurve(1.0);
            float slope=(y1-sampleProfileToneCurve(1.0-dx))/dx;
            return y1+slope*(value-1.0);
        }
        float encodeProfileOverrangeValue(float value) {
            value=max(value,0.0);
            return value*(256.0+value)/(256.0*(1.0+value));
        }
        float decodeProfileOverrangeValue(float value) {
            value=max(value,0.0);
            float discriminant=max(64.0*value*value-127.0*value+64.0,0.0);
            return 16.0*(8.0*value-8.0+sqrt(discriminant));
        }
        float applyProfileExposureRampValue(float value, bool preserveHighlights) {
            float black=uProfileExposureRampBlack;
            float radius=uProfileExposureRampRadius;
            if (value<=black-radius) return 0.0;
            if (value>=black+radius) {
                float ramped=max((value-black)*uProfileExposureRampSlope,0.0);
                return (preserveHighlights || uProfileExposureSupportOverrange) ?
                    ramped : min(ramped,1.0);
            }
            float y=value-(black-radius);
            return uProfileExposureRampQScale*y*y;
        }
        vec3 applyProfileExposureRamp(vec3 color) {
            if (!uProfileExposureRampEnabled) return color*uProfileExposureLinearGain;
            return vec3(
                applyProfileExposureRampValue(color.r,false),
                applyProfileExposureRampValue(color.g,false),
                applyProfileExposureRampValue(color.b,false));
        }
        void adobeRgbTone(inout float maxValue,inout float midValue,inout float minValue) {
            float oldMax=maxValue;
            float oldMid=midValue;
            float oldMin=minValue;
            maxValue=uProfileExposureSupportOverrange ?
                sampleProfileToneCurveOverrange(oldMax) : sampleProfileToneCurve(oldMax);
            minValue=uProfileExposureSupportOverrange ?
                sampleProfileToneCurveOverrange(oldMin) : sampleProfileToneCurve(oldMin);
            if (abs(oldMax-oldMin)<1e-6) midValue=minValue;
            else midValue=minValue+(maxValue-minValue)*(oldMid-oldMin)/(oldMax-oldMin);
        }
        vec3 applyAdobeCurve(vec3 color) {
            color=uProfileExposureSupportOverrange ? vec3(
                encodeProfileOverrangeValue(color.r),
                encodeProfileOverrangeValue(color.g),
                encodeProfileOverrangeValue(color.b)) : clamp(color,vec3(0.0),vec3(1.0));
            float r=color.r;
            float g=color.g;
            float b=color.b;
            if (r>=g) {
                if (g>b) adobeRgbTone(r,g,b);
                else if (b>r) adobeRgbTone(b,r,g);
                else if (b>g) adobeRgbTone(r,b,g);
                else {
                    r=uProfileExposureSupportOverrange ?
                        sampleProfileToneCurveOverrange(r) : sampleProfileToneCurve(r);
                    g=uProfileExposureSupportOverrange ?
                        sampleProfileToneCurveOverrange(g) : sampleProfileToneCurve(g);
                    b=g;
                }
            } else {
                if (r>=b) adobeRgbTone(g,r,b);
                else if (b>g) adobeRgbTone(b,g,r);
                else adobeRgbTone(g,b,r);
            }
            vec3 toned=vec3(r,g,b);
            if (uProfileExposureSupportOverrange) return vec3(
                decodeProfileOverrangeValue(toned.r),
                decodeProfileOverrangeValue(toned.g),
                decodeProfileOverrangeValue(toned.b));
            return clamp(toned,vec3(0.0),vec3(1.0));
        }
        void main() {
            vec3 profileColor=texture(uInputTexture,vTexCoord).rgb;
            vec3 exposed=applyProfileExposureRamp(profileColor);
            vec3 engineColor=uProfileToEngineTransform*exposed;
            vec3 toned=uOutputTransform*applyAdobeCurve(engineColor);
            fragColor=vec4(toned,1.0);
        }
    """.trimIndent()

    // Original RawSrgbPass runs once AFTER linear-RGB tone and adjustments.
    val finalSrgb = """
        #version 300 es
        precision highp float;
        precision highp sampler2D;
        in vec2 vTexCoord;
        layout(location=0) out vec4 fragColor;
        uniform sampler2D uInputTexture;
        vec3 linearToSrgb(vec3 c) {
            c=max(c,vec3(0.0));
            vec3 lo=c*12.92;
            vec3 hi=1.055*pow(c,vec3(1.0/2.4))-0.055;
            bvec3 useHigh=greaterThan(c,vec3(0.0031308));
            return vec3(useHigh.r ? hi.r : lo.r,
                useHigh.g ? hi.g : lo.g,
                useHigh.b ? hi.b : lo.b);
        }
        void main() {
            vec3 color=texture(uInputTexture,vTexCoord).rgb;
            fragColor=vec4(clamp(linearToSrgb(color),0.0,1.0),1.0);
        }
    """.trimIndent()
}
