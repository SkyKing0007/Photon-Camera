#!/usr/bin/env python3
from pathlib import Path
import sys, shutil
if len(sys.argv)!=3: raise SystemExit('usage: transform_26633_r1.py BASE OUT')
base=Path(sys.argv[1]); root=Path(sys.argv[2])
if root.exists(): shutil.rmtree(root)
shutil.copytree(base,root)

def read(rel): return (root/rel).read_text()
def write(rel,s): (root/rel).write_text(s)
def once(s,old,new,label):
    n=s.count(old)
    if n!=1: raise SystemExit(f'{label}: expected 1 anchor, got {n}')
    return s.replace(old,new,1)

# 1) SHORT whole-observation coherence, preserving scalar bracket ownership.
rel='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
s=read(rel)
old='''        float effectiveLossWeight(vec4 referenceNormalized, vec4 scaledShort) {
            vec4 phaseLoss = vec4(0.0);
            float severeSingle = 0.0;
            for (int phase = 0; phase < 4; ++phase) {
                float predicted = max(scaledShort[phase], 0.0);
                float reference = max(referenceNormalized[phase], 0.0);
                float relativeLoss = max(predicted - reference, 0.0) / max(predicted, 0.05);
                float signalGate = smoothstep(0.72, 0.92, predicted);
                phaseLoss[phase] = signalGate * smoothstep(0.05, 0.12, relativeLoss);
                severeSingle = max(severeSingle,
                    smoothstep(0.94, 0.98, reference) * signalGate *
                    smoothstep(0.12, 0.22, relativeLoss));
            }
            return max(secondHighest4(phaseLoss), severeSingle);
        }
        float literalLossWeight(
'''
new='''        float effectiveLossWeight(vec4 referenceNormalized, vec4 scaledShort) {
            vec4 phaseLoss = vec4(0.0);
            float severeSingle = 0.0;
            for (int phase = 0; phase < 4; ++phase) {
                float predicted = max(scaledShort[phase], 0.0);
                float reference = max(referenceNormalized[phase], 0.0);
                float relativeLoss = max(predicted - reference, 0.0) / max(predicted, 0.05);
                float signalGate = smoothstep(0.72, 0.92, predicted);
                phaseLoss[phase] = signalGate * smoothstep(0.05, 0.12, relativeLoss);
                severeSingle = max(severeSingle,
                    smoothstep(0.94, 0.98, reference) * signalGate *
                    smoothstep(0.12, 0.22, relativeLoss));
            }
            return max(secondHighest4(phaseLoss), severeSingle);
        }
        /* IRIS_26633_SHORT_WHOLE_OBSERVATION_COHERENCE
         * Preserve the successful 26604/26605 invariant: SHORT receives ONE scalar observation
         * weight for the complete Bayer/RGB observation. Phase-local measurements are evidence
         * only; they never become independent bracket owners. At a measurable clipped boundary,
         * compare exposure-normalized SHORT against NORMAL on the same CFA phases. Two moderate
         * contradictions or one severe high-signal contradiction attenuate the WHOLE rescue.
         * Fully censored cores have insufficient measurable NORMAL evidence to disprove SHORT and
         * therefore retain 26632 rescue unchanged. This targets misregistered chroma rails without
         * reducing coherent chandelier/cloud/sign highlight recovery.
         */
        float wholeObservationCoherence(vec4 referenceNormalized, vec4 scaledShort) {
            vec4 contradiction = vec4(0.0);
            float severeSingle = 0.0;
            int measurablePhases = 0;
            for (int phase = 0; phase < 4; ++phase) {
                float reference = max(referenceNormalized[phase], 0.0);
                float predicted = max(scaledShort[phase], 0.0);
                float measurableNormal = 1.0 - smoothstep(0.82, 0.90, reference);
                float signal = smoothstep(0.10, 0.25, min(reference, predicted));
                float relevance = measurableNormal * signal;
                if (relevance > 0.15) measurablePhases += 1;
                float relativeError = abs(predicted - reference) /
                    max(max(reference, predicted), 0.05);
                contradiction[phase] = relevance * smoothstep(0.06, 0.16, relativeError);
                severeSingle = max(severeSingle,
                    relevance * smoothstep(0.16, 0.30, relativeError));
            }
            if (measurablePhases < 2) return 1.0;
            float repeatedContradiction = secondHighest4(contradiction);
            float penalty = max(repeatedContradiction, severeSingle);
            return clamp(1.0 - penalty, 0.0, 1.0);
        }
        float literalLossWeight(
'''
s=once(s,old,new,'short coherence helper')
old='''            float shortHeadroom = wholeShortHeadroom(shortPeakRaw);
            float componentTrust = clamp(texture(uComponentTrust, flowUv).r, 0.0, 1.0);
            /* IRIS_26611_BOUNDARY_PROVEN_SHORT_RESCUE_ONLY
'''
new='''            float shortHeadroom = wholeShortHeadroom(shortPeakRaw);
            float componentTrust = clamp(texture(uComponentTrust, flowUv).r, 0.0, 1.0);
            float observationCoherence = wholeObservationCoherence(
                referenceNormalized, scaledShort);
            /* IRIS_26611_BOUNDARY_PROVEN_SHORT_RESCUE_ONLY
'''
s=once(s,old,new,'short coherence value')
old='''            float rescueConfidence = min(shortHeadroom, componentTrust);

            /* IRIS_26611_SHORT_COMPLETE_COMMON_PHYSICAL_CAP
'''
new='''            float rescueConfidence = min(
                shortHeadroom, min(componentTrust, observationCoherence));

            /* IRIS_26633_SHORT_SCALAR_COHERENCE_CAP
             * This cap modifies only the relaxed highlight rescue. ordinaryWeight remains intact,
             * so coherent/non-highlight SHORT behavior is byte-for-byte semantically preserved.
             * No per-phase weight reaches the common accumulator. */

            /* IRIS_26611_SHORT_COMPLETE_COMMON_PHYSICAL_CAP
'''
s=once(s,old,new,'short coherence cap')
write(rel,s)

# 2) Motion shadow toe, 1x final presentation only; UHDR gainmap file untouched.
rel='app/src/main/assets/shaders/motionv2/render.glsl'
s=read(rel)
anchor='''vec3 iris26630AdaptiveColorV5(vec3 rgb,float userSaturation){
'''
helper='''/* IRIS_26633_MONOTONIC_DEEP_SHADOW_TOE
 * Universal output-referred shadow presentation only. The toe has positive slope at black,
 * becomes C1 identity by 0.18 linear guide, and scales RGB uniformly so hue is unchanged.
 * It is Motion-only; Night and the 26632 UHDR gain-map equation are untouched. */
float iris26633ShadowToeGuide(float guide){
    const float toeEnd=0.18;
    const float deepScale=0.72;
    float x=max(guide,0.0);
    if(x>=toeEnd) return x;
    float t=clamp(x/toeEnd,0.0,1.0);
    float smoothFactor=t*t*(3.0-2.0*t);
    return x*mix(deepScale,1.0,smoothFactor);
}
vec3 iris26633ApplyShadowToe(vec3 rgb){
    if(iris26592MotionHdrHandoff==0) return rgb;
    rgb=max(rgb,vec3(0.0));
    float guide=max(luminance(rgb),max3(rgb));
    if(guide<=1.0e-7) return rgb;
    float mapped=iris26633ShadowToeGuide(guide);
    return rgb*(mapped/guide);
}

vec3 iris26630AdaptiveColorV5(vec3 rgb,float userSaturation){
'''
s=once(s,anchor,helper,'render toe helper')
old='''    /* IRIS_26621_FINAL_DOMAIN_SINGLE_PRESENTATION
     * motionV2DisplayGain/outputExposureScale are consumed only by the shared global tone seed.
     * Local Laplacian supplies an absolute mapped luminance target, never a second exposure gain.
     */
    linearSrgb=fitDisplayGamut(linearSrgb);
'''
new='''    /* IRIS_26621_FINAL_DOMAIN_SINGLE_PRESENTATION
     * motionV2DisplayGain/outputExposureScale are consumed only by the shared global tone seed.
     * Local Laplacian supplies an absolute mapped luminance target, never a second exposure gain.
     */
    linearSrgb=iris26633ApplyShadowToe(linearSrgb);
    linearSrgb=fitDisplayGamut(linearSrgb);
'''
s=once(s,old,new,'render toe application')
write(rel,s)

# 3) Adaptive residual luma cleanup for normal Motion 1x only; Super Res residual denoise frozen.
rel='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'
s=read(rel)
old='''            val requestedLumaScale = irisSettings.lumaDenoise.coerceIn(0f, 2f)
            val noiseEquivalentSupport =
                (1f / checkNotNull(sabreNoiseScale)).coerceIn(1f, stacked.mergedFrameCount.toFloat())
            requireParity(noiseEquivalentSupport.isFinite() && noiseEquivalentSupport >= 1f,
                "missing/malformed noise-equivalent temporal support")
            /* IRIS_26545_SHARED_RESIDUAL_DENOISE_CONTROLS
'''
new='''            val requestedLumaScale = irisSettings.lumaDenoise.coerceIn(0f, 2f)
            val noiseEquivalentSupport =
                (1f / checkNotNull(sabreNoiseScale)).coerceIn(1f, stacked.mergedFrameCount.toFloat())
            requireParity(noiseEquivalentSupport.isFinite() && noiseEquivalentSupport >= 1f,
                "missing/malformed noise-equivalent temporal support")
            /* IRIS_26633_LOW_SUPPORT_RESIDUAL_LUMA_FLOOR
             * Worm-shaped residual luma is exposed when Sabre's measured noise-equivalent support
             * remains low even after a large nominal frame count. Keep the existing MGC/Pecan
             * residual denoise owner and measured noise model; add only a bounded support-derived
             * luma floor. Pecan's frequency/outlier/revert tuning remains the structure authority.
             * No ISO/scene-brightness heuristic and no post-render blur is introduced. */
            val supportDeficit26633 =
                ((3.0f - noiseEquivalentSupport) / 2.0f).coerceIn(0f, 1f)
            val supportGate26633 = supportDeficit26633 * supportDeficit26633 *
                (3.0f - 2.0f * supportDeficit26633)
            val automaticLumaScale26633 = if (irisSettings.noiseReductionEnabled) {
                0.35f * supportGate26633
            } else 0f
            /* IRIS_26545_SHARED_RESIDUAL_DENOISE_CONTROLS
'''
s=once(s,old,new,'auto luma support')
old='''            val lumaScale = requestedLumaScale
            val chromaScale = irisSettings.chromaDenoise.coerceIn(0f, 2f)
'''
new='''            val lumaScale = maxOf(requestedLumaScale, automaticLumaScale26633).coerceIn(0f, 2f)
            val chromaScale = irisSettings.chromaDenoise.coerceIn(0f, 2f)
'''
s=once(s,old,new,'luma scale floor')

# telemetry include auto/support
old='''                "luma=$lumaScale chroma=$chromaScale executed=$runFullResolutionDenoise " +
                "pass=$denoisePass noiseSource=$noiseAuthority mgcBase=${mgcBase.timestamp} " +
'''
new='''                "luma=$lumaScale chroma=$chromaScale automaticLuma26633=$automaticLumaScale26633 " +
                "noiseEquivalentSupport=$noiseEquivalentSupport executed=$runFullResolutionDenoise " +
                "pass=$denoisePass noiseSource=$noiseAuthority mgcBase=${mgcBase.timestamp} " +
'''
s=once(s,old,new,'denoise telemetry')
write(rel,s)

# 4) True2x Motion shadow toe parity in CPU + embedded GPU publication.
rel='app/src/main/cpp/motionv2_jpeg444_jni.cpp'
s=read(rel)
old='''inline Vec3 renderHeadroom(Vec3 rgb,const Params&p,float localMappedGuide){
    rgb=clampNonnegative(rgb);float y=std::max(luma(rgb),0.f),pk=peak(rgb),guide=std::max(y,pk);
'''
new='''inline float iris26633ShadowToeGuide(float guide){
    constexpr float toeEnd=0.18f,deepScale=0.72f;
    float x=std::max(guide,0.f);if(x>=toeEnd)return x;
    float t=clampf(x/toeEnd,0.f,1.f),smoothFactor=t*t*(3.f-2.f*t);
    return x*(deepScale+(1.f-deepScale)*smoothFactor);
}
inline Vec3 iris26633ApplyShadowToe(Vec3 rgb,const Params&p){
    if(!p.motionHdrHandoff)return rgb;rgb=clampNonnegative(rgb);
    float guide=std::max(luma(rgb),peak(rgb));if(guide<=1.0e-7f)return rgb;
    return mul(rgb,iris26633ShadowToeGuide(guide)/guide);
}
inline Vec3 renderHeadroom(Vec3 rgb,const Params&p,float localMappedGuide){
    rgb=clampNonnegative(rgb);float y=std::max(luma(rgb),0.f),pk=peak(rgb),guide=std::max(y,pk);
'''
s=once(s,old,new,'native cpu toe helper')
old='''    float pk2=peak(rgb);if(pk2>1.f)rgb=mul(rgb,1.f/std::max(pk2,1.0e-6f));
    return iris26630AdaptiveColorV5(clampNonnegative(rgb),p.saturation);
}
'''
new='''    rgb=iris26633ApplyShadowToe(rgb,p);
    float pk2=peak(rgb);if(pk2>1.f)rgb=mul(rgb,1.f/std::max(pk2,1.0e-6f));
    return iris26630AdaptiveColorV5(clampNonnegative(rgb),p.saturation);
}
'''
s=once(s,old,new,'native cpu toe apply')
# embedded GLSL helper before irisHeadroom
old='''vec3 irisHeadroom(vec3 rgb,float localMappedGuide){
    rgb=irisClampNonnegative(rgb);
'''
new='''float iris26633ShadowToeGuide(float guide){
    const float toeEnd=0.18,deepScale=0.72;
    float x=max(guide,0.0);if(x>=toeEnd)return x;
    float t=clamp(x/toeEnd,0.0,1.0),smoothFactor=t*t*(3.0-2.0*t);
    return x*mix(deepScale,1.0,smoothFactor);
}
vec3 iris26633ApplyShadowToe(vec3 rgb){
    if(uMotionHdrHandoff==0)return rgb;rgb=irisClampNonnegative(rgb);
    float guide=max(irisLuma(rgb),irisPeak(rgb));if(guide<=1.0e-7)return rgb;
    return rgb*(iris26633ShadowToeGuide(guide)/guide);
}
vec3 irisHeadroom(vec3 rgb,float localMappedGuide){
    rgb=irisClampNonnegative(rgb);
'''
s=once(s,old,new,'native gpu toe helper')
old='''    float pk2=irisPeak(rgb);if(pk2>1.0)rgb*=1.0/max(pk2,1.0e-6);
    return iris26630AdaptiveColorV5(irisClampNonnegative(rgb),uSaturation);
}
'''
new='''    rgb=iris26633ApplyShadowToe(rgb);
    float pk2=irisPeak(rgb);if(pk2>1.0)rgb*=1.0/max(pk2,1.0e-6);
    return iris26630AdaptiveColorV5(irisClampNonnegative(rgb),uSaturation);
}
'''
s=once(s,old,new,'native gpu toe apply')
write(rel,s)

# 5) version
rel='app/version.properties'
s=read(rel)
s=once(s,'VERSION_NAME=0.9726632','VERSION_NAME=0.9726633','version name')
s=once(s,'VERSION_BUILD=26632','VERSION_BUILD=26633','version build')
write(rel,s)

print('PASS transform 26633 R1: SHORT whole-observation coherence + normal-Motion low-support luma + monotonic shadow toe; Super Res residual denoise frozen')
