precision highp float;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
uniform sampler2D ProfileHueSatMap;
uniform sampler2D ProfileLookMap;
uniform sampler2D Acr3Curve;
uniform int acr3CurveSize;
uniform int acr3Enabled;
uniform int profileHueDivisions;
uniform int profileSatDivisions;
uniform int profileValueDivisions;
uniform int lookHueDivisions;
uniform int lookSatDivisions;
uniform int lookValueDivisions;
uniform vec3 sensorToProfileRow0;
uniform vec3 sensorToProfileRow1;
uniform vec3 sensorToProfileRow2;
uniform vec3 profileToSrgbRow0;
uniform vec3 profileToSrgbRow1;
uniform vec3 profileToSrgbRow2;
out vec3 Output;

#ifndef USE_PROFILE_HUESAT
#define USE_PROFILE_HUESAT 0
#endif
#ifndef USE_PROFILE_LOOK
#define USE_PROFILE_LOOK 0
#endif

/* IRIS_26628_DNG_HSV_PROFILE_MAP
 * Independently written equivalent of the DNG HSV table mechanics used by bjzhou.  SensorSpecifics
 * carries linear-encoding DNG tables, so no creative/global saturation rule exists here.  The
 * logical 3D table is flattened with x=saturation and y=value*hueDivisions+hue.
 */
vec3 iris26628RgbToHsv(vec3 rgb) {
    float maxValue=max(rgb.r,max(rgb.g,rgb.b));
    float minValue=min(rgb.r,min(rgb.g,rgb.b));
    float delta=maxValue-minValue;
    float hue=0.0;
    if(delta>1.0e-6){
        if(maxValue==rgb.r) hue=mod((rgb.g-rgb.b)/delta,6.0);
        else if(maxValue==rgb.g) hue=((rgb.b-rgb.r)/delta)+2.0;
        else hue=((rgb.r-rgb.g)/delta)+4.0;
    }
    if(hue<0.0)hue+=6.0;
    return vec3(hue,maxValue>1.0e-6?delta/maxValue:0.0,maxValue);
}
vec3 iris26628HsvToRgb(vec3 hsv) {
    float hue=mod(hsv.x,6.0); if(hue<0.0)hue+=6.0;
    float sat=max(hsv.y,0.0), value=max(hsv.z,0.0);
    float chroma=value*sat;
    float x=chroma*(1.0-abs(mod(hue,2.0)-1.0));
    vec3 rgb;
    if(hue<1.0)rgb=vec3(chroma,x,0.0);
    else if(hue<2.0)rgb=vec3(x,chroma,0.0);
    else if(hue<3.0)rgb=vec3(0.0,chroma,x);
    else if(hue<4.0)rgb=vec3(0.0,x,chroma);
    else if(hue<5.0)rgb=vec3(x,0.0,chroma);
    else rgb=vec3(chroma,0.0,x);
    return rgb+vec3(value-chroma);
}
vec3 iris26628TableFetch(sampler2D tableTex,int sat,int hue,int value,int hueDivisions){
    return texelFetch(tableTex,ivec2(sat,value*hueDivisions+hue),0).rgb;
}
vec3 iris26628SampleMap(sampler2D tableTex,int hDiv,int sDiv,int vDiv,vec3 hsv){
    if(hDiv<=0||sDiv<=0||vDiv<=0)return vec3(0.0,1.0,1.0);
    float hScaled=hsv.x*float(hDiv)/6.0;
    float sScaled=clamp(hsv.y,0.0,1.0)*float(max(sDiv-1,0));
    float vScaled=clamp(hsv.z,0.0,1.0)*float(max(vDiv-1,0));
    int h0=int(floor(hScaled)); int h1=h0+1;
    if(h0>=hDiv-1){h0=hDiv-1;h1=0;}
    int s0=min(int(floor(sScaled)),max(sDiv-2,0)); int s1=min(s0+1,sDiv-1);
    int v0=min(int(floor(vScaled)),max(vDiv-2,0)); int v1=min(v0+1,vDiv-1);
    float hf=hScaled-float(h0),sf=sScaled-float(s0),vf=vScaled-float(v0);
    vec3 p000=iris26628TableFetch(tableTex,s0,h0,v0,hDiv);
    vec3 p001=iris26628TableFetch(tableTex,s0,h1,v0,hDiv);
    vec3 p010=iris26628TableFetch(tableTex,s1,h0,v0,hDiv);
    vec3 p011=iris26628TableFetch(tableTex,s1,h1,v0,hDiv);
    if(vDiv>1){
        p000=mix(p000,iris26628TableFetch(tableTex,s0,h0,v1,hDiv),vf);
        p001=mix(p001,iris26628TableFetch(tableTex,s0,h1,v1,hDiv),vf);
        p010=mix(p010,iris26628TableFetch(tableTex,s1,h0,v1,hDiv),vf);
        p011=mix(p011,iris26628TableFetch(tableTex,s1,h1,v1,hDiv),vf);
    }
    return mix(mix(p000,p001,hf),mix(p010,p011,hf),sf);
}
vec3 iris26628ApplyMap(vec3 color,sampler2D tableTex,int hDiv,int sDiv,int vDiv){
    /* Never independently clip a negative profile-space component.  Such edge excursions bypass
     * the nonlinear profile map and remain linear until the proven common-axis gamut floor below. */
    if(min(color.r,min(color.g,color.b))<0.0)return color;
    vec3 hsv=iris26628RgbToHsv(color);
    vec3 modify=iris26628SampleMap(tableTex,hDiv,sDiv,vDiv,hsv);
    hsv.x=mod(hsv.x+modify.x*6.0/360.0,6.0); if(hsv.x<0.0)hsv.x+=6.0;
    hsv.y=clamp(hsv.y*modify.y,0.0,1.0);
    /* DNG profile tables are defined on [0,1].  Preserve Iris HDR headroom above 1 instead of
     * clipping it: lookup clamps to the profile boundary while value scaling extends linearly. */
    hsv.z=max(hsv.z*modify.z,0.0);
    return iris26628HsvToRgb(hsv);
}


/* IRIS_26638_DEFAULT_ACR3_COLOR_RENDER_OWNER
 * Faithful max/mid/min RGB relationship from bjzhou default AdobeCurve. The sampled curve is
 * exact and linearly interpolated; values above 1 use the same end-slope continuation concept.
 * ACR3 owns photographic channel separation only: after profile->Display-P3 conversion the
 * original calibrated Display-P3 luminance is restored uniformly, so exposure/26635 tone remain
 * separate authorities. Negative profile/display excursions bypass this nonlinear color owner. */
float iris26638SampleAcr3(float value){
    if(acr3CurveSize<=1)return value;
    if(value>1.0){
        float y1=texelFetch(Acr3Curve,ivec2(acr3CurveSize-1,0),0).r;
        const float dx=0.001;
        float p=(1.0-dx)*float(acr3CurveSize-1);
        int i0=int(floor(p));
        int i1=min(i0+1,acr3CurveSize-1);
        float y0=mix(texelFetch(Acr3Curve,ivec2(i0,0),0).r,
                     texelFetch(Acr3Curve,ivec2(i1,0),0).r,p-float(i0));
        return y1+((y1-y0)/dx)*(value-1.0);
    }
    float p=clamp(value,0.0,1.0)*float(acr3CurveSize-1);
    int i0=int(floor(p));
    int i1=min(i0+1,acr3CurveSize-1);
    return mix(texelFetch(Acr3Curve,ivec2(i0,0),0).r,
               texelFetch(Acr3Curve,ivec2(i1,0),0).r,p-float(i0));
}
void iris26638AdobeRgbTone(inout float mx,inout float md,inout float mn){
    float oldMx=mx,oldMd=md,oldMn=mn;
    mx=iris26638SampleAcr3(oldMx);
    mn=iris26638SampleAcr3(oldMn);
    if(abs(oldMx-oldMn)<1.0e-6)md=mn;
    else md=mn+(mx-mn)*(oldMd-oldMn)/(oldMx-oldMn);
}
vec3 iris26638ApplyAcr3(vec3 color){
    float r=color.r,g=color.g,b=color.b;
    if(r>=g){
        if(g>b)iris26638AdobeRgbTone(r,g,b);
        else if(b>r)iris26638AdobeRgbTone(b,r,g);
        else if(b>g)iris26638AdobeRgbTone(r,b,g);
        else { r=iris26638SampleAcr3(r); g=iris26638SampleAcr3(g); b=g; }
    }else{
        if(r>=b)iris26638AdobeRgbTone(g,r,b);
        else if(b>g)iris26638AdobeRgbTone(b,g,r);
        else iris26638AdobeRgbTone(g,b,r);
    }
    return vec3(r,g,b);
}

void main(){
    ivec2 xy=ivec2(gl_FragCoord.xy);
    vec3 cameraRgb=max(texelFetch(InputBuffer,xy,0).rgb,vec3(0.0));
    /* IRIS_26653_HIGHLIGHT_TONE_DEFERRED_TO_FINAL_RENDER: cameraRgb unchanged here. */
    vec3 profileRgb=vec3(dot(sensorToProfileRow0,cameraRgb),dot(sensorToProfileRow1,cameraRgb),dot(sensorToProfileRow2,cameraRgb));
#if USE_PROFILE_HUESAT == 1
    profileRgb=iris26628ApplyMap(profileRgb,ProfileHueSatMap,profileHueDivisions,profileSatDivisions,profileValueDivisions);
#endif
#if USE_PROFILE_LOOK == 1
    profileRgb=iris26628ApplyMap(profileRgb,ProfileLookMap,lookHueDivisions,lookSatDivisions,lookValueDivisions);
#endif
    vec3 linearDisplayOriginal=vec3(dot(profileToSrgbRow0,profileRgb),dot(profileToSrgbRow1,profileRgb),dot(profileToSrgbRow2,profileRgb));
    vec3 linearDisplay=linearDisplayOriginal;
    if(acr3Enabled!=0
            && min(profileRgb.r,min(profileRgb.g,profileRgb.b))>=0.0
            && min(linearDisplayOriginal.r,min(linearDisplayOriginal.g,linearDisplayOriginal.b))>=0.0){
        vec3 renderedProfile=iris26638ApplyAcr3(profileRgb);
        vec3 renderedDisplay=vec3(dot(profileToSrgbRow0,renderedProfile),dot(profileToSrgbRow1,renderedProfile),dot(profileToSrgbRow2,renderedProfile));
        const vec3 displayP3Luma=vec3(0.22897456,0.69173852,0.07928691);
        float targetY=dot(linearDisplayOriginal,displayP3Luma);
        float renderedY=dot(renderedDisplay,displayP3Luma);
        if(targetY>=0.0 && renderedY>1.0e-8){
            linearDisplay=renderedDisplay*(targetY/renderedY);
            /* IRIS_26639_ACR3_CALIBRATED_CHROMA_FLOOR
             * ACR3 may reshape/enhance the calibrated color, but saturation=1.0 must never lose
             * channel separation that the DNG color solution already established. Restore only the
             * missing span around the same luminance-neutral axis; common-axis gamut safety remains
             * the sole negative-excursion owner below. */
            float baselineSpan=max(linearDisplayOriginal.r,max(linearDisplayOriginal.g,linearDisplayOriginal.b))
                    -min(linearDisplayOriginal.r,min(linearDisplayOriginal.g,linearDisplayOriginal.b));
            float renderedSpan=max(linearDisplay.r,max(linearDisplay.g,linearDisplay.b))
                    -min(linearDisplay.r,min(linearDisplay.g,linearDisplay.b));
            if(renderedSpan+1.0e-8<baselineSpan){
                if(renderedSpan>1.0e-8){
                    vec3 chroma=linearDisplay-vec3(targetY);
                    linearDisplay=vec3(targetY)+chroma*(baselineSpan/renderedSpan);
                }else{
                    linearDisplay=linearDisplayOriginal;
                }
            }
        }
    }
    /* Frozen pink/cyan-edge invariant: translate all channels together, never clip one channel. */
    float negativeFloor=min(linearDisplay.r,min(linearDisplay.g,linearDisplay.b));
    if(negativeFloor<0.0)linearDisplay-=vec3(negativeFloor);
    Output=max(linearDisplay,vec3(0.0));
}
