precision highp float;
precision highp int;
precision mediump sampler2D;
uniform sampler2D HdrBuffer;
uniform sampler2D SdrBuffer;
uniform ivec2 gainMapSize;
uniform float hdrExposureScale;
uniform float displayGain;
uniform int motionHdrHandoff;
uniform float maxGainRatio;
uniform float irisOutputZoom;
/* IRIS_26718_UHDR_HIGH_ZOOM_DETAIL_PARITY */
uniform sampler2D iris26718HighZoomDetail;
uniform int iris26718HighZoomDetailEnabled;
uniform vec2 iris26752PlanBDetailScale;
uniform vec2 iris26752PlanBDetailOrigin;
uniform sampler2D iris26621LocalToneLog;
uniform int iris26621LocalToneEnabled;
uniform float iris26623ToneBroadNearFraction;
uniform float iris26623ToneHardFraction;
uniform float iris26623ToneBaseSceneWhite;
uniform float iris26623ToneAdaptiveSceneWhite;
uniform int iris26653HighlightCompressionEnabled;
uniform float iris26653HighlightKnee;
uniform float iris26653AdaptiveWhitePoint;
uniform float iris26704BodyToneStrength;
/* IRIS_26524_UHDR_ZOOM_GEOMETRY_PARITY */
out float Output;

/* IRIS_26498_FULL_RESOLUTION_ULTRAHDR_GAIN_AUTHORITY_SUPERSEDED_26641
 * 26641 intentionally replaces the former one-gain-sample-per-primary-pixel geometry with a
 * half-linear-resolution Motion gain map. HDR and SDR intents are filtered in linear light at the
 * same source center before their quotient is formed; the completed gain field is never blurred
 * or dilated. The SDR image remains the exact spatial/color primary.
 */
const float UHDR_OFFSET = 0.015625;
float luminance(vec3 c){return dot(c,vec3(0.22897456,0.69173852,0.07928691));}
float max3(vec3 c){return max(c.r,max(c.g,c.b));}
/* IRIS_26890_B_ONLY_USER_EXPORTED_SHADOW_TOE
 * Frozen source: 26889 actual GLSL; derivatives/spline coordinates are computed
 * exactly from the user's exported HTML JSON, not hand-traced from a chart.
 * B ONLY, global guide 0..0.25. Static/exported EDITED-to-ORIGINAL ratio
 * rescales the actual scene-adaptive 26889 result; avoids assuming that the
 * HTML editor's approximate y-axis was the true compiled 26889 equation.
 * C1 blend reaches exact untouched 26889 response at source x=0.25.
 * The editor's 'compress' curve was UNCHANGED and is deliberately unchanged.
 * 'teal' is an unselected optional reference curve, not an invented auto mode.
 */
uniform int iris26890BToeEnabled;
float iris26890EditorOriginal_darker(float x){
    // Exact monotone cubic (Fritsch-Carlson/PCHIP) exported editor coefficients.
    if(x<=0.01){
        float t=clamp((x-0.0)/0.01,0.0,1.0);
        return ((-0.00235753526355*t+-0.00217579806978)*t+0.0305333333333)*t+0.0;
    }
    if(x<=0.025){
        float t=clamp((x-0.01)/0.015,0.0,1.0);
        return ((0.00528534071737*t+-0.011949037822)*t+0.0286636971047)*t+0.026;
    }
    if(x<=0.05){
        float t=clamp((x-0.025)/0.025,0.0,1.0);
        return ((0.000236072687822*t+-0.00260547870898)*t+0.0343694060212)*t+0.048;
    }
    if(x<=0.075){
        float t=clamp((x-0.05)/0.025,0.0,1.0);
        return ((-0.00149333333333*t+-0.000373333333333)*t+0.0298666666667)*t+0.08;
    }
    if(x<=0.1){
        float t=clamp((x-0.075)/0.025,0.0,1.0);
        return ((-0.00301714285714*t+0.000377142857143)*t+0.02464)*t+0.108;
    }
    if(x<=0.125){
        float t=clamp((x-0.1)/0.025,0.0,1.0);
        return ((0.00164720496894*t+-0.0049900621118)*t+0.0163428571429)*t+0.13;
    }
    if(x<=0.15){
        float t=clamp((x-0.125)/0.025,0.0,1.0);
        return ((0.00227995758218*t+-0.00358430540827)*t+0.0113043478261)*t+0.143;
    }
    if(x<=0.2){
        float t=clamp((x-0.15)/0.05,0.0,1.0);
        return ((0.0024199695122*t+0.00062881097561)*t+0.0219512195122)*t+0.153;
    }
    if(x<=0.25){
        float t=clamp((x-0.2)/0.05,0.0,1.0);
        return ((-0.00978931451613*t+0.0183205645161)*t+0.03046875)*t+0.178;
    }
    if(x<=0.32){
        float t=clamp((x-0.25)/0.07,0.0,1.0);
        return ((0.00707558248955*t+-0.00891429216697)*t+0.0528387096774)*t+0.217;
    }
    return 0.985;
}

float iris26890EditorEdited_darker(float x){
    // Exact monotone cubic (Fritsch-Carlson/PCHIP) exported editor coefficients.
    if(x<=0.027){
        float t=clamp((x-0.0)/0.027,0.0,1.0);
        return ((-0.000264552766529*t+-0.00250055712358)*t+0.0224651098901)*t+0.0;
    }
    if(x<=0.0504){
        float t=clamp((x-0.027)/0.0234,0.0,1.0);
        return ((0.00518316507548*t+-0.00703079077305)*t+0.0144476256976)*t+0.0197;
    }
    if(x<=0.0711){
        float t=clamp((x-0.0504)/0.0207,0.0,1.0);
        return ((-0.00565400927552*t+0.0104571859797)*t+0.0140968232958)*t+0.0323;
    }
    if(x<=0.1016){
        float t=clamp((x-0.0711)/0.0305,0.0,1.0);
        return ((0.000416837256523*t+-0.00171102114898)*t+0.0265941838925)*t+0.0512;
    }
    if(x<=0.1287){
        float t=clamp((x-0.1016)/0.0271,0.0,1.0);
        return ((0.00379200700302*t+-0.00449213507404)*t+0.021700128071)*t+0.0765;
    }
    if(x<=0.1472){
        float t=clamp((x-0.1287)/0.0185,0.0,1.0);
        return ((-0.0044198172045*t+0.00687333158672)*t+0.0164464856178)*t+0.0975;
    }
    if(x<=0.1728){
        float t=clamp((x-0.1472)/0.0256,0.0,1.0);
        return ((0.00470586580239*t+-0.00713844135641)*t+0.023432575554)*t+0.1164;
    }
    if(x<=0.2083){
        float t=clamp((x-0.1728)/0.0355,0.0,1.0);
        return ((-0.00451352976111*t+0.00894002179951)*t+0.0322735079616)*t+0.1374;
    }
    if(x<=0.25){
        float t=clamp((x-0.2083)/0.0417,0.0,1.0);
        return ((-0.00670051500831*t+0.00659317622062)*t+0.0430073387877)*t+0.1741;
    }
    if(x<=0.32){
        float t=clamp((x-0.25)/0.07,0.0,1.0);
        return ((0.0148232093656*t+-0.0244095459191)*t+0.0605863365535)*t+0.217;
    }
    return 0.985;
}

float iris26890EditorOriginal_brighter(float x){
    // Exact monotone cubic (Fritsch-Carlson/PCHIP) exported editor coefficients.
    if(x<=0.01){
        float t=clamp((x-0.0)/0.01,0.0,1.0);
        return ((-1.25786163522e-05*t+0.00134591194969)*t+0.00866666666667)*t+0.0;
    }
    if(x<=0.025){
        float t=clamp((x-0.01)/0.015,0.0,1.0);
        return ((-0.00462470734059*t+0.00764357526511)*t+0.0169811320755)*t+0.01;
    }
    if(x<=0.05){
        float t=clamp((x-0.025)/0.025,0.0,1.0);
        return ((0.00314816237674*t+-0.00580509668331)*t+0.0306569343066)*t+0.03;
    }
    if(x<=0.075){
        float t=clamp((x-0.05)/0.025,0.0,1.0);
        return ((-0.00729600597238*t+0.0078047779022)*t+0.0284912280702)*t+0.058;
    }
    if(x<=0.1){
        float t=clamp((x-0.075)/0.025,0.0,1.0);
        return ((0.00218459694336*t+-0.00639736290081)*t+0.0222127659574)*t+0.087;
    }
    if(x<=0.15){
        float t=clamp((x-0.1)/0.05,0.0,1.0);
        return ((-0.00141804015583*t+-0.002525621816)*t+0.0319436619718)*t+0.105;
    }
    if(x<=0.2){
        float t=clamp((x-0.15)/0.05,0.0,1.0);
        return ((0.00458829787234*t+-0.00822659574468)*t+0.0226382978723)*t+0.133;
    }
    if(x<=0.25){
        float t=clamp((x-0.2)/0.05,0.0,1.0);
        return ((0.00486610564474*t+-0.00381610564474)*t+0.01995)*t+0.152;
    }
    if(x<=0.32){
        float t=clamp((x-0.25)/0.07,0.0,1.0);
        return ((-0.0156029849063*t+0.0329204370036)*t+0.0376825479026)*t+0.173;
    }
    return 0.985;
}

float iris26890EditorEdited_brighter(float x){
    // Exact monotone cubic (Fritsch-Carlson/PCHIP) exported editor coefficients.
    if(x<=0.0263){
        float t=clamp((x-0.0)/0.0263,0.0,1.0);
        return ((-5.83868925969e-05*t+-0.00122622966768)*t+0.0146846165603)*t+0.0;
    }
    if(x<=0.049){
        float t=clamp((x-0.0263)/0.0227,0.0,1.0);
        return ((0.00122518120554*t+-0.0021317903926)*t+0.0104066091871)*t+0.0134;
    }
    if(x<=0.0817){
        float t=clamp((x-0.049)/0.0327,0.0,1.0);
        return ((0.00121904970035*t+-0.000662983841501)*t+0.0141439341412)*t+0.0229;
    }
    if(x<=0.113){
        float t=clamp((x-0.0817)/0.0313,0.0,1.0);
        return ((-0.00122773608162*t+0.00335797715187)*t+0.0157697589297)*t+0.0376;
    }
    if(x<=0.1429){
        float t=clamp((x-0.113)/0.0299,0.0,1.0);
        return ((0.0007277344229*t+0.000210767201372)*t+0.0179614983757)*t+0.0555;
    }
    if(x<=0.1735){
        float t=clamp((x-0.1429)/0.0306,0.0,1.0);
        return ((0.00144706554712*t+0.000605214618648)*t+0.0210477198342)*t+0.0744;
    }
    if(x<=0.209){
        float t=clamp((x-0.1735)/0.0355,0.0,1.0);
        return ((-0.00742511973608*t+0.0132664016705)*t+0.0308587180656)*t+0.0975;
    }
    if(x<=0.25){
        float t=clamp((x-0.209)/0.041,0.0,1.0);
        return ((-0.0015549215266*t+-0.000201772843271)*t+0.0405566943699)*t+0.1342;
    }
    if(x<=0.32){
        float t=clamp((x-0.25)/0.07,0.0,1.0);
        return ((0.00730439127028*t+-0.0128943153495)*t+0.0605899240792)*t+0.173;
    }
    return 0.985;
}
float iris26890BSourceToe(float sourceGuide,float originalMappedGuide){
    if(iris26890BToeEnabled==0 || iris26653HighlightCompressionEnabled!=0
        || sourceGuide<=0.0 || sourceGuide>=0.25)return originalMappedGuide;
    float x=sourceGuide;
    float fromDark=max(iris26890EditorOriginal_darker(x),1.0e-8);
    float fromBright=max(iris26890EditorOriginal_brighter(x),1.0e-8);
    float ratioDark=clamp(iris26890EditorEdited_darker(x)/fromDark,0.0,1.0);
    float ratioBright=clamp(iris26890EditorEdited_brighter(x)/fromBright,0.0,1.0);
    // Existing scene-dependent brightnessTargetGain is the only blend owner:
    // low representative displayGain (1.22) -> darker-scene user shape,
    // high representative displayGain (1.50) -> brighter-scene user shape.
    float blend=smoothstep(1.22,1.50,displayGain);
    float ratio=mix(ratioDark,ratioBright,blend);
    // Smoothly return the *actual 26889 equation*, not the editor trace.
    ratio=mix(ratio,1.0,smoothstep(0.20,0.25,x));
    return max(originalMappedGuide,0.0)*ratio;
}

float iris26640Smoothstep(float a,float b,float x){
    float t=clamp((x-a)/max(b-a,1.0e-6),0.0,1.0);
    return t*t*(3.0-2.0*t);
}
float iris26640HighlightPressure(){
    float broad=iris26640Smoothstep(0.015,0.060,clamp(iris26623ToneBroadNearFraction,0.0,1.0));
    float hard=iris26640Smoothstep(0.010,0.050,clamp(iris26623ToneHardFraction,0.0,1.0));
    float baseWhite=max(iris26623ToneBaseSceneWhite,1.0);
    float adaptiveWhite=max(iris26623ToneAdaptiveSceneWhite,baseWhite);
    float span=max(adaptiveWhite/baseWhite-1.0,0.0);
    float spanPressure=iris26640Smoothstep(0.08,0.35,span);
    return clamp(max(0.70*broad+0.30*spanPressure,0.75*hard),0.0,1.0);
}
void iris26640LegacyBody(float x,float requested,out float value,out float derivative){
    float whiteAnchor=min(0.95,requested);
    float bodyGain=requested;
    if(requested>whiteAnchor)bodyGain=min(requested,4.0*whiteAnchor-1.0e-4);
    float safeWhite=max(whiteAnchor,1.0e-6);
    float shoulderRatio=max(bodyGain/safeWhite-1.0,0.0);
    float oneMinus=1.0-x;
    float cubic=whiteAnchor*x+(bodyGain-whiteAnchor)*x*oneMinus*oneMinus;
    float rational=bodyGain*x/(1.0+shoulderRatio*x);
    float cubicDerivative=whiteAnchor+(bodyGain-whiteAnchor)*oneMinus*(1.0-3.0*x);
    float rationalDerivative=bodyGain/((1.0+shoulderRatio*x)*(1.0+shoulderRatio*x));
    value=0.5*(cubic+rational);
    derivative=0.5*(cubicDerivative+rationalDerivative);
}
float iris26640LegacyMap(float sourceGuide){
    float x=max(sourceGuide,0.0);
    float requested=max(displayGain,1.0e-6)*hdrExposureScale;
    float whiteAnchor=min(0.95,requested);
    float bodyGain=requested;
    if(requested>whiteAnchor)bodyGain=min(requested,4.0*whiteAnchor-1.0e-4);
    float safeWhite=max(whiteAnchor,1.0e-6);
    float shoulderRatio=max(bodyGain/safeWhite-1.0,0.0);
    if(x<=1.0){
        float value=0.0; float derivative=0.0;
        iris26640LegacyBody(x,requested,value,derivative);
        return value;
    }
    float rationalSlope=bodyGain/((1.0+shoulderRatio)*(1.0+shoulderRatio));
    float bodySlope=0.5*(whiteAnchor+rationalSlope);
    float reserve=max(1.0-whiteAnchor,0.0);
    if(reserve<=1.0e-6)return whiteAnchor;
    float tailScale=reserve/max(bodySlope,1.0e-6);
    float excess=x-1.0;
    return whiteAnchor+reserve*excess/(excess+tailScale);
}
float iris26640MapMotionSdrGuide(float sourceGuide){
    float x=max(sourceGuide,0.0);
    float requested=max(displayGain,1.0e-6)*hdrExposureScale;
    float legacy=iris26640LegacyMap(x);
    float adaptiveEnable=iris26640Smoothstep(1.05,1.25,requested);
    const float upperStart=0.65;
    if(adaptiveEnable<=1.0e-7 || x<=upperStart)return legacy;
    float pressure=iris26640HighlightPressure();
    /* IRIS_26706_VISUAL_HIGHLIGHT_SPACING
     * 26705 proved that broad visually flattened highlights can cluster at nominal source white
     * even when hard sensor clipping is not the deciding condition. Preserve the exact mapping
     * through source guide 0.65, but for broad highlight pressure reserve more SDR code space above
     * nominal white and increase (rather than decrease) the C1 source-white slope. This remains one
     * global pointwise monotone scalar: no spatial mask, no semantic scene class, no SHORT ownership
     * change, and no channel-dependent operation. */
    float targetWhite=mix(0.945,0.895,pressure);
    float targetSlope=mix(0.360,0.620,pressure);
    float startValue=0.0; float startSlope=0.0;
    iris26640LegacyBody(upperStart,requested,startValue,startSlope);
    float width=1.0-upperStart;
    float secant=(targetWhite-startValue)/width;
    if(secant<=1.0e-6)return legacy;
    float m0=max(startSlope,0.0);
    float m1=max(targetSlope,0.0);
    float a=m0/secant; float b=m1/secant;
    float norm2=a*a+b*b;
    if(norm2>9.0){float limiter=3.0/sqrt(norm2);m0*=limiter;m1*=limiter;}
    float candidate;
    if(x<=1.0){
        float t=clamp((x-upperStart)/width,0.0,1.0);
        float t2=t*t; float t3=t2*t;
        candidate=(2.0*t3-3.0*t2+1.0)*startValue
            +(t3-2.0*t2+t)*width*m0
            +(-2.0*t3+3.0*t2)*targetWhite
            +(t3-t2)*width*m1;
    }else{
        float reserve=max(1.0-targetWhite,0.0);
        float tailScale=reserve/max(m1,1.0e-6);
        float excess=x-1.0;
        candidate=targetWhite+reserve*excess/(excess+tailScale);
    }
    return mix(legacy,candidate,adaptiveEnable);
}

/* IRIS_26653_UHDR_SHARED_FINAL_SDR_TONE
 * Gain-map intent must model the exact same completed SDR global tone as MotionV2Render. */
float iris26653MapMotionSdrGuide(float sourceGuide){
    float x=max(sourceGuide,0.0);
    float off=iris26640MapMotionSdrGuide(x);
    if(iris26653HighlightCompressionEnabled==0 || x<=0.65)return off;
    float requested=max(displayGain,1.0e-6)*hdrExposureScale;
    float enable=iris26640Smoothstep(1.05,1.25,requested);
    if(enable<=1.0e-7)return off;
    float scenePressure=iris26640HighlightPressure();
    float kneePressure=clamp((0.90-iris26653HighlightKnee)/(0.90-0.55),0.0,1.0);
    float pressure=max(scenePressure,kneePressure);
    float targetWhite=mix(0.915,0.890,pressure);
    float targetSlope=mix(0.090,0.055,pressure);
    const float startX=0.65;
    float startValue=0.0; float startSlope=0.0;
    iris26640LegacyBody(startX,requested,startValue,startSlope);
    float width=1.0-startX;
    float secant=(targetWhite-startValue)/width;
    if(secant<=1.0e-6)return off;
    float m0=max(startSlope,0.0); float m1=max(targetSlope,0.0);
    float a=m0/secant; float b=m1/secant; float norm2=a*a+b*b;
    if(norm2>9.0){float limiter=3.0/sqrt(norm2);m0*=limiter;m1*=limiter;}
    float candidate;
    if(x<=1.0){
        float t=clamp((x-startX)/width,0.0,1.0); float t2=t*t; float t3=t2*t;
        candidate=(2.0*t3-3.0*t2+1.0)*startValue
            +(t3-2.0*t2+t)*width*m0
            +(-2.0*t3+3.0*t2)*targetWhite
            +(t3-t2)*width*m1;
    }else{
        float reserve=max(1.0-targetWhite,0.0);
        float whiteSpan=max(1.0,sqrt(max(iris26653AdaptiveWhitePoint,1.0)));
        float tailScale=reserve/max(m1,1.0e-6)*whiteSpan;
        float excess=x-1.0;
        candidate=targetWhite+reserve*excess/(excess+tailScale);
    }
    return mix(off,candidate,enable);
}
/* IRIS_26660_OBJECT_COLOR_GAMMA
 * IRIS_26671_UPPER_GAMMA_RELEASE
 * Exact SDR mirror of MotionV2Render. No spatial sampling/threshold is introduced here.
 * The corrected SDR denominator is gamma-shaped while the HDR numerator below remains on the
 * exact successful-26658 local-structure target, preserving the existing UHDR brightness pop. */
float iris26660ObjectColorGamma(float mappedGuide){
    float y=max(mappedGuide,0.0);
    if(motionHdrHandoff==0 || iris26653HighlightCompressionEnabled==0) return y;
    const float gammaValue=2.50;
    const float influencePower=6.0;
    const float whiteScale=0.90;
    float gammaOwned;
    if(y<=1.0){
        float w=pow(clamp(y,0.0,1.0),influencePower);
        float gammaMapped=whiteScale*pow(max(y,1.0e-8),gammaValue);
        gammaOwned=mix(y,gammaMapped,w);
    }else{
        const float endSlope=influencePower*(whiteScale-1.0)+whiteScale*gammaValue;
        gammaOwned=whiteScale+(y-1.0)*endSlope;
    }

    /* IRIS_26671_SINGLE_HIGHLIGHT_LUMINANCE_OWNER
     * 26670 proved that SHORT recovers real extended-linear highlight separation, while the
     * completed 26653 highlight tone and the later 26660 object-color gamma both compressed the
     * same upper display range. Preserve exact 26670 behavior through mapped linear guide 0.78.
     * Above that true-highlight boundary, release only the second gamma compression with a C1
     * smoothstep until mapped white, leaving the already-completed 26653 tone as the sole upper
     * luminance owner. No spatial sample, local mask, semantic scene class, or channel-dependent
     * operation is introduced; RGB remains uniformly scaled by the caller and hue stays unchanged.
     */
    const float releaseStart=0.78;
    if(y<=releaseStart) return gammaOwned;
    if(y>=1.0) return y;
    float t=clamp((y-releaseStart)/(1.0-releaseStart),0.0,1.0);
    float release=t*t*(3.0-2.0*t);
    return mix(gammaOwned,y,release);
}

float iris26640SharedSdrGuide(float sourceGuide,vec2 masterSourcePixel){
    float globalMapped=iris26890BSourceToe(sourceGuide,iris26653MapMotionSdrGuide(sourceGuide));
    if(iris26621LocalToneEnabled==0)return globalMapped;
    vec2 toneSize=vec2(textureSize(iris26621LocalToneLog,0));
    vec2 uv=(masterSourcePixel+vec2(0.5))/max(toneSize,vec2(1.0));
    vec2 halfTexel=vec2(0.5)/max(toneSize,vec2(1.0));
    float localLog=texture(iris26621LocalToneLog,clamp(uv,halfTexel,vec2(1.0)-halfTexel)).r;
    float localMapped=exp2(clamp(localLog,-12.0,0.0));
    float localStrength=smoothstep(0.030,0.100,globalMapped);
    return mix(globalMapped,localMapped,localStrength);
}
uniform float iris26792SdrBodyContrast;

/* IRIS_26824_ADAPTIVE_BODY_S_CURVE_GAINMAP_MIRROR
 * Mirror only the new negative 26824 branch in the SDR denominator. Existing positive 26704
 * local-tone/gain-map behavior is deliberately not broadened. */
float iris26824AdaptiveBodySGuide(float mappedGuide){
    float y=max(mappedGuide,0.0);
    float strength=clamp(-iris26704BodyToneStrength,0.0,1.0);
    if(strength<=1.0e-7 || y<=0.0)return y;
    float lowGate=smoothstep(0.055,0.180,y);
    float highGate=1.0-smoothstep(0.500,0.760,y);
    float bodyWeight=clamp(lowGate*highGate,0.0,1.0);
    return mix(y,y*y,0.24*strength*bodyWeight);
}

/* IRIS_26770_MIDTONE_PRESENTATION_TRIM_GAINMAP_MIRROR
 * Exact pointwise mirror of render.glsl so the UHDR quotient uses the published SDR appearance
 * as its denominator. HDR target ownership is unchanged. */
/* IRIS_26783_SDR_BODY_CONTRAST_UHDR_REBASE
 * Strengthen only the finished SDR body's pointwise luminance separation. Exact black/deep-shadow
 * identity extends through 0.10 and upper/highlight identity remains from 0.78. The gain-map shader
 * carries this exact same function, so the decoded UHDR target remains owned by the frozen matched
 * HDR intent while the SDR denominator changes. */
float iris26770MidtonePresentationTrim(float mappedGuide){
    float y=max(mappedGuide,0.0);
    float low=smoothstep(0.10,0.24,y);
    float high=1.0-smoothstep(0.50,0.78,y);
    float w=clamp(low*high,0.0,1.0);
    return mix(y,y*y,clamp(iris26792SdrBodyContrast,0.0,0.35)*w);
}
float iris26660SharedSdrGuide(float sourceGuide,vec2 masterSourcePixel){
    float sharedSdr=iris26640SharedSdrGuide(sourceGuide,masterSourcePixel);
    sharedSdr=iris26824AdaptiveBodySGuide(sharedSdr);
    return iris26770MidtonePresentationTrim(iris26660ObjectColorGamma(sharedSdr));
}
float srgbDecode(float x){x=clamp(x,0.0,1.0);return x<=0.04045?x/12.92:pow((x+0.055)/1.055,2.4);}
vec3 srgbDecode(vec3 c){return vec3(srgbDecode(c.r),srgbDecode(c.g),srgbDecode(c.b));}


vec3 iris26524BilinearHdr(vec2 sourcePixel){
    ivec2 sz=textureSize(HdrBuffer,0);
    vec2 hi=max(vec2(sz)-vec2(1.0),vec2(0.0));
    vec2 q=clamp(sourcePixel,vec2(0.0),hi);
    ivec2 p0=ivec2(floor(q));
    ivec2 p1=min(p0+ivec2(1),sz-ivec2(1));
    vec2 f=fract(q);
    vec3 a=mix(texelFetch(HdrBuffer,ivec2(p0.x,p0.y),0).rgb,
               texelFetch(HdrBuffer,ivec2(p1.x,p0.y),0).rgb,f.x);
    vec3 b=mix(texelFetch(HdrBuffer,ivec2(p0.x,p1.y),0).rgb,
               texelFetch(HdrBuffer,ivec2(p1.x,p1.y),0).rgb,f.x);
    return mix(a,b,f.y);
}
/* IRIS_26550_GAINMAP_GENERAL_GEOMETRY
 * Motion and Night may request detached lower-resolution gain maps. Map every gain pixel back to
 * the corresponding full-resolution SDR/HDR pixel center instead of accidentally reading only a
 * top-left fraction of the image. Motion adds 26641 linear-light matched pre-divide filtering.
 */
vec3 iris26550BilinearSdr(vec2 sourcePixel){
    ivec2 sz=textureSize(SdrBuffer,0);
    vec2 hi=max(vec2(sz)-vec2(1.0),vec2(0.0));
    vec2 q=clamp(sourcePixel,vec2(0.0),hi);
    ivec2 p0=ivec2(floor(q));
    ivec2 p1=min(p0+ivec2(1),sz-ivec2(1));
    vec2 f=fract(q);
    vec3 a=mix(texelFetch(SdrBuffer,ivec2(p0.x,p0.y),0).rgb,
               texelFetch(SdrBuffer,ivec2(p1.x,p0.y),0).rgb,f.x);
    vec3 b=mix(texelFetch(SdrBuffer,ivec2(p0.x,p1.y),0).rgb,
               texelFetch(SdrBuffer,ivec2(p1.x,p1.y),0).rgb,f.x);
    return mix(a,b,f.y);
}
/* IRIS_26641_LINEAR_LIGHT_SDR_PREDIVIDE_DOWNSAMPLE
 * Motion's half-resolution gain map averages decoded SDR radiance before dividing by the matched
 * HDR intent. At an exact 2x reduction the bilinear center sample is a 2x2 linear-light box.
 * Night deliberately keeps the pre-26641 encoded-bilinear/decode behavior. */
vec3 iris26641BilinearSdrLinear(vec2 sourcePixel){
    ivec2 sz=textureSize(SdrBuffer,0);
    vec2 hi=max(vec2(sz)-vec2(1.0),vec2(0.0));
    vec2 q=clamp(sourcePixel,vec2(0.0),hi);
    ivec2 p0=ivec2(floor(q));
    ivec2 p1=min(p0+ivec2(1),sz-ivec2(1));
    vec2 f=fract(q);
    vec3 a=mix(srgbDecode(texelFetch(SdrBuffer,ivec2(p0.x,p0.y),0).rgb),
               srgbDecode(texelFetch(SdrBuffer,ivec2(p1.x,p0.y),0).rgb),f.x);
    vec3 b=mix(srgbDecode(texelFetch(SdrBuffer,ivec2(p0.x,p1.y),0).rgb),
               srgbDecode(texelFetch(SdrBuffer,ivec2(p1.x,p1.y),0).rgb),f.x);
    return mix(a,b,f.y);
}
float iris26718HighZoomLogDetail(vec2 sourcePixel){
    if(iris26718HighZoomDetailEnabled==0)return 0.0;
    /* IRIS_26752_IPOL_PLAN_B_NONINTEGER_SAMPLE
     * Preserve the paper's arbitrary continuous output lattice instead of snapping Plan B to
     * the retired fixed true-2x direct-CFA lattice. */
    vec2 local=sourcePixel*iris26752PlanBDetailScale-iris26752PlanBDetailOrigin;
    ivec2 sz=textureSize(iris26718HighZoomDetail,0);
    if(any(lessThan(local,vec2(0.0)))||any(greaterThan(local,vec2(sz)-vec2(1.0))))return 0.0;
    /* IRIS_26834_UNIVERSAL_HIGH_ZOOM_VISIBLE_CROP_GUARD
     * High-zoom detail is never trusted near its reconstruction boundary. The producer reserves
     * a 32-texel target halo per side; keep the outer 16 texels at exact native Sabre/VGN and
     * transition only from 16..24. Thus a visible 30x/120x crop cannot magnify edge uncertainty
     * into barcode stripes. This rule is zoom-independent for every high-zoom detail route. */
    vec2 edgeDistance=min(local,vec2(sz)-vec2(1.0)-local);
    float minEdge=min(edgeDistance.x,edgeDistance.y);
    if(minEdge<=16.0)return 0.0;
    float trustedInterior=smoothstep(16.0,24.0,minEdge);
    vec2 uv=(local+vec2(0.5))/vec2(sz);
    return clamp(texture(iris26718HighZoomDetail,uv).r,-0.56,0.56)*trustedInterior;
}

void main(){
    ivec2 p=ivec2(gl_FragCoord.xy);
    if(any(greaterThanEqual(p,gainMapSize))){Output=0.0;return;}
    float zoom=max(irisOutputZoom,1.0);
    ivec2 sdrSize=textureSize(SdrBuffer,0);
    vec2 sourcePixel=(vec2(p)+vec2(0.5))*vec2(sdrSize)/vec2(gainMapSize)-vec2(0.5);
    vec2 masterSourcePixel=sourcePixel;
    vec3 hdrRgb;
    if(zoom<=1.00001){
        hdrRgb=iris26524BilinearHdr(masterSourcePixel);
    }else{
        ivec2 hdrSize=textureSize(HdrBuffer,0);
        vec2 center=(vec2(hdrSize)-vec2(1.0))*0.5;
        masterSourcePixel=center+(sourcePixel-center)/zoom;
        hdrRgb=iris26524BilinearHdr(masterSourcePixel);
    }
    if(iris26718HighZoomDetailEnabled!=0){
        hdrRgb=max(hdrRgb*exp2(iris26718HighZoomLogDetail(masterSourcePixel)),vec3(0.0));
    }
    vec3 hdrPositive=max(hdrRgb,vec3(0.0));
    float sdr=motionHdrHandoff!=0
        ? max(luminance(iris26641BilinearSdrLinear(sourcePixel)),0.0)
        : max(luminance(srgbDecode(iris26550BilinearSdr(sourcePixel))),0.0);
    float safeMax=max(maxGainRatio,1.001);
    float ratio;
    if(motionHdrHandoff!=0){
        /* IRIS_26641_TRUE_MATCHED_SDR_HDR_INTENT_QUOTIENT
         * Both intents come from the same canonical extended-linear Motion master, same source
         * sample, same 26623 global tone prerequisites, and the same Local-Laplacian structure.
         * There is no luma eligibility threshold and no spatial gain dilation. The HDR intent
         * departs from SDR only by the amount that the SDR rendition is actually compressing the
         * shared linear-light target; weak body compression therefore collapses naturally to unity
         * while broad real highlight compression participates coherently. */
        float sourceY=max(luminance(hdrPositive),0.0);
        float sourceGuide=max(sourceY,max3(hdrPositive));
        if(sourceGuide<=1.0e-7 || sourceY<=1.0e-9){
            ratio=1.0;
        }else{
            float globalSdrGuide=max(iris26653MapMotionSdrGuide(sourceGuide),0.0);
            float sharedSdrGuide26658=max(iris26640SharedSdrGuide(sourceGuide,masterSourcePixel),0.0);
            float sharedSdrGuide=max(iris26660SharedSdrGuide(sourceGuide,masterSourcePixel),0.0);
            /* IRIS_26660_UHDR_POP_TARGET_FROZEN_TO_26658
             * Preserve the exact 26658 HDR target/local-structure scale. Only the SDR denominator
             * uses the smooth object-color gamma, so the decoded HDR brightness target stays 26658. */
            float localStructureScale=globalSdrGuide>1.0e-7
                ? sharedSdrGuide26658/globalSdrGuide : 1.0;
            float requested=max(displayGain,1.0e-6)*hdrExposureScale;
            float sdrModelY=sourceY*(sharedSdrGuide/sourceGuide);
            float linearTargetY=sourceY*requested*max(localStructureScale,0.0);
            /* IRIS_26641_TRUE_MATCHED_INTENT_DELTA
             * The HDR rendition differs from the completed SDR rendition by the full luminance
             * that the matched SDR model compressed away. 26640 multiplied this delta by the
             * compression fraction a second time, effectively squaring moderate compression and
             * under-restoring scenes such as the plant shelf. Keep the actual completed SDR as
             * the spatial/color base and restore the full matched-intent delta exactly once. */
            float matchedIntentDelta=max(linearTargetY-sdrModelY,0.0);
            float hdrIntentY=sdr+matchedIntentDelta;
            ratio=clamp((hdrIntentY+UHDR_OFFSET)/(sdr+UHDR_OFFSET),1.0,safeMax);
        }
    }else{
        float hdrTargetScale=hdrExposureScale;
        float hdr=max(luminance(hdrPositive*hdrTargetScale),0.0);
        ratio=clamp((hdr+UHDR_OFFSET)/(sdr+UHDR_OFFSET),1.0,safeMax);
    }
    Output=clamp(log2(ratio)/max(log2(safeMax),1.0e-6),0.0,1.0);
}
