from pathlib import Path
import shutil, sys, re

base=Path(sys.argv[1])
out=Path(sys.argv[2])
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out)

def p(rel): return out/rel

def replace_once(rel, old, new, label):
    path=p(rel); s=path.read_text(); n=s.count(old)
    if n!=1: raise SystemExit(f'{label}: expected exactly 1 anchor, got {n} in {rel}')
    path.write_text(s.replace(old,new,1))

def replace_span_once(rel, start, end, new, label):
    path=p(rel); s=path.read_text(); a=s.find(start)
    if a<0: raise SystemExit(f'{label}: start missing in {rel}')
    b=s.find(end,a+len(start))
    if b<0: raise SystemExit(f'{label}: end missing in {rel}')
    if s.find(start,a+1)>=0: raise SystemExit(f'{label}: duplicate start in {rel}')
    path.write_text(s[:a]+new+s[b:])

# 1) SHORT: eliminate literal-core geometry bypass; exact ordinary physical cap remains inherited.
shader='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
replace_once(shader,
'''            /* IRIS_26608_LOCAL_BOUNDARY_PROOF_WITH_CLIPPED_CORE_BYPASS
             * At least two clipped CFA phases define a censored core where NORMAL cannot provide
             * local geometry; retain 26607 component propagation there. Everywhere else, including
             * one-phase/high-gradient transitions, local flow.w evidence caps rescue confidence. */
            float localResidualConfidence =
                1.0 - smoothstep(2.0, 8.0, max(flow.w, 0.0));
            float literalCore = step(
                uSourceClippingPoint, secondHighest4(referenceRaw));
            float localGeometry = mix(localResidualConfidence, 1.0, literalCore);
            float rescueConfidence = min(
                shortHeadroom, min(componentTrust, localGeometry));

            /* IRIS_26609_SHORT_PROTECTION_PARITY_CONTRACT
             * ordinaryWeight contains the full measurable NORMAL-style rejection + dilation.
             * When NORMAL becomes physically censored, only its invalid reference-photometric
             * agreement may relax. The exact same ordinary-rejection unblocker/flow protection,
             * separately dilated as physicalWeight, remains a hard cap together with SHORT
             * source headroom and validated local/component geometry. targetLoss can never erase
             * physical protection. */
            float censoredCoreWeight = min(physicalWeight, rescueConfidence);''',
'''            /* IRIS_26610_NO_LITERAL_CORE_GEOMETRY_BYPASS
             * A clipped NORMAL core makes NORMAL-reference photometry invalid, but it does not make
             * SHORT geometry automatically valid. The same local affine residual proof remains a
             * hard requirement everywhere, including two-phase literal clipping. This permanently
             * removes the 26608/26609 literalCore -> geometry=1 escape that device samples showed
             * could admit pink/magenta/blue boundary disagreement under large residuals. */
            float localResidualConfidence =
                1.0 - smoothstep(2.0, 8.0, max(flow.w, 0.0));
            float localGeometry = localResidualConfidence;
            float rescueConfidence = min(
                shortHeadroom, min(componentTrust, localGeometry));

            /* IRIS_26610_SHORT_COMPLETE_PHYSICAL_CAP
             * ordinaryWeight remains bit-for-bit the measurable NORMAL-style weight whenever
             * physicalCensoring=0. In a proven censored core only the invalid NORMAL-reference
             * photometric term may relax; the inherited ordinary-rejection unblocker protection,
             * exact common dilation, SHORT headroom, component trust, and local residual remain
             * mandatory. No clipping state may erase the local residual cap. */
            float sharedPhysicalProtection = min(physicalWeight, localResidualConfidence);
            float censoredCoreWeight = min(sharedPhysicalProtection, rescueConfidence);''',
'short clipped-core geometry parity')
# Only proven two-phase physical RAW censorship may relax ordinary exposure-normalized photometry.
replace_once(shader,
'''        float literalLossWeight(
            vec4 referenceRaw,
            vec4 scaledShort,
            vec4 peakShortRaw
        ) {
            float literal = 0.0;
            float explained = 1.0;
            for (int phase = 0; phase < 4; ++phase) {
                if (referenceRaw[phase] >= uSourceClippingPoint) {
                    literal = 1.0;
                    float phaseHeadroom = peakShortRaw[phase] < uSourceClippingPoint ? 1.0 : 0.0;
                    float signalProof = smoothstep(0.85, 0.95, scaledShort[phase]);
                    explained = min(explained, phaseHeadroom * signalProof);
                }
            }
            return literal * explained;
        }''',
'''        float literalLossWeight(
            vec4 referenceRaw,
            vec4 scaledShort,
            vec4 peakShortRaw
        ) {
            /* IRIS_26610_TWO_PHASE_PHYSICAL_CENSORSHIP_ONLY
             * Guides are already exposure-normalized before ordinary Sabre rejection. Therefore
             * ordinary photometric protection remains physically valid for SHORT unless NORMAL
             * has lost at least two CFA phases to literal RAW clipping. A one-phase or merely
             * effective/downstream highlight-risk signal may request/carry SHORT, but it may not
             * bypass ordinary NORMAL photometric rejection. */
            if (secondHighest4(referenceRaw) < uSourceClippingPoint) return 0.0;
            float explained = 1.0;
            for (int phase = 0; phase < 4; ++phase) {
                if (referenceRaw[phase] >= uSourceClippingPoint) {
                    float phaseHeadroom = peakShortRaw[phase] < uSourceClippingPoint ? 1.0 : 0.0;
                    float signalProof = smoothstep(0.85, 0.95, scaledShort[phase]);
                    explained = min(explained, phaseHeadroom * signalProof);
                }
            }
            return explained;
        }''',
'short two-phase physical censorship gate')
replace_once(shader,
'''            float finalWeight = mix(ordinaryWeight, censoredCoreWeight, targetLoss);
            oWeight = clamp(finalWeight, 0.0, 1.0);
            oRescueOnlyWeight = clamp(censoredCoreWeight * targetLoss, 0.0, 1.0);
            oLossCandidate = targetLoss;''',
'''            /* IRIS_26610_ONLY_PHYSICAL_CENSORSHIP_RELAXES_PHOTOMETRY
             * effectiveLoss remains useful telemetry/evidence, but cannot replace ordinaryWeight.
             * Only proven two-phase literal RAW censorship invalidates NORMAL-reference photometry. */
            float physicalCensoring = clamp(literalLoss, 0.0, 1.0);
            float finalWeight = mix(ordinaryWeight, censoredCoreWeight, physicalCensoring);
            oWeight = clamp(finalWeight, 0.0, 1.0);
            oRescueOnlyWeight = clamp(censoredCoreWeight * physicalCensoring, 0.0, 1.0);
            oLossCandidate = targetLoss;''',
'short physical-censorship-only rescue blend')

# Update inherited marker wording only, no ordinary rejection mechanics change.
s=p(shader).read_text().replace('IRIS_26609_SHARED_NORMAL_SHORT_PHYSICAL_PROTECTION_OUTPUT','IRIS_26610_SHARED_NORMAL_SHORT_PHYSICAL_PROTECTION_OUTPUT')
p(shader).write_text(s)

# 2) Stacker marker/variable identity only; mechanics inherited exactly.
stack='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
s=p(stack).read_text()
for old,new in [
 ('shortPhysicalReverseWeight26609','shortPhysicalReverseWeight26610'),
 ('shortPhysicalWeight26609','shortPhysicalWeight26610'),
 ('IRIS_26609_SHARED_NORMAL_SHORT_PHYSICAL_PROTECTION_TEXTURE','IRIS_26610_SHARED_NORMAL_SHORT_PHYSICAL_PROTECTION_TEXTURE'),
 ('26609 SHORT physical reverse weight missing','26610 SHORT physical reverse weight missing'),
 ('26609 SHORT exact ordinary-rejection physical reverse weight','26610 SHORT exact ordinary-rejection physical reverse weight'),
 ('26609 SHORT shared physical post-dilation weight','26610 SHORT shared physical post-dilation weight')]:
    s=s.replace(old,new)
p(stack).write_text(s)

# 3) MotionV2Render: replace 26609 post-shoulder stretch with source-domain plan.
render='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
s=p(render).read_text()
start='    /* IRIS_26609_SAMPLE_CALIBRATED_IRIS_RENDITION\n'
end='    public MotionV2Render() { super("", "MotionV2Render"); }'
a=s.find(start); b=s.find(end,a)
if a<0 or b<0: raise SystemExit('MotionV2Render 26609 tone block bounds')
new_block='''    /* IRIS_26610_SOURCE_DOMAIN_HIGHLIGHT_RENDITION\n     * Photon samples are visual references only; Iris retains its own pipeline. 26609 tried to\n     * stretch values after the rational shoulder had already crowded broad highlights. 26610\n     * instead uses the uncompressed max-RGB/luma source guide and the already-owned p99/p998\n     * scene statistics. Everything through the final-domain 0.40 body anchor is mathematically\n     * unchanged; only the ordered highlight tail is redistributed before SDR/UHDR/SR diverge. */\n    static final float IRIS_26610_SDR_BODY_ANCHOR = 0.40f;\n    static final float IRIS_26610_SDR_P99_TARGET = 0.95f;\n    static final float IRIS_26610_SDR_P998_TARGET = 0.995f;\n    static final float IRIS_26610_HDR_P99_TARGET = 4.40f;\n    static final float IRIS_26610_HDR_P998_TARGET = 5.15f;\n\n    public static final class Iris26610TonePlan {\n        public final float sourceP99Final;\n        public final float sourceP998Final;\n        public final float hdrP99Boost;\n        public final float hdrP998Boost;\n        public final float strength;\n        Iris26610TonePlan(float sourceP99Final, float sourceP998Final,\n                          float hdrP99Boost, float hdrP998Boost, float strength) {\n            this.sourceP99Final = sourceP99Final;\n            this.sourceP998Final = sourceP998Final;\n            this.hdrP99Boost = hdrP99Boost;\n            this.hdrP998Boost = hdrP998Boost;\n            this.strength = strength;\n        }\n    }\n\n    public static Iris26610TonePlan iris26610TonePlan(Parameters parameters) {\n        if (parameters == null || !parameters.motionV2Active) {\n            return new Iris26610TonePlan(0.0f, 0.0f, 1.0f, 1.0f, 0.0f);\n        }\n        float gain = Math.max(parameters.motionV2DisplayGain, 1.0e-6f);\n        float p99Guide = Math.max(parameters.motionV2ToneP99Guide, 0.0f);\n        float p998Guide = Math.max(parameters.motionV2ToneP998Guide, p99Guide);\n        float sourceP99Final = p99Guide * gain * OUTPUT_EXPOSURE_SCALE;\n        float sourceP998Final = p998Guide * gain * OUTPUT_EXPOSURE_SCALE;\n        boolean ordered = Float.isFinite(sourceP99Final) && Float.isFinite(sourceP998Final)\n                && sourceP99Final > IRIS_26610_SDR_BODY_ANCHOR + 0.02f\n                && sourceP998Final > sourceP99Final + 0.01f;\n        if (!ordered) {\n            return new Iris26610TonePlan(sourceP99Final, sourceP998Final, 1.0f, 1.0f, 0.0f);\n        }\n        float hdrP99Boost = Math.max(1.0f, IRIS_26610_HDR_P99_TARGET\n                / Math.max(sourceP99Final, 1.0e-4f));\n        float hdrP998Boost = Math.max(hdrP99Boost, IRIS_26610_HDR_P998_TARGET\n                / Math.max(sourceP998Final, 1.0e-4f));\n        return new Iris26610TonePlan(sourceP99Final, sourceP998Final,\n                hdrP99Boost, hdrP998Boost, 1.0f);\n    }\n\n    static float iris26610BaselineMotionSdr(float sourceFinal) {\n        if (sourceFinal <= IRIS_26610_SDR_BODY_ANCHOR) return sourceFinal;\n        float reserve = 1.0f - IRIS_26610_SDR_BODY_ANCHOR;\n        float excess = sourceFinal - IRIS_26610_SDR_BODY_ANCHOR;\n        return IRIS_26610_SDR_BODY_ANCHOR + reserve * excess / (excess + reserve);\n    }\n\n    static float iris26610MapMotionSdrSourceFinal(float sourceFinal, Iris26610TonePlan plan) {\n        float baseline = iris26610BaselineMotionSdr(sourceFinal);\n        if (plan == null || plan.strength <= 0.0f\n                || sourceFinal <= IRIS_26610_SDR_BODY_ANCHOR) return baseline;\n        float a = plan.sourceP99Final;\n        float b = plan.sourceP998Final;\n        if (!(b > a + 0.01f && a > IRIS_26610_SDR_BODY_ANCHOR + 0.02f)) return baseline;\n        float mapped;\n        if (sourceFinal <= a) {\n            float t = iris26582Clamp((sourceFinal - IRIS_26610_SDR_BODY_ANCHOR)\n                    / (a - IRIS_26610_SDR_BODY_ANCHOR), 0.0f, 1.0f);\n            mapped = IRIS_26610_SDR_BODY_ANCHOR\n                    + t * (IRIS_26610_SDR_P99_TARGET - IRIS_26610_SDR_BODY_ANCHOR);\n        } else if (sourceFinal <= b) {\n            float t = iris26582Clamp((sourceFinal - a) / (b - a), 0.0f, 1.0f);\n            mapped = IRIS_26610_SDR_P99_TARGET\n                    + t * (IRIS_26610_SDR_P998_TARGET - IRIS_26610_SDR_P99_TARGET);\n        } else {\n            float excess = sourceFinal - b;\n            float span = Math.max(b - a, 0.05f);\n            mapped = IRIS_26610_SDR_P998_TARGET + (1.0f - IRIS_26610_SDR_P998_TARGET)\n                    * excess / (excess + span);\n        }\n        return baseline + (mapped - baseline) * plan.strength;\n    }\n\n    static float iris26610MapMotionSdrFinalGuide(float sourceGuide, float brightnessTargetGain,\n                                                  Iris26610TonePlan plan) {\n        float sourceFinal = sourceGuide * Math.max(brightnessTargetGain, 1.0e-6f)\n                * OUTPUT_EXPOSURE_SCALE;\n        return iris26610MapMotionSdrSourceFinal(sourceFinal, plan);\n    }\n\n    static float iris26610MapHdrTargetLuma(float hdrBase, float sourceFinal, Iris26610TonePlan plan) {\n        if (plan == null || plan.strength <= 0.0f || hdrBase <= 0.0f) return hdrBase;\n        float a = plan.sourceP99Final;\n        float b = plan.sourceP998Final;\n        if (!(b > a + 0.01f && a > IRIS_26610_SDR_BODY_ANCHOR + 0.02f)) return hdrBase;\n        float start = Math.max(IRIS_26610_SDR_BODY_ANCHOR, a * 0.75f);\n        if (sourceFinal <= start) return hdrBase;\n        float boost;\n        if (sourceFinal <= a) {\n            float t = iris26582Clamp((sourceFinal - start) / Math.max(a - start, 1.0e-6f), 0.0f, 1.0f);\n            boost = 1.0f + t * (plan.hdrP99Boost - 1.0f);\n        } else if (sourceFinal <= b) {\n            float t = iris26582Clamp((sourceFinal - a) / Math.max(b - a, 1.0e-6f), 0.0f, 1.0f);\n            boost = plan.hdrP99Boost + t * (plan.hdrP998Boost - plan.hdrP99Boost);\n        } else {\n            boost = plan.hdrP998Boost;\n        }\n        return hdrBase * (1.0f + (boost - 1.0f) * plan.strength);\n    }\n\n'''
s=s[:a]+new_block+s[b:]
# update remaining references
repls={
'Iris26609TonePlan':'Iris26610TonePlan',
'iris26609TonePlan':'iris26610TonePlan',
'iris26609Tone':'iris26610Tone',
'iris26609OldP99Mapped':'iris26610SourceP99Final',
'iris26609OldP998Mapped':'iris26610SourceP998Final',
'iris26609HdrP99Final':'iris26610HdrP99Boost',
'iris26609HdrP998Final':'iris26610HdrP998Boost',
'iris26609ToneStrength':'iris26610ToneStrength',
'IRIS_26609_SDR_UHDR_SR_RENDITION_PARITY':'IRIS_26610_SOURCE_DOMAIN_SDR_UHDR_SR_PARITY',
}
for old,new in repls.items(): s=s.replace(old,new)
# field access names
s=s.replace('iris26610Tone.oldP99Mapped','iris26610Tone.sourceP99Final')
s=s.replace('iris26610Tone.oldP998Mapped','iris26610Tone.sourceP998Final')
s=s.replace('iris26610Tone.hdrP99Final','iris26610Tone.hdrP99Boost')
s=s.replace('iris26610Tone.hdrP998Final','iris26610Tone.hdrP998Boost')
p(render).write_text(s)

# 4) 1x render shader source-domain map.
render_glsl='app/src/main/assets/shaders/motionv2/render.glsl'
s=p(render_glsl).read_text()
s=s.replace('iris26609OldP99Mapped','iris26610SourceP99Final').replace('iris26609OldP998Mapped','iris26610SourceP998Final').replace('iris26609ToneStrength','iris26610ToneStrength')
# replace helper span
sa=s.find('float iris26609StretchSdrMapped('); eb=s.find('\nfloat mapFinalSdrGuide',sa)
if sa<0 or eb<0: raise SystemExit('render.glsl 26609 helper span')
helper='''float iris26610MapSdrSourceFinal(float sourceFinal) {\n    const float body=0.40;\n    const float targetP99=0.95;\n    const float targetP998=0.995;\n    float reserve=1.0-body;\n    float baseline=sourceFinal<=body?sourceFinal:body+reserve*(sourceFinal-body)/(sourceFinal-body+reserve);\n    float strength=clamp(iris26610ToneStrength,0.0,1.0);\n    float a=iris26610SourceP99Final,b=iris26610SourceP998Final;\n    if(strength<=0.0||sourceFinal<=body||a<=body+0.02||b<=a+0.01) return baseline;\n    float mapped;\n    if(sourceFinal<=a){\n        float t=clamp((sourceFinal-body)/max(a-body,1.0e-6),0.0,1.0);\n        mapped=body+t*(targetP99-body);\n    }else if(sourceFinal<=b){\n        float t=clamp((sourceFinal-a)/max(b-a,1.0e-6),0.0,1.0);\n        mapped=targetP99+t*(targetP998-targetP99);\n    }else{\n        float excess=sourceFinal-b;\n        float span=max(b-a,0.05);\n        mapped=targetP998+(1.0-targetP998)*excess/(excess+span);\n    }\n    return mix(baseline,mapped,strength);\n}\n'''
s=s[:sa]+helper+s[eb:]
old='''        float knee=clamp(iris26604MotionSdrKneeFinal,0.20,0.80);\n        if(targetFinal<=knee) return targetFinal;\n        float reserve=max(1.0-knee,1.0e-6);\n        float excess=max(targetFinal-knee,0.0);\n        float oldMapped=knee+reserve*excess/(excess+reserve);\n        return iris26609StretchSdrMapped(oldMapped);'''
new='''        /* IRIS_26610_SOURCE_DOMAIN_SDR_OWNER */\n        return iris26610MapSdrSourceFinal(targetFinal);'''
if s.count(old)!=1: raise SystemExit(f'render.glsl old final map count {s.count(old)}')
s=s.replace(old,new,1)
p(render_glsl).write_text(s)

# 5) Gainmap shader: source-guide domain decides HDR tail position.
gain='app/src/main/assets/shaders/motionv2/gainmap.glsl'
s=p(gain).read_text()
for old,new in [('iris26609HdrP99Final','iris26610SourceP99Final'),('iris26609HdrP998Final','iris26610SourceP998Final'),('iris26609ToneStrength','iris26610ToneStrength')]: s=s.replace(old,new)
# old helper
sa=s.find('float iris26609MapHdrTarget('); eb=s.find('\nvec3 iris26524BilinearHdr',sa)
if sa<0 or eb<0: raise SystemExit('gainmap old helper span')
helper='''float max3(vec3 v){return max(v.r,max(v.g,v.b));}\nfloat iris26610MapHdrTarget(float hdrBase,float sourceFinal){\n    float strength=clamp(iris26610ToneStrength,0.0,1.0);\n    float a=iris26610SourceP99Final,b=iris26610SourceP998Final;\n    if(strength<=0.0||hdrBase<=0.0||a<=0.42||b<=a+0.01) return hdrBase;\n    float p99Boost=max(1.0,4.40/max(a,1.0e-4));\n    float p998Boost=max(p99Boost,5.15/max(b,1.0e-4));\n    float start=max(0.40,a*0.75);\n    if(sourceFinal<=start) return hdrBase;\n    float boost;\n    if(sourceFinal<=a){float t=clamp((sourceFinal-start)/max(a-start,1.0e-6),0.0,1.0);boost=mix(1.0,p99Boost,t);}\n    else if(sourceFinal<=b){float t=clamp((sourceFinal-a)/max(b-a,1.0e-6),0.0,1.0);boost=mix(p99Boost,p998Boost,t);}\n    else boost=p998Boost;\n    return hdrBase*mix(1.0,boost,strength);\n}\n'''
s=s[:sa]+helper+s[eb:]
old='''    float hdrBase=max(luminance(max(hdrRgb,vec3(0.0))*hdrTargetScale),0.0);\n    float hdr=motionHdrHandoff!=0?iris26609MapHdrTarget(hdrBase):hdrBase;'''
new='''    vec3 hdrPositive=max(hdrRgb,vec3(0.0));\n    float hdrBase=max(luminance(hdrPositive*hdrTargetScale),0.0);\n    float sourceFinal=max3(hdrPositive)*hdrTargetScale;\n    float hdr=motionHdrHandoff!=0?iris26610MapHdrTarget(hdrBase,sourceFinal):hdrBase;'''
if s.count(old)!=1: raise SystemExit('gainmap call anchor')
s=s.replace(old,new,1)
p(gain).write_text(s)

# 6) Adaptive predictor uses exact source-domain SDR map.
adapt='app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl'
s=p(adapt).read_text()
for old,new in [('iris26609OldP99Mapped','iris26610SourceP99Final'),('iris26609OldP998Mapped','iris26610SourceP998Final'),('iris26609ToneStrength','iris26610ToneStrength')]: s=s.replace(old,new)
sa=s.find('float iris26609StretchSdrMapped('); eb=s.find('\nfloat iris26585PostTonePreGamutPeak',sa)
if sa<0 or eb<0: raise SystemExit('adaptive old helper span')
helper='''float iris26610MapSdrSourceFinal(float sourceFinal){\n    const float body=0.40,targetP99=0.95,targetP998=0.995;\n    float reserve=1.0-body;\n    float baseline=sourceFinal<=body?sourceFinal:body+reserve*(sourceFinal-body)/(sourceFinal-body+reserve);\n    float strength=clamp(iris26610ToneStrength,0.0,1.0),a=iris26610SourceP99Final,b=iris26610SourceP998Final;\n    if(strength<=0.0||sourceFinal<=body||a<=body+0.02||b<=a+0.01)return baseline;\n    float mapped;\n    if(sourceFinal<=a){float t=clamp((sourceFinal-body)/max(a-body,1.0e-6),0.0,1.0);mapped=body+t*(targetP99-body);}\n    else if(sourceFinal<=b){float t=clamp((sourceFinal-a)/max(b-a,1.0e-6),0.0,1.0);mapped=targetP99+t*(targetP998-targetP99);}\n    else{float e=sourceFinal-b,span=max(b-a,0.05);mapped=targetP998+(1.0-targetP998)*e/(e+span);}\n    return mix(baseline,mapped,strength);\n}\n'''
s=s[:sa]+helper+s[eb:]
old='''        float targetFinal=sourceGuide*max(displayGain,1.0e-6)*outputExposureScale;\n        float mappedFinal=targetFinal;\n        if(targetFinal>kneeFinal){\n            float reserve=1.0-kneeFinal;\n            float excess=targetFinal-kneeFinal;\n            mappedFinal=kneeFinal+reserve*excess/(excess+reserve);\n            mappedFinal=iris26609StretchSdrMapped(mappedFinal);\n        }'''
new='''        float targetFinal=sourceGuide*max(displayGain,1.0e-6)*outputExposureScale;\n        float mappedFinal=iris26610MapSdrSourceFinal(targetFinal);'''
if s.count(old)!=1: raise SystemExit('adaptive map owner anchor')
s=s.replace(old,new,1)
p(adapt).write_text(s)

# 7) Adaptive Java field bindings.
adapt_java='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java'
s=p(adapt_java).read_text()
for old,new in [('Iris26609TonePlan','Iris26610TonePlan'),('iris26609TonePlan','iris26610TonePlan'),('iris26609Tone','iris26610Tone'),('iris26609OldP99Mapped','iris26610SourceP99Final'),('iris26609OldP998Mapped','iris26610SourceP998Final'),('iris26609ToneStrength','iris26610ToneStrength'),('IRIS_26609_TONE_PREDICTOR_PARITY','IRIS_26610_SOURCE_DOMAIN_TONE_PREDICTOR_PARITY')]: s=s.replace(old,new)
s=s.replace('iris26610Tone.oldP99Mapped','iris26610Tone.sourceP99Final').replace('iris26610Tone.oldP998Mapped','iris26610Tone.sourceP998Final')
p(adapt_java).write_text(s)

# 8) True2x Java args use new plan fields.
enc='app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java'
s=p(enc).read_text()
for old,new in [('Iris26609TonePlan','Iris26610TonePlan'),('iris26609TonePlan','iris26610TonePlan'),('iris26609Tone','iris26610Tone'),('iris26609OldP99Mapped','iris26610SourceP99Final'),('iris26609OldP998Mapped','iris26610SourceP998Final'),('iris26609HdrP99Final','iris26610HdrP99Boost'),('iris26609HdrP998Final','iris26610HdrP998Boost'),('iris26609ToneStrength','iris26610ToneStrength')]: s=s.replace(old,new)
s=s.replace('iris26610Tone.oldP99Mapped','iris26610Tone.sourceP99Final').replace('iris26610Tone.oldP998Mapped','iris26610Tone.sourceP998Final').replace('iris26610Tone.hdrP99Final','iris26610Tone.hdrP99Boost').replace('iris26610Tone.hdrP998Final','iris26610Tone.hdrP998Boost')
p(enc).write_text(s)

# 9) Native true2x CPU/GPU source-domain parity.
native='app/src/main/cpp/motionv2_jpeg444_jni.cpp'
s=p(native).read_text()
# identifier semantics
for old,new in [('iris26609OldP99Mapped','iris26610SourceP99Final'),('iris26609OldP998Mapped','iris26610SourceP998Final'),('iris26609HdrP99Final','iris26610HdrP99Boost'),('iris26609HdrP998Final','iris26610HdrP998Boost'),('iris26609ToneStrength','iris26610ToneStrength'),('uIris26609OldP99Mapped','uIris26610SourceP99Final'),('uIris26609OldP998Mapped','uIris26610SourceP998Final'),('uIris26609HdrP99Final','uIris26610HdrP99Boost'),('uIris26609HdrP998Final','uIris26610HdrP998Boost'),('uIris26609ToneStrength','uIris26610ToneStrength')]: s=s.replace(old,new)
# CPU helpers span
sa=s.find('inline float iris26609StretchSdrMapped('); eb=s.find('\ninline Vec3 renderHeadroom',sa)
if sa<0 or eb<0: raise SystemExit('native CPU helper span')
helper='''inline float iris26610MapSdrSourceFinal(float sourceFinal,const Params&p){\n    constexpr float body=0.40f,targetP99=0.95f,targetP998=0.995f;\n    float reserve=1.f-body;\n    float baseline=sourceFinal<=body?sourceFinal:body+reserve*(sourceFinal-body)/(sourceFinal-body+reserve);\n    float strength=clampf(p.iris26610ToneStrength,0.f,1.f),a=p.iris26610SourceP99Final,b=p.iris26610SourceP998Final;\n    if(strength<=0.f||sourceFinal<=body||a<=body+0.02f||b<=a+0.01f)return baseline;\n    float mapped;\n    if(sourceFinal<=a){float t=clampf((sourceFinal-body)/std::max(a-body,1.0e-6f),0.f,1.f);mapped=body+t*(targetP99-body);}\n    else if(sourceFinal<=b){float t=clampf((sourceFinal-a)/std::max(b-a,1.0e-6f),0.f,1.f);mapped=targetP99+t*(targetP998-targetP99);}\n    else{float e=sourceFinal-b,span=std::max(b-a,0.05f);mapped=targetP998+(1.f-targetP998)*e/(e+span);}\n    return baseline+(mapped-baseline)*strength;\n}\ninline float iris26610MapHdrTarget(float hdrBase,float sourceFinal,const Params&p){\n    float strength=clampf(p.iris26610ToneStrength,0.f,1.f),a=p.iris26610SourceP99Final,b=p.iris26610SourceP998Final;\n    if(strength<=0.f||hdrBase<=0.f||a<=0.42f||b<=a+0.01f)return hdrBase;\n    float p99Boost=std::max(1.f,p.iris26610HdrP99Boost),p998Boost=std::max(p99Boost,p.iris26610HdrP998Boost);\n    float start=std::max(0.40f,a*0.75f);if(sourceFinal<=start)return hdrBase;float boost;\n    if(sourceFinal<=a){float t=clampf((sourceFinal-start)/std::max(a-start,1.0e-6f),0.f,1.f);boost=1.f+t*(p99Boost-1.f);}\n    else if(sourceFinal<=b){float t=clampf((sourceFinal-a)/std::max(b-a,1.0e-6f),0.f,1.f);boost=p99Boost+t*(p998Boost-p99Boost);}\n    else boost=p998Boost;\n    return hdrBase*(1.f+(boost-1.f)*strength);\n}\n'''
s=s[:sa]+helper+s[eb:]
# CPU SDR both cached/noncached owner occurrences
old='''if(targetFinal>knee){float excess=targetFinal-knee;mappedFinal=knee+reserve*excess/(excess+reserve);mappedFinal=iris26609StretchSdrMapped(mappedFinal,p);}'''
count=s.count(old)
if count<1: raise SystemExit(f'native CPU SDR old count={count}')
s=s.replace(old,'''mappedFinal=iris26610MapSdrSourceFinal(targetFinal,p);''')
# CPU gain anchors (2) use source max-RGB final domain
old='''float hdrBase=std::max(luma(clampNonnegative(hdr))*hdrScale,0.f),hdrY=p.motionHdrHandoff?iris26609MapHdrTarget(hdrBase,p):hdrBase,sdrY'''
count=s.count(old)
if count!=2: raise SystemExit(f'native CPU gain old count={count}')
s=s.replace(old,'''float hdrBase=std::max(luma(clampNonnegative(hdr))*hdrScale,0.f),sourceFinal=peak(clampNonnegative(hdr))*hdrScale,hdrY=p.motionHdrHandoff?iris26610MapHdrTarget(hdrBase,sourceFinal,p):hdrBase,sdrY''')
# GPU helpers span
sa=s.find('float iris26609StretchSdrMapped('); eb=s.find('\nvec3 irisHeadroom',sa)
if sa<0 or eb<0: raise SystemExit('native GPU helper span')
helper_gpu='''float iris26610MapSdrSourceFinal(float sourceFinal){\n    const float body=0.40,targetP99=0.95,targetP998=0.995;float reserve=1.0-body;\n    float baseline=sourceFinal<=body?sourceFinal:body+reserve*(sourceFinal-body)/(sourceFinal-body+reserve);\n    float strength=clamp(uIris26610ToneStrength,0.0,1.0),a=uIris26610SourceP99Final,b=uIris26610SourceP998Final;\n    if(strength<=0.0||sourceFinal<=body||a<=body+0.02||b<=a+0.01)return baseline;float mapped;\n    if(sourceFinal<=a){float t=clamp((sourceFinal-body)/max(a-body,1.0e-6),0.0,1.0);mapped=body+t*(targetP99-body);}\n    else if(sourceFinal<=b){float t=clamp((sourceFinal-a)/max(b-a,1.0e-6),0.0,1.0);mapped=targetP99+t*(targetP998-targetP99);}\n    else{float e=sourceFinal-b,span=max(b-a,0.05);mapped=targetP998+(1.0-targetP998)*e/(e+span);}\n    return mix(baseline,mapped,strength);\n}\nfloat iris26610MapHdrTarget(float hdrBase,float sourceFinal){\n    float strength=clamp(uIris26610ToneStrength,0.0,1.0),a=uIris26610SourceP99Final,b=uIris26610SourceP998Final;\n    if(strength<=0.0||hdrBase<=0.0||a<=0.42||b<=a+0.01)return hdrBase;float p99Boost=max(1.0,uIris26610HdrP99Boost),p998Boost=max(p99Boost,uIris26610HdrP998Boost);\n    float start=max(0.40,a*0.75);if(sourceFinal<=start)return hdrBase;float boost;\n    if(sourceFinal<=a){float t=clamp((sourceFinal-start)/max(a-start,1.0e-6),0.0,1.0);boost=mix(1.0,p99Boost,t);}\n    else if(sourceFinal<=b){float t=clamp((sourceFinal-a)/max(b-a,1.0e-6),0.0,1.0);boost=mix(p99Boost,p998Boost,t);}\n    else boost=p998Boost;return hdrBase*mix(1.0,boost,strength);\n}\n'''
s=s[:sa]+helper_gpu+s[eb:]
old='''if(targetFinal>knee){float excess=targetFinal-knee;mappedFinal=knee+reserve*excess/(excess+reserve);mappedFinal=iris26609StretchSdrMapped(mappedFinal);}'''
if s.count(old)!=1: raise SystemExit(f'native GPU SDR old count={s.count(old)}')
s=s.replace(old,'''mappedFinal=iris26610MapSdrSourceFinal(targetFinal);''',1)
old='''float hdrBase=max(irisLuma(irisClampNonnegative(hdr))*hdrScale,0.0);\n        float hdrY=uMotionHdrHandoff!=0?iris26609MapHdrTarget(hdrBase):hdrBase;'''
new='''float hdrBase=max(irisLuma(irisClampNonnegative(hdr))*hdrScale,0.0);\n        float sourceFinal=irisPeak(irisClampNonnegative(hdr))*hdrScale;\n        float hdrY=uMotionHdrHandoff!=0?iris26610MapHdrTarget(hdrBase,sourceFinal):hdrBase;'''
if s.count(old)!=1: raise SystemExit('native GPU gain call')
s=s.replace(old,new,1)
p(native).write_text(s)

# 10) Version.
version='app/version.properties'
s=p(version).read_text()
for old,new in [('VERSION_NAME=0.9726609','VERSION_NAME=0.9726610'),('VERSION_BUILD=26609','VERSION_BUILD=26610')]:
    if s.count(old)!=1: raise SystemExit(f'version anchor {old} count={s.count(old)}')
    s=s.replace(old,new,1)
p(version).write_text(s)

allow=[
'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/version.properties']
changed=[]
for q in sorted((out/'app').rglob('*')):
    if q.is_file():
        rel=str(q.relative_to(out)); b=base/rel
        if not b.exists() or q.read_bytes()!=b.read_bytes(): changed.append(rel)
if sorted(changed)!=sorted(allow):
    raise SystemExit('scope mismatch\nactual='+repr(changed)+'\nexpected='+repr(allow))
print('PASS transform scope exactly 10')
for rel in changed: print(rel)
