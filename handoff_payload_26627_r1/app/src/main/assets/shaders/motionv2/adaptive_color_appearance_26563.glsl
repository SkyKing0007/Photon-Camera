precision highp float;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
uniform float displayGain;
uniform float sceneWhite;
uniform int iris26598MotionPublication;
uniform float iris26623ToneBroadNearFraction;
uniform float iris26623ToneHardFraction;
uniform float iris26623ToneBaseSceneWhite;
uniform float iris26623ToneAdaptiveSceneWhite;
out vec3 Output;
#ifndef CALIBRATED_PROFILE
#define CALIBRATED_PROFILE 0
#endif

/*
 * IRIS_26563_UNIVERSAL_ADAPTIVE_COLOR_APPEARANCE
 *
 * Common extended linear-Display-P3 appearance stage. It must be able to increase weak legitimate
 * chroma, but may not invent color on neutrals, rotate hue, alter Display-P3 linear luminance,
 * amplify incoherent chroma noise, or create new clipped magenta/cyan subject borders.
 *
 * Colorfulness is changed only by scaling the center pixel's chroma vector around its own
 * luminance axis. Neighborhood samples are used exclusively as reliability/edge gates; they are
 * never mixed into the output pixel, so fabric/foliage/skin spatial detail is not blurred here.
 */

const vec3 LUMA_WEIGHTS = vec3(0.22897456, 0.69173852, 0.07928691);

float luminanceOf(vec3 rgb) {
    return dot(rgb, LUMA_WEIGHTS);
}

float maximumComponent(vec3 rgb) {
    return max(rgb.r, max(rgb.g, rgb.b));
}

ivec2 safePosition(ivec2 position, ivec2 imageSize) {
    return clamp(position, ivec2(0), imageSize - ivec2(1));
}

vec3 rgbAt(ivec2 position, ivec2 imageSize) {
    return max(texelFetch(InputBuffer, safePosition(position, imageSize), 0).rgb, vec3(0.0));
}

float componentGainLimit(float luminanceValue, float chromaValue) {
    if (chromaValue > 1.0e-7) {
        return max(1.0, (1.0 - luminanceValue) / chromaValue);
    }
    if (chromaValue < -1.0e-7) {
        return max(1.0, (0.0 - luminanceValue) / chromaValue);
    }
    return 4.0;
}

/* IRIS_26585_TONE_AWARE_HIGHLIGHT_CHROMA_PRESERVATION
 * 26584 creates real highlight headroom later in MotionV2Render. The previous appearance
 * safety test treated any pre-tone projected channel >=1 as out of gamut, which could suppress
 * legitimate warm chroma before the global scalar tone map had a chance to compress it safely.
 * Reproduce the exact 26584/26582 scalar shoulder here only as a safety predictor; this stage
 * still changes colorfulness solely along the center pixel's own chroma axis.
 */
float iris26585MapHeadroomGuide(float guide) {
    const float toneStart = 0.50;
    const float logShape = 6.0;
    const float outputExposureScale = 0.80;
    if (guide <= toneStart) return guide;
    float whitePoint = max(sceneWhite, toneStart + 0.05);
    float u = max((guide - toneStart) / max(whitePoint - toneStart, 1.0e-6), 0.0);
    float shaped;
    if (iris26598MotionPublication != 0) {
        /* IRIS_26598_TONE_AWARE_PREDICTOR_PARITY
         * Predict the exact successful-26597 Motion publication curve. The old 26585 log endpoint
         * predictor otherwise treats sceneWhite as display white and can suppress legitimate
         * highlight chroma that 26597 would safely retain. Literals are the exact V1.1 ESSL-safe
         * anchors used by motionv2/render.glsl.
         */
        const float sceneAnchor = 0.834284246;
        const float tailSlope = 5.03442907;
        if (u <= 1.0) {
            shaped = sceneAnchor * u;
        } else {
            shaped = 1.0 - (1.0 - sceneAnchor) / (1.0 + tailSlope * (u - 1.0));
        }
    } else {
        /* Night keeps the exact successful pre-26598 appearance predictor. */
        float x = clamp(u, 0.0, 1.0);
        shaped = log(1.0 + logShape * x) / log(1.0 + logShape);
    }
    float preScaleDisplayWhite = 1.0 / outputExposureScale;
    return toneStart + (preScaleDisplayWhite - toneStart) * shaped;
}

/* IRIS_26623_SCENE_ADAPTIVE_UPPER_TONE
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

float iris26623LegacyMap(float sourceGuide){
    float x=max(sourceGuide,0.0);
    float requested=max(displayGain,1.0e-6)*0.80;
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
    float requested=max(displayGain,1.0e-6)*0.80;
    float legacy=iris26623LegacyMap(x);
    float adaptiveEnable=smoothstep(1.05,1.25,requested);
    const float upperStart=0.65;
    if(adaptiveEnable<=1.0e-7 || x<=upperStart) return legacy;

    float pressure=iris26623HighlightPressure();
    float targetWhite=mix(0.925,0.885,pressure);
    float targetSlope=mix(0.270,0.200,pressure);
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


float iris26585PostTonePreGamutPeak(vec3 preDisplayRgb) {
    const float outputExposureScale = 0.80;
    vec3 sourceRgb=max(preDisplayRgb,vec3(0.0));
    float sourceLuma=max(luminanceOf(sourceRgb),0.0);
    float sourcePeak=maximumComponent(sourceRgb);
    float sourceGuide=max(sourceLuma,sourcePeak);
    if(sourceGuide<=1.0e-7) return 0.0;
    if(iris26598MotionPublication!=0){
        float mappedFinal=iris26623MapMotionSdrFinalGuide(sourceGuide);
        return sourcePeak*(mappedFinal/sourceGuide);
    }
    vec3 postRgb=sourceRgb*max(displayGain,1.0e-6);
    float postLuma=max(luminanceOf(postRgb),0.0);
    float postPeak=maximumComponent(postRgb);
    float guide=max(postLuma,postPeak);
    float mappedGuide=iris26585MapHeadroomGuide(guide);
    return postPeak*(mappedGuide/guide)*outputExposureScale;
}

float iris26585ToneSafeHighlightGain(float centerLuma, vec3 centerChroma, float requestedGain) {
    float lo = 1.0;
    float hi = max(1.0, requestedGain);
    for (int iteration = 0; iteration < 7; ++iteration) {
        float mid = 0.5 * (lo + hi);
        vec3 candidate = vec3(centerLuma) + centerChroma * mid;
        if (iris26585PostTonePreGamutPeak(candidate) <= 0.995) lo = mid;
        else hi = mid;
    }
    return lo;
}

void main() {
    ivec2 position = ivec2(gl_FragCoord.xy);
    ivec2 imageSize = textureSize(InputBuffer, 0);
    vec3 centerRgb = rgbAt(position, imageSize);
#if CALIBRATED_PROFILE == 1
    Output = centerRgb;
    return;
#endif
    float centerLuma = luminanceOf(centerRgb);
    vec3 centerChroma = centerRgb - vec3(centerLuma);
    float centerChromaMagnitude = length(centerChroma);
    float relativeChroma = centerChromaMagnitude / max(centerLuma, 0.08);

    ivec2 offsets[4] = ivec2[4](
        ivec2(-1, 0), ivec2(1, 0), ivec2(0, -1), ivec2(0, 1));
    vec3 chromaSum = centerChroma;
    float chromaMagnitudeSum = centerChromaMagnitude;
    float maximumLumaDelta = 0.0;
    for (int index = 0; index < 4; ++index) {
        vec3 neighborRgb = rgbAt(position + offsets[index], imageSize);
        float neighborLuma = luminanceOf(neighborRgb);
        vec3 neighborChroma = neighborRgb - vec3(neighborLuma);
        chromaSum += neighborChroma;
        chromaMagnitudeSum += length(neighborChroma);
        maximumLumaDelta = max(maximumLumaDelta, abs(neighborLuma - centerLuma));
    }

    vec3 localMeanChroma = chromaSum / 5.0;
    float localMeanMagnitude = chromaMagnitudeSum / 5.0;
    float directionalCoherence = length(localMeanChroma) / max(localMeanMagnitude, 1.0e-6);
    float chromaDisagreement = length(centerChroma - localMeanChroma);

    /* Exact neutral carries no chroma to scale. Tiny chroma also stays below the activation ramp,
     * which prevents low-level color noise from being promoted as legitimate colorfulness.
     */
    float neutralActivation = smoothstep(0.0035, 0.018, centerChromaMagnitude);

    /* Preserve the successful weak-chroma restoration exactly. Profileless devices also need a
     * bounded appearance correction for coherent medium color after the colorimetric matrix solve.
     * The extra term starts before the OnePlus blue/yellow failure range, then fades before very
     * strong chroma so already-correct deep reds are not pushed further. It remains subject to the
     * exact existing shadow/highlight/edge/coherence/gamut gates below.
     */
    float chromaRolloff = 1.0 - smoothstep(0.08, 0.45, relativeChroma);
    float coherentColorActivation = smoothstep(0.18, 0.32, relativeChroma)
        * (1.0 - smoothstep(0.85, 1.25, relativeChroma));

    float positiveDisplayGain = max(displayGain, 1.0e-6);
    float projectedScale=iris26598MotionPublication!=0
        ? positiveDisplayGain*0.80 : positiveDisplayGain;
    float projectedLuma = centerLuma * projectedScale;
    float projectedPeak = maximumComponent(centerRgb) * projectedScale;
    float shadowGate = smoothstep(0.015, 0.075, projectedLuma);
    float highlightGate = 1.0 - smoothstep(0.72, 0.98, projectedPeak);

    /* Random/mottled chroma has low local directional coherence or disagrees with its local mean.
     * Strong luminance boundaries are protected so saturation cannot recreate colored subject
     * borders around clipped/high-contrast objects.
     */
    float coherenceGate = smoothstep(0.45, 0.82, directionalCoherence);
    float agreementGate = 1.0 - smoothstep(0.018, 0.085, chromaDisagreement);
    float edgeGate = 1.0 - smoothstep(
        0.025, 0.11, maximumLumaDelta * projectedScale);
    float reliability = coherenceGate * agreementGate * edgeGate;

    /* IRIS_26627_PROFILELESS_COHERENT_COLOR_RESTORE
     * Up to +20% additional medium-chroma appearance authority. Combined gain is still hard-capped
     * by the inherited 1.32x legacy bound and component gamut limit. Clipped/high-gradient bright
     * boundaries receive zero new authority through highlightGate * edgeGate * reliability.
     */
    float requestedGain = 1.0 + (0.32
        * neutralActivation
        * chromaRolloff + 0.20 * coherentColorActivation)
        * shadowGate
        * highlightGate
        * reliability;

    /* Preserve the exact <=26584 path as a floor. */
    float inputPeak = maximumComponent(centerRgb);
    float gamutGainLimit = 4.0;
    if (inputPeak >= 1.0 || projectedPeak >= 1.0) {
        gamutGainLimit = 1.0;
    } else {
        gamutGainLimit = min(gamutGainLimit, componentGainLimit(centerLuma, centerChroma.r));
        gamutGainLimit = min(gamutGainLimit, componentGainLimit(centerLuma, centerChroma.g));
        gamutGainLimit = min(gamutGainLimit, componentGainLimit(centerLuma, centerChroma.b));
    }
    float legacyChromaGain = clamp(min(requestedGain, gamutGainLimit), 1.0, 1.32);

    /* The added path exists only where the legacy highlight gate was suppressing an otherwise
     * reliable weak chroma vector. Exact neutrals remain neutral because neutralActivation is 0,
     * and no neighboring hue is ever copied. The gain is capped at 1.12x and then binary-limited
     * against the actual post-tone/pre-gamut peak, so the later renderer need not clip or whiten it.
     */
    float legacyHighlightSuppression = 1.0 - highlightGate;
    float basePostTonePeak = iris26585PostTonePreGamutPeak(centerRgb);
    float toneHeadroomGate = 1.0 - smoothstep(0.94, 0.995, basePostTonePeak);
    float highlightRequestedGain = 1.0 + 0.12
        * neutralActivation
        * chromaRolloff
        * shadowGate
        * legacyHighlightSuppression
        * reliability
        * toneHeadroomGate;
    float highlightFloorGainLimit = 4.0;
    if (centerChroma.r < -1.0e-7) highlightFloorGainLimit = min(
        highlightFloorGainLimit, (0.0 - centerLuma) / centerChroma.r);
    if (centerChroma.g < -1.0e-7) highlightFloorGainLimit = min(
        highlightFloorGainLimit, (0.0 - centerLuma) / centerChroma.g);
    if (centerChroma.b < -1.0e-7) highlightFloorGainLimit = min(
        highlightFloorGainLimit, (0.0 - centerLuma) / centerChroma.b);
    highlightRequestedGain = min(highlightRequestedGain, min(1.12, highlightFloorGainLimit));
    float toneSafeHighlightGain = iris26585ToneSafeHighlightGain(
        centerLuma, centerChroma, highlightRequestedGain);

    float adaptiveChromaGain = max(legacyChromaGain, toneSafeHighlightGain);
    if (adaptiveChromaGain <= 1.000001) {
        Output = centerRgb;
        return;
    }

    /* Scaling one chroma vector around its own Display-P3 luminance preserves that luminance and
     * preserves the chroma direction/hue. No neighboring color is mixed into the output.
     */
    Output = vec3(centerLuma) + centerChroma * adaptiveChromaGain;
}
