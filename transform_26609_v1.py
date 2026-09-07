from pathlib import Path
import shutil, sys, re

base=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/mnt/data/26609_work/base')
out=Path(sys.argv[2]) if len(sys.argv)>2 else Path('/mnt/data/26609_work/candidate_26609_dev')
if out.exists(): shutil.rmtree(out)
shutil.copytree(base,out)

def p(rel): return out/rel

def replace_once(rel, old, new, label):
    path=p(rel); s=path.read_text()
    n=s.count(old)
    if n!=1: raise SystemExit(f'{label}: expected exactly 1 anchor, got {n} in {rel}')
    path.write_text(s.replace(old,new,1))

def insert_after_once(rel, anchor, text, label):
    replace_once(rel, anchor, anchor+text, label)

# 1) Sabre shared physical-protection output from the exact ordinary rejection owner.
shader='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
replace_once(shader,
'''        layout(location = 0) out float oReverseWeight;\n        layout(location = 1) out float oPixelDifference;''',
'''        layout(location = 0) out float oReverseWeight;\n        layout(location = 1) out float oPixelDifference;\n        /* IRIS_26609_SHARED_NORMAL_SHORT_PHYSICAL_PROTECTION_OUTPUT\n         * This is not a second approximation of NORMAL protection. It is emitted by the exact\n         * ordinary Sabre rejection invocation from the same unblocker/flow decision that caps\n         * NORMAL. HIGHLIGHT_SHORT may relax only reference-photometric agreement in a proven\n         * censored core; this physical reverse weight remains mandatory. */\n        layout(location = 2) out float oPhysicalReverseWeight;''',
'add exact physical output')
replace_once(shader,
'''            oReverseWeight = 1.0 - weight;\n            oPixelDifference = pixelDifference;''',
'''            oReverseWeight = 1.0 - weight;\n            oPixelDifference = pixelDifference;\n            oPhysicalReverseWeight = clamp(unblocker, 0.0, 1.0);''',
'write exact physical output')

# Active 26607/26608 rescue only: bind shared physical weight and forbid rescue replacement.
active_marker='''            /* IRIS_26608_LOCAL_BOUNDARY_PROOF_WITH_CLIPPED_CORE_BYPASS\n             * At least two clipped CFA phases define a censored core where NORMAL cannot provide\n             * local geometry; retain 26607 component propagation there. Everywhere else, including\n             * one-phase/high-gradient transitions, local flow.w evidence caps rescue confidence. */'''
s=p(shader).read_text()
idx=s.find(active_marker)
if idx<0: raise SystemExit('active short rescue marker missing')
# Require unique active uniform list immediately before marker's function, not dormant older shader.
start=s.rfind('    val shortRescueWeight26607 = """',0,idx)
end=s.find('    """.trimIndent()',idx)
if start<0 or end<0: raise SystemExit('active short rescue block boundaries missing')
block=s[start:end]
if block.count('uniform sampler2D uOrdinaryWeight;')!=1: raise SystemExit('active ordinary uniform count')
block=block.replace('uniform sampler2D uOrdinaryWeight;','uniform sampler2D uOrdinaryWeight;\n        uniform sampler2D uPhysicalWeight;',1)
old='''            float ordinaryWeight = texture(uOrdinaryWeight, referenceUv).r;'''
if block.count(old)!=1: raise SystemExit('active ordinary sample count')
block=block.replace(old, old+'''\n            float physicalWeight = texture(uPhysicalWeight, referenceUv).r;''',1)
old2='''            oWeight = clamp(mix(ordinaryWeight, rescueConfidence, targetLoss), 0.0, 1.0);\n            oRescueOnlyWeight = clamp(rescueConfidence * targetLoss, 0.0, 1.0);'''
new2='''            /* IRIS_26609_SHORT_PROTECTION_PARITY_CONTRACT\n             * ordinaryWeight contains the full measurable NORMAL-style rejection + dilation.\n             * When NORMAL becomes physically censored, only its invalid reference-photometric\n             * agreement may relax. The exact same ordinary-rejection unblocker/flow protection,\n             * separately dilated as physicalWeight, remains a hard cap together with SHORT\n             * source headroom and validated local/component geometry. targetLoss can never erase\n             * physical protection. */\n            float censoredCoreWeight = min(physicalWeight, rescueConfidence);\n            float finalWeight = mix(ordinaryWeight, censoredCoreWeight, targetLoss);\n            oWeight = clamp(finalWeight, 0.0, 1.0);\n            oRescueOnlyWeight = clamp(censoredCoreWeight * targetLoss, 0.0, 1.0);'''
if block.count(old2)!=1: raise SystemExit('active old rescue replacement count')
block=block.replace(old2,new2,1)
s=s[:start]+block+s[end:]
p(shader).write_text(s)

# 2) Stacker: capture exact ordinary-rejection physical output only for SHORT, dilate same way, feed rescue.
stack='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
replace_once(stack,
'''        pixelDifference: Int,\n        guideWidth: Int,''',
'''        pixelDifference: Int,\n        physicalReverseWeight: Int = 0,\n        guideWidth: Int,''',
'renderSabreRejection signature')
replace_once(stack,
'''        draw(program, guideWidth, guideHeight, intArrayOf(reverseWeight, pixelDifference))''',
'''        val targets = if (physicalReverseWeight != 0) {\n            intArrayOf(reverseWeight, pixelDifference, physicalReverseWeight)\n        } else {\n            intArrayOf(reverseWeight, pixelDifference)\n        }\n        draw(program, guideWidth, guideHeight, targets)''',
'renderSabreRejection MRT targets')
# Create exact physical reverse texture before rejection call in active temporal loop.
anchor='''                val pixelDifference = createTexture(\n                    extractedWidth,\n                    extractedHeight,\n                    GLES30.GL_R8,\n                    GLES30.GL_NEAREST,\n                )\n                val durationRobustness = sabreExposureDurationRobustness(frames.first(), frame)'''
replacement='''                val pixelDifference = createTexture(\n                    extractedWidth,\n                    extractedHeight,\n                    GLES30.GL_R8,\n                    GLES30.GL_NEAREST,\n                )\n                /* IRIS_26609_SHARED_NORMAL_SHORT_PHYSICAL_PROTECTION_TEXTURE\n                 * Only SHORT retains the third MRT from the exact ordinary rejection pass. */\n                val shortPhysicalReverseWeight26609 = if (\n                    frame.role == RawBurstFrameRole.HIGHLIGHT_SHORT\n                ) {\n                    createTexture(\n                        extractedWidth, extractedHeight, GLES30.GL_R8, GLES30.GL_LINEAR,\n                    )\n                } else {\n                    0\n                }\n                val durationRobustness = sabreExposureDurationRobustness(frames.first(), frame)'''
replace_once(stack,anchor,replacement,'create physical reverse')
replace_once(stack,
'''                    reverseWeight,\n                    pixelDifference,\n                    extractedWidth,''',
'''                    reverseWeight,\n                    pixelDifference,\n                    shortPhysicalReverseWeight26609,\n                    extractedWidth,''',
'pass physical reverse')
# Dilate exact physical reverse with the exact common dilation before SHORT rescue.
replace_once(stack,
'''                var shortRescueOnlyWeight26607 = 0\n                var shortLossCandidateWeight26607 = 0\n                renderDilation(reverseWeight, frameWeight)\n                if (frame.role == RawBurstFrameRole.HIGHLIGHT_SHORT) {''',
'''                var shortRescueOnlyWeight26607 = 0\n                var shortLossCandidateWeight26607 = 0\n                var shortPhysicalWeight26609 = 0\n                renderDilation(reverseWeight, frameWeight)\n                if (frame.role == RawBurstFrameRole.HIGHLIGHT_SHORT) {\n                    check(shortPhysicalReverseWeight26609 != 0) {\n                        "26609 SHORT physical reverse weight missing"\n                    }\n                    shortPhysicalWeight26609 = createTexture(\n                        coverageWidth, coverageHeight, GLES30.GL_R8, GLES30.GL_LINEAR,\n                    )\n                    /* Exact same dilation implementation as ordinary NORMAL/Sabre weight. */\n                    renderDilation(shortPhysicalReverseWeight26609, shortPhysicalWeight26609)\n                    releaseOwnedTexture(\n                        shortPhysicalReverseWeight26609,\n                        "26609 SHORT exact ordinary-rejection physical reverse weight",\n                    )''',
'dilate shared physical protection')
# Add physicalWeight argument to rescue call.
replace_once(stack,
'''                        ordinaryWeight = frameWeight,\n                        referenceExtracted = referenceExtracted,''',
'''                        ordinaryWeight = frameWeight,\n                        physicalWeight = shortPhysicalWeight26609,\n                        referenceExtracted = referenceExtracted,''',
'feed physical weight')
# release physicalWeight after rescue before frameWeight replacement.
replace_once(stack,
'''                    releaseOwnedTexture(frameWeight, "26607 ordinary SHORT post-dilation weight")\n                    releaseOwnedTexture(component.texture, "26607 SHORT component trust")\n                    frameWeight = rescuedWeight''',
'''                    releaseOwnedTexture(frameWeight, "26607 ordinary SHORT post-dilation weight")\n                    releaseOwnedTexture(\n                        shortPhysicalWeight26609,\n                        "26609 SHORT shared physical post-dilation weight",\n                    )\n                    shortPhysicalWeight26609 = 0\n                    releaseOwnedTexture(component.texture, "26607 SHORT component trust")\n                    frameWeight = rescuedWeight''',
'release physical weight')
# Modify rescue helper signature and bind.
replace_once(stack,
'''    private fun renderSabreShortRescueWeight26607(\n        ordinaryWeight: Int,\n        referenceExtracted: Int,''',
'''    private fun renderSabreShortRescueWeight26607(\n        ordinaryWeight: Int,\n        physicalWeight: Int,\n        referenceExtracted: Int,''',
'rescue helper signature')
# Shift remaining texture units only inside the active 26607 helper.
s=p(stack).read_text(); a=s.find('    private fun renderSabreShortRescueWeight26607('); b=s.find('\n    private fun ',a+10)
if a<0 or b<0: raise SystemExit('rescue helper bounds')
blk=s[a:b]
old_bind='        bindTexture(program, \"uOrdinaryWeight\", 0, ordinaryWeight)\n        bindTexture(program, \"uReferenceExtractedBayer\", 1, referenceExtracted)'
new_bind='        bindTexture(program, \"uOrdinaryWeight\", 0, ordinaryWeight)\n        bindTexture(program, \"uPhysicalWeight\", 1, physicalWeight)\n        bindTexture(program, \"uReferenceExtractedBayer\", 2, referenceExtracted)'
if blk.count(old_bind)!=1: raise SystemExit(f'active rescue bind count={blk.count(old_bind)}')
blk=blk.replace(old_bind,new_bind,1)
# units currently ref1 short2 flow3 component4; after insertion ref already set 2, shift others.
for old,new in [
    ('"uShortExtractedBayer", 2, shortExtracted','"uShortExtractedBayer", 3, shortExtracted'),
    ('"uFlow", 3, flow.texture','"uFlow", 4, flow.texture'),
    ('"uComponentTrust", 4, componentTrust','"uComponentTrust", 5, componentTrust')]:
    if blk.count(old)!=1: raise SystemExit(f'rescue unit anchor {old} count={blk.count(old)}')
    blk=blk.replace(old,new,1)
s=s[:a]+blk+s[b:];p(stack).write_text(s)

# 3) MotionV2Render: a single derived tone plan shared with 1x/adaptive/SR.
render='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
insert_anchor='''    private static final int GAINMAP_DOWNSAMPLE = 1;\n'''
insert_text='''\n    /* IRIS_26609_SAMPLE_CALIBRATED_IRIS_RENDITION\n     * Photon samples are visual references only. Iris keeps its own architecture and uses the\n     * already-owned generic p99/p998 tail statistics to preserve highlight ordering. The body\n     * through the 0.40 final-domain anchor is unchanged. Broad structured highlights are spread\n     * across the remaining SDR code range, while the UHDR target expands only the same upper tail.\n     * No scene/object classifier is used. */\n    static final float IRIS_26609_SDR_STRETCH_START = 0.72f;\n    static final float IRIS_26609_SDR_P99_TARGET = 0.88f;\n    static final float IRIS_26609_SDR_P998_TARGET = 0.995f;\n    static final float IRIS_26609_HDR_P99_BOOST = 1.35f;\n    static final float IRIS_26609_HDR_P998_BOOST = 2.40f;\n\n    public static final class Iris26609TonePlan {\n        public final float oldP99Mapped;\n        public final float oldP998Mapped;\n        public final float hdrP99Final;\n        public final float hdrP998Final;\n        public final float strength;\n        Iris26609TonePlan(float oldP99Mapped, float oldP998Mapped,\n                          float hdrP99Final, float hdrP998Final, float strength) {\n            this.oldP99Mapped = oldP99Mapped;\n            this.oldP998Mapped = oldP998Mapped;\n            this.hdrP99Final = hdrP99Final;\n            this.hdrP998Final = hdrP998Final;\n            this.strength = strength;\n        }\n    }\n\n    public static Iris26609TonePlan iris26609TonePlan(Parameters parameters) {\n        if (parameters == null || !parameters.motionV2Active) {\n            return new Iris26609TonePlan(0.0f, 0.0f, 0.0f, 0.0f, 0.0f);\n        }\n        float gain = Math.max(parameters.motionV2DisplayGain, 1.0e-6f);\n        float p99Guide = Math.max(parameters.motionV2ToneP99Guide, 0.0f);\n        float p998Guide = Math.max(parameters.motionV2ToneP998Guide, p99Guide);\n        float oldP99 = iris26604MapMotionSdrFinalGuide(p99Guide, gain);\n        float oldP998 = iris26604MapMotionSdrFinalGuide(p998Guide, gain);\n        float hdrP99 = p99Guide * gain * OUTPUT_EXPOSURE_SCALE;\n        float hdrP998 = p998Guide * gain * OUTPUT_EXPOSURE_SCALE;\n        float strength = iris26582Clamp(parameters.motionV2ToneAdaptiveStrength, 0.0f, 1.0f);\n        boolean ordered = Float.isFinite(oldP99) && Float.isFinite(oldP998)\n                && Float.isFinite(hdrP99) && Float.isFinite(hdrP998)\n                && oldP99 > IRIS_26609_SDR_STRETCH_START + 0.01f\n                && oldP998 > oldP99 + 0.005f\n                && hdrP998 > hdrP99 + 0.02f;\n        if (!ordered) strength = 0.0f;\n        return new Iris26609TonePlan(oldP99, oldP998, hdrP99, hdrP998, strength);\n    }\n\n    static float iris26609StretchMotionSdrMapped(float oldMapped, Iris26609TonePlan plan) {\n        if (plan == null || plan.strength <= 0.0f\n                || oldMapped <= IRIS_26609_SDR_STRETCH_START) return oldMapped;\n        float a = plan.oldP99Mapped;\n        float b = plan.oldP998Mapped;\n        if (!(b > a + 0.005f && a > IRIS_26609_SDR_STRETCH_START + 0.01f)) return oldMapped;\n        float stretched;\n        if (oldMapped <= a) {\n            float t = iris26582Clamp((oldMapped - IRIS_26609_SDR_STRETCH_START)\n                    / (a - IRIS_26609_SDR_STRETCH_START), 0.0f, 1.0f);\n            stretched = IRIS_26609_SDR_STRETCH_START\n                    + t * (IRIS_26609_SDR_P99_TARGET - IRIS_26609_SDR_STRETCH_START);\n        } else if (oldMapped <= b) {\n            float t = iris26582Clamp((oldMapped - a) / (b - a), 0.0f, 1.0f);\n            stretched = IRIS_26609_SDR_P99_TARGET\n                    + t * (IRIS_26609_SDR_P998_TARGET - IRIS_26609_SDR_P99_TARGET);\n        } else {\n            float t = iris26582Clamp((oldMapped - b) / Math.max(1.0f - b, 1.0e-6f),\n                    0.0f, 1.0f);\n            stretched = IRIS_26609_SDR_P998_TARGET\n                    + t * (1.0f - IRIS_26609_SDR_P998_TARGET);\n        }\n        stretched = iris26582Clamp(stretched, oldMapped, 1.0f);\n        return oldMapped + (stretched - oldMapped) * plan.strength;\n    }\n\n    static float iris26609MapMotionSdrFinalGuide(float sourceGuide, float brightnessTargetGain,\n                                                  Iris26609TonePlan plan) {\n        return iris26609StretchMotionSdrMapped(\n                iris26604MapMotionSdrFinalGuide(sourceGuide, brightnessTargetGain), plan);\n    }\n\n    static float iris26609MapHdrTargetLuma(float hdrBase, Iris26609TonePlan plan) {\n        if (plan == null || plan.strength <= 0.0f || hdrBase <= 0.0f) return hdrBase;\n        float a = plan.hdrP99Final;\n        float b = plan.hdrP998Final;\n        if (!(b > a + 0.02f && a > 0.0f)) return hdrBase;\n        float start = Math.min(a, Math.max(0.80f, a * 0.75f));\n        float boost = 1.0f;\n        if (hdrBase > start && hdrBase <= a) {\n            float t = iris26582Clamp((hdrBase - start) / Math.max(a - start, 1.0e-6f), 0.0f, 1.0f);\n            boost = 1.0f + t * (IRIS_26609_HDR_P99_BOOST - 1.0f);\n        } else if (hdrBase > a && hdrBase <= b) {\n            float t = iris26582Clamp((hdrBase - a) / Math.max(b - a, 1.0e-6f), 0.0f, 1.0f);\n            boost = IRIS_26609_HDR_P99_BOOST\n                    + t * (IRIS_26609_HDR_P998_BOOST - IRIS_26609_HDR_P99_BOOST);\n        } else if (hdrBase > b) {\n            boost = IRIS_26609_HDR_P998_BOOST;\n        }\n        float applied = 1.0f + (boost - 1.0f) * plan.strength;\n        return hdrBase * applied;\n    }\n'''
insert_after_once(render,insert_anchor,insert_text,'insert 26609 tone plan')
# Run: derive plan and pass 1x render uniforms.
replace_once(render,
'''        float sceneWhite = iris26598PublicationSceneWhite(basePipeline.mParameters);''',
'''        float sceneWhite = iris26598PublicationSceneWhite(basePipeline.mParameters);\n        final Iris26609TonePlan iris26609Tone = iris26609TonePlan(basePipeline.mParameters);''',
'derive tone plan')
replace_once(render,
'''        glProg.setVar("iris26604MotionSdrKneeFinal", IRIS_26604_MOTION_SDR_KNEE_FINAL);\n                glProg.setVar("outputExposureScale", OUTPUT_EXPOSURE_SCALE);''',
'''        glProg.setVar("iris26604MotionSdrKneeFinal", IRIS_26604_MOTION_SDR_KNEE_FINAL);\n        glProg.setVar("iris26609OldP99Mapped", iris26609Tone.oldP99Mapped);\n        glProg.setVar("iris26609OldP998Mapped", iris26609Tone.oldP998Mapped);\n        glProg.setVar("iris26609ToneStrength", iris26609Tone.strength);\n                glProg.setVar("outputExposureScale", OUTPUT_EXPOSURE_SCALE);''',
'pass render tone anchors')
# Gainmap uniforms.
replace_once(render,
'''                glProg.setVar("maxGainRatio", maxGainRatio);\n                glProg.setVar("irisOutputZoom", irisOutputZoom);''',
'''                glProg.setVar("maxGainRatio", maxGainRatio);\n                glProg.setVar("iris26609HdrP99Final", iris26609Tone.hdrP99Final);\n                glProg.setVar("iris26609HdrP998Final", iris26609Tone.hdrP998Final);\n                glProg.setVar("iris26609ToneStrength", iris26609Tone.strength);\n                glProg.setVar("irisOutputZoom", irisOutputZoom);''',
'pass gainmap tone anchors')
# Add log proof in final render line.
replace_once(render,
'''                + " localTone=false"\n                + " sharpening=false");''',
'''                + " iris26609OldP99Mapped=" + iris26609Tone.oldP99Mapped\n                + " iris26609OldP998Mapped=" + iris26609Tone.oldP998Mapped\n                + " iris26609HdrP99Final=" + iris26609Tone.hdrP99Final\n                + " iris26609HdrP998Final=" + iris26609Tone.hdrP998Final\n                + " iris26609ToneStrength=" + iris26609Tone.strength\n                + " IRIS_26609_SDR_UHDR_SR_RENDITION_PARITY=true"\n                + " localTone=false"\n                + " sharpening=false");''',
'log tone plan')

# 4) 1x render shader: uniforms + exact piecewise upper-tail stretch.
render_glsl='app/src/main/assets/shaders/motionv2/render.glsl'
replace_once(render_glsl,
'''uniform float iris26604MotionSdrKneeFinal;''',
'''uniform float iris26604MotionSdrKneeFinal;\nuniform float iris26609OldP99Mapped;\nuniform float iris26609OldP998Mapped;\nuniform float iris26609ToneStrength;''',
'render glsl uniforms')
# inject helper before mapFinalSdrGuide
map_anchor='''float mapFinalSdrGuide(float sourceGuide) {'''
helper='''float iris26609StretchSdrMapped(float oldMapped) {\n    const float start=0.72;\n    const float targetP99=0.88;\n    const float targetP998=0.995;\n    float strength=clamp(iris26609ToneStrength,0.0,1.0);\n    float a=iris26609OldP99Mapped;\n    float b=iris26609OldP998Mapped;\n    if(strength<=0.0||oldMapped<=start||a<=start+0.01||b<=a+0.005) return oldMapped;\n    float stretched=oldMapped;\n    if(oldMapped<=a){\n        float t=clamp((oldMapped-start)/max(a-start,1.0e-6),0.0,1.0);\n        stretched=start+t*(targetP99-start);\n    }else if(oldMapped<=b){\n        float t=clamp((oldMapped-a)/max(b-a,1.0e-6),0.0,1.0);\n        stretched=targetP99+t*(targetP998-targetP99);\n    }else{\n        float t=clamp((oldMapped-b)/max(1.0-b,1.0e-6),0.0,1.0);\n        stretched=targetP998+t*(1.0-targetP998);\n    }\n    stretched=clamp(stretched,oldMapped,1.0);\n    return mix(oldMapped,stretched,strength);\n}\n\n'''
replace_once(render_glsl,map_anchor,helper+map_anchor,'render glsl stretch helper')
replace_once(render_glsl,
'''        return knee+reserve*excess/(excess+reserve);''',
'''        float oldMapped=knee+reserve*excess/(excess+reserve);\n        return iris26609StretchSdrMapped(oldMapped);''',
'render glsl use stretch')
# Need ensure targetFinal <= knee also returns identity; and for > knee old <=.72 can identity.

# 5) Gainmap 1x HDR target expansion.
gain_glsl='app/src/main/assets/shaders/motionv2/gainmap.glsl'
replace_once(gain_glsl,
'''uniform float maxGainRatio;\nuniform float irisOutputZoom;''',
'''uniform float maxGainRatio;\nuniform float iris26609HdrP99Final;\nuniform float iris26609HdrP998Final;\nuniform float iris26609ToneStrength;\nuniform float irisOutputZoom;''',
'gain glsl uniforms')
helper_gain='''\nfloat iris26609MapHdrTarget(float hdrBase){\n    float strength=clamp(iris26609ToneStrength,0.0,1.0);\n    float a=iris26609HdrP99Final,b=iris26609HdrP998Final;\n    if(strength<=0.0||hdrBase<=0.0||a<=0.0||b<=a+0.02) return hdrBase;\n    float start=min(a,max(0.80,a*0.75));\n    float boost=1.0;\n    if(hdrBase>start&&hdrBase<=a){\n        float t=clamp((hdrBase-start)/max(a-start,1.0e-6),0.0,1.0);\n        boost=mix(1.0,1.35,t);\n    }else if(hdrBase>a&&hdrBase<=b){\n        float t=clamp((hdrBase-a)/max(b-a,1.0e-6),0.0,1.0);\n        boost=mix(1.35,2.40,t);\n    }else if(hdrBase>b){\n        boost=2.40;\n    }\n    return hdrBase*mix(1.0,boost,strength);\n}\n'''
insert_after_once(gain_glsl,
'''vec3 srgbDecode(vec3 c){return vec3(srgbDecode(c.r),srgbDecode(c.g),srgbDecode(c.b));}\n''',helper_gain,'gain hdr helper')
replace_once(gain_glsl,
'''    float hdr=max(luminance(max(hdrRgb,vec3(0.0))*hdrTargetScale),0.0);''',
'''    float hdrBase=max(luminance(max(hdrRgb,vec3(0.0))*hdrTargetScale),0.0);\n    float hdr=motionHdrHandoff!=0?iris26609MapHdrTarget(hdrBase):hdrBase;''',
'gain apply hdr expansion')

# 6) Adaptive color predictor exact SDR map parity.
adapt_java='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java'
replace_once(adapt_java,
'''        float sceneWhite = MotionV2Render.iris26598PublicationSceneWhite(basePipeline.mParameters);\n        glProg.setVar("sceneWhite", sceneWhite);''',
'''        float sceneWhite = MotionV2Render.iris26598PublicationSceneWhite(basePipeline.mParameters);\n        final MotionV2Render.Iris26609TonePlan iris26609Tone =\n                MotionV2Render.iris26609TonePlan(basePipeline.mParameters);\n        glProg.setVar("sceneWhite", sceneWhite);\n        glProg.setVar("iris26609OldP99Mapped", iris26609Tone.oldP99Mapped);\n        glProg.setVar("iris26609OldP998Mapped", iris26609Tone.oldP998Mapped);\n        glProg.setVar("iris26609ToneStrength", iris26609Tone.strength);''',
'adaptive pass tone plan')
replace_once(adapt_java,
'''                + " displayGain=" + displayGain''',
'''                + " displayGain=" + displayGain\n                + " iris26609ToneStrength=" + iris26609Tone.strength\n                + " IRIS_26609_TONE_PREDICTOR_PARITY=true"''',
'adaptive log')

adapt_glsl='app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl'
replace_once(adapt_glsl,
'''uniform float displayGain;''',
'''uniform float displayGain;\nuniform float iris26609OldP99Mapped;\nuniform float iris26609OldP998Mapped;\nuniform float iris26609ToneStrength;''',
'adaptive shader uniforms')
# Insert same helper before predictor function. Identify function around current map.
s=p(adapt_glsl).read_text()
anchor='''float iris26585PostTonePreGamutPeak(vec3 preDisplayRgb) {'''
if s.count(anchor)!=1: raise SystemExit(f'adaptive predictor anchor count {s.count(anchor)}')
helper_adapt='''float iris26609StretchSdrMapped(float oldMapped) {\n    const float start=0.72,targetP99=0.88,targetP998=0.995;\n    float strength=clamp(iris26609ToneStrength,0.0,1.0);\n    float a=iris26609OldP99Mapped,b=iris26609OldP998Mapped;\n    if(strength<=0.0||oldMapped<=start||a<=start+0.01||b<=a+0.005) return oldMapped;\n    float stretched=oldMapped;\n    if(oldMapped<=a){float t=clamp((oldMapped-start)/max(a-start,1.0e-6),0.0,1.0);stretched=start+t*(targetP99-start);}\n    else if(oldMapped<=b){float t=clamp((oldMapped-a)/max(b-a,1.0e-6),0.0,1.0);stretched=targetP99+t*(targetP998-targetP99);}\n    else{float t=clamp((oldMapped-b)/max(1.0-b,1.0e-6),0.0,1.0);stretched=targetP998+t*(1.0-targetP998);}\n    stretched=clamp(stretched,oldMapped,1.0);\n    return mix(oldMapped,stretched,strength);\n}\n\n'''
s=s.replace(anchor,helper_adapt+anchor,1)
# Current motion branch returns sourcePeak*(mappedFinal/sourceGuide); replace after old rational.
old='''        if(targetFinal>kneeFinal){\n            float reserve=1.0-kneeFinal;\n            float excess=targetFinal-kneeFinal;\n            mappedFinal=kneeFinal+reserve*excess/(excess+reserve);\n        }\n        return sourcePeak*(mappedFinal/sourceGuide);'''
new='''        if(targetFinal>kneeFinal){\n            float reserve=1.0-kneeFinal;\n            float excess=targetFinal-kneeFinal;\n            mappedFinal=kneeFinal+reserve*excess/(excess+reserve);\n            mappedFinal=iris26609StretchSdrMapped(mappedFinal);\n        }\n        return sourcePeak*(mappedFinal/sourceGuide);'''
if s.count(old)!=1: raise SystemExit(f'adaptive old map count {s.count(old)}')
s=s.replace(old,new,1);p(adapt_glsl).write_text(s)

# 7) True2x Java passes same derived anchors to native.
enc='app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java'
replace_once(enc,
'''            final float publicationSceneWhite =\n                    MotionV2Render.iris26598PublicationSceneWhite(parameters);''',
'''            final float publicationSceneWhite =\n                    MotionV2Render.iris26598PublicationSceneWhite(parameters);\n            final MotionV2Render.Iris26609TonePlan iris26609Tone =\n                    MotionV2Render.iris26609TonePlan(parameters);''',
'true2x derive tone plan')
replace_once(enc,
'''                    parameters.motionV2DisplayGain, exposureEv, shadows, contrast,\n                    publicationSceneWhite, parameters.motionV2Active,''',
'''                    parameters.motionV2DisplayGain, exposureEv, shadows, contrast,\n                    publicationSceneWhite, parameters.motionV2Active,\n                    iris26609Tone.oldP99Mapped, iris26609Tone.oldP998Mapped,\n                    iris26609Tone.hdrP99Final, iris26609Tone.hdrP998Final,\n                    iris26609Tone.strength,''',
'true2x call tone args')
replace_once(enc,
'''                    + " publicationSceneWhite=" + publicationSceneWhite''',
'''                    + " publicationSceneWhite=" + publicationSceneWhite\n                    + " iris26609OldP99Mapped=" + iris26609Tone.oldP99Mapped\n                    + " iris26609OldP998Mapped=" + iris26609Tone.oldP998Mapped\n                    + " iris26609HdrP99Final=" + iris26609Tone.hdrP99Final\n                    + " iris26609HdrP998Final=" + iris26609Tone.hdrP998Final\n                    + " iris26609ToneStrength=" + iris26609Tone.strength''',
'true2x log tone plan')
replace_once(enc,
'''            float exposureEv, float shadows, float contrast, float sceneWhite, boolean motionHdrHandoff,\n            Bitmap watermark,''',
'''            float exposureEv, float shadows, float contrast, float sceneWhite, boolean motionHdrHandoff,\n            float iris26609OldP99Mapped, float iris26609OldP998Mapped,\n            float iris26609HdrP99Final, float iris26609HdrP998Final, float iris26609ToneStrength,\n            Bitmap watermark,''',
'true2x native signature java')

# 8) Native true2x CPU + GPU exact parity.
native='app/src/main/cpp/motionv2_jpeg444_jni.cpp'
# Params fields
replace_once(native,
'''    float residualZoom=1.f,displayGain=1.f,exposureEv=0.f,shadows=0.f,contrast=0.f,sceneWhite=1.f;''',
'''    float residualZoom=1.f,displayGain=1.f,exposureEv=0.f,shadows=0.f,contrast=0.f,sceneWhite=1.f;\n    float iris26609OldP99Mapped=0.f,iris26609OldP998Mapped=0.f;\n    float iris26609HdrP99Final=0.f,iris26609HdrP998Final=0.f,iris26609ToneStrength=0.f;''',
'native params tone fields')
# CPU helper functions before renderHeadroom.
anchor='''inline Vec3 renderHeadroom(Vec3 rgb,const Params&p){'''
helpers='''inline float iris26609StretchSdrMapped(float oldMapped,const Params&p){\n    constexpr float start=0.72f,targetP99=0.88f,targetP998=0.995f;\n    float strength=clampf(p.iris26609ToneStrength,0.f,1.f),a=p.iris26609OldP99Mapped,b=p.iris26609OldP998Mapped;\n    if(strength<=0.f||oldMapped<=start||a<=start+0.01f||b<=a+0.005f)return oldMapped;\n    float stretched=oldMapped;\n    if(oldMapped<=a){float t=clampf((oldMapped-start)/std::max(a-start,1.0e-6f),0.f,1.f);stretched=start+t*(targetP99-start);}\n    else if(oldMapped<=b){float t=clampf((oldMapped-a)/std::max(b-a,1.0e-6f),0.f,1.f);stretched=targetP99+t*(targetP998-targetP99);}\n    else{float t=clampf((oldMapped-b)/std::max(1.f-b,1.0e-6f),0.f,1.f);stretched=targetP998+t*(1.f-targetP998);}\n    stretched=clampf(stretched,oldMapped,1.f);return oldMapped+(stretched-oldMapped)*strength;\n}\ninline float iris26609MapHdrTarget(float hdrBase,const Params&p){\n    float strength=clampf(p.iris26609ToneStrength,0.f,1.f),a=p.iris26609HdrP99Final,b=p.iris26609HdrP998Final;\n    if(strength<=0.f||hdrBase<=0.f||a<=0.f||b<=a+0.02f)return hdrBase;\n    float start=std::min(a,std::max(0.80f,a*0.75f)),boost=1.f;\n    if(hdrBase>start&&hdrBase<=a){float t=clampf((hdrBase-start)/std::max(a-start,1.0e-6f),0.f,1.f);boost=1.f+t*(1.35f-1.f);}\n    else if(hdrBase>a&&hdrBase<=b){float t=clampf((hdrBase-a)/std::max(b-a,1.0e-6f),0.f,1.f);boost=1.35f+t*(2.40f-1.35f);}\n    else if(hdrBase>b)boost=2.40f;\n    return hdrBase*(1.f+(boost-1.f)*strength);\n}\n\n'''
replace_once(native,anchor,helpers+anchor,'native tone helpers')
# CPU SDR current rational -> stretch.
replace_once(native,
'''        if(targetFinal>knee){float excess=targetFinal-knee;mappedFinal=knee+reserve*excess/(excess+reserve);}\n        if(guide>1.0e-7f)rgb=mul(rgb,mappedFinal/guide);''',
'''        if(targetFinal>knee){float excess=targetFinal-knee;mappedFinal=knee+reserve*excess/(excess+reserve);mappedFinal=iris26609StretchSdrMapped(mappedFinal,p);}\n        if(guide>1.0e-7f)rgb=mul(rgb,mappedFinal/guide);''',
'native CPU SDR stretch')
# two CPU gain copies apply HDR target
for old in [
'''float hdrY=std::max(luma(clampNonnegative(hdr))*hdrScale,0.f),sdrY''']:
    s=p(native).read_text(); count=s.count(old)
    if count!=2: raise SystemExit(f'CPU hdrY anchors expected 2 got {count}')
    s=s.replace(old,'''float hdrBase=std::max(luma(clampNonnegative(hdr))*hdrScale,0.f),hdrY=p.motionHdrHandoff?iris26609MapHdrTarget(hdrBase,p):hdrBase,sdrY''')
    p(native).write_text(s)
# GPU shader uniforms.
replace_once(native,
'''uniform float uSceneWhite;\nuniform int uMotionHdrHandoff;''',
'''uniform float uSceneWhite;\nuniform int uMotionHdrHandoff;\nuniform float uIris26609OldP99Mapped;\nuniform float uIris26609OldP998Mapped;\nuniform float uIris26609HdrP99Final;\nuniform float uIris26609HdrP998Final;\nuniform float uIris26609ToneStrength;''',
'gpu tone uniforms')
# GPU helper insert before irisHeadroom.
anchor='''vec3 irisHeadroom(vec3 rgb){'''
helpers_gpu='''float iris26609StretchSdrMapped(float oldMapped){\n    const float start=0.72,targetP99=0.88,targetP998=0.995;\n    float strength=clamp(uIris26609ToneStrength,0.0,1.0),a=uIris26609OldP99Mapped,b=uIris26609OldP998Mapped;\n    if(strength<=0.0||oldMapped<=start||a<=start+0.01||b<=a+0.005)return oldMapped;\n    float stretched=oldMapped;\n    if(oldMapped<=a){float t=clamp((oldMapped-start)/max(a-start,1.0e-6),0.0,1.0);stretched=start+t*(targetP99-start);}\n    else if(oldMapped<=b){float t=clamp((oldMapped-a)/max(b-a,1.0e-6),0.0,1.0);stretched=targetP99+t*(targetP998-targetP99);}\n    else{float t=clamp((oldMapped-b)/max(1.0-b,1.0e-6),0.0,1.0);stretched=targetP998+t*(1.0-targetP998);}\n    stretched=clamp(stretched,oldMapped,1.0);return mix(oldMapped,stretched,strength);\n}\nfloat iris26609MapHdrTarget(float hdrBase){\n    float strength=clamp(uIris26609ToneStrength,0.0,1.0),a=uIris26609HdrP99Final,b=uIris26609HdrP998Final;\n    if(strength<=0.0||hdrBase<=0.0||a<=0.0||b<=a+0.02)return hdrBase;\n    float start=min(a,max(0.80,a*0.75)),boost=1.0;\n    if(hdrBase>start&&hdrBase<=a){float t=clamp((hdrBase-start)/max(a-start,1.0e-6),0.0,1.0);boost=mix(1.0,1.35,t);}\n    else if(hdrBase>a&&hdrBase<=b){float t=clamp((hdrBase-a)/max(b-a,1.0e-6),0.0,1.0);boost=mix(1.35,2.40,t);}\n    else if(hdrBase>b)boost=2.40;\n    return hdrBase*mix(1.0,boost,strength);\n}\n\n'''
replace_once(native,anchor,helpers_gpu+anchor,'gpu tone helpers')
replace_once(native,
'''        if(targetFinal>knee){float excess=targetFinal-knee;mappedFinal=knee+reserve*excess/(excess+reserve);}\n        if(guide>1.0e-7)rgb*=mappedFinal/guide;''',
'''        if(targetFinal>knee){float excess=targetFinal-knee;mappedFinal=knee+reserve*excess/(excess+reserve);mappedFinal=iris26609StretchSdrMapped(mappedFinal);}\n        if(guide>1.0e-7)rgb*=mappedFinal/guide;''',
'gpu SDR stretch')
replace_once(native,
'''        float hdrY=max(irisLuma(irisClampNonnegative(hdr))*hdrScale,0.0);''',
'''        float hdrBase=max(irisLuma(irisClampNonnegative(hdr))*hdrScale,0.0);\n        float hdrY=uMotionHdrHandoff!=0?iris26609MapHdrTarget(hdrBase):hdrBase;''',
'gpu HDR expansion')
# GPU setParams add uniforms.
replace_once(native,
'''glUniform1f(loc("uSceneWhite"),params->sceneWhite);glUniform1i(loc("uMotionHdrHandoff"),params->motionHdrHandoff?1:0);''',
'''glUniform1f(loc("uSceneWhite"),params->sceneWhite);glUniform1i(loc("uMotionHdrHandoff"),params->motionHdrHandoff?1:0);glUniform1f(loc("uIris26609OldP99Mapped"),params->iris26609OldP99Mapped);glUniform1f(loc("uIris26609OldP998Mapped"),params->iris26609OldP998Mapped);glUniform1f(loc("uIris26609HdrP99Final"),params->iris26609HdrP99Final);glUniform1f(loc("uIris26609HdrP998Final"),params->iris26609HdrP998Final);glUniform1f(loc("uIris26609ToneStrength"),params->iris26609ToneStrength);''',
'gpu set tone params')
# JNI signature native add 5 floats after motionHdrHandoff.
replace_once(native,
'''jfloatArray sensorToProfile,jfloatArray profileToDisplay,jfloat displayGain,jfloat exposureEv,jfloat shadows,jfloat contrast,jfloat sceneWhite,jboolean motionHdrHandoff,jobject watermarkBitmap,''',
'''jfloatArray sensorToProfile,jfloatArray profileToDisplay,jfloat displayGain,jfloat exposureEv,jfloat shadows,jfloat contrast,jfloat sceneWhite,jboolean motionHdrHandoff,\n        jfloat iris26609OldP99Mapped,jfloat iris26609OldP998Mapped,jfloat iris26609HdrP99Final,jfloat iris26609HdrP998Final,jfloat iris26609ToneStrength,jobject watermarkBitmap,''',
'native JNI signature tone args')
# Params assign and validation.
replace_once(native,
'''p.motionHdrHandoff=motionHdrHandoff==JNI_TRUE;p.sceneWhite=p.motionHdrHandoff?std::max(1.f,(float)sceneWhite):std::max(1.f,std::min(6.f,0.90f*std::max(1.f,p.displayGain)));''',
'''p.motionHdrHandoff=motionHdrHandoff==JNI_TRUE;p.sceneWhite=p.motionHdrHandoff?std::max(1.f,(float)sceneWhite):std::max(1.f,std::min(6.f,0.90f*std::max(1.f,p.displayGain)));p.iris26609OldP99Mapped=(float)iris26609OldP99Mapped;p.iris26609OldP998Mapped=(float)iris26609OldP998Mapped;p.iris26609HdrP99Final=(float)iris26609HdrP99Final;p.iris26609HdrP998Final=(float)iris26609HdrP998Final;p.iris26609ToneStrength=clampf((float)iris26609ToneStrength,0.f,1.f);''',
'native assign tone params')
replace_once(native,
'''if(!std::isfinite(p.displayGain)||p.displayGain<=0.f||!std::isfinite(p.exposureEv)||!std::isfinite(p.shadows)||!std::isfinite(p.contrast)||!std::isfinite(p.residualZoom)||!std::isfinite(p.sceneWhite)||p.sceneWhite<=0.f)return JNI_FALSE;''',
'''if(!std::isfinite(p.displayGain)||p.displayGain<=0.f||!std::isfinite(p.exposureEv)||!std::isfinite(p.shadows)||!std::isfinite(p.contrast)||!std::isfinite(p.residualZoom)||!std::isfinite(p.sceneWhite)||p.sceneWhite<=0.f||!std::isfinite(p.iris26609OldP99Mapped)||!std::isfinite(p.iris26609OldP998Mapped)||!std::isfinite(p.iris26609HdrP99Final)||!std::isfinite(p.iris26609HdrP998Final)||!std::isfinite(p.iris26609ToneStrength))return JNI_FALSE;''',
'native validate tone params')

# 9) Version.
version='app/version.properties'
s=p(version).read_text()
# robust increment exact current values
for old,new in [('VERSION_NAME=0.9726608','VERSION_NAME=0.9726609'),('VERSION_BUILD=26608','VERSION_BUILD=26609')]:
    if s.count(old)!=1: raise SystemExit(f'version anchor {old} count={s.count(old)}')
    s=s.replace(old,new,1)
p(version).write_text(s)

# Exact scope proof.
allow=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl',
'app/version.properties']
changed=[]
for q in sorted((out/'app').rglob('*')):
    if not q.is_file(): continue
    rel=str(q.relative_to(out))
    b=base/rel
    if not b.exists() or q.read_bytes()!=b.read_bytes(): changed.append(rel)
if sorted(changed)!=sorted(allow):
    raise SystemExit('scope mismatch\nactual='+repr(changed)+'\nexpected='+repr(allow))
print('PASS transform scope exactly 10')
for rel in changed: print(rel)
