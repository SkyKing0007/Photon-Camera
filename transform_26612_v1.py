#!/usr/bin/env python3
from pathlib import Path
import shutil, sys
if len(sys.argv)!=3: raise SystemExit('usage: apply_candidate.py <base> <out>')
base=Path(sys.argv[1]).resolve(); out=Path(sys.argv[2]).resolve()
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out)
APP=out/'app' if (out/'app').is_dir() else out

def replace_once(rel,old,new,label):
    p=APP/rel; s=p.read_text(); n=s.count(old)
    if n!=1: raise SystemExit(f'{label}: expected 1 anchor, got {n} in {rel}')
    p.write_text(s.replace(old,new,1))

def replace_region(rel,start,end,new,label):
    p=APP/rel; s=p.read_text();
    if s.count(start)!=1 or s.count(end)!=1: raise SystemExit(f'{label}: nonunique region in {rel}: start={s.count(start)} end={s.count(end)}')
    a=s.index(start); b=s.index(end,a)
    if b<=a: raise SystemExit(f'{label}: bad order')
    p.write_text(s[:a]+new+s[b:])

def must(rel,text,label):
    if text not in (APP/rel).read_text(): raise SystemExit(f'{label}: missing {text}')

VER='version.properties'
RENDERJ='src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
ADAPTJ='src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java'
ENC='src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java'
RENDER='src/main/assets/shaders/motionv2/render.glsl'
GAIN='src/main/assets/shaders/motionv2/gainmap.glsl'
ADAPT='src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl'
CPP='src/main/cpp/motionv2_jpeg444_jni.cpp'

replace_once(VER,'VERSION_NAME=0.9726611\nVERSION_BUILD=26611\n','VERSION_NAME=0.9726612\nVERSION_BUILD=26612\n','version')

# Java single plan authority. Default/broad-low-lift exactly reproduces 26610; compact and high display-gain pressure
# continuously reserve more SDR range and more UHDR range. No day/night/object semantic branch.
start='    /* IRIS_26610_SOURCE_DOMAIN_HIGHLIGHT_RENDITION\n'
end='    public MotionV2Render() { super("", "MotionV2Render"); }\n'
new=r'''    /* IRIS_26612_UNIVERSAL_BODY_BROAD_COMPACT_PRESENTATION
     * One content-driven Motion presentation plan for any object and any lighting condition.
     * The plan consumes only already-owned source statistics: p99/p995/p998 max-RGB guide,
     * coherent broad-tail strength, compact-tail strength, hard-ceiling occupancy, adaptive
     * structured-tail support, and display-gain pressure. There is no day/night/window/cloud/
     * lamp semantic branch. The 0.40 final-domain body remains mathematically unchanged.
     *
     * 26610 is retained exactly when there is no compact pressure and no high-lift broad pressure:
     * p99=0.95, p998=0.995 and the inserted p995 point lies exactly on the 26610 line. Compact
     * highlights continuously reserve more SDR distance around the halo while the tiny p998 core
     * may still approach white. High display gain adds protection because the body lift itself
     * increases highlight crowding. UHDR uses the same source anchors and expands only the real
     * HDR tail; SDR, UHDR, adaptive-color prediction and true2x CPU/GPU consume this one plan. */
    static final float IRIS_26612_SDR_BODY_ANCHOR = 0.40f;
    static final float IRIS_26612_LEGACY_SDR_P99_TARGET = 0.95f;
    static final float IRIS_26612_LEGACY_SDR_P998_TARGET = 0.995f;
    static final float IRIS_26612_LEGACY_HDR_P99_TARGET = 4.40f;
    static final float IRIS_26612_LEGACY_HDR_P998_TARGET = 5.15f;

    public static final class Iris26612TonePlan {
        public final float sourceP99Final;
        public final float sourceP995Final;
        public final float sourceP998Final;
        public final float sdrP99Target;
        public final float sdrP995Target;
        public final float sdrP998Target;
        public final float hdrP99Boost;
        public final float hdrP995Boost;
        public final float hdrP998Boost;
        public final float broadPressure;
        public final float compactPressure;
        public final float gainPressure;
        public final float strength;
        Iris26612TonePlan(float sourceP99Final, float sourceP995Final, float sourceP998Final,
                          float sdrP99Target, float sdrP995Target, float sdrP998Target,
                          float hdrP99Boost, float hdrP995Boost, float hdrP998Boost,
                          float broadPressure, float compactPressure, float gainPressure,
                          float strength) {
            this.sourceP99Final = sourceP99Final;
            this.sourceP995Final = sourceP995Final;
            this.sourceP998Final = sourceP998Final;
            this.sdrP99Target = sdrP99Target;
            this.sdrP995Target = sdrP995Target;
            this.sdrP998Target = sdrP998Target;
            this.hdrP99Boost = hdrP99Boost;
            this.hdrP995Boost = hdrP995Boost;
            this.hdrP998Boost = hdrP998Boost;
            this.broadPressure = broadPressure;
            this.compactPressure = compactPressure;
            this.gainPressure = gainPressure;
            this.strength = strength;
        }
    }

    private static float iris26612Smoothstep(float a, float b, float x) {
        float t = iris26582Clamp((x - a) / Math.max(b - a, 1.0e-6f), 0.0f, 1.0f);
        return t * t * (3.0f - 2.0f * t);
    }

    public static Iris26612TonePlan iris26612TonePlan(Parameters parameters) {
        if (parameters == null || !parameters.motionV2Active) {
            return new Iris26612TonePlan(0.0f, 0.0f, 0.0f,
                    IRIS_26612_LEGACY_SDR_P99_TARGET, 0.975f,
                    IRIS_26612_LEGACY_SDR_P998_TARGET,
                    1.0f, 1.0f, 1.0f, 0.0f, 0.0f, 0.0f, 0.0f);
        }
        float gain = Math.max(parameters.motionV2DisplayGain, 1.0e-6f);
        float p99Guide = Math.max(parameters.motionV2ToneP99Guide, 0.0f);
        float p995Guide = Math.max(parameters.motionV2ToneP995Guide, p99Guide);
        float p998Guide = Math.max(parameters.motionV2ToneP998Guide, p995Guide);
        float sourceP99Final = p99Guide * gain * OUTPUT_EXPOSURE_SCALE;
        float sourceP995Final = p995Guide * gain * OUTPUT_EXPOSURE_SCALE;
        float sourceP998Final = p998Guide * gain * OUTPUT_EXPOSURE_SCALE;
        boolean ordered = Float.isFinite(sourceP99Final) && Float.isFinite(sourceP995Final)
                && Float.isFinite(sourceP998Final)
                && sourceP99Final > IRIS_26612_SDR_BODY_ANCHOR + 0.02f
                && sourceP998Final > sourceP99Final + 0.01f;
        if (!ordered) {
            return new Iris26612TonePlan(sourceP99Final, sourceP995Final, sourceP998Final,
                    IRIS_26612_LEGACY_SDR_P99_TARGET, 0.975f,
                    IRIS_26612_LEGACY_SDR_P998_TARGET,
                    1.0f, 1.0f, 1.0f, 0.0f, 0.0f, 0.0f, 0.0f);
        }
        sourceP995Final = Math.max(sourceP99Final + 0.002f,
                Math.min(sourceP995Final, sourceP998Final - 0.002f));
        float sourceSpan = Math.max(sourceP998Final - sourceP99Final, 1.0e-6f);
        float p995Position = iris26582Clamp(
                (sourceP995Final - sourceP99Final) / sourceSpan, 0.0f, 1.0f);

        float broad = iris26582Clamp(parameters.motionV2ToneProjectedBroadTailStrength, 0.0f, 1.0f);
        float compactOwned = iris26582Clamp(parameters.motionV2ToneCompactTailStrength, 0.0f, 1.0f);
        float adaptive = iris26582Clamp(parameters.motionV2ToneAdaptiveStrength, 0.0f, 1.0f);
        float hardFraction = iris26582Clamp(
                parameters.motionV2ToneProjectedHardCeilingFraction, 0.0f, 1.0f);
        float log2Gain = (float)(Math.log(Math.max(gain, 1.0f)) / Math.log(2.0));
        float gainPressure = iris26612Smoothstep(1.0f, 2.10f, log2Gain);
        /* Population-gated compactTailStrength can intentionally be zero for a tiny lamp. The
         * hard-ceiling + already-owned structured/adaptive support recovers that coherent sparse
         * case without accepting a lone hot pixel. Broad dominance suppresses the sparse vote. */
        float sparseStructuredCompact = iris26612Smoothstep(0.0005f, 0.0060f, hardFraction)
                * (1.0f - iris26612Smoothstep(0.35f, 0.75f, broad)) * adaptive;
        float compactEvidence = Math.max(compactOwned, sparseStructuredCompact);
        float compactPressure = compactEvidence * (0.55f + 0.45f * gainPressure)
                * (1.0f - 0.35f * broad);
        compactPressure = iris26582Clamp(compactPressure, 0.0f, 1.0f);
        float highLiftReserve = iris26612Smoothstep(0.35f, 0.90f, gainPressure);
        float broadPressure = iris26582Clamp(broad * highLiftReserve, 0.0f, 1.0f);

        float legacyP995Target = IRIS_26612_LEGACY_SDR_P99_TARGET
                + p995Position * (IRIS_26612_LEGACY_SDR_P998_TARGET
                - IRIS_26612_LEGACY_SDR_P99_TARGET);
        float sdrP99Target = iris26582Clamp(IRIS_26612_LEGACY_SDR_P99_TARGET
                - 0.040f * broadPressure - 0.130f * compactPressure, 0.80f,
                IRIS_26612_LEGACY_SDR_P99_TARGET);
        float sdrP995Target = legacyP995Target
                - 0.020f * broadPressure - 0.050f * compactPressure;
        if (broadPressure > 1.0e-6f || compactPressure > 1.0e-6f) {
            sdrP995Target = iris26582Clamp(sdrP995Target,
                    sdrP99Target + 0.001f, IRIS_26612_LEGACY_SDR_P998_TARGET - 0.001f);
        }
        float sdrP998Target = IRIS_26612_LEGACY_SDR_P998_TARGET;

        float hdrP99Target = IRIS_26612_LEGACY_HDR_P99_TARGET
                + 0.15f * broadPressure + 0.20f * compactPressure;
        float hdrP998Target = IRIS_26612_LEGACY_HDR_P998_TARGET
                + 0.35f * broadPressure + 1.25f * compactPressure;
        hdrP998Target = Math.min(hdrP998Target, 7.0f);
        float hdrP99Boost = Math.max(1.0f, hdrP99Target / Math.max(sourceP99Final, 1.0e-4f));
        float hdrP998Boost = Math.max(hdrP99Boost,
                hdrP998Target / Math.max(sourceP998Final, 1.0e-4f));
        float legacyP995Boost = hdrP99Boost + p995Position * (hdrP998Boost - hdrP99Boost);
        float hdrP995Boost = legacyP995Boost
                * (1.0f + 0.08f * broadPressure + 0.16f * compactPressure);
        hdrP995Boost = Math.max(hdrP99Boost, Math.min(hdrP995Boost, hdrP998Boost));

        return new Iris26612TonePlan(sourceP99Final, sourceP995Final, sourceP998Final,
                sdrP99Target, sdrP995Target, sdrP998Target,
                hdrP99Boost, hdrP995Boost, hdrP998Boost,
                broadPressure, compactPressure, gainPressure, 1.0f);
    }

    static float iris26612BaselineMotionSdr(float sourceFinal) {
        if (sourceFinal <= IRIS_26612_SDR_BODY_ANCHOR) return sourceFinal;
        float reserve = 1.0f - IRIS_26612_SDR_BODY_ANCHOR;
        float excess = sourceFinal - IRIS_26612_SDR_BODY_ANCHOR;
        return IRIS_26612_SDR_BODY_ANCHOR + reserve * excess / (excess + reserve);
    }

    static float iris26612MapMotionSdrSourceFinal(float sourceFinal, Iris26612TonePlan plan) {
        float baseline = iris26612BaselineMotionSdr(sourceFinal);
        if (plan == null || plan.strength <= 0.0f
                || sourceFinal <= IRIS_26612_SDR_BODY_ANCHOR) return baseline;
        float a = plan.sourceP99Final, c = plan.sourceP995Final, b = plan.sourceP998Final;
        if (!(b > a + 0.01f && c > a && c < b
                && a > IRIS_26612_SDR_BODY_ANCHOR + 0.02f)) return baseline;
        float mapped;
        if (sourceFinal <= a) {
            float t = iris26582Clamp((sourceFinal - IRIS_26612_SDR_BODY_ANCHOR)
                    / (a - IRIS_26612_SDR_BODY_ANCHOR), 0.0f, 1.0f);
            mapped = IRIS_26612_SDR_BODY_ANCHOR
                    + t * (plan.sdrP99Target - IRIS_26612_SDR_BODY_ANCHOR);
        } else if (sourceFinal <= c) {
            float t = iris26582Clamp((sourceFinal - a) / Math.max(c - a, 1.0e-6f), 0.0f, 1.0f);
            mapped = plan.sdrP99Target + t * (plan.sdrP995Target - plan.sdrP99Target);
        } else if (sourceFinal <= b) {
            float t = iris26582Clamp((sourceFinal - c) / Math.max(b - c, 1.0e-6f), 0.0f, 1.0f);
            mapped = plan.sdrP995Target + t * (plan.sdrP998Target - plan.sdrP995Target);
        } else {
            float excess = sourceFinal - b;
            float span = Math.max(b - a, 0.05f);
            mapped = plan.sdrP998Target + (1.0f - plan.sdrP998Target)
                    * excess / (excess + span);
        }
        return baseline + (mapped - baseline) * plan.strength;
    }

    static float iris26612MapMotionSdrFinalGuide(float sourceGuide, float brightnessTargetGain,
                                                  Iris26612TonePlan plan) {
        float sourceFinal = sourceGuide * Math.max(brightnessTargetGain, 1.0e-6f)
                * OUTPUT_EXPOSURE_SCALE;
        return iris26612MapMotionSdrSourceFinal(sourceFinal, plan);
    }

    static float iris26612MapHdrTargetLuma(float hdrBase, float sourceFinal, Iris26612TonePlan plan) {
        if (plan == null || plan.strength <= 0.0f || hdrBase <= 0.0f) return hdrBase;
        float a = plan.sourceP99Final, c = plan.sourceP995Final, b = plan.sourceP998Final;
        if (!(b > a + 0.01f && c > a && c < b
                && a > IRIS_26612_SDR_BODY_ANCHOR + 0.02f)) return hdrBase;
        float start = Math.max(IRIS_26612_SDR_BODY_ANCHOR, a * 0.75f);
        if (sourceFinal <= start) return hdrBase;
        float boost;
        if (sourceFinal <= a) {
            float t = iris26582Clamp((sourceFinal - start) / Math.max(a - start, 1.0e-6f), 0.0f, 1.0f);
            boost = 1.0f + t * (plan.hdrP99Boost - 1.0f);
        } else if (sourceFinal <= c) {
            float t = iris26582Clamp((sourceFinal - a) / Math.max(c - a, 1.0e-6f), 0.0f, 1.0f);
            boost = plan.hdrP99Boost + t * (plan.hdrP995Boost - plan.hdrP99Boost);
        } else if (sourceFinal <= b) {
            float t = iris26582Clamp((sourceFinal - c) / Math.max(b - c, 1.0e-6f), 0.0f, 1.0f);
            boost = plan.hdrP995Boost + t * (plan.hdrP998Boost - plan.hdrP995Boost);
        } else {
            boost = plan.hdrP998Boost;
        }
        return hdrBase * (1.0f + (boost - 1.0f) * plan.strength);
    }

'''
replace_region(RENDERJ,start,end,new,'MotionV2Render plan')

# Java owner usages/telemetry.
replace_once(RENDERJ,'final Iris26610TonePlan iris26610Tone = iris26610TonePlan(basePipeline.mParameters);',
'''final Iris26612TonePlan iris26612Tone = iris26612TonePlan(basePipeline.mParameters);''','render plan local')
for old,newv,label in [
('glProg.setVar("iris26610SourceP99Final", iris26610Tone.sourceP99Final);',
 'glProg.setVar("iris26612SourceP99Final", iris26612Tone.sourceP99Final);\n        glProg.setVar("iris26612SourceP995Final", iris26612Tone.sourceP995Final);\n        glProg.setVar("iris26612SourceP998Final", iris26612Tone.sourceP998Final);\n        glProg.setVar("iris26612SdrP99Target", iris26612Tone.sdrP99Target);\n        glProg.setVar("iris26612SdrP995Target", iris26612Tone.sdrP995Target);\n        glProg.setVar("iris26612SdrP998Target", iris26612Tone.sdrP998Target);\n        glProg.setVar("iris26612ToneStrength", iris26612Tone.strength);','render uniforms'),
('glProg.setVar("iris26610SourceP998Final", iris26610Tone.sourceP998Final);\n        glProg.setVar("iris26610ToneStrength", iris26610Tone.strength);','', 'remove old render uniforms'),
('glProg.setVar("iris26610HdrP99Boost", iris26610Tone.hdrP99Boost);',
 'glProg.setVar("iris26612SourceP99Final", iris26612Tone.sourceP99Final);\n                glProg.setVar("iris26612SourceP995Final", iris26612Tone.sourceP995Final);\n                glProg.setVar("iris26612SourceP998Final", iris26612Tone.sourceP998Final);\n                glProg.setVar("iris26612HdrP99Boost", iris26612Tone.hdrP99Boost);\n                glProg.setVar("iris26612HdrP995Boost", iris26612Tone.hdrP995Boost);\n                glProg.setVar("iris26612HdrP998Boost", iris26612Tone.hdrP998Boost);\n                glProg.setVar("iris26612ToneStrength", iris26612Tone.strength);','gain uniforms'),
('glProg.setVar("iris26610HdrP998Boost", iris26610Tone.hdrP998Boost);\n                glProg.setVar("iris26610ToneStrength", iris26610Tone.strength);','', 'remove old gain uniforms'),
]: replace_once(RENDERJ,old,newv,label)
# replace telemetry block tokens individually
for old,newv,label in [
('iris26610Tone.sourceP99Final','iris26612Tone.sourceP99Final','tele p99'),
('iris26610Tone.sourceP998Final','iris26612Tone.sourceP998Final','tele p998'),
('iris26610Tone.hdrP99Boost','iris26612Tone.hdrP99Boost','tele hdr99'),
('iris26610Tone.hdrP998Boost','iris26612Tone.hdrP998Boost','tele hdr998'),
('iris26610Tone.strength','iris26612Tone.strength','tele strength'),
('IRIS_26610_SOURCE_DOMAIN_SDR_UHDR_SR_PARITY=true','IRIS_26612_UNIVERSAL_BODY_BROAD_COMPACT_SDR_UHDR_SR_PARITY=true','tele marker')
]:
    p=APP/RENDERJ; s=p.read_text();
    # all remaining references are telemetry strings/expressions after functional replacements; replace all safely.
    p.write_text(s.replace(old,newv))
# add extended 26612 telemetry before marker
replace_once(RENDERJ,
'''                + " iris26610ToneStrength=" + iris26612Tone.strength
                + " IRIS_26612_UNIVERSAL_BODY_BROAD_COMPACT_SDR_UHDR_SR_PARITY=true"
''',
'''                + " iris26612ToneStrength=" + iris26612Tone.strength
                + " iris26612SourceP995Final=" + iris26612Tone.sourceP995Final
                + " iris26612SdrTargets=" + iris26612Tone.sdrP99Target + ","
                    + iris26612Tone.sdrP995Target + "," + iris26612Tone.sdrP998Target
                + " iris26612HdrBoosts=" + iris26612Tone.hdrP99Boost + ","
                    + iris26612Tone.hdrP995Boost + "," + iris26612Tone.hdrP998Boost
                + " iris26612BroadPressure=" + iris26612Tone.broadPressure
                + " iris26612CompactPressure=" + iris26612Tone.compactPressure
                + " iris26612GainPressure=" + iris26612Tone.gainPressure
                + " IRIS_26612_UNIVERSAL_BODY_BROAD_COMPACT_SDR_UHDR_SR_PARITY=true"
''','render telemetry extension')

# Render GLSL uniforms + map function.
replace_once(RENDER,
'''uniform float iris26610SourceP99Final;
uniform float iris26610SourceP998Final;
uniform float iris26610ToneStrength;
''',
'''uniform float iris26612SourceP99Final;
uniform float iris26612SourceP995Final;
uniform float iris26612SourceP998Final;
uniform float iris26612SdrP99Target;
uniform float iris26612SdrP995Target;
uniform float iris26612SdrP998Target;
uniform float iris26612ToneStrength;
''','render uniforms glsl')
start='float iris26610MapSdrSourceFinal(float sourceFinal) {'
end='float mapFinalSdrGuide(float sourceGuide) {'
new=r'''float iris26612MapSdrSourceFinal(float sourceFinal) {
    const float body=0.40;
    float reserve=1.0-body;
    float baseline=sourceFinal<=body?sourceFinal:body+reserve*(sourceFinal-body)/(sourceFinal-body+reserve);
    float strength=clamp(iris26612ToneStrength,0.0,1.0);
    float a=iris26612SourceP99Final,c=iris26612SourceP995Final,b=iris26612SourceP998Final;
    if(strength<=0.0||sourceFinal<=body||a<=body+0.02||c<=a||b<=c||b<=a+0.01) return baseline;
    float mapped;
    if(sourceFinal<=a){
        float t=clamp((sourceFinal-body)/max(a-body,1.0e-6),0.0,1.0);
        mapped=body+t*(iris26612SdrP99Target-body);
    }else if(sourceFinal<=c){
        float t=clamp((sourceFinal-a)/max(c-a,1.0e-6),0.0,1.0);
        mapped=mix(iris26612SdrP99Target,iris26612SdrP995Target,t);
    }else if(sourceFinal<=b){
        float t=clamp((sourceFinal-c)/max(b-c,1.0e-6),0.0,1.0);
        mapped=mix(iris26612SdrP995Target,iris26612SdrP998Target,t);
    }else{
        float excess=sourceFinal-b;
        float span=max(b-a,0.05);
        mapped=iris26612SdrP998Target+(1.0-iris26612SdrP998Target)*excess/(excess+span);
    }
    return mix(baseline,mapped,strength);
}

'''
replace_region(RENDER,start,end,new,'render map glsl')
replace_once(RENDER,'return iris26610MapSdrSourceFinal(targetFinal);','return iris26612MapSdrSourceFinal(targetFinal);','render function call')

# Adaptive Java + shader mirrors exact SDR plan.
replace_once(ADAPTJ,
'''        final MotionV2Render.Iris26610TonePlan iris26610Tone =
                MotionV2Render.iris26610TonePlan(basePipeline.mParameters);
        glProg.setVar("sceneWhite", sceneWhite);
        glProg.setVar("iris26610SourceP99Final", iris26610Tone.sourceP99Final);
        glProg.setVar("iris26610SourceP998Final", iris26610Tone.sourceP998Final);
        glProg.setVar("iris26610ToneStrength", iris26610Tone.strength);
''',
'''        final MotionV2Render.Iris26612TonePlan iris26612Tone =
                MotionV2Render.iris26612TonePlan(basePipeline.mParameters);
        glProg.setVar("sceneWhite", sceneWhite);
        glProg.setVar("iris26612SourceP99Final", iris26612Tone.sourceP99Final);
        glProg.setVar("iris26612SourceP995Final", iris26612Tone.sourceP995Final);
        glProg.setVar("iris26612SourceP998Final", iris26612Tone.sourceP998Final);
        glProg.setVar("iris26612SdrP99Target", iris26612Tone.sdrP99Target);
        glProg.setVar("iris26612SdrP995Target", iris26612Tone.sdrP995Target);
        glProg.setVar("iris26612SdrP998Target", iris26612Tone.sdrP998Target);
        glProg.setVar("iris26612ToneStrength", iris26612Tone.strength);
''','adaptive java plan')
replace_once(ADAPTJ,
'''                + " iris26610ToneStrength=" + iris26610Tone.strength
                + " IRIS_26610_SOURCE_DOMAIN_TONE_PREDICTOR_PARITY=true"
''',
'''                + " iris26612ToneStrength=" + iris26612Tone.strength
                + " iris26612BroadPressure=" + iris26612Tone.broadPressure
                + " iris26612CompactPressure=" + iris26612Tone.compactPressure
                + " iris26612GainPressure=" + iris26612Tone.gainPressure
                + " IRIS_26612_UNIVERSAL_TONE_PREDICTOR_PARITY=true"
''','adaptive java telemetry')
replace_once(ADAPT,
'''uniform float iris26610SourceP99Final;
uniform float iris26610SourceP998Final;
uniform float iris26610ToneStrength;
''',
'''uniform float iris26612SourceP99Final;
uniform float iris26612SourceP995Final;
uniform float iris26612SourceP998Final;
uniform float iris26612SdrP99Target;
uniform float iris26612SdrP995Target;
uniform float iris26612SdrP998Target;
uniform float iris26612ToneStrength;
''','adaptive glsl uniforms')
start='float iris26610MapSdrSourceFinal(float sourceFinal){'
end='float iris26585PostTonePreGamutPeak(vec3 preDisplayRgb) {'
new=r'''float iris26612MapSdrSourceFinal(float sourceFinal){
    const float body=0.40;
    float reserve=1.0-body;
    float baseline=sourceFinal<=body?sourceFinal:body+reserve*(sourceFinal-body)/(sourceFinal-body+reserve);
    float strength=clamp(iris26612ToneStrength,0.0,1.0);
    float a=iris26612SourceP99Final,c=iris26612SourceP995Final,b=iris26612SourceP998Final;
    if(strength<=0.0||sourceFinal<=body||a<=body+0.02||c<=a||b<=c||b<=a+0.01)return baseline;
    float mapped;
    if(sourceFinal<=a){float t=clamp((sourceFinal-body)/max(a-body,1.0e-6),0.0,1.0);mapped=mix(body,iris26612SdrP99Target,t);}
    else if(sourceFinal<=c){float t=clamp((sourceFinal-a)/max(c-a,1.0e-6),0.0,1.0);mapped=mix(iris26612SdrP99Target,iris26612SdrP995Target,t);}
    else if(sourceFinal<=b){float t=clamp((sourceFinal-c)/max(b-c,1.0e-6),0.0,1.0);mapped=mix(iris26612SdrP995Target,iris26612SdrP998Target,t);}
    else{float e=sourceFinal-b,span=max(b-a,0.05);mapped=iris26612SdrP998Target+(1.0-iris26612SdrP998Target)*e/(e+span);}
    return mix(baseline,mapped,strength);
}

'''
replace_region(ADAPT,start,end,new,'adaptive map')
replace_once(ADAPT,'float mappedFinal=iris26610MapSdrSourceFinal(targetFinal);','float mappedFinal=iris26612MapSdrSourceFinal(targetFinal);','adaptive map call')

# Gainmap GLSL: exact same source anchors and HDR boost plan.
replace_once(GAIN,
'''uniform float iris26610SourceP99Final;
uniform float iris26610SourceP998Final;
uniform float iris26610ToneStrength;
''',
'''uniform float iris26612SourceP99Final;
uniform float iris26612SourceP995Final;
uniform float iris26612SourceP998Final;
uniform float iris26612HdrP99Boost;
uniform float iris26612HdrP995Boost;
uniform float iris26612HdrP998Boost;
uniform float iris26612ToneStrength;
''','gain uniforms')
# inspect and replace function start/end
start='float iris26610MapHdrTarget(float hdrBase,float sourceFinal){'
end='vec3 iris26524BilinearHdr(vec2 sourcePixel){'
new=r'''float iris26612MapHdrTarget(float hdrBase,float sourceFinal){
    float strength=clamp(iris26612ToneStrength,0.0,1.0);
    float a=iris26612SourceP99Final,c=iris26612SourceP995Final,b=iris26612SourceP998Final;
    if(strength<=0.0||hdrBase<=0.0||a<=0.42||c<=a||b<=c||b<=a+0.01)return hdrBase;
    float start=max(0.40,a*0.75);
    if(sourceFinal<=start)return hdrBase;
    float boost;
    if(sourceFinal<=a){float t=clamp((sourceFinal-start)/max(a-start,1.0e-6),0.0,1.0);boost=mix(1.0,iris26612HdrP99Boost,t);}
    else if(sourceFinal<=c){float t=clamp((sourceFinal-a)/max(c-a,1.0e-6),0.0,1.0);boost=mix(iris26612HdrP99Boost,iris26612HdrP995Boost,t);}
    else if(sourceFinal<=b){float t=clamp((sourceFinal-c)/max(b-c,1.0e-6),0.0,1.0);boost=mix(iris26612HdrP995Boost,iris26612HdrP998Boost,t);}
    else boost=iris26612HdrP998Boost;
    return hdrBase*mix(1.0,boost,strength);
}

'''
replace_region(GAIN,start,end,new,'gain map')
replace_once(GAIN,'float hdr=motionHdrHandoff!=0?iris26610MapHdrTarget(hdrBase,sourceFinal):hdrBase;','float hdr=motionHdrHandoff!=0?iris26612MapHdrTarget(hdrBase,sourceFinal):hdrBase;','gain call')

# Encoder: pass the single Java plan to true2x native.
replace_once(ENC,
'''            final MotionV2Render.Iris26610TonePlan iris26610Tone =
                    MotionV2Render.iris26610TonePlan(parameters);
''',
'''            final MotionV2Render.Iris26612TonePlan iris26612Tone =
                    MotionV2Render.iris26612TonePlan(parameters);
''','encoder plan')
replace_once(ENC,
'''                    iris26610Tone.sourceP99Final, iris26610Tone.sourceP998Final,
                    iris26610Tone.hdrP99Boost, iris26610Tone.hdrP998Boost,
                    iris26610Tone.strength,
''',
'''                    iris26612Tone.sourceP99Final, iris26612Tone.sourceP995Final,
                    iris26612Tone.sourceP998Final,
                    iris26612Tone.sdrP99Target, iris26612Tone.sdrP995Target,
                    iris26612Tone.sdrP998Target,
                    iris26612Tone.hdrP99Boost, iris26612Tone.hdrP995Boost,
                    iris26612Tone.hdrP998Boost, iris26612Tone.strength,
''','encoder native args')
# telemetry replace old block
replace_once(ENC,
'''                    + " iris26610SourceP99Final=" + iris26610Tone.sourceP99Final
                    + " iris26610SourceP998Final=" + iris26610Tone.sourceP998Final
                    + " iris26610HdrP99Boost=" + iris26610Tone.hdrP99Boost
                    + " iris26610HdrP998Boost=" + iris26610Tone.hdrP998Boost
                    + " iris26610ToneStrength=" + iris26610Tone.strength
''',
'''                    + " iris26612SourceP99Final=" + iris26612Tone.sourceP99Final
                    + " iris26612SourceP995Final=" + iris26612Tone.sourceP995Final
                    + " iris26612SourceP998Final=" + iris26612Tone.sourceP998Final
                    + " iris26612SdrTargets=" + iris26612Tone.sdrP99Target + ","
                        + iris26612Tone.sdrP995Target + "," + iris26612Tone.sdrP998Target
                    + " iris26612HdrBoosts=" + iris26612Tone.hdrP99Boost + ","
                        + iris26612Tone.hdrP995Boost + "," + iris26612Tone.hdrP998Boost
                    + " iris26612BroadPressure=" + iris26612Tone.broadPressure
                    + " iris26612CompactPressure=" + iris26612Tone.compactPressure
                    + " iris26612GainPressure=" + iris26612Tone.gainPressure
                    + " iris26612ToneStrength=" + iris26612Tone.strength
                    + " IRIS_26612_TRUE2X_UNIVERSAL_PRESENTATION_PLAN=true"
''','encoder telemetry')
replace_once(ENC,
'''            float iris26610SourceP99Final, float iris26610SourceP998Final,
            float iris26610HdrP99Boost, float iris26610HdrP998Boost, float iris26610ToneStrength,
''',
'''            float iris26612SourceP99Final, float iris26612SourceP995Final,
            float iris26612SourceP998Final,
            float iris26612SdrP99Target, float iris26612SdrP995Target, float iris26612SdrP998Target,
            float iris26612HdrP99Boost, float iris26612HdrP995Boost, float iris26612HdrP998Boost,
            float iris26612ToneStrength,
''','encoder native signature')

# Native CPU + embedded GPU: transport and mirror exact Java plan.
replace_once(CPP,
'''    float iris26610SourceP99Final=0.f,iris26610SourceP998Final=0.f;
    float iris26610HdrP99Boost=0.f,iris26610HdrP998Boost=0.f,iris26610ToneStrength=0.f;
''',
'''    float iris26612SourceP99Final=0.f,iris26612SourceP995Final=0.f,iris26612SourceP998Final=0.f;
    float iris26612SdrP99Target=0.95f,iris26612SdrP995Target=0.975f,iris26612SdrP998Target=0.995f;
    float iris26612HdrP99Boost=1.f,iris26612HdrP995Boost=1.f,iris26612HdrP998Boost=1.f,iris26612ToneStrength=0.f;
''','native params')
start='inline float iris26610MapSdrSourceFinal(float sourceFinal,const Params&p){'
end='inline Vec3 renderHeadroom(Vec3 rgb,const Params&p){'
new=r'''inline float iris26612MapSdrSourceFinal(float sourceFinal,const Params&p){
    constexpr float body=0.40f;
    float reserve=1.f-body;
    float baseline=sourceFinal<=body?sourceFinal:body+reserve*(sourceFinal-body)/(sourceFinal-body+reserve);
    float strength=clampf(p.iris26612ToneStrength,0.f,1.f),a=p.iris26612SourceP99Final,c=p.iris26612SourceP995Final,b=p.iris26612SourceP998Final;
    if(strength<=0.f||sourceFinal<=body||a<=body+0.02f||c<=a||b<=c||b<=a+0.01f)return baseline;
    float mapped;
    if(sourceFinal<=a){float t=clampf((sourceFinal-body)/std::max(a-body,1.0e-6f),0.f,1.f);mapped=body+t*(p.iris26612SdrP99Target-body);}
    else if(sourceFinal<=c){float t=clampf((sourceFinal-a)/std::max(c-a,1.0e-6f),0.f,1.f);mapped=p.iris26612SdrP99Target+t*(p.iris26612SdrP995Target-p.iris26612SdrP99Target);}
    else if(sourceFinal<=b){float t=clampf((sourceFinal-c)/std::max(b-c,1.0e-6f),0.f,1.f);mapped=p.iris26612SdrP995Target+t*(p.iris26612SdrP998Target-p.iris26612SdrP995Target);}
    else{float e=sourceFinal-b,span=std::max(b-a,0.05f);mapped=p.iris26612SdrP998Target+(1.f-p.iris26612SdrP998Target)*e/(e+span);}
    return baseline+(mapped-baseline)*strength;
}
inline float iris26612MapHdrTarget(float hdrBase,float sourceFinal,const Params&p){
    float strength=clampf(p.iris26612ToneStrength,0.f,1.f),a=p.iris26612SourceP99Final,c=p.iris26612SourceP995Final,b=p.iris26612SourceP998Final;
    if(strength<=0.f||hdrBase<=0.f||a<=0.42f||c<=a||b<=c||b<=a+0.01f)return hdrBase;
    float start=std::max(0.40f,a*0.75f);if(sourceFinal<=start)return hdrBase;float boost;
    if(sourceFinal<=a){float t=clampf((sourceFinal-start)/std::max(a-start,1.0e-6f),0.f,1.f);boost=1.f+t*(p.iris26612HdrP99Boost-1.f);}
    else if(sourceFinal<=c){float t=clampf((sourceFinal-a)/std::max(c-a,1.0e-6f),0.f,1.f);boost=p.iris26612HdrP99Boost+t*(p.iris26612HdrP995Boost-p.iris26612HdrP99Boost);}
    else if(sourceFinal<=b){float t=clampf((sourceFinal-c)/std::max(b-c,1.0e-6f),0.f,1.f);boost=p.iris26612HdrP995Boost+t*(p.iris26612HdrP998Boost-p.iris26612HdrP995Boost);}
    else boost=p.iris26612HdrP998Boost;
    return hdrBase*(1.f+(boost-1.f)*strength);
}
'''
replace_region(CPP,start,end,new,'native cpu maps')
replace_once(CPP,'mappedFinal=iris26610MapSdrSourceFinal(targetFinal,p);','mappedFinal=iris26612MapSdrSourceFinal(targetFinal,p);','native cpu sdr call')

# Two CPU publication helpers (direct and cached) must be byte-equivalent.
pp=APP/CPP; ss=pp.read_text(); nn=ss.count('iris26610MapHdrTarget(hdrBase,sourceFinal,p)')
if nn!=2: raise SystemExit(f'native cpu hdr calls: expected 2 anchors, got {nn}')
pp.write_text(ss.replace('iris26610MapHdrTarget(hdrBase,sourceFinal,p)','iris26612MapHdrTarget(hdrBase,sourceFinal,p)'))

# Embedded GPU uniforms.
replace_once(CPP,
'''uniform float uIris26610SourceP99Final;
uniform float uIris26610SourceP998Final;
uniform float uIris26610HdrP99Boost;
uniform float uIris26610HdrP998Boost;
uniform float uIris26610ToneStrength;
''',
'''uniform float uIris26612SourceP99Final;
uniform float uIris26612SourceP995Final;
uniform float uIris26612SourceP998Final;
uniform float uIris26612SdrP99Target;
uniform float uIris26612SdrP995Target;
uniform float uIris26612SdrP998Target;
uniform float uIris26612HdrP99Boost;
uniform float uIris26612HdrP995Boost;
uniform float uIris26612HdrP998Boost;
uniform float uIris26612ToneStrength;
''','native gpu uniforms')
start='float iris26610MapSdrSourceFinal(float sourceFinal){'
end='vec3 irisHeadroom(vec3 rgb){'
new=r'''float iris26612MapSdrSourceFinal(float sourceFinal){
    const float body=0.40;float reserve=1.0-body;float baseline=sourceFinal<=body?sourceFinal:body+reserve*(sourceFinal-body)/(sourceFinal-body+reserve);
    float strength=clamp(uIris26612ToneStrength,0.0,1.0),a=uIris26612SourceP99Final,c=uIris26612SourceP995Final,b=uIris26612SourceP998Final;
    if(strength<=0.0||sourceFinal<=body||a<=body+0.02||c<=a||b<=c||b<=a+0.01)return baseline;float mapped;
    if(sourceFinal<=a){float t=clamp((sourceFinal-body)/max(a-body,1e-6),0.0,1.0);mapped=mix(body,uIris26612SdrP99Target,t);}
    else if(sourceFinal<=c){float t=clamp((sourceFinal-a)/max(c-a,1e-6),0.0,1.0);mapped=mix(uIris26612SdrP99Target,uIris26612SdrP995Target,t);}
    else if(sourceFinal<=b){float t=clamp((sourceFinal-c)/max(b-c,1e-6),0.0,1.0);mapped=mix(uIris26612SdrP995Target,uIris26612SdrP998Target,t);}
    else{float e=sourceFinal-b,span=max(b-a,0.05);mapped=uIris26612SdrP998Target+(1.0-uIris26612SdrP998Target)*e/(e+span);}return mix(baseline,mapped,strength);
}
float iris26612MapHdrTarget(float hdrBase,float sourceFinal){
    float strength=clamp(uIris26612ToneStrength,0.0,1.0),a=uIris26612SourceP99Final,c=uIris26612SourceP995Final,b=uIris26612SourceP998Final;
    if(strength<=0.0||hdrBase<=0.0||a<=0.42||c<=a||b<=c||b<=a+0.01)return hdrBase;float start=max(0.40,a*0.75);if(sourceFinal<=start)return hdrBase;float boost;
    if(sourceFinal<=a){float t=clamp((sourceFinal-start)/max(a-start,1e-6),0.0,1.0);boost=mix(1.0,uIris26612HdrP99Boost,t);}
    else if(sourceFinal<=c){float t=clamp((sourceFinal-a)/max(c-a,1e-6),0.0,1.0);boost=mix(uIris26612HdrP99Boost,uIris26612HdrP995Boost,t);}
    else if(sourceFinal<=b){float t=clamp((sourceFinal-c)/max(b-c,1e-6),0.0,1.0);boost=mix(uIris26612HdrP995Boost,uIris26612HdrP998Boost,t);}
    else boost=uIris26612HdrP998Boost;return hdrBase*mix(1.0,boost,strength);
}
'''
replace_region(CPP,start,end,new,'native gpu maps')
replace_once(CPP,'mappedFinal=iris26610MapSdrSourceFinal(targetFinal);','mappedFinal=iris26612MapSdrSourceFinal(targetFinal);','gpu sdr call')
replace_once(CPP,'iris26610MapHdrTarget(hdrBase,sourceFinal)','iris26612MapHdrTarget(hdrBase,sourceFinal)','gpu hdr call')

# GPU uniform setters exact plan.
old='glUniform1f(loc("uIris26610SourceP99Final"),params->iris26610SourceP99Final);glUniform1f(loc("uIris26610SourceP998Final"),params->iris26610SourceP998Final);glUniform1f(loc("uIris26610HdrP99Boost"),params->iris26610HdrP99Boost);glUniform1f(loc("uIris26610HdrP998Boost"),params->iris26610HdrP998Boost);glUniform1f(loc("uIris26610ToneStrength"),params->iris26610ToneStrength);'
new='glUniform1f(loc("uIris26612SourceP99Final"),params->iris26612SourceP99Final);glUniform1f(loc("uIris26612SourceP995Final"),params->iris26612SourceP995Final);glUniform1f(loc("uIris26612SourceP998Final"),params->iris26612SourceP998Final);glUniform1f(loc("uIris26612SdrP99Target"),params->iris26612SdrP99Target);glUniform1f(loc("uIris26612SdrP995Target"),params->iris26612SdrP995Target);glUniform1f(loc("uIris26612SdrP998Target"),params->iris26612SdrP998Target);glUniform1f(loc("uIris26612HdrP99Boost"),params->iris26612HdrP99Boost);glUniform1f(loc("uIris26612HdrP995Boost"),params->iris26612HdrP995Boost);glUniform1f(loc("uIris26612HdrP998Boost"),params->iris26612HdrP998Boost);glUniform1f(loc("uIris26612ToneStrength"),params->iris26612ToneStrength);'
replace_once(CPP,old,new,'gpu setter')

# JNI signature and assignment/validation.
replace_once(CPP,
'''        jfloat iris26610SourceP99Final,jfloat iris26610SourceP998Final,jfloat iris26610HdrP99Boost,jfloat iris26610HdrP998Boost,jfloat iris26610ToneStrength,jobject watermarkBitmap,
''',
'''        jfloat iris26612SourceP99Final,jfloat iris26612SourceP995Final,jfloat iris26612SourceP998Final,
        jfloat iris26612SdrP99Target,jfloat iris26612SdrP995Target,jfloat iris26612SdrP998Target,
        jfloat iris26612HdrP99Boost,jfloat iris26612HdrP995Boost,jfloat iris26612HdrP998Boost,jfloat iris26612ToneStrength,jobject watermarkBitmap,
''','jni signature')
old='p.iris26610SourceP99Final=(float)iris26610SourceP99Final;p.iris26610SourceP998Final=(float)iris26610SourceP998Final;p.iris26610HdrP99Boost=(float)iris26610HdrP99Boost;p.iris26610HdrP998Boost=(float)iris26610HdrP998Boost;p.iris26610ToneStrength=clampf((float)iris26610ToneStrength,0.f,1.f);'
new='p.iris26612SourceP99Final=(float)iris26612SourceP99Final;p.iris26612SourceP995Final=(float)iris26612SourceP995Final;p.iris26612SourceP998Final=(float)iris26612SourceP998Final;p.iris26612SdrP99Target=(float)iris26612SdrP99Target;p.iris26612SdrP995Target=(float)iris26612SdrP995Target;p.iris26612SdrP998Target=(float)iris26612SdrP998Target;p.iris26612HdrP99Boost=(float)iris26612HdrP99Boost;p.iris26612HdrP995Boost=(float)iris26612HdrP995Boost;p.iris26612HdrP998Boost=(float)iris26612HdrP998Boost;p.iris26612ToneStrength=clampf((float)iris26612ToneStrength,0.f,1.f);'
replace_once(CPP,old,new,'jni assign')
old='||!std::isfinite(p.iris26610SourceP99Final)||!std::isfinite(p.iris26610SourceP998Final)||!std::isfinite(p.iris26610HdrP99Boost)||!std::isfinite(p.iris26610HdrP998Boost)||!std::isfinite(p.iris26610ToneStrength)'
new='||!std::isfinite(p.iris26612SourceP99Final)||!std::isfinite(p.iris26612SourceP995Final)||!std::isfinite(p.iris26612SourceP998Final)||!std::isfinite(p.iris26612SdrP99Target)||!std::isfinite(p.iris26612SdrP995Target)||!std::isfinite(p.iris26612SdrP998Target)||!std::isfinite(p.iris26612HdrP99Boost)||!std::isfinite(p.iris26612HdrP995Boost)||!std::isfinite(p.iris26612HdrP998Boost)||!std::isfinite(p.iris26612ToneStrength)'
replace_once(CPP,old,new,'jni validation')

# Final stale owner guards.
for rel in [RENDERJ,ADAPTJ,ENC,RENDER,GAIN,ADAPT,CPP]:
    txt=(APP/rel).read_text()
    # old identifiers may survive only in historical comments; active function/uniform names must be gone.
    for forbidden in ['iris26610MapSdrSourceFinal(', 'iris26610MapHdrTarget(', 'Iris26610TonePlan iris26610Tone', 'uIris26610SourceP99Final']:
        if forbidden in txt: raise SystemExit(f'stale active 26610 presentation owner survived {rel}: {forbidden}')
must(RENDERJ,'IRIS_26612_UNIVERSAL_BODY_BROAD_COMPACT_PRESENTATION','plan marker')
must(RENDER,'iris26612SdrP995Target','1x target')
must(GAIN,'iris26612HdrP995Boost','1x UHDR midtail')
must(CPP,'uIris26612SdrP995Target','true2x GPU parity')
print('PASS transform 26612 V1')
