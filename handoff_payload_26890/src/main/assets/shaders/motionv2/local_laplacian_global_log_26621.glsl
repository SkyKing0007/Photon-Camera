precision highp float;
precision highp int;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
uniform float displayGain;
uniform float outputExposureScale;
uniform float iris26623ToneBroadNearFraction;
uniform float iris26623ToneHardFraction;
uniform float iris26623ToneBaseSceneWhite;
uniform float iris26623ToneAdaptiveSceneWhite;
uniform int iris26653HighlightCompressionEnabled;
uniform float iris26653HighlightKnee;
uniform float iris26653AdaptiveWhitePoint;
out float Output;

const vec3 IRIS_LUMA = vec3(0.22897456,0.69173852,0.07928691);
const float IRIS_LOG_FLOOR = 0.000244140625; /* 2^-12 */

float irisMax3(vec3 v){return max(v.r,max(v.g,v.b));}
float irisGuide(vec3 rgb){
    rgb=max(rgb,vec3(0.0));
    return max(dot(rgb,IRIS_LUMA),irisMax3(rgb));
}

/* IRIS_26632_SMOOTHER_UPPER_TONE
 * 26632 preserves the same pointwise/global owner and 0.65 entry but reserves more ordered SDR
 * range through source white. No spatial mask, edge boost, or local-protection change.
 *
 * IRIS_26623_SCENE_ADAPTIVE_UPPER_TONE
 * 26622 proved that the image-formation and Local-Laplacian architecture are sound, but two
 * very different scenes still crowded real HDR separation into the last few SDR code values.
 * Preserve the exact 26621/26622 mapping through source guide 0.65. Above that point, derive one
 * scene-wide highlight pressure from already-solved broad/hard ceiling occupancy plus the robust
 * adaptive/base scene-white ratio. This is not scene recognition: no sky/window/lamp semantics.
 * The upper body is a monotone C1 Hermite continuation and the >1 tail is a C1 rational shoulder.
 * Sparse highlights keep a high white anchor; broad HDR fields reserve more SDR range. */
float iris26623HighlightPressure(){
    float broad=smoothstep(0.015,0.060,clamp(iris26623ToneBroadNearFraction,0.0,1.0));
    float hard=smoothstep(0.010,0.050,clamp(iris26623ToneHardFraction,0.0,1.0));
    float baseWhite=max(iris26623ToneBaseSceneWhite,1.0);
    float adaptiveWhite=max(iris26623ToneAdaptiveSceneWhite,baseWhite);
    float span=max(adaptiveWhite/baseWhite-1.0,0.0);
    float spanPressure=smoothstep(0.08,0.35,span);
    return clamp(max(0.70*broad+0.30*spanPressure,0.75*hard),0.0,1.0);
}

void iris26623LegacyBody(float x,float requested,out float value,out float derivative){
    float whiteAnchor=min(0.95,requested);
    float bodyGain=requested;
    if(requested>whiteAnchor) bodyGain=min(requested,4.0*whiteAnchor-1.0e-4);
    float safeWhite=max(whiteAnchor,1.0e-6);
    float ratio=max(bodyGain/safeWhite-1.0,0.0);
    float oneMinus=1.0-x;
    float cubic=whiteAnchor*x+(bodyGain-whiteAnchor)*x*oneMinus*oneMinus;
    float rational=bodyGain*x/(1.0+ratio*x);
    float cubicDerivative=whiteAnchor+(bodyGain-whiteAnchor)*oneMinus*(1.0-3.0*x);
    float rationalDerivative=bodyGain/((1.0+ratio*x)*(1.0+ratio*x));
    value=0.5*(cubic+rational);
    derivative=0.5*(cubicDerivative+rationalDerivative);
}

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

float iris26623LegacyMap(float sourceGuide){
    float x=max(sourceGuide,0.0);
    float requested=max(displayGain,1.0e-6)*max(outputExposureScale,1.0e-6);
    float whiteAnchor=min(0.95,requested);
    float bodyGain=requested;
    if(requested>whiteAnchor) bodyGain=min(requested,4.0*whiteAnchor-1.0e-4);
    float safeWhite=max(whiteAnchor,1.0e-6);
    float ratio=max(bodyGain/safeWhite-1.0,0.0);
    if(x<=1.0){
        float value=0.0;
        float derivative=0.0;
        iris26623LegacyBody(x,requested,value,derivative);
        return value;
    }
    float rationalSlopeAtWhite=bodyGain/((1.0+ratio)*(1.0+ratio));
    float bodySlopeAtWhite=0.5*(whiteAnchor+rationalSlopeAtWhite);
    float reserve=max(1.0-whiteAnchor,0.0);
    if(reserve<=1.0e-6)return whiteAnchor;
    float tailScale=reserve/max(bodySlopeAtWhite,1.0e-6);
    float excess=x-1.0;
    return whiteAnchor+reserve*excess/(excess+tailScale);
}

float iris26623MapMotionSdrFinalGuide(float sourceGuide){
    float x=max(sourceGuide,0.0);
    float requested=max(displayGain,1.0e-6)*max(outputExposureScale,1.0e-6);
    float legacy=iris26623LegacyMap(x);
    float adaptiveEnable=smoothstep(1.05,1.25,requested);
    const float upperStart=0.65;
    if(adaptiveEnable<=1.0e-7 || x<=upperStart) return legacy;

    float pressure=iris26623HighlightPressure();
    float targetWhite=mix(0.945,0.925,pressure);
    float targetSlope=mix(0.360,0.300,pressure);
    float startValue=0.0;
    float startSlope=0.0;
    iris26623LegacyBody(upperStart,requested,startValue,startSlope);
    float width=1.0-upperStart;
    float secant=(targetWhite-startValue)/width;
    if(secant<=1.0e-6) return legacy;

    float m0=max(startSlope,0.0);
    float m1=max(targetSlope,0.0);
    float a=m0/secant;
    float b=m1/secant;
    float norm2=a*a+b*b;
    if(norm2>9.0){
        float limiter=3.0/sqrt(norm2);
        m0*=limiter;
        m1*=limiter;
    }

    float candidate;
    if(x<=1.0){
        float t=clamp((x-upperStart)/width,0.0,1.0);
        float t2=t*t;
        float t3=t2*t;
        float h00=2.0*t3-3.0*t2+1.0;
        float h10=t3-2.0*t2+t;
        float h01=-2.0*t3+3.0*t2;
        float h11=t3-t2;
        candidate=h00*startValue+h10*width*m0+h01*targetWhite+h11*width*m1;
    }else{
        float reserve=max(1.0-targetWhite,0.0);
        float tailScale=reserve/max(m1,1.0e-6);
        float excess=x-1.0;
        candidate=targetWhite+reserve*excess/(excess+tailScale);
    }
    return mix(legacy,candidate,adaptiveEnable);
}

/* IRIS_26653_SINGLE_FINAL_HIGHLIGHT_TONE
 * OFF is exact 26652. ON is applied only after brightnessTargetGain/displayGain is frozen.
 * Below source guide 0.65 the map is exactly OFF; above it one C1 monotone curve preserves
 * visible spacing of the real extended-linear >1.0 HDR master. */
float iris26653MapMotionSdrFinalGuide(float sourceGuide){
    float x=max(sourceGuide,0.0);
    float off=iris26623MapMotionSdrFinalGuide(x);
    if(iris26653HighlightCompressionEnabled==0 || x<=0.65)return off;
    float requested=max(displayGain,1.0e-6)*max(outputExposureScale,1.0e-6);
    float enable=smoothstep(1.05,1.25,requested);
    if(enable<=1.0e-7)return off;
    float scenePressure=iris26623HighlightPressure();
    float kneePressure=clamp((0.90-iris26653HighlightKnee)/(0.90-0.55),0.0,1.0);
    float pressure=max(scenePressure,kneePressure);
    float targetWhite=mix(0.915,0.890,pressure);
    float targetSlope=mix(0.090,0.055,pressure);
    const float startX=0.65;
    float startValue=0.0; float startSlope=0.0;
    iris26623LegacyBody(startX,requested,startValue,startSlope);
    float width=1.0-startX;
    float secant=(targetWhite-startValue)/width;
    if(secant<=1.0e-6)return off;
    float m0=max(startSlope,0.0);
    float m1=max(targetSlope,0.0);
    float a=m0/secant; float b=m1/secant;
    float norm2=a*a+b*b;
    if(norm2>9.0){float limiter=3.0/sqrt(norm2);m0*=limiter;m1*=limiter;}
    float candidate;
    if(x<=1.0){
        float t=clamp((x-startX)/width,0.0,1.0);
        float t2=t*t; float t3=t2*t;
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

void main(){
    ivec2 p=ivec2(gl_FragCoord.xy);
    float sourceGuide=irisGuide(texelFetch(InputBuffer,p,0).rgb);
    float mapped=iris26890BSourceToe(sourceGuide,iris26653MapMotionSdrFinalGuide(sourceGuide));
    Output=log2(max(mapped,IRIS_LOG_FLOOR));
}
