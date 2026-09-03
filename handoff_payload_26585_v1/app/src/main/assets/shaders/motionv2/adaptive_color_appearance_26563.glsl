precision highp float;
precision mediump sampler2D;

uniform sampler2D InputBuffer;
uniform float displayGain;
uniform float sceneWhite;
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
    float x = clamp((guide - toneStart) / max(whitePoint - toneStart, 1.0e-6), 0.0, 1.0);
    float shaped = log(1.0 + logShape * x) / log(1.0 + logShape);
    float preScaleDisplayWhite = 1.0 / outputExposureScale;
    return toneStart + (preScaleDisplayWhite - toneStart) * shaped;
}

float iris26585PostTonePreGamutPeak(vec3 preDisplayRgb) {
    const float outputExposureScale = 0.80;
    vec3 postRgb = max(preDisplayRgb, vec3(0.0)) * max(displayGain, 1.0e-6);
    float postLuma = max(luminanceOf(postRgb), 0.0);
    float postPeak = maximumComponent(postRgb);
    float guide = max(postLuma, postPeak);
    if (guide <= 1.0e-7) return 0.0;
    float mappedGuide = iris26585MapHeadroomGuide(guide);
    return postPeak * (mappedGuide / guide) * outputExposureScale;
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

    /* Weak legitimate color receives the most restoration. Medium chroma rapidly rolls off and
     * already-strong chroma receives no meaningful additional gain.
     */
    float chromaRolloff = 1.0 - smoothstep(0.08, 0.45, relativeChroma);

    float positiveDisplayGain = max(displayGain, 1.0e-6);
    float projectedLuma = centerLuma * positiveDisplayGain;
    float projectedPeak = maximumComponent(centerRgb) * positiveDisplayGain;
    float shadowGate = smoothstep(0.015, 0.075, projectedLuma);
    float highlightGate = 1.0 - smoothstep(0.72, 0.98, projectedPeak);

    /* Random/mottled chroma has low local directional coherence or disagrees with its local mean.
     * Strong luminance boundaries are protected so saturation cannot recreate colored subject
     * borders around clipped/high-contrast objects.
     */
    float coherenceGate = smoothstep(0.45, 0.82, directionalCoherence);
    float agreementGate = 1.0 - smoothstep(0.018, 0.085, chromaDisagreement);
    float edgeGate = 1.0 - smoothstep(
        0.025, 0.11, maximumLumaDelta * positiveDisplayGain);
    float reliability = coherenceGate * agreementGate * edgeGate;

    float requestedGain = 1.0 + 0.32
        * neutralActivation
        * chromaRolloff
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
