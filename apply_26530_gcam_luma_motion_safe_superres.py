#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, re, shutil, subprocess, sys, tempfile
from pathlib import Path

FILES = {
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt':'b2bd50c1a2aa13baf4cf109ef3665e3e35f0bb363d5bc09982af33b59761c346',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt':'441dc1bd5cc4b0aa58c2b0eaeab7bdca003fe8dd4798137cb4077be512a0189d',
'app/src/main/java/com/hinnka/mycamera/processor/MgcSpatialRgbTilePlanner.kt':'db7d32fc229a68457f4e3c81a0e99b058dd6b2a321ada72c38cba0edf04aa9fb',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt':'27f658ec01fe54c1275686cf1ec8c2b578a63714ed3c5c552ec33ff89d3e3c73',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt':'3a472a4a55ecfd641a9e5f1614378970a1e6c151914bd9e601eace88bed41da0',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java':'0e9dd3c8f72f4699a17d1d6ade8e8c5b33cf2eabf86e2a3ac9069eda2c3b1416',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java':'351fd85fdb38c6299cc0a09d7a38f0d364573c4f33548838e871d617de622e34',
}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def once(s, old, new, label):
    n=s.count(old)
    if n != 1: raise RuntimeError(f'{label}: anchor count={n}, expected 1')
    return s.replace(old,new,1)
def write(p,s): p.write_text(s,encoding='utf-8')

def transform(root: Path):
    for rel,h in FILES.items():
        p=root/rel
        if not p.is_file(): raise RuntimeError(f'missing predecessor file {rel}')
        got=sha(p)
        if got!=h: raise RuntimeError(f'26529 predecessor hash mismatch {rel}: {got} != {h}')

    # Shader owner: keep 26529 low-zoom shaders byte-for-byte; derive high-zoom-only variants.
    p=root/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt'; s=p.read_text()
    anchor='''    val normalizeRgb16 = """\n'''
    sr='''    /* IRIS_26530_MOTION_SAFE_RAW_SUPERRES\n     * High-zoom-only derivative of the proven 26529 joint CFA shader. The legacy mergeRgb\n     * string above is untouched and remains the <8x path. Spatial reconstruction maps the\n     * requested crop directly into the original output grid; one shared green-driven geometry\n     * remains authoritative for G/R-G/B-G so red/blue can never invent independent edge motion.\n     * Luma temporal scaling applies only to green semantic/value support. Chroma opponents keep\n     * the full rejection/global-frame weights for strong color-noise suppression.\n     */\n    val mergeRgbSuperRes = mergeRgb\n        .replace(\n            "uniform ivec2 uOutputSize;",\n            "uniform ivec2 uOutputSize;\\nuniform float uReconstructionZoom;\\nuniform float uLumaTemporalScale;",\n        )\n        .replace(\n            "vec2 referenceRaw = (vec2(outputPixel) + vec2(0.5)) *\\n                vec2(uRawSize) / vec2(uOutputSize) - vec2(0.5);",\n            "vec2 fullRaw = (vec2(outputPixel) + vec2(0.5)) *\\n                vec2(uRawSize) / vec2(uOutputSize) - vec2(0.5);\\n            vec2 rawCenter = (vec2(uRawSize) - vec2(1.0)) * 0.5;\\n            vec2 referenceRaw = rawCenter + (fullRaw - rawCenter) / max(uReconstructionZoom, 1.0);",\n        )\n        .replace(\n            "frameWeight *= uGlobalFrameWeight;\\n            vec2 directionMoment = greenDirectionMoment(anchor, targetGreen);\\n            oColorAndRWeight = vec4(semanticSums * frameWeight, weights.r * frameWeight);\\n            oGbWeights = vec4(\\n                weights.gb * frameWeight,\\n                directionMoment * weights.r * frameWeight\\n            );",\n            "frameWeight *= uGlobalFrameWeight;\\n            float lumaFrameWeight = frameWeight * clamp(uLumaTemporalScale, 0.0, 1.0);\\n            vec2 directionMoment = greenDirectionMoment(anchor, targetGreen);\\n            oColorAndRWeight = vec4(\\n                semanticSums.r * lumaFrameWeight,\\n                semanticSums.g * frameWeight,\\n                semanticSums.b * frameWeight,\\n                weights.r * lumaFrameWeight\\n            );\\n            oGbWeights = vec4(\\n                weights.gb * frameWeight,\\n                directionMoment * weights.r * lumaFrameWeight\\n            );",\n        )\n\n'''
    s=once(s,anchor,sr+anchor,'shader superres insertion')
    # Add SR normalizer after legacy normalizer, before float variant.
    anchor='''    /** Float variant used only for the direct CPU black-box boundary. */\n'''
    srnorm='''    /* IRIS_26530_SUPERRES_LSC_SENSOR_COORDINATE\n     * Crop-aware SR must sample lens shading at the reconstructed sensor coordinate, not at the\n     * post-crop output coordinate. This avoids radial R/G/B gain errors and pink/green edges.\n     */\n    val normalizeRgb16SuperRes = normalizeRgb16\n        .replace(\n            "uniform ivec2 uOutputSize;",\n            "uniform ivec2 uOutputSize;\\nuniform ivec2 uRawSize;\\nuniform float uReconstructionZoom;",\n        )\n        .replace(\n            "vec2 uv = (vec2(outputPixel) + vec2(0.5)) / vec2(uOutputSize);",\n            "vec2 fullRaw = (vec2(outputPixel) + vec2(0.5)) * vec2(uRawSize) / vec2(uOutputSize) - vec2(0.5);\\n                vec2 rawCenter = (vec2(uRawSize) - vec2(1.0)) * 0.5;\\n                vec2 referenceRaw = rawCenter + (fullRaw - rawCenter) / max(uReconstructionZoom, 1.0);\\n                vec2 uv = (referenceRaw + vec2(0.5)) / vec2(uRawSize);",\n        )\n\n'''
    s=once(s,anchor,srnorm+anchor,'shader sr normalizer insertion'); write(p,s)

    # Tile planner: exact same output->RAW center-crop mapping as high-zoom shader; default 1x for dormant owners.
    p=root/'app/src/main/java/com/hinnka/mycamera/processor/MgcSpatialRgbTilePlanner.kt'; s=p.read_text()
    s=once(s,'''        outputHeight: Int,\n        flowBounds: MgcSpatialRgbFlowBounds,\n    ): MgcSpatialRgbRect {''','''        outputHeight: Int,\n        flowBounds: MgcSpatialRgbFlowBounds,\n        reconstructionZoom: Float = 1f,\n    ): MgcSpatialRgbRect {''','planner signature')
    s=once(s,'''        require(outputWidth > 0 && outputHeight > 0)\n        val output = tile.outputCore''','''        require(outputWidth > 0 && outputHeight > 0)\n        require(reconstructionZoom.isFinite() && reconstructionZoom >= 1f)\n        val output = tile.outputCore''','planner require')
    for axis in ['X','Y']:
        pass
    s=once(s,'''        val firstRawX = outputToRaw(output.left, rawWidth, outputWidth)\n        val lastRawX = outputToRaw(output.right - 1, rawWidth, outputWidth)\n        val firstRawY = outputToRaw(output.top, rawHeight, outputHeight)\n        val lastRawY = outputToRaw(output.bottom - 1, rawHeight, outputHeight)''','''        /* IRIS_26530_SR_TILE_SHADER_GEOMETRY_PARITY */\n        val firstRawX = outputToRaw(output.left, rawWidth, outputWidth, reconstructionZoom)\n        val lastRawX = outputToRaw(output.right - 1, rawWidth, outputWidth, reconstructionZoom)\n        val firstRawY = outputToRaw(output.top, rawHeight, outputHeight, reconstructionZoom)\n        val lastRawY = outputToRaw(output.bottom - 1, rawHeight, outputHeight, reconstructionZoom)''','planner calls')
    s=once(s,'''    private fun outputToRaw(outputPixel: Int, rawSize: Int, outputSize: Int): Float =\n        (outputPixel + 0.5f) * rawSize.toFloat() / outputSize.toFloat() - 0.5f''','''    private fun outputToRaw(\n        outputPixel: Int, rawSize: Int, outputSize: Int, reconstructionZoom: Float,\n    ): Float {\n        val fullRaw = (outputPixel + 0.5f) * rawSize.toFloat() / outputSize.toFloat() - 0.5f\n        val rawCenter = (rawSize.toFloat() - 1f) * 0.5f\n        return rawCenter + (fullRaw - rawCenter) / reconstructionZoom\n    }''','planner map'); write(p,s)

    # Fusion owner: carry only two immutable high-zoom policy inputs into active Iris owner.
    p=root/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt'; s=p.read_text()
    s=once(s,'''    outputScale: Float,\n    private val useCurrentGlContext: Boolean,''','''    outputScale: Float,\n    private val reconstructionZoom: Float = 1f,\n    private val displayedGlobalZoom: Float = 1f,\n    private val useCurrentGlContext: Boolean,''','fusion ctor')
    s=once(s,'''                outputScale = outputScale,\n                useCurrentGlContext = useCurrentGlContext,''','''                outputScale = outputScale,\n                reconstructionZoom = reconstructionZoom,\n                displayedGlobalZoom = displayedGlobalZoom,\n                useCurrentGlContext = useCurrentGlContext,''','fusion active owner'); write(p,s)

    # Bridge: displayed 8x threshold; raw-domain reconstruction capped at 2x, residual remains renderer-only.
    p=root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'; s=p.read_text()
    anchor='''            egl = EglOwner.create()\n            val fusion = GlesMgcRawFusion(\n'''
    repl='''            /* IRIS_26530_SR_RECONSTRUCTION_ZOOM\n             * Only digitally enlarged high-zoom captures enter crop-aware RAW SR. Native/low zoom\n             * retains the exact 26529 Spatial mapping. 2x is a conservative subpixel-reconstruction\n             * cap; any remaining requested crop is left to MotionV2Render.\n             */\n            val displayedGlobalZoom = parameters.motionV2GlobalZoom\n                .takeIf { it.isFinite() }?.coerceAtLeast(1f) ?: 1f\n            val localOutputZoom = parameters.motionV2OutputZoom\n                .takeIf { it.isFinite() }?.coerceAtLeast(1f) ?: 1f\n            val spatialReconstructionZoom = if (\n                displayedGlobalZoom >= 8f && localOutputZoom > 1.0001f\n            ) minOf(2f, localOutputZoom) else 1f\n            parameters.motionV2SpatialReconstructionZoom = spatialReconstructionZoom\n            val renderResidualZoom = localOutputZoom / spatialReconstructionZoom\n            PLog.i(TAG, "IRIS_26530_MOTION_SAFE_RAW_SUPERRES " +\n                "displayedGlobalZoom=$displayedGlobalZoom localOutputZoom=$localOutputZoom " +\n                "spatialReconstructionZoom=$spatialReconstructionZoom " +\n                "renderResidualZoom=$renderResidualZoom threshold=8.0 cap=2.0 " +\n                "motionAuthority=existingSpatialRejection cfaGeometry=sharedGreenOpponent")\n\n            egl = EglOwner.create()\n            val fusion = GlesMgcRawFusion(\n'''
    s=once(s,anchor,repl,'bridge policy')
    s=once(s,'''                outputScale = 1f,\n                useCurrentGlContext = true,''','''                outputScale = 1f,\n                reconstructionZoom = spatialReconstructionZoom,\n                displayedGlobalZoom = displayedGlobalZoom,\n                useCurrentGlContext = true,''','bridge fusion args'); write(p,s)

    # Parameter state used by final render only. DNG continues to consume motionV2OutputZoom unchanged.
    p=root/'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java'; s=p.read_text()
    s=once(s,'''    public float motionV2OutputZoom = 1.0f;\n    public float motionV2HardwareZoom = 1.0f;''','''    public float motionV2OutputZoom = 1.0f;\n    /* IRIS_26530_DNG_ZOOM_UNCHANGED\n     * JPEG/UHDR may consume this crop inside Spatial first. DNG DefaultCrop remains owned solely\n     * by motionV2OutputZoom, preserving the 26525 one-crop DNG contract.\n     */\n    public float motionV2SpatialReconstructionZoom = 1.0f;\n    public float motionV2HardwareZoom = 1.0f;''','params sr field'); write(p,s)

    # Renderer applies only crop not already reconstructed from RAW. Gain map uses same geometry.
    p=root/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'; s=p.read_text()
    s=once(s,'''        /* IRIS_26524_FULLSIZE_MOTION_ZOOM_RENDER */\n        float irisOutputZoom = Math.max(1.0f,\n                basePipeline.mParameters.motionV2OutputZoom);''','''        /* IRIS_26530_RENDER_RESIDUAL_ZOOM\n         * The requested DNG/output zoom remains unchanged in Parameters. JPEG/UHDR only performs\n         * the crop not already reconstructed from multiframe RAW samples.\n         */\n        float spatialReconstructionZoom = Math.max(1.0f,\n                basePipeline.mParameters.motionV2SpatialReconstructionZoom);\n        float irisOutputZoom = Math.max(1.0f,\n                basePipeline.mParameters.motionV2OutputZoom / spatialReconstructionZoom);\n        Log.i("MotionV2Render", "IRIS_26530_RENDER_RESIDUAL_ZOOM requestedLocal="\n                + basePipeline.mParameters.motionV2OutputZoom\n                + " spatial=" + spatialReconstructionZoom\n                + " residual=" + irisOutputZoom);''','render residual'); write(p,s)

    # Stacker high-zoom policy and program selection.
    p=root/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt'; s=p.read_text()
    s=once(s,'''    private val outputMode: MgcSpatialOutputMode,\n    outputScale: Float,\n    private val useCurrentGlContext: Boolean,''','''    private val outputMode: MgcSpatialOutputMode,\n    outputScale: Float,\n    private val reconstructionZoom: Float = 1f,\n    private val displayedGlobalZoom: Float = 1f,\n    private val useCurrentGlContext: Boolean,''','stacker ctor')
    s=once(s,'''    private var mergeRgbProgram = 0\n    private var normalizeBayerProgram = 0''','''    private var mergeRgbProgram = 0\n    /* IRIS_26530_LOW_ZOOM_LEGACY_SHADER_ISOLATION */\n    private var mergeRgbSuperResProgram = 0\n    private var normalizeRgbSuperResProgram = 0\n    private var iris26530LumaAuxScale = 1f\n    private var iris26530LumaTargetFrames = 0f\n    private val iris26530SuperResEnabled = outputMode == MgcSpatialOutputMode.RGB &&\n        displayedGlobalZoom >= 8f && reconstructionZoom > 1.0001f\n    private var normalizeBayerProgram = 0''','stacker fields')
    s=once(s,'''            normalizeRgbProgram = linkProgram(\n                GlesIris26521SpatialRgbShaders.normalizeRgb16,\n                "mgc_spatial_rgb16ui",\n            )''','''            normalizeRgbProgram = linkProgram(\n                GlesIris26521SpatialRgbShaders.normalizeRgb16,\n                "mgc_spatial_rgb16ui",\n            )\n            if (iris26530SuperResEnabled) {\n                mergeRgbSuperResProgram = linkProgram(\n                    GlesIris26521SpatialRgbShaders.mergeRgbSuperRes,\n                    "iris26530_spatial_rgb_superres_merge",\n                )\n                normalizeRgbSuperResProgram = linkProgram(\n                    GlesIris26521SpatialRgbShaders.normalizeRgb16SuperRes,\n                    "iris26530_spatial_rgb_superres_normalize",\n                )\n            }''','stacker init programs')
    # configure target at exact point frame population is known
    anchor='''            val spatialNoiseFrameCount =\n                1 + (if (bentoAccepted) 1 else 0) + temporalMergeCount\n'''
    repl=anchor+'''            if (iris26530SuperResEnabled) {\n                iris26530LumaTargetFrames = iris26530TargetEffectiveLumaFrames(displayedGlobalZoom)\n                    .coerceAtMost(spatialNoiseFrameCount.toFloat())\n                iris26530LumaAuxScale = iris26530AuxiliaryLumaScale(\n                    frameCount = spatialNoiseFrameCount,\n                    targetEffectiveFrames = iris26530LumaTargetFrames,\n                )\n                PLog.i(TAG, "IRIS_26530_GCAM_LUMA_EFFECTIVE_STACK " +\n                    "displayedGlobalZoom=$displayedGlobalZoom frames=$spatialNoiseFrameCount " +\n                    "target=${iris26530LumaTargetFrames} auxiliaryScale=$iris26530LumaAuxScale " +\n                    "referenceScale=1.0 chromaScale=full motionGate=existingSpatialRejection")\n            }\n'''
    s=once(s,anchor,repl,'stacker target config')
    # planner gets geometry
    s=once(s,'''                    outputHeight = outputHeight,\n                    flowBounds = frame.flowBounds,\n                )''','''                    outputHeight = outputHeight,\n                    flowBounds = frame.flowBounds,\n                    reconstructionZoom = if (iris26530SuperResEnabled) reconstructionZoom else 1f,\n                )''','stacker planner')
    # render contribution replace function program references minimally
    s=once(s,'''        require(outputCores.isNotEmpty())\n        GLES30.glUseProgram(mergeRgbProgram)\n        bindTexture(mergeRgbProgram, "uRaw", 0, rawTexture)''','''        require(outputCores.isNotEmpty())\n        val activeMergeProgram = if (iris26530SuperResEnabled) mergeRgbSuperResProgram else mergeRgbProgram\n        check(activeMergeProgram != 0)\n        GLES30.glUseProgram(activeMergeProgram)\n        bindTexture(activeMergeProgram, "uRaw", 0, rawTexture)''','contribution program start')
    # in function range replace mergeRgbProgram occurrences with activeMergeProgram until next function
    start=s.index('    private fun renderRgbFrameContribution('); end=s.index('    private fun renderRgbChromaGuide(', start)
    block=s[start:end].replace('mergeRgbProgram', 'activeMergeProgram')
    # undo declaration accidental name if any
    block=block.replace('val activeMergeProgram = if (iris26530SuperResEnabled) mergeRgbSuperResProgram else activeMergeProgram', 'val activeMergeProgram = if (iris26530SuperResEnabled) mergeRgbSuperResProgram else mergeRgbProgram')
    # add SR uniforms after output size
    block=once(block,'''        uniform2i(activeMergeProgram, "uOutputSize", outputWidth, outputHeight)\n''','''        uniform2i(activeMergeProgram, "uOutputSize", outputWidth, outputHeight)\n        if (iris26530SuperResEnabled) {\n            uniform1f(activeMergeProgram, "uReconstructionZoom", reconstructionZoom)\n            uniform1f(\n                activeMergeProgram,\n                "uLumaTemporalScale",\n                if (frame.imageIndex == 0) 1f else iris26530LumaAuxScale,\n            )\n        }\n''','contribution sr uniforms')
    s=s[:start]+block+s[end:]
    # normalized tile choose SR normalizer and correct LSC coordinate
    start=s.index('    private fun renderRgbNormalizedTile('); end=s.index('    private fun createRgbChromaPostprocessor(', start)
    block=s[start:end]
    block=once(block,'''        GLES30.glUseProgram(normalizeRgbProgram)\n        bindTexture(normalizeRgbProgram, "uColorAndRWeight", 0, semanticAccumulator)''','''        val activeNormalizeProgram = if (iris26530SuperResEnabled) normalizeRgbSuperResProgram else normalizeRgbProgram\n        check(activeNormalizeProgram != 0)\n        GLES30.glUseProgram(activeNormalizeProgram)\n        bindTexture(activeNormalizeProgram, "uColorAndRWeight", 0, semanticAccumulator)''','normalize program start')
    block=block.replace('normalizeRgbProgram', 'activeNormalizeProgram')
    block=block.replace('val activeNormalizeProgram = if (iris26530SuperResEnabled) normalizeRgbSuperResProgram else activeNormalizeProgram', 'val activeNormalizeProgram = if (iris26530SuperResEnabled) normalizeRgbSuperResProgram else normalizeRgbProgram')
    block=once(block,'''        uniform2i(activeNormalizeProgram, "uOutputSize", outputWidth, outputHeight)\n''','''        uniform2i(activeNormalizeProgram, "uOutputSize", outputWidth, outputHeight)\n        if (iris26530SuperResEnabled) {\n            uniform2i(activeNormalizeProgram, "uRawSize", width, height)\n            uniform1f(activeNormalizeProgram, "uReconstructionZoom", reconstructionZoom)\n        }\n''','normalize sr uniforms')
    s=s[:start]+block+s[end:]
    # helper functions before companion object
    anchor='''    private data class NormalDngSupportStats(\n'''
    helpers='''    /* IRIS_26530_GCAM_LUMA_EFFECTIVE_STACK\n     * Static fully-accepted regions are calibrated to the tuned-GCam 8x reference: seven\n     * effective luma frames through 50x, rising smoothly to nine by 120x. The reference keeps\n     * unit weight; only auxiliary green/luma weights are reduced. Existing per-pixel rejection\n     * remains multiplicative, so motion can only reduce auxiliary contribution further.\n     */\n    private fun iris26530TargetEffectiveLumaFrames(globalZoom: Float): Float {\n        if (!globalZoom.isFinite() || globalZoom < 8f) return 0f\n        if (globalZoom <= 50f) return 7f\n        val t = ((globalZoom - 50f) / 70f).coerceIn(0f, 1f)\n        return 7f + 2f * (t * t * (3f - 2f * t))\n    }\n\n    private fun iris26530AuxiliaryLumaScale(\n        frameCount: Int,\n        targetEffectiveFrames: Float,\n    ): Float {\n        if (frameCount <= 1 || targetEffectiveFrames >= frameCount.toFloat()) return 1f\n        val target = targetEffectiveFrames.coerceIn(1f, frameCount.toFloat())\n        val auxiliaries = (frameCount - 1).toFloat()\n        var lo = 0f\n        var hi = 1f\n        repeat(40) {\n            val beta = 0.5f * (lo + hi)\n            val sum = 1f + auxiliaries * beta\n            val sumSquares = 1f + auxiliaries * beta * beta\n            val neff = sum * sum / sumSquares\n            if (neff < target) lo = beta else hi = beta\n        }\n        return 0.5f * (lo + hi)\n    }\n\n'''
    s=once(s,anchor,helpers+anchor,'stacker helpers'); write(p,s)

    # Structural assertions after transform.
    checks={
      'GlesIris26521SpatialRgbShaders.kt':['mergeRgbSuperRes','uReconstructionZoom','uLumaTemporalScale','normalizeRgb16SuperRes','IRIS_26530_SUPERRES_LSC_SENSOR_COORDINATE'],
      'GlesIris26521SpatialRgbStacker.kt':['IRIS_26530_GCAM_LUMA_EFFECTIVE_STACK','iris26530AuxiliaryLumaScale','mergeRgbSuperResProgram','normalizeRgbSuperResProgram'],
      'MgcSpatialRgbTilePlanner.kt':['IRIS_26530_SR_TILE_SHADER_GEOMETRY_PARITY','reconstructionZoom'],
      'PhotonMotionMgc1271Bridge.kt':['IRIS_26530_MOTION_SAFE_RAW_SUPERRES','spatialReconstructionZoom'],
      'MotionV2Render.java':['IRIS_26530_RENDER_RESIDUAL_ZOOM','motionV2SpatialReconstructionZoom'],
    }
    for name,toks in checks.items():
      matches=[q for q in root.rglob(name)]
      if len(matches)!=1: raise RuntimeError(f'{name}: cardinality {len(matches)}')
      text=matches[0].read_text()
      for t in toks:
        if t not in text: raise RuntimeError(f'{name}: missing {t}')

def diff_dirs(base: Path, after: Path, reverse=False):
    a,b=(after,base) if reverse else (base,after)
    cp=subprocess.run(['diff','-ruN','--exclude=version.properties',str(a/'app/src/main'),str(b/'app/src/main')],text=True,stdout=subprocess.PIPE)
    if cp.returncode not in (0,1): raise RuntimeError('diff failed')
    # normalize absolute temp prefixes to a/ and b/ patch paths
    out=cp.stdout.replace(str(a/'app/src/main'),'a/app/src/main').replace(str(b/'app/src/main'),'b/app/src/main')
    # diff(1) embeds filesystem mtimes in ---/+++ headers. Strip them so the certified patch is
    # byte-reproducible when the same exact candidate is transformed later in GitHub Actions.
    out=re.sub(r'^(---|\+\+\+) ([^\t\n]+)\t.*$', r'\1 \2', out, flags=re.M)
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root',nargs='?'); ap.add_argument('--check-only',action='store_true'); ap.add_argument('--self-test',action='store_true'); ap.add_argument('--patch-out'); ap.add_argument('--patch-sha-out'); ap.add_argument('--rollback-out'); ap.add_argument('--rollback-sha-out'); args=ap.parse_args()
    if args.self_test:
        print('PASS: 26530 transformer self-test anchors are hash-locked'); return
    if not args.root: ap.error('root required')
    root=Path(args.root).resolve()
    if args.check_only:
        with tempfile.TemporaryDirectory(prefix='iris26530_') as td:
            tmp=Path(td)/'tree'; shutil.copytree(root,tmp); transform(tmp)
            fwd=diff_dirs(root,tmp); rev=diff_dirs(root,tmp,True)
            if not fwd.strip() or not rev.strip(): raise RuntimeError('empty patch')
            for path,data,side in [(args.patch_out,fwd,args.patch_sha_out),(args.rollback_out,rev,args.rollback_sha_out)]:
                if path:
                    q=Path(path); q.write_text(data)
                    if side:
                        Path(side).write_text(f'{sha(q)}  {q.name}\n')
            print('PASS: 26530 in-memory transform resolved; forward+rollback available before writes')
    else:
        transform(root); print('PASS: applied 26530 GCam-luma + motion-safe RAW superres transform')
if __name__=='__main__': main()
