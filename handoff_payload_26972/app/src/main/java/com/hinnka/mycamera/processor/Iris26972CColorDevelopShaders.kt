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
    val color = """
        #version 300 es
        precision highp float;
        precision highp sampler2D;
        precision highp int;
        uniform highp sampler2D uExtendedCameraRgb;
        uniform sampler2D uHueSatMap;
        uniform sampler2D uLookMap;
        uniform sampler2D uAdobeAcr3;
        uniform int uAcr3Size;
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
        layout(location=0) out highp vec4 oEncodedSdr;
        layout(location=1) out highp vec4 oLinearHdr;

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
        float curveAt(float x) {
            float bounded=clamp(x,0.0,1.0)*float(uAcr3Size-1);
            int lo=int(floor(bounded));int hi=min(lo+1,uAcr3Size-1);
            return mix(texelFetch(uAdobeAcr3,ivec2(lo,0),0).r,
                texelFetch(uAdobeAcr3,ivec2(hi,0),0).r,fract(bounded));
        }
        float adobeCurve(float x) {
            if(x<0.0)return x;
            if(x<=1.0)return curveAt(x);
            const float step=0.001;
            return curveAt(1.0)+(curveAt(1.0)-curveAt(1.0-step))*(x-1.0)/step;
        }
        void adobeOrdered(inout float hi,inout float mid,inout float low) {
            float h=hi,m=mid,l=low;
            hi=adobeCurve(h);low=adobeCurve(l);
            mid=abs(h-l)<1e-6?low:low+(hi-low)*(m-l)/(h-l);
        }
        vec3 adobeRgb(vec3 value) {
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
        vec3 commonAxisFloor(vec3 c) {
            float minimum=min(c.r,min(c.g,c.b));
            return minimum<0.0 ? c-vec3(minimum) : c;
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
            vec3 profile=matSensorToProfile(cameraRgb);
            if(uHueSatEnabled)profile=profileMap(profile,uHueSatMap,uHueSatDims);
            if(uLookEnabled)profile=profileMap(profile,uLookMap,uLookDims);
            // Scene-linear reference is independent of the Adobe SDR curve,
            // transfer OETF and 8-bit publication. Overrange remains available.
            vec3 extended=commonAxisFloor(matProfileToLinearSrgb(profile));
            vec3 rendered=commonAxisFloor(matProfileToLinearSrgb(adobeRgb(profile)));
            oLinearHdr=vec4(extended,1.0);
            oEncodedSdr=vec4(srgbEncode(rendered),1.0);
        }
    """.trimIndent()
}
