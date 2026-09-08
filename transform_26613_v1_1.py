from pathlib import Path
import re, shutil, sys
if len(sys.argv)!=3: raise SystemExit('usage: transform_26613_v1_1.py BASE OUT')
base=Path(sys.argv[1]); out=Path(sys.argv[2])
if not (base/'app').is_dir(): raise SystemExit('base app missing')
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out)

def p(rel): return out/rel

def replace_once(text, old, new, label):
    n=text.count(old)
    if n!=1: raise SystemExit(f'{label}: expected 1 exact match got {n}')
    return text.replace(old,new,1)

def sub_once(text, pattern, repl, label, flags=0):
    outt,n=re.subn(pattern,repl,text,count=1,flags=flags)
    if n!=1: raise SystemExit(f'{label}: expected 1 regex match got {n}')
    return outt

# 1 render.glsl: retire moving quantile knots, fixed C1 upper shoulder.
f=p('app/src/main/assets/shaders/motionv2/render.glsl'); s=f.read_text()
s=sub_once(s, r'uniform float iris26612SourceP99Final;\nuniform float iris26612SourceP995Final;\nuniform float iris26612SourceP998Final;\nuniform float iris26612SdrP99Target;\nuniform float iris26612SdrP995Target;\nuniform float iris26612SdrP998Target;\nuniform float iris26612ToneStrength;\n', '', 'render old uniforms')
s=sub_once(s, r'float iris26612MapSdrSourceFinal\(float sourceFinal\) \{.*?\n\}\n\nfloat mapFinalSdrGuide', '''/* IRIS_26613_FIXED_DOMAIN_UPPER_HIGHLIGHT_SHOULDER
 * Device 26612 proved that scene-quantile knots can collapse together and create artificial
 * slope changes while also remapping unrelated body structure. Motion now has one fixed-domain,
 * C1-continuous scalar shoulder. Values through 0.80 final-linear are exact identity; only the
 * upper display range is compressed. No histogram percentile participates in publication. */
float iris26613MapSdrSourceFinal(float sourceFinal) {
    const float knee = 0.80;
    const float reserve = 1.0 - knee;
    if (sourceFinal <= knee) return sourceFinal;
    float excess = sourceFinal - knee;
    return knee + reserve * excess / (excess + reserve);
}

float mapFinalSdrGuide''', 'render map function', re.S)
s=s.replace('/* IRIS_26610_SOURCE_DOMAIN_SDR_OWNER */\n        return iris26612MapSdrSourceFinal(targetFinal);', '/* IRIS_26613_FIXED_DOMAIN_SDR_OWNER */\n        return iris26613MapSdrSourceFinal(targetFinal);')
f.write_text(s)

# 2 gainmap.glsl: clean extended-HDR master is direct HDR authority; no quantile target boost.
f=p('app/src/main/assets/shaders/motionv2/gainmap.glsl'); s=f.read_text()
s=sub_once(s, r'uniform float iris26612SourceP99Final;\nuniform float iris26612SourceP995Final;\nuniform float iris26612SourceP998Final;\nuniform float iris26612HdrP99Boost;\nuniform float iris26612HdrP995Boost;\nuniform float iris26612HdrP998Boost;\nuniform float iris26612ToneStrength;\n', '', 'gainmap old uniforms')
s=sub_once(s, r'float max3\(vec3 v\)\{return max\(v\.r,max\(v\.g,v\.b\)\);\}\nfloat iris26612MapHdrTarget\(float hdrBase,float sourceFinal\)\{.*?\n\}\n\n', 'float max3(vec3 v){return max(v.r,max(v.g,v.b));}\n\n', 'gainmap hdr map', re.S)
s=replace_once(s, '    float sourceFinal=max3(hdrPositive)*hdrTargetScale;\n    float hdr=motionHdrHandoff!=0?iris26612MapHdrTarget(hdrBase,sourceFinal):hdrBase;\n', '    /* IRIS_26613_CLEAN_HDR_MASTER_GAIN_AUTHORITY\n     * The common clean extended-HDR master is already scene-radiance authority. UHDR derives only\n     * its reversible HDR/SDR relationship here; no second percentile-driven HDR boost exists. */\n    float hdr=hdrBase;\n', 'gainmap main')
f.write_text(s)

# 3 adaptive appearance GLSL: predictor mirrors fixed Motion shoulder only.
f=p('app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl'); s=f.read_text()
s=sub_once(s, r'uniform float iris26612SourceP99Final;\nuniform float iris26612SourceP995Final;\nuniform float iris26612SourceP998Final;\nuniform float iris26612SdrP99Target;\nuniform float iris26612SdrP995Target;\nuniform float iris26612SdrP998Target;\nuniform float iris26612ToneStrength;\n', '', 'adaptive old uniforms')
s=sub_once(s, r'float iris26612MapSdrSourceFinal\(float sourceFinal\)\{.*?\n\}\n\nfloat iris26585PostTonePreGamutPeak', '''float iris26613MapSdrSourceFinal(float sourceFinal){
    const float knee=0.80;
    const float reserve=1.0-knee;
    if(sourceFinal<=knee)return sourceFinal;
    float excess=sourceFinal-knee;
    return knee+reserve*excess/(excess+reserve);
}

float iris26585PostTonePreGamutPeak''', 'adaptive map', re.S)
s=s.replace('float mappedFinal=iris26612MapSdrSourceFinal(targetFinal);','float mappedFinal=iris26613MapSdrSourceFinal(targetFinal);')
f.write_text(s)

# 4 MotionV2Render.java: remove quantile plan authority and setters; fixed knee constants/functions.
f=p('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'); s=f.read_text()
start=s.index('    /* IRIS_26612_UNIVERSAL_BODY_BROAD_COMPACT_PRESENTATION')
end=s.index('    public MotionV2Render() { super("", "MotionV2Render"); }')
new='''    /* IRIS_26613_FIXED_DOMAIN_UPPER_HIGHLIGHT_PRESENTATION
     * 26612's moving p99/p995/p998 knots are retired as rendition authorities. Motion publication
     * is exact identity through 0.80 final-linear and uses one C1 rational shoulder above it.
     * Scene statistics remain diagnostic inputs elsewhere only; they cannot move this curve. */
    public static final float IRIS_26613_SDR_KNEE_FINAL = 0.80f;

    static float iris26613MapMotionSdrSourceFinal(float sourceFinal) {
        if (sourceFinal <= IRIS_26613_SDR_KNEE_FINAL) return sourceFinal;
        float reserve = 1.0f - IRIS_26613_SDR_KNEE_FINAL;
        float excess = sourceFinal - IRIS_26613_SDR_KNEE_FINAL;
        return IRIS_26613_SDR_KNEE_FINAL + reserve * excess / (excess + reserve);
    }

    static float iris26613MapMotionSdrFinalGuide(float sourceGuide, float brightnessTargetGain) {
        float sourceFinal = sourceGuide * Math.max(brightnessTargetGain, 1.0e-6f)
                * OUTPUT_EXPOSURE_SCALE;
        return iris26613MapMotionSdrSourceFinal(sourceFinal);
    }

    static float iris26613MapHdrTargetLuma(float hdrBase) {
        return hdrBase;
    }

'''
s=s[:start]+new+s[end:]
s=s.replace('        final Iris26612TonePlan iris26612Tone = iris26612TonePlan(basePipeline.mParameters);\n','')
for line in [
'        glProg.setVar("iris26612SourceP99Final", iris26612Tone.sourceP99Final);\n',
'        glProg.setVar("iris26612SourceP995Final", iris26612Tone.sourceP995Final);\n',
'        glProg.setVar("iris26612SourceP998Final", iris26612Tone.sourceP998Final);\n',
'        glProg.setVar("iris26612SdrP99Target", iris26612Tone.sdrP99Target);\n',
'        glProg.setVar("iris26612SdrP995Target", iris26612Tone.sdrP995Target);\n',
'        glProg.setVar("iris26612SdrP998Target", iris26612Tone.sdrP998Target);\n',
'        glProg.setVar("iris26612ToneStrength", iris26612Tone.strength);\n',
'                glProg.setVar("iris26612SourceP99Final", iris26612Tone.sourceP99Final);\n',
'                glProg.setVar("iris26612SourceP995Final", iris26612Tone.sourceP995Final);\n',
'                glProg.setVar("iris26612SourceP998Final", iris26612Tone.sourceP998Final);\n',
'                glProg.setVar("iris26612HdrP99Boost", iris26612Tone.hdrP99Boost);\n',
'                glProg.setVar("iris26612HdrP995Boost", iris26612Tone.hdrP995Boost);\n',
'                glProg.setVar("iris26612HdrP998Boost", iris26612Tone.hdrP998Boost);\n',
'                glProg.setVar("iris26612ToneStrength", iris26612Tone.strength);\n']:
    s=s.replace(line,'')
# The removed 26612 gain-map setter block left a spaces-only line in its place. Preserve
# surrounding source exactly while normalizing only that newly-created blank line.
s=s.replace('                                                \n', '\n')
# Replace the old telemetry tail block exactly by regex.
s=sub_once(s, r'\n\s*\+ " iris26610SourceP99Final=" \+ iris26612Tone\.sourceP99Final.*?\+ " IRIS_26612_UNIVERSAL_BODY_BROAD_COMPACT_SDR_UHDR_SR_PARITY=true"', '\n                + " iris26613SdrKneeFinal=" + IRIS_26613_SDR_KNEE_FINAL\n                + " iris26613QuantileToneAuthority=false"\n                + " iris26613CleanHdrMasterGainAuthority=true"\n                + " IRIS_26613_FIXED_DOMAIN_SDR_UHDR_SR_PARITY=true"', 'render telemetry', re.S)
f.write_text(s)

# 5 Adaptive Java: remove plan and uniforms; report fixed predictor.
f=p('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java'); s=f.read_text()
s=sub_once(s, r'        final MotionV2Render\.Iris26612TonePlan iris26612Tone =\n                MotionV2Render\.iris26612TonePlan\(basePipeline\.mParameters\);\n', '', 'adaptive java plan')
s=sub_once(s, r'        glProg\.setVar\("iris26612SourceP99Final".*?        glProg\.setVar\("iris26612ToneStrength", iris26612Tone\.strength\);\n', '', 'adaptive java setters', re.S)
s=sub_once(s, r'\n\s*\+ " iris26612ToneStrength=" \+ iris26612Tone\.strength.*?\+ " IRIS_26612_UNIVERSAL_TONE_PREDICTOR_PARITY=true"', '\n                + " iris26613SdrKneeFinal=" + MotionV2Render.IRIS_26613_SDR_KNEE_FINAL\n                + " iris26613QuantileToneAuthority=false"\n                + " IRIS_26613_FIXED_DOMAIN_TONE_PREDICTOR_PARITY=true"', 'adaptive java telemetry', re.S)
f.write_text(s)

# 6 Encoder Java: remove plan transport and quantile telemetry/signature.
f=p('app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java'); s=f.read_text()
s=sub_once(s, r'            final MotionV2Render\.Iris26612TonePlan iris26612Tone =\n                    MotionV2Render\.iris26612TonePlan\(parameters\);\n', '', 'encoder plan')
s=sub_once(s, r'                    publicationSceneWhite, parameters\.motionV2Active,\n                    iris26612Tone\.sourceP99Final, iris26612Tone\.sourceP995Final,\n                    iris26612Tone\.sourceP998Final,\n                    iris26612Tone\.sdrP99Target, iris26612Tone\.sdrP995Target,\n                    iris26612Tone\.sdrP998Target,\n                    iris26612Tone\.hdrP99Boost, iris26612Tone\.hdrP995Boost,\n                    iris26612Tone\.hdrP998Boost, iris26612Tone\.strength,\n                    watermark,', '                    publicationSceneWhite, parameters.motionV2Active,\n                    watermark,', 'encoder args')
s=sub_once(s, r'\n\s*\+ " iris26612SourceP99Final=".*?\+ " IRIS_26612_TRUE2X_UNIVERSAL_PRESENTATION_PLAN=true"', '\n                    + " iris26613SdrKneeFinal=" + MotionV2Render.IRIS_26613_SDR_KNEE_FINAL\n                    + " iris26613QuantileToneAuthority=false"\n                    + " iris26613CleanHdrMasterGainAuthority=true"\n                    + " IRIS_26613_TRUE2X_FIXED_DOMAIN_PRESENTATION=true"', 'encoder telemetry', re.S)
s=sub_once(s, r'            float exposureEv, float shadows, float contrast, float sceneWhite, boolean motionHdrHandoff,\n            float iris26612SourceP99Final, float iris26612SourceP995Final,\n            float iris26612SourceP998Final,\n            float iris26612SdrP99Target, float iris26612SdrP995Target, float iris26612SdrP998Target,\n            float iris26612HdrP99Boost, float iris26612HdrP995Boost, float iris26612HdrP998Boost,\n            float iris26612ToneStrength,\n            Bitmap watermark,', '            float exposureEv, float shadows, float contrast, float sceneWhite, boolean motionHdrHandoff,\n            Bitmap watermark,', 'encoder native signature')
f.write_text(s)

# 7 C++ true2x CPU/GPU publication: remove plan fields/args, fixed shoulder, no HDR boost.
f=p('app/src/main/cpp/motionv2_jpeg444_jni.cpp'); s=f.read_text()
s=sub_once(s, r'    float iris26612SourceP99Final=0\.f,iris26612SourceP995Final=0\.f,iris26612SourceP998Final=0\.f;\n    float iris26612SdrP99Target=0\.95f,iris26612SdrP995Target=0\.975f,iris26612SdrP998Target=0\.995f;\n    float iris26612HdrP99Boost=1\.f,iris26612HdrP995Boost=1\.f,iris26612HdrP998Boost=1\.f,iris26612ToneStrength=0\.f;\n', '', 'cpp params fields')
s=sub_once(s, r'inline float iris26612MapSdrSourceFinal\(float sourceFinal,const Params&p\)\{.*?\n\}\ninline float iris26612MapHdrTarget\(float hdrBase,float sourceFinal,const Params&p\)\{.*?\n\}\n', '''inline float iris26613MapSdrSourceFinal(float sourceFinal){
    constexpr float knee=0.80f,reserve=0.20f;
    if(sourceFinal<=knee)return sourceFinal;
    float excess=sourceFinal-knee;
    return knee+reserve*excess/(excess+reserve);
}
''', 'cpp maps', re.S)
s=s.replace('constexpr float scale=0.80f,knee=0.40f,reserve=0.60f;','constexpr float scale=0.80f;')
s=s.replace('mappedFinal=iris26612MapSdrSourceFinal(targetFinal,p);','mappedFinal=iris26613MapSdrSourceFinal(targetFinal);')
s=s.replace('float hdrBase=std::max(luma(clampNonnegative(hdr))*hdrScale,0.f),sourceFinal=peak(clampNonnegative(hdr))*hdrScale,hdrY=p.motionHdrHandoff?iris26612MapHdrTarget(hdrBase,sourceFinal,p):hdrBase,sdrY=', 'float hdrBase=std::max(luma(clampNonnegative(hdr))*hdrScale,0.f),hdrY=hdrBase,sdrY=')
# GPU shader uniforms and map functions
s=sub_once(s, r'uniform float uIris26612SourceP99Final;\nuniform float uIris26612SourceP995Final;\nuniform float uIris26612SourceP998Final;\nuniform float uIris26612SdrP99Target;\nuniform float uIris26612SdrP995Target;\nuniform float uIris26612SdrP998Target;\nuniform float uIris26612HdrP99Boost;\nuniform float uIris26612HdrP995Boost;\nuniform float uIris26612HdrP998Boost;\nuniform float uIris26612ToneStrength;\n', '', 'cpp gpu uniforms')
s=sub_once(s, r'float iris26612MapSdrSourceFinal\(float sourceFinal\)\{.*?\n\}\nfloat iris26612MapHdrTarget\(float hdrBase,float sourceFinal\)\{.*?\n\}\n', '''float iris26613MapSdrSourceFinal(float sourceFinal){
    const float knee=0.80,reserve=0.20;
    if(sourceFinal<=knee)return sourceFinal;
    float excess=sourceFinal-knee;
    return knee+reserve*excess/(excess+reserve);
}
''', 'cpp gpu maps', re.S)
s=s.replace('mappedFinal=iris26612MapSdrSourceFinal(targetFinal);','mappedFinal=iris26613MapSdrSourceFinal(targetFinal);')
s=s.replace('float hdrY=uMotionHdrHandoff!=0?iris26612MapHdrTarget(hdrBase,sourceFinal):hdrBase;','float hdrY=hdrBase;')
# remove giant glUniform chain segment for old fields
s=sub_once(s, r';glUniform1f\(loc\("uIris26612SourceP99Final"\),params->iris26612SourceP99Final\).*?;glUniform1f\(loc\("uIris26612ToneStrength"\),params->iris26612ToneStrength\)', '', 'cpp gpu setters', re.S)
s=s.replace('        float sourceFinal=irisPeak(irisClampNonnegative(hdr))*hdrScale;\n        float hdrY=hdrBase;', '        float hdrY=hdrBase;')
# JNI signature old args
s=sub_once(s, r'        jfloatArray sensorToProfile,jfloatArray profileToDisplay,jfloat displayGain,jfloat exposureEv,jfloat shadows,jfloat contrast,jfloat sceneWhite,jboolean motionHdrHandoff,\n        jfloat iris26612SourceP99Final,jfloat iris26612SourceP995Final,jfloat iris26612SourceP998Final,\n        jfloat iris26612SdrP99Target,jfloat iris26612SdrP995Target,jfloat iris26612SdrP998Target,\n        jfloat iris26612HdrP99Boost,jfloat iris26612HdrP995Boost,jfloat iris26612HdrP998Boost,jfloat iris26612ToneStrength,jobject watermarkBitmap,', '        jfloatArray sensorToProfile,jfloatArray profileToDisplay,jfloat displayGain,jfloat exposureEv,jfloat shadows,jfloat contrast,jfloat sceneWhite,jboolean motionHdrHandoff,\n        jobject watermarkBitmap,', 'cpp JNI sig')
# Params assignment line remove all quantile assignments
s=sub_once(s, r';p\.iris26612SourceP99Final=\(float\)iris26612SourceP99Final;.*?;p\.iris26612ToneStrength=clampf\(\(float\)iris26612ToneStrength,0\.f,1\.f\)', '', 'cpp param assigns', re.S)
# finite validation remove old fields
s=sub_once(s, r'\|\|!std::isfinite\(p\.iris26612SourceP99Final\).*?\|\|!std::isfinite\(p\.iris26612ToneStrength\)', '', 'cpp finite checks', re.S)
f.write_text(s)

# 8 Postprocessor: pass real Sabre support read-only into final false-color owner.
f=p('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'); s=f.read_text()
s=replace_once(s, '''    fun process(
        obtainCpuOutput: () -> ByteBuffer,
        deferCpuReadback: Boolean,
        onFinalSubmitted: (() -> Unit)? = null,
    ): Result {''', '''    fun process(
        obtainCpuOutput: () -> ByteBuffer,
        deferCpuReadback: Boolean,
        onFinalSubmitted: (() -> Unit)? = null,
        sabreSupportR: Int = 0,
        sabreSupportGb: Int = 0,
    ): Result {''', 'post process signature')
s=s.replace('        dispatchUniversalAdaptiveColor(assembledRgb, workA)','        dispatchUniversalAdaptiveColor(assembledRgb, workA, sabreSupportR, sabreSupportGb)')
s=replace_once(s, '''    private fun dispatchUniversalAdaptiveColor(source: Int, destination: Int) {
        check(universalAdaptiveColorProgram != 0)
        GLES31.glUseProgram(universalAdaptiveColorProgram)
        setImageSize(universalAdaptiveColorProgram)
        bindImage(0, source, GLES31.GL_READ_ONLY)
        bindImage(1, destination, GLES31.GL_WRITE_ONLY)
        trackedDispatch(
            "IRIS 26561 universal adaptive color",
            intArrayOf(source),
            intArrayOf(destination),
        )
        clearImages()
    }''', '''    private fun dispatchUniversalAdaptiveColor(
        source: Int,
        destination: Int,
        sabreSupportR: Int,
        sabreSupportGb: Int,
    ) {
        check(universalAdaptiveColorProgram != 0)
        val sabreSupportValid = sabreSupportR != 0 && sabreSupportGb != 0
        check((sabreSupportR == 0) == (sabreSupportGb == 0)) {
            "Sabre RGB support provenance must be provided as an R + GB pair"
        }
        GLES31.glUseProgram(universalAdaptiveColorProgram)
        setImageSize(universalAdaptiveColorProgram)
        bindImage(0, source, GLES31.GL_READ_ONLY)
        bindImage(1, destination, GLES31.GL_WRITE_ONLY)
        GLES31.glUniform1i(
            host.uniformLocation(universalAdaptiveColorProgram, "uSabreSupportValid"),
            if (sabreSupportValid) 1 else 0,
        )
        if (sabreSupportValid) {
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0 + 2)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, sabreSupportR)
            GLES31.glUniform1i(host.uniformLocation(universalAdaptiveColorProgram, "uSabreWeightR"), 2)
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0 + 3)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, sabreSupportGb)
            GLES31.glUniform1i(host.uniformLocation(universalAdaptiveColorProgram, "uSabreWeightsGb"), 3)
        }
        trackedDispatch(
            "IRIS 26613 Sabre-support-aware universal adaptive color",
            if (sabreSupportValid) intArrayOf(source, sabreSupportR, sabreSupportGb) else intArrayOf(source),
            intArrayOf(destination),
        )
        if (sabreSupportValid) {
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0 + 3)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, 0)
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0 + 2)
            GLES30.glBindTexture(GLES30.GL_TEXTURE_2D, 0)
            GLES30.glActiveTexture(GLES30.GL_TEXTURE0)
        }
        clearImages()
    }''', 'post dispatch')
# shader declarations
s=replace_once(s, '''        layout(rgba16ui, binding = 0) readonly uniform highp uimage2D uSource;
        layout(rgba16ui, binding = 1) writeonly uniform highp uimage2D uDestination;
        uniform ivec2 uImageSize;
''', '''        layout(rgba16ui, binding = 0) readonly uniform highp uimage2D uSource;
        layout(rgba16ui, binding = 1) writeonly uniform highp uimage2D uDestination;
        uniform ivec2 uImageSize;
        /* IRIS_26613_SABRE_CHANNEL_SUPPORT_PROVENANCE
         * Exact accumulated R/G/B weights from the common Sabre accumulator, sampled read-only.
         * These weights can authorize a decisive neutral false-color correction but never alter
         * temporal contribution, geometry, Resolve, VGN, or genuine supported color. */
        uniform highp sampler2D uSabreWeightR;
        uniform highp sampler2D uSabreWeightsGb;
        uniform int uSabreSupportValid;
''', 'post shader declarations')
# insert support evidence before fail-closed proof.
anchor='''            /* Fail-closed false-color proof.
             * 1) The center must disagree materially with same-surface consensus.'''
insert='''            vec3 sabreChannelSupport = vec3(1.0);
            float sabreSupportEvidence = 0.0;
            float sabreWeakChannelDirection = 0.0;
            if (uSabreSupportValid != 0) {
                sabreChannelSupport = vec3(
                    max(texelFetch(uSabreWeightR, p, 0).r, 0.0),
                    max(texelFetch(uSabreWeightsGb, p, 0).r, 0.0),
                    max(texelFetch(uSabreWeightsGb, p, 0).g, 0.0));
                float supportMax = max(sabreChannelSupport.r,
                    max(sabreChannelSupport.g, sabreChannelSupport.b));
                float supportMin = min(sabreChannelSupport.r,
                    min(sabreChannelSupport.g, sabreChannelSupport.b));
                float supportImbalance = supportMax > 1.0e-7
                    ? clamp((supportMax - supportMin) / supportMax, 0.0, 1.0) : 0.0;
                int weakChannel = sabreChannelSupport.r <= sabreChannelSupport.g &&
                        sabreChannelSupport.r <= sabreChannelSupport.b ? 0 :
                    (sabreChannelSupport.g <= sabreChannelSupport.b ? 1 : 2);
                vec3 supportTargetChroma = consensusNormalizedChroma * centerScale;
                vec3 supportDesiredDelta = supportTargetChroma - centerChroma;
                float supportDesiredLength = length(supportDesiredDelta);
                float weakIncrease = weakChannel == 0 ? supportDesiredDelta.r :
                    (weakChannel == 1 ? supportDesiredDelta.g : supportDesiredDelta.b);
                sabreWeakChannelDirection = supportDesiredLength > 1.0e-7
                    ? clamp(weakIncrease / supportDesiredLength, 0.0, 1.0) : 0.0;
                /* Continuous physical evidence: the more one channel lacks actual reconstruction
                 * support and the more the neutral correction specifically restores that channel,
                 * the stronger the evidence. No scene/object threshold participates. */
                sabreSupportEvidence = supportImbalance * sabreWeakChannelDirection;
            }

            /* Fail-closed false-color proof.
             * 1) The center must disagree materially with same-surface consensus.'''
s=replace_once(s,anchor,insert,'post support insertion')
# replace scoring block to allow actual support provenance to substitute for brittle RGB phase guess, while preserving legacy path.
old='''            float isolatedEvidence = smoothstep(1.35, 2.75, centerToConsensusMagnitude);
            float phaseConfidence = phaseLikeEvidence * mix(0.70, 1.0, isolatedEvidence);
            float falseColorScore = centerOutlierEvidence * neutralConsensusEvidence * surfaceSupport *
                neutralSurfaceSupport * phaseConfidence * (1.0 - realColorConfidence);
            float falseColorGate = smoothstep(0.72, 0.90, falseColorScore);
'''
new='''            float isolatedEvidence = smoothstep(1.35, 2.75, centerToConsensusMagnitude);
            float phaseConfidence = phaseLikeEvidence * mix(0.70, 1.0, isolatedEvidence);
            float falseColorBase = centerOutlierEvidence * neutralConsensusEvidence * surfaceSupport *
                neutralSurfaceSupport * (1.0 - realColorConfidence);
            float legacyFalseColorScore = falseColorBase * phaseConfidence;
            float physicalFalseColorScore = falseColorBase * sabreSupportEvidence;
            float falseColorScore = max(legacyFalseColorScore, physicalFalseColorScore);
            float falseColorGate = smoothstep(0.72, 0.90, falseColorScore);
'''
s=replace_once(s,old,new,'post score')
# Replace decisive proof: Sabre uses physical support; non-Sabre retains exact legacy phase proof.
old='''            float decisiveNeutralCfaProof =
                smoothstep(0.92, 0.985, falseColorScore) *
                smoothstep(0.88, 0.985, phaseLikeEvidence) *
                smoothstep(0.90, 0.995, neutralSurfaceSupport) *
                smoothstep(0.90, 0.995, targetNeutral) *
                (1.0 - smoothstep(0.02, 0.12, realColorConfidence));
'''
new='''            float legacyDecisiveNeutralCfaProof =
                smoothstep(0.92, 0.985, legacyFalseColorScore) *
                smoothstep(0.88, 0.985, phaseLikeEvidence) *
                smoothstep(0.90, 0.995, neutralSurfaceSupport) *
                smoothstep(0.90, 0.995, targetNeutral) *
                (1.0 - smoothstep(0.02, 0.12, realColorConfidence));
            float sabreDecisiveNeutralCfaProof =
                smoothstep(0.72, 0.94, physicalFalseColorScore) *
                smoothstep(0.20, 0.55, sabreSupportEvidence) *
                smoothstep(0.90, 0.995, neutralSurfaceSupport) *
                smoothstep(0.90, 0.995, targetNeutral) *
                (1.0 - smoothstep(0.02, 0.12, realColorConfidence));
            float decisiveNeutralCfaProof = uSabreSupportValid != 0
                ? sabreDecisiveNeutralCfaProof : legacyDecisiveNeutralCfaProof;
'''
s=replace_once(s,old,new,'post decisive')
f.write_text(s)

# 9 Stacker: retain copied R weight provenance and pass exact R/G/B weights to post-VGN cleanup.
f=p('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'); s=f.read_text()
s=replace_once(s, '''            renderSabreDehomogenize(
                resolveAccumulatedColor26604,
                resolveAccumulatedWeightsGb26604,
                accumulatedCoverage,
                alphaScale = accumulatedWeightScale / effectiveEvidenceCount26607.toFloat(),
                alphaBias = 1f / effectiveEvidenceCount26607.toFloat(),
            )''', '''            val sabreRSupport26613 = renderSabreDehomogenize(
                resolveAccumulatedColor26604,
                resolveAccumulatedWeightsGb26604,
                accumulatedCoverage,
                alphaScale = accumulatedWeightScale / effectiveEvidenceCount26607.toFloat(),
                alphaBias = 1f / effectiveEvidenceCount26607.toFloat(),
            )
            check(sabreRSupport26613 != 0) { "26613 Sabre R support provenance missing" }''', 'stacker dehom call')
s=replace_once(s, '''            val chromaResult = chromaPostprocessor.process(
                obtainCpuOutput = { checkNotNull(cpuOutput) },
                deferCpuReadback = exportGpuLinearRgbSource,
                onFinalSubmitted = if (exportGpuLinearRgbSource) {
                    { GLES30.glFlush() }
                } else {
                    null
                },
            )''', '''            val chromaResult = chromaPostprocessor.process(
                obtainCpuOutput = { checkNotNull(cpuOutput) },
                deferCpuReadback = exportGpuLinearRgbSource,
                onFinalSubmitted = if (exportGpuLinearRgbSource) {
                    { GLES30.glFlush() }
                } else {
                    null
                },
                sabreSupportR = sabreRSupport26613,
                sabreSupportGb = resolveAccumulatedWeightsGb26604,
            )
            releaseOwnedTexture(sabreRSupport26613, "26613 Sabre R support provenance")
            PLog.i(
                SABRE_TAG,
                "IRIS_26613_SABRE_RGB_SUPPORT_PROVENANCE " +
                    "source=COMMON_ACCUMULATED_R_G_B_WEIGHTS readOnly=true " +
                    "changesTemporalWeights=false changesResolve=false changesVgn=false",
            )''', 'stacker process call')
s=s.replace('    ) {\n        val copiedRWeight = createTexture(width, height, GLES30.GL_R16F, GLES30.GL_NEAREST)', '    ): Int {\n        val copiedRWeight = createTexture(width, height, GLES30.GL_R16F, GLES30.GL_NEAREST)',1)
s=replace_once(s, '''        } finally {
            GLES30.glBlendFunc(GLES30.GL_ONE, GLES30.GL_ONE)
            GLES30.glDisable(GLES30.GL_BLEND)
        }
    }

    /**
     * IRIS_26545_SABRE_MEASURED_SUPPORT''', '''        } finally {
            GLES30.glBlendFunc(GLES30.GL_ONE, GLES30.GL_ONE)
            GLES30.glDisable(GLES30.GL_BLEND)
        }
        return copiedRWeight
    }

    /**
     * IRIS_26545_SABRE_MEASURED_SUPPORT''', 'stacker return support')
f.write_text(s)

# 10 version
f=p('app/version.properties'); s=f.read_text()
s=re.sub(r'VERSION_NAME=.*', 'VERSION_NAME=0.9726613', s)
s=re.sub(r'VERSION_BUILD=.*', 'VERSION_BUILD=26613', s)
f.write_text(s)

# sanity expected no 26612 active presentation names in changed presentation files
for rel in [
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
]:
    txt=p(rel).read_text()
    if 'iris26612' in txt or 'IRIS_26612_' in txt:
        print('NOTE legacy 26612 marker remains in',rel)
print('candidate created')
