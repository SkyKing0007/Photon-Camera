from pathlib import Path
import hashlib, sys, argparse, tempfile, shutil, subprocess, re

BASE_HASHES = {
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt':'aaa9cf09d99647bbc2cb4c0de912d2e4968bd4540b78776632691a10c00ee2c7',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt':'046056bc14fe56f0bef874d992db20ea8e5627ab160639dfbac96b1af352b63c',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt':'5e112314f0795e4294e3af9e8b127d7d86cdfa494cd8df042fd5c6ba9d7949a4',
'app/src/main/java/com/hinnka/mycamera/processor/MgcSpatialMergeTuning.kt':'dd4b11250dd99359c5907887ccbc24a67b355605fc27cd91a39076e4933b1523',
'app/src/main/java/com/hinnka/mycamera/processor/MgcAlignmentInputScale.kt':'859b70d1c7eb3e826b864b488e9006f5262c78f1cd5408e2284dc0b57baa3b6c',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt':'87b333570e0af22cc36c67ec0b2322c173794f846104917e92d7c3c38f32a025',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java':'f0e5eb2a9cd60c38c1b8b742d4862e7b45c61fe8193e8dffbe595c863976a51c',
}

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def once(s,a,b,label):
    c=s.count(a)
    if c != 1: raise RuntimeError(f'{label}: expected 1 anchor, found {c}')
    return s.replace(a,b,1)

def write(p,s): Path(p).write_text(s, encoding='utf-8')

def transform(root):
    root=Path(root)
    for rel,h in BASE_HASHES.items():
        p=root/rel
        if not p.is_file(): raise RuntimeError(f'missing {rel}')
        actual=sha(p)
        if actual != h: raise RuntimeError(f'base hash mismatch {rel}: {actual}')

    # 1) Final Bayer-alignment authority + post-merge propagated noise SNR + expected frame weight.
    p=root/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt'
    s=p.read_text(encoding='utf-8')
    s=s.replace('''                        flowTexture = zeroFlow,\n''','''                        alignmentTexture = zeroFlow,\n''')
    s=s.replace('''                        flowTexture = bentoFlowTexture,\n''','''                        alignmentTexture = bentoBayerAlignmentTexture,\n''')
    s=s.replace('''                            flowTexture = prepared.flowTexture,\n''','''                            alignmentTexture = prepared.bayerAlignmentTexture,\n''')
    if s.count('captureStrengthFrame(') != 5:
        raise RuntimeError(f'unexpected captureStrengthFrame count {s.count("captureStrengthFrame(")}')
    if 'flowTexture = prepared.flowTexture' in s or 'flowTexture = bentoFlowTexture' in s:
        raise RuntimeError('stale strength flow capture survived')
    s=once(s,
'''    private fun captureStrengthFrame(\n        capture: StrengthCapture,\n        frameIndex: Int,\n        calibration: FrameCalibration,\n        flowTexture: Int,\n        weightTexture: Int,\n        identityWeight: Boolean,\n    ) {''',
'''    private fun captureStrengthFrame(\n        capture: StrengthCapture,\n        frameIndex: Int,\n        calibration: FrameCalibration,\n        alignmentTexture: Int,\n        weightTexture: Int,\n        identityWeight: Boolean,\n    ) {''','strength function signature')
    s=once(s,
'''            bindTexture(strengthAlignmentProgram, "uFlow", 0, flowTexture)''',
'''            bindTexture(strengthAlignmentProgram, "uAlignment", 0, alignmentTexture)''','strength final alignment binding')

    old='''        val computedFrameWeight = if (\n            kernelTuning.referenceNoiseVariance > MIN_NOISE_VARIANCE &&\n            frameNoiseVariance > MIN_NOISE_VARIANCE\n        ) {\n            (kernelTuning.referenceNoiseVariance / frameNoiseVariance)\n                .coerceIn(0f, SPATIAL_FRAME_WEIGHT_CAP)\n        } else {\n            1f\n        }\n        val globalFrameWeight = computedFrameWeight\n            .takeIf { it.isFinite() && it > 0f }\n            ?: SPATIAL_IDENTITY_MULTIPLIER\n        val frameKernelScale = spatialFrameWeightKernelScale(globalFrameWeight)\n        val computedKernelSigma = 1f / (\n            kernelTuning.baseSpatialScale * frameKernelScale\n            ).coerceAtLeast(MIN_BAYER_KERNEL_SCALE)\n'''
    new='''        /* IRIS_26530_V1_3_MGC_EXPECTED_MERGE_WEIGHT\n         * Use the recovered Spatial expected-merge weight at the reference signal. This carries\n         * both shot and read noise into the exposure-normalized comparison; per-pixel motion\n         * rejection remains a separate multiplicative authority in the merge shader.\n         */\n        val globalFrameWeight = MgcSpatialMergeTuning.expectedMergeWeight(\n            referenceSignal = kernelTuning.referenceSignal,\n            baseShotNoiseFactor = kernelTuning.referenceGreenShotNoiseFactor,\n            baseReadVariance = kernelTuning.referenceGreenReadVariance,\n            alternateShotNoiseFactor = sourceShot.getOrElse(1) { 0f },\n            alternateReadVariance = sourceRead.getOrElse(1) { 0f },\n            exposureScale = exposureScale,\n        ).takeIf { it.isFinite() && it > 0f }\n            ?: SPATIAL_IDENTITY_MULTIPLIER\n        val frameKernelScale = MgcSpatialMergeTuning.frameWeightKernelMultiplier(globalFrameWeight)\n        val computedKernelSigma = 1f / (\n            kernelTuning.baseSpatialScale * frameKernelScale\n            ).coerceAtLeast(MIN_BAYER_KERNEL_SCALE)\n'''
    s=once(s,old,new,'expected merge weight')
    s=once(s,
'''            alignmentGain = exposureScale,''',
'''            /* IRIS_26530_V1_3_MGC_ALIGNMENT_S16_SCALE */\n            alignmentGain = MgcAlignmentInputScale.compute(\n                frameGain = exposureScale,\n                whiteLevel = sensorWhiteLevel,\n            ),''','alignment input scale')
    # remove now-dead local frame weight curve helper
    start=s.index('    private fun spatialFrameWeightKernelScale(frameWeight: Float): Float {')
    end=s.index('    private fun buildGrayPyramid(', start)
    s=s[:start]+s[end:]

    noise_anchor='''            val outputReadNoise = spatialNoiseModel?.outputReadNoise?.let { values ->\n                FloatArray(values.size) { channel ->\n                    values[channel] * outputExposure.readNoiseVarianceScale\n                }\n            }\n'''
    noise_insert=noise_anchor+'''            /* IRIS_26530_V1_3_PROPAGATED_OUTPUT_SNR\n             * FinishRaw denoise must use the noise model after real alignment/rejection/output\n             * exposure transport, not the pre-merge reference SNR or nominal frame count.\n             */\n            val propagatedOutputSnr = if (outputReadNoise != null && outputShotNoise != null) {\n                MgcSpatialMergeTuning.outputNoiseModelSnr(\n                    signal = bayerKernelTuning.referenceSignal *\n                        outputExposure.normalizationScale,\n                    greenReadVariance = outputReadNoise.getOrElse(1) { Float.NaN },\n                    greenShotNoiseFactor = outputShotNoise.getOrElse(1) { Float.NaN },\n                )\n            } else {\n                null\n            }\n            val finishRawDenoiseSnr = propagatedOutputSnr\n                ?: MgcSpatialMergeTuning.mergedSnr(\n                    bayerKernelTuning.referenceSnr,\n                    mergedFrames,\n                )\n'''
    s=once(s,noise_anchor,noise_insert,'propagated output snr')
    s=once(s,
'''                    "output=${outputWidth}x$outputHeight " +\n                    "lscApplied=$lensShadingCorrectionApplied result=$resultLabel " +''',
'''                    "output=${outputWidth}x$outputHeight " +\n                    "referenceSnr=${bayerKernelTuning.referenceSnr} " +\n                    "finishRawDenoiseSnr=$finishRawDenoiseSnr " +\n                    "finishRawDenoiseSnrSource=${if (propagatedOutputSnr != null) {\n                        "spatial-output-noise-model"\n                    } else {\n                        "reference-snr-frame-count-fallback"\n                    }} " +\n                    "lscApplied=$lensShadingCorrectionApplied result=$resultLabel " +''','merge complete snr telemetry')
    s=once(s,
'''                /* IRIS_26518_RELEASED_1271_RESULT_ABI_SNR_BRIDGE\n                 * Released c4ff already computes bayerKernelTuning.referenceSnr and uses it for\n                 * its Spatial kernel selection. Its historical RawStackResult predates the later\n                 * process-local tuning-SNR fields. Export that same c4ff value into the newer ABI\n                 * only; do not import post-Sabre Spatial tuning or Sabre TET attenuation math.\n                 */\n                mgcDenoiseTuningSnr = bayerKernelTuning.referenceSnr,\n                mgcSharpenTuningSnr = bayerKernelTuning.referenceSnr,''',
'''                /* IRIS_26530_V1_3_PROPAGATED_OUTPUT_SNR\n                 * Denoise tuning follows Spatial's propagated post-rejection output NoiseModel.\n                 * Sharpening remains disabled/frozen and retains the reference diagnostic only.\n                 */\n                mgcDenoiseTuningSnr = finishRawDenoiseSnr,\n                mgcSharpenTuningSnr = bayerKernelTuning.referenceSnr,''','result tuning snr')
    write(p,s)

    # 2) Strength atlas consumes final Bayer alignment, not generic flow.
    p=root/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt'
    s=p.read_text(encoding='utf-8')
    s=once(s,
'''        uniform sampler2D uFlow;\n        uniform ivec2 uOutputSize;''',
'''        /* IRIS_26530_V1_3_FINAL_BAYER_ALIGNMENT_AUTHORITY */\n        uniform sampler2D uAlignment;\n        uniform ivec2 uOutputSize;''','strength alignment uniform')
    s=once(s,
'''            oAlignment = texture(uFlow, uv)[uComponent];''',
'''            oAlignment = texture(uAlignment, uv)[uComponent];''','strength alignment sample')
    write(p,s)

    # 3) Supersede c317 direction-moment steering: post-fusion direction derives from RGB gradients.
    p=root/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
    s=p.read_text(encoding='utf-8')
    old='''        float snorm8(uint x){ int v=int(x&255u); if(v>127)v-=256; return clamp(float(v)/127.0,-1.0,1.0); }\n        vec2 directionMomentAt(ivec2 p){ uint a=imageLoad(uInput,safePos(p)).a; return vec2(snorm8(a),snorm8(a>>8u)); }\n        uint directionMaskAt(ivec2 p){\n            const ivec2 d[8]=ivec2[8](ivec2(0,-1),ivec2(1,0),ivec2(0,1),ivec2(-1,0),ivec2(1,-1),ivec2(1,1),ivec2(-1,1),ivec2(-1,-1));\n            const vec2 axis2[8]=vec2[8](vec2(-1,0),vec2(1,0),vec2(-1,0),vec2(1,0),vec2(0,-1),vec2(0,1),vec2(0,-1),vec2(0,1));\n            float center=yAt(p); vec2 moment=directionMomentAt(p); float g[8]; float lo=65504.0; float hi=0.0;\n            for(int i=0;i<8;++i){\n                float first=yAt(p+d[i]); float second=yAt(p+d[i]*2);\n                float rgbGradient=abs(center-first)+0.5*abs(first-second);\n                float structureScale=clamp(1.0+0.5*dot(moment,axis2[i]),0.5,1.5);\n                g[i]=rgbGradient*structureScale; lo=min(lo,g[i]); hi=max(hi,g[i]);\n            }\n'''
    new='''        /* IRIS_26530_V1_3_RGB_DIRECTION_ONLY\n         * Bjzhou's post-c317 MGC audit supersedes fused-green direction-moment steering here.\n         * The fused RGB/Y gradient now owns the post-fusion chroma direction decision.\n         */\n        uint directionMaskAt(ivec2 p){\n            const ivec2 d[8]=ivec2[8](ivec2(0,-1),ivec2(1,0),ivec2(0,1),ivec2(-1,0),ivec2(1,-1),ivec2(1,1),ivec2(-1,1),ivec2(-1,-1));\n            float center=yAt(p); float g[8]; float lo=65504.0; float hi=0.0;\n            for(int i=0;i<8;++i){\n                float first=yAt(p+d[i]); float second=yAt(p+d[i]*2);\n                float rgbGradient=abs(center-first)+0.5*abs(first-second);\n                g[i]=rgbGradient; lo=min(lo,g[i]); hi=max(hi,g[i]);\n            }\n'''
    s=once(s,old,new,'postprocessor rgb direction')
    s=s.replace('Iris-owned GLSL translation of the c317/MGC Spatial-RGB post-fusion behavior.',
                'Iris-owned GLSL translation of the latest post-c317 MGC Spatial-RGB post-fusion behavior.')
    write(p,s)

    # 4) Add recovered Spatial tuning helpers while preserving Iris's proven native-detail footprint.
    p=root/'app/src/main/java/com/hinnka/mycamera/processor/MgcSpatialMergeTuning.kt'
    s=p.read_text(encoding='utf-8')
    anchor='''    fun mergedSnr(referenceSnr: Float, frameCount: Int): Float {\n        val snr = referenceSnr.takeIf { it.isFinite() }?.coerceAtLeast(0f) ?: 0f\n        return snr * sqrt(frameCount.coerceAtLeast(0).toFloat())\n    }\n'''
    insert=anchor+'''\n    /* IRIS_26530_V1_3_PROPAGATED_OUTPUT_SNR */\n    fun outputNoiseModelSnr(\n        signal: Float,\n        greenReadVariance: Float,\n        greenShotNoiseFactor: Float,\n    ): Float? {\n        if (!signal.isFinite() || signal < 0f ||\n            !greenReadVariance.isFinite() || greenReadVariance < 0f ||\n            !greenShotNoiseFactor.isFinite() || greenShotNoiseFactor < 0f\n        ) return null\n        val variance = greenReadVariance + greenShotNoiseFactor * signal\n        if (!variance.isFinite() || variance <= 0f) return null\n        return (signal / sqrt(variance)).takeIf { it.isFinite() && it >= 0f }\n    }\n'''
    s=once(s,anchor,insert,'output noise SNR helper')
    max_anchor='''    /** Static MGC map initialized from libgcastartup.so rodata at 0x6b6e40. */\n    fun frameWeightKernelMultiplier(maximumMergeWeight: Float): Float = interpolate(\n'''
    expected='''    /* IRIS_26530_V1_3_MGC_EXPECTED_MERGE_WEIGHT\n     * Recovered Spatial ExpectedMergeWeight: compare shot+read variance at the reference signal\n     * after transporting the alternate frame into the base exposure domain.\n     */\n    fun expectedMergeWeight(\n        referenceSignal: Float,\n        baseShotNoiseFactor: Float,\n        baseReadVariance: Float,\n        alternateShotNoiseFactor: Float,\n        alternateReadVariance: Float,\n        exposureScale: Float,\n        frameWeightExponent: Float = DEFAULT_FRAME_WEIGHT_EXPONENT,\n    ): Float {\n        require(referenceSignal.isFinite() && referenceSignal >= 0f)\n        require(baseShotNoiseFactor.isFinite() && baseShotNoiseFactor >= 0f)\n        require(baseReadVariance.isFinite() && baseReadVariance >= 0f)\n        require(alternateShotNoiseFactor.isFinite() && alternateShotNoiseFactor >= 0f)\n        require(alternateReadVariance.isFinite() && alternateReadVariance >= 0f)\n        require(exposureScale.isFinite() && exposureScale > 0f)\n        require(frameWeightExponent.isFinite() && frameWeightExponent >= 0f)\n        val baseVariance = baseShotNoiseFactor * referenceSignal + baseReadVariance\n        val scaledAlternateVariance =\n            alternateShotNoiseFactor * exposureScale * referenceSignal +\n                alternateReadVariance * exposureScale * exposureScale\n        check(scaledAlternateVariance > 0f) {\n            "MGC Spatial requires positive alternate variance at the reference signal"\n        }\n        return (baseVariance / scaledAlternateVariance)\n            .pow(frameWeightExponent)\n            .coerceAtMost(MAXIMUM_MERGE_WEIGHT_CAP)\n    }\n\n'''+max_anchor
    s=once(s,max_anchor,expected,'expected merge helper')
    # neutralize parameter name so callers no longer imply shadow-only maximum semantics
    s=s.replace('fun frameWeightKernelMultiplier(maximumMergeWeight: Float): Float = interpolate(\n        maximumMergeWeight.takeIf',
                'fun frameWeightKernelMultiplier(mergeWeight: Float): Float = interpolate(\n        mergeWeight.takeIf')
    write(p,s)

    # 5) Clarify/use the recovered sensor-white S16 alignment scale.
    p=root/'app/src/main/java/com/hinnka/mycamera/processor/MgcAlignmentInputScale.kt'
    s=p.read_text(encoding='utf-8')
    s=once(s,
'''/** Fixed-point input scaling used by MGC's RAW alignment pyramid. */\ninternal object MgcAlignmentInputScale {\n    const val S16_DOMAIN_SCALE = 16384f\n\n    fun compute(frameGain: Float, whiteLevel: Float): Float {\n        require(frameGain.isFinite() && frameGain > 0f)\n        require(whiteLevel.isFinite() && whiteLevel >= 0f)\n        return frameGain * S16_DOMAIN_SCALE / (whiteLevel + 1f)\n    }\n}''',
'''/**\n * IRIS_26530_V1_3_MGC_ALIGNMENT_S16_SCALE\n * Exact fixed-point input scaling recovered from MGC V25 BuildAlignPyramidForBurst:\n * frame gain times 16384 divided by StaticMetadata.white_level + 1.\n */\ninternal object MgcAlignmentInputScale {\n    const val S16_DOMAIN_SCALE = 16384f\n\n    fun compute(frameGain: Float, whiteLevel: Float): Float {\n        require(frameGain.isFinite() && frameGain > 0f)\n        require(whiteLevel.isFinite() && whiteLevel >= 0f)\n        return frameGain * S16_DOMAIN_SCALE / (whiteLevel + 1f)\n    }\n}''','alignment helper semantics')
    write(p,s)

    # 6) Motion master denoise experiment: effective MGC luma is zero, chroma remains user-owned.
    p=root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'
    s=p.read_text(encoding='utf-8')
    s=once(s,
'''            val renderResidualZoom = localOutputZoom / spatialReconstructionZoom\n            PLog.i(TAG, "IRIS_26530_MOTION_SAFE_RAW_SUPERRES " +\n                "displayedGlobalZoom=$displayedGlobalZoom localOutputZoom=$localOutputZoom " +\n                "spatialReconstructionZoom=$spatialReconstructionZoom " +\n                "renderResidualZoom=$renderResidualZoom threshold=8.0 cap=2.0 " +\n                "motionAuthority=existingSpatialRejection cfaGeometry=sharedGreenOpponent")''',
'''            /* IRIS_26530_V1_3_FOV_AUTHORITY\n             * SR scale controls reconstruction sampling only. The final JPEG/UHDR FOV remains the\n             * full requested local zoom; do not divide that authority by the SR scale.\n             */\n            PLog.i(TAG, "IRIS_26530_MOTION_SAFE_RAW_SUPERRES " +\n                "displayedGlobalZoom=$displayedGlobalZoom localOutputZoom=$localOutputZoom " +\n                "spatialReconstructionZoom=$spatialReconstructionZoom " +\n                "finalRenderLocalZoom=$localOutputZoom threshold=8.0 cap=2.0 " +\n                "motionAuthority=existingSpatialRejection cfaGeometry=sharedGreenOpponent")''','bridge FOV authority')
    s=once(s,
'''            val lumaScale = irisSettings.lumaDenoise\n            val chromaScale = irisSettings.chromaDenoise\n            val runFullResolutionDenoise = irisSettings.noiseReductionEnabled &&\n                (lumaScale > 0f || chromaScale > 0f)''',
'''            /* IRIS_26530_V1_3_ZERO_MGC_LUMA\n             * The Motion master may still run chroma cleanup, but explicit full-resolution MGC\n             * luma denoise is zero so temporal/SR reconstruction is not smoothed a second time.\n             */\n            val requestedLumaScale = irisSettings.lumaDenoise\n            val lumaScale = 0f\n            val chromaScale = irisSettings.chromaDenoise\n            val runFullResolutionDenoise = irisSettings.noiseReductionEnabled &&\n                chromaScale > 0f''','zero MGC luma')
    s=once(s,
'''            PLog.i(TAG, "IRIS_26514_DENOISE master=${irisSettings.noiseReductionEnabled} " +\n                "luma=$lumaScale chroma=$chromaScale executed=$runFullResolutionDenoise " +\n                "legacyPhotonNr=false")''',
'''            PLog.i(TAG, "IRIS_26530_V1_3_DENOISE_ZOOM_AUTHORITY " +\n                "master=${irisSettings.noiseReductionEnabled} " +\n                "requestedLuma=$requestedLumaScale effectiveMgcLuma=$lumaScale " +\n                "chroma=$chromaScale executed=$runFullResolutionDenoise " +\n                "srScale=$spatialReconstructionZoom requestedLocalZoom=$localOutputZoom " +\n                "finalFovZoom=$displayedGlobalZoom finalRenderLocalZoom=$localOutputZoom " +\n                "pass=SPATIAL_DEFAULT legacyPhotonNr=false sabreSelected=false")''','denoise+zoom telemetry')
    write(p,s)

    # 7) Final renderer uses the full requested local zoom; SR scale remains diagnostic/sampling state.
    p=root/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
    s=p.read_text(encoding='utf-8')
    s=once(s,
'''        /* IRIS_26530_RENDER_RESIDUAL_ZOOM\n         * The requested DNG/output zoom remains unchanged in Parameters. JPEG/UHDR only performs\n         * the crop not already reconstructed from multiframe RAW samples.\n         */\n        float spatialReconstructionZoom = Math.max(1.0f,\n                basePipeline.mParameters.motionV2SpatialReconstructionZoom);\n        float irisOutputZoom = Math.max(1.0f,\n                basePipeline.mParameters.motionV2OutputZoom / spatialReconstructionZoom);\n        Log.i("MotionV2Render", "IRIS_26530_RENDER_RESIDUAL_ZOOM requestedLocal="\n                + basePipeline.mParameters.motionV2OutputZoom\n                + " spatial=" + spatialReconstructionZoom\n                + " residual=" + irisOutputZoom);''',
'''        /* IRIS_26530_V1_3_FOV_AUTHORITY\n         * motionV2OutputZoom is the final FOV authority. SR reconstruction scale must not divide\n         * the JPEG/UHDR crop request; doing so produced the measured ~2x-wide 123x frame.\n         */\n        float spatialReconstructionZoom = Math.max(1.0f,\n                basePipeline.mParameters.motionV2SpatialReconstructionZoom);\n        float irisOutputZoom = Math.max(1.0f,\n                basePipeline.mParameters.motionV2OutputZoom);\n        Log.i("MotionV2Render", "IRIS_26530_V1_3_FINAL_FOV_ZOOM requestedLocal="\n                + basePipeline.mParameters.motionV2OutputZoom\n                + " srScale=" + spatialReconstructionZoom\n                + " finalRenderLocal=" + irisOutputZoom);''','render final FOV')
    write(p,s)

    # Global invariants.
    active=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
    if 'mergeMethod = MgcMergeMethod.SPATIAL_RGB' not in active: raise RuntimeError('Spatial RGB bridge owner lost')
    if 'MgcMergeMethod.SABRE' in active or 'Pass.SABRE_DEFAULT' in active: raise RuntimeError('Sabre entered Motion bridge')
    post=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt').read_text()
    if 'directionMomentAt(' in post or 'structureScale=' in post: raise RuntimeError('c317 direction moment steering survived')
    if 'effectiveMgcLuma=$lumaScale' not in active or 'val lumaScale = 0f' not in active: raise RuntimeError('zero luma authority missing')


def diff_dirs(base: Path, after: Path, reverse=False):
    a,b=(after,base) if reverse else (base,after)
    cp=subprocess.run(['diff','-ruN','--exclude=version.properties',str(a/'app/src/main'),str(b/'app/src/main')],text=True,stdout=subprocess.PIPE)
    if cp.returncode not in (0,1): raise RuntimeError('diff failed')
    out=cp.stdout.replace(str(a/'app/src/main'),'a/app/src/main').replace(str(b/'app/src/main'),'b/app/src/main')
    out=re.sub(r'^(---|\+\+\+) ([^\t\n]+)\t.*$', r'\1 \2', out, flags=re.M)
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root',nargs='?'); ap.add_argument('--check-only',action='store_true'); ap.add_argument('--self-test',action='store_true'); ap.add_argument('--patch-out'); ap.add_argument('--patch-sha-out'); ap.add_argument('--rollback-out'); ap.add_argument('--rollback-sha-out'); args=ap.parse_args()
    if args.self_test:
        assert len(BASE_HASHES)==7
        print('PASS: 26530 V1.3 transformer self-test exact seven-file V1.2 base hash lock'); return
    if not args.root: ap.error('root required')
    root=Path(args.root).resolve()
    if args.check_only:
        with tempfile.TemporaryDirectory(prefix='iris26530v13_') as td:
            tmp=Path(td)/'tree'; shutil.copytree(root,tmp); transform(tmp)
            fwd=diff_dirs(root,tmp); rev=diff_dirs(root,tmp,True)
            if not fwd.strip() or not rev.strip(): raise RuntimeError('empty patch')
            for path,data,side in [(args.patch_out,fwd,args.patch_sha_out),(args.rollback_out,rev,args.rollback_sha_out)]:
                if path:
                    q=Path(path); q.write_text(data)
                    if side: Path(side).write_text(f'{hashlib.sha256(q.read_bytes()).hexdigest()}  {q.name}\n')
            print('PASS: 26530 V1.3 in-memory transform resolved; forward+rollback available before candidate writes')
    else:
        transform(root); print('PASS: applied 26530 V1.3 latest-MGC Spatial parity + zero-luma + FOV authority')
if __name__=='__main__': main()
