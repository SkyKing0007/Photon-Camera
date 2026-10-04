from pathlib import Path
import shutil, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: transform_26761.py <base> <out>')
base = Path(sys.argv[1]); out = Path(sys.argv[2])
if out.exists(): shutil.rmtree(out)
shutil.copytree(base, out)

def replace_once(path, old, new):
    p = out / path
    s = p.read_text()
    n = s.count(old)
    if n != 1:
        raise SystemExit(f'{path}: anchor count {n} expected 1')
    p.write_text(s.replace(old, new, 1))

# Shared measured-output-SNR policy: preserve 0.50 at >=20, ramp linearly to 1.00 at <=10.
path='app/src/main/java/com/hinnka/mycamera/processor/MgcSabreKernelTuning.kt'
old='''    internal fun effectiveSnr(referenceSnr: Float, frameCount: Int): Float =\n        referenceSnr * sqrt(frameCount.toFloat() / 12f)\n\n    private fun interpolate(x: Float, vararg points: Pair<Float, Float>): Float {\n'''
new='''    internal fun effectiveSnr(referenceSnr: Float, frameCount: Int): Float =\n        referenceSnr * sqrt(frameCount.toFloat() / 12f)\n\n    /* IRIS_26761_MEASURED_SNR_CHROMA_SCALE\n     * One shared policy drives both Motion residual chroma and the additional true-2x SR\n     * chroma-consensus blend. The input is propagated output tuning SNR derived from measured\n     * RAW signal plus the calibrated read/shot-noise model and measured Sabre merge scale; ISO\n     * is never interpreted as scene brightness. The upper two existing MGC chroma tuning knots\n     * define the transition: <=10 permits full cleanup, >=20 preserves the proven 0.50 owner,\n     * and the interval between them is linear. Local material/color protections remain downstream.\n     */\n    internal fun adaptiveResidualChromaScale26761(outputTuningSnr: Float): Float {\n        val snr = outputTuningSnr.takeIf { it.isFinite() }?.coerceAtLeast(0f) ?: 20f\n        return when {\n            snr <= 10f -> 1.0f\n            snr >= 20f -> 0.50f\n            else -> 1.0f - 0.05f * (snr - 10f)\n        }\n    }\n\n    private fun interpolate(x: Float, vararg points: Pair<Float, Float>): Float {\n'''
replace_once(path, old, new)

# Bridge: use shared measured-SNR scale for normal/non-SR residual chroma; custom and Night unchanged.
path='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'
replace_once(path,
'''import com.hinnka.mycamera.processor.GpuLinearRgbStorage\n''',
'''import com.hinnka.mycamera.processor.GpuLinearRgbStorage\nimport com.hinnka.mycamera.processor.MgcSabreKernelTuning\n''')
old='''            /* IRIS_26733_MOTION_AUTO_RESIDUAL_CHROMA_HALF_SCALE\n             * The 26727..26732 audit proved Auto remained at 1.0 even after VGN became primary color\n             * owner. Motion Auto is now genuinely subordinate at 0.5x user scale. Because MGC uses\n             * strength-squared noise scaling internally, this is roughly one quarter of the prior\n             * denoise variance authority. Custom Exact remains exact and Night remains unchanged. */\n            val automaticResidualChromaScale26733 = if (!parameters.irisNightActive && customResidualChroma == null) {\n                (0.5f * chromaScale).coerceIn(0f, 2f)\n            } else {\n                chromaScale\n            }\n            val residualChromaEnabled = customResidualChromaEnabled ||\n                (customResidualChroma == null && automaticResidualChromaScale26733 > 0f)\n            val denoisePass = MgcFullResolutionDenoise.Pass.SABRE_DEFAULT\n            val runFullResolutionDenoise = irisSettings.noiseReductionEnabled &&\n                (lumaScale > 0f || residualChromaEnabled)\n            if (!parameters.irisNightActive) {\n                PLog.i("MotionTrace", "IRIS_26733_RESIDUAL_CHROMA_CONTROL mode=${if (customResidualChroma != null) "CUSTOM_EXACT" else "AUTO_SNR_HALF"} levels=${customResidualChroma?.contentToString() ?: "AUTO"} requestedScale=$chromaScale appliedAutoScale=$automaticResidualChromaScale26733 bypass=${customResidualChroma != null && !customResidualChromaEnabled}")\n            }\n'''
new='''            /* IRIS_26761_MOTION_MEASURED_SNR_RESIDUAL_CHROMA\n             * 26733's fixed 0.50 Auto scale is superseded only for Motion Auto. The shared 26761\n             * measured-output-SNR policy permits 1.00 at SNR<=10, ramps through 0.60..0.80 in\n             * moderate SNR, and returns to the proven 0.50 at SNR>=20. This is a maximum residual\n             * strength only: the inherited Sabre residual support map, MGC chroma outlier logic,\n             * VGN ownership, and 26728 physically-supported pre-VGN chroma floor remain intact.\n             * Custom Exact remains exact and Night remains unchanged. */\n            val automaticResidualChromaFactor26761 =\n                if (!parameters.irisNightActive && customResidualChroma == null) {\n                    MgcSabreKernelTuning.adaptiveResidualChromaScale26761(tuningSnr!!)\n                } else {\n                    0.50f\n                }\n            val automaticResidualChromaScale26761 = if (!parameters.irisNightActive && customResidualChroma == null) {\n                (automaticResidualChromaFactor26761 * chromaScale).coerceIn(0f, 2f)\n            } else {\n                chromaScale\n            }\n            val residualChromaEnabled = customResidualChromaEnabled ||\n                (customResidualChroma == null && automaticResidualChromaScale26761 > 0f)\n            val denoisePass = MgcFullResolutionDenoise.Pass.SABRE_DEFAULT\n            val runFullResolutionDenoise = irisSettings.noiseReductionEnabled &&\n                (lumaScale > 0f || residualChromaEnabled)\n            if (!parameters.irisNightActive) {\n                PLog.i("MotionTrace", "IRIS_26761_RESIDUAL_CHROMA_CONTROL mode=${if (customResidualChroma != null) "CUSTOM_EXACT" else "AUTO_MEASURED_SNR"} levels=${customResidualChroma?.contentToString() ?: "AUTO"} requestedScale=$chromaScale referenceSnr=$referenceSnr outputTuningSnr=$tuningSnr permittedFactor=$automaticResidualChromaFactor26761 appliedAutoScale=$automaticResidualChromaScale26761 bypass=${customResidualChroma != null && !customResidualChromaEnabled}")\n            }\n'''
replace_once(path, old, new)
replace_once(path,
'''                    chromaStrengthScale = if (customResidualChroma != null) 0f else automaticResidualChromaScale26733,\n''',
'''                    chromaStrengthScale = if (customResidualChroma != null) 0f else automaticResidualChromaScale26761,\n''')

# Stacker: pass the exact propagated output tuning SNR into the live true-2x GPU guide renderer.
path='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
old='''                val rawResult=reconstructTrue2x(\n                    frames, images, reconstructionEvidence, nativeHdrAuthority26601, exportNormalStackedDng,\n                )\n'''
new='''                val outputTuningSnr26761 = kernelTuning.referenceSnr / sqrt(sabreNoiseModelScale)\n                val rawResult=reconstructTrue2x(\n                    frames, images, reconstructionEvidence, nativeHdrAuthority26601, exportNormalStackedDng,\n                    outputTuningSnr26761,\n                )\n'''
replace_once(path, old, new)
old='''    private fun runTrue2xGpu(\n        images: List<SafeImage>,\n        evidence: List<True2xFrameEvidence>,\n        directOutputFile: File?,\n        renderOutputFile: File,\n        nativeVgnGuideTexture: Int,\n        fullOutputWidth: Int,\n        fullOutputHeight: Int,\n    ): True2xPhaseStats {\n'''
new='''    private fun runTrue2xGpu(\n        images: List<SafeImage>,\n        evidence: List<True2xFrameEvidence>,\n        directOutputFile: File?,\n        renderOutputFile: File,\n        nativeVgnGuideTexture: Int,\n        fullOutputWidth: Int,\n        fullOutputHeight: Int,\n        outputTuningSnr26761: Float,\n    ): True2xPhaseStats {\n'''
replace_once(path, old, new)
old='''        require(nativeVgnGuideTexture != 0) { "26568 true2x requires live native Sabre/VGN guide texture" }\n        val maxTexture = IntArray(1)\n'''
new='''        require(nativeVgnGuideTexture != 0) { "26568 true2x requires live native Sabre/VGN guide texture" }\n        require(outputTuningSnr26761.isFinite() && outputTuningSnr26761 >= 0f) {\n            "26761 true2x output tuning SNR invalid: $outputTuningSnr26761"\n        }\n        val srChromaDenoiseFactor26761 =\n            MgcSabreKernelTuning.adaptiveResidualChromaScale26761(outputTuningSnr26761)\n        PLog.i(SABRE_TAG, "IRIS_26761_SR_CHROMA_SNR_CONTROL outputTuningSnr=$outputTuningSnr26761 " +\n            "permittedFactor=$srChromaDenoiseFactor26761 nativeVgnChromaOwner=true localMaterialGate=true")\n        MotionTrace.processingState(\n            "IRIS_26761_SR_CHROMA_SNR_CONTROL",\n            "outputTuningSnr=$outputTuningSnr26761 permittedFactor=$srChromaDenoiseFactor26761 " +\n                "nativeVgnChromaOwner=true localMaterialGate=true",\n        )\n        val maxTexture = IntArray(1)\n'''
replace_once(path, old, new)
old='''                            uniform2i(program,"uOutputOrigin",left,top); uniform2i(program,"uOutputFullSize",fullOutputWidth,fullOutputHeight); uniform2i(program,"uGuideSize",width,height)\n                            draw(program,tileWidth,tileHeight,intArrayOf(render))\n'''
new='''                            uniform2i(program,"uOutputOrigin",left,top); uniform2i(program,"uOutputFullSize",fullOutputWidth,fullOutputHeight); uniform2i(program,"uGuideSize",width,height)\n                            uniform1f(program,"uChromaDenoiseStrength26761",srChromaDenoiseFactor26761)\n                            draw(program,tileWidth,tileHeight,intArrayOf(render))\n'''
replace_once(path, old, new)
old='''    private fun reconstructTrue2x(\n        frames: List<RawStackFrame>,\n        images: List<SafeImage>,\n        evidence: List<True2xFrameEvidence>,\n        nativeVgnGuideTexture: Int,\n        preserveLinearRgbForDng: Boolean,\n    ): True2xResult {\n'''
new='''    private fun reconstructTrue2x(\n        frames: List<RawStackFrame>,\n        images: List<SafeImage>,\n        evidence: List<True2xFrameEvidence>,\n        nativeVgnGuideTexture: Int,\n        preserveLinearRgbForDng: Boolean,\n        outputTuningSnr26761: Float,\n    ): True2xResult {\n'''
replace_once(path, old, new)
replace_once(path,
'''        return reconstructDirectTrue2x26733(\n            frames, images, evidence, nativeVgnGuideTexture, preserveLinearRgbForDng,\n        )\n''',
'''        return reconstructDirectTrue2x26733(\n            frames, images, evidence, nativeVgnGuideTexture, preserveLinearRgbForDng,\n            outputTuningSnr26761,\n        )\n''')
old='''    private fun reconstructDirectTrue2x26733(\n        frames: List<RawStackFrame>,\n        images: List<SafeImage>,\n        evidence: List<True2xFrameEvidence>,\n        nativeVgnGuideTexture: Int,\n        preserveLinearRgbForDng: Boolean,\n    ): True2xResult {\n'''
new='''    private fun reconstructDirectTrue2x26733(\n        frames: List<RawStackFrame>,\n        images: List<SafeImage>,\n        evidence: List<True2xFrameEvidence>,\n        nativeVgnGuideTexture: Int,\n        preserveLinearRgbForDng: Boolean,\n        outputTuningSnr26761: Float,\n    ): True2xResult {\n'''
replace_once(path, old, new)
replace_once(path,
'''            val phase=runTrue2xGpu(images,evidence,directGpuFile,renderGpuFile,nativeVgnGuideTexture,outputWidth,outputHeight)\n''',
'''            val phase=runTrue2xGpu(images,evidence,directGpuFile,renderGpuFile,nativeVgnGuideTexture,outputWidth,outputHeight,outputTuningSnr26761)\n''')

# Shader: retain the exact 26760 same-material consensus, replace only the fixed blend maximum.
path='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
replace_once(path,
'''        uniform ivec2 uGuideSize;\n        layout(location = 0) out vec4 oRenderRgb;\n''',
'''        uniform ivec2 uGuideSize;\n        uniform float uChromaDenoiseStrength26761;\n        layout(location = 0) out vec4 oRenderRgb;\n''')
replace_once(path,
'''            float chromaDenoise26760 = 0.50 * (1.0 - 0.75 * materialBoundary);\n            selectedChroma = mix(selectedChroma, denoisedChroma26760, chromaDenoise26760);\n''',
'''            /* IRIS_26761_SUPER_RES_MEASURED_SNR_CHROMA_BLEND\n             * Preserve the complete 26760 same-material/native-VGN consensus and coherent-color\n             * retention. Only its maximum blend becomes the shared measured-output-SNR factor.\n             * materialBoundary still retreats the cleanup to 25% of that permitted maximum. */\n            float chromaDenoise26761 = clamp(uChromaDenoiseStrength26761, 0.50, 1.00) *\n                (1.0 - 0.75 * materialBoundary);\n            selectedChroma = mix(selectedChroma, denoisedChroma26760, chromaDenoise26761);\n''')

# Version only; same guarded build script will perform the authoritative build.
path='app/version.properties'
replace_once(path, 'VERSION_NAME=0.9726760\nVERSION_BUILD=26760\n', 'VERSION_NAME=0.9726761\nVERSION_BUILD=26761\n')

print('PASS transform 26761 exact 5-file measured-SNR chroma scope')
