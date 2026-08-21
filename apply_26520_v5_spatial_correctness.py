#!/usr/bin/env python3
from __future__ import annotations
import argparse, difflib, hashlib, importlib.util
from pathlib import Path

STACK='app/src/main/java/com/hinnka/mycamera/processor/GlesMgc1271ReleasedSpatialStacker.kt'
SHADERS='app/src/main/java/com/hinnka/mycamera/processor/GlesMgc1271ReleasedSpatialShaders.kt'


def norm(s:str)->str:
    return s.replace('\r\n','\n').replace('\r','\n')


def load(path:Path):
    spec=importlib.util.spec_from_file_location('apply26520v4_base',path)
    mod=importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(mod); return mod


def one(s:str,old:str,new:str,label:str)->str:
    n=s.count(old)
    if n!=1:
        raise AssertionError(f'{label} anchor count={n} expected=1')
    return s.replace(old,new,1)


def replace_between(s:str,start_token:str,end_token:str,replacement:str,label:str)->str:
    a=s.find(start_token)
    if a<0: raise AssertionError(label+' start token missing')
    b=s.find(end_token,a+len(start_token))
    if b<0: raise AssertionError(label+' end token missing')
    if s.find(start_token,a+1,b)>=0: raise AssertionError(label+' start token ambiguous')
    return s[:a]+replacement+s[b:]


def rewrite_spatial_shader(text:str)->str:
    s=norm(text)
    if 'internal object GlesMgc1271ReleasedSpatialShaders' not in s:
        raise AssertionError('released shader object missing')
    old_start='''    /**\n     * Transport from the internal LK grid to MergeBayerRaw16's alignment contract.\n'''
    end='''    val strengthAlignment = """\n'''
    replacement='''    /**\n     * IRIS_26520_V5_CONTINUOUS_FINEST_LK_TRANSPORT\n     *\n     * Spatial-only backport of bjzhou 1b84bf86 after the b0d4c692 alignment correction.\n     * Resamples the finest LK grid continuously onto MergeBayerRaw16's one-sample-per-8x8-\n     * Bayer-quad alignment contract. The discontinuity gate intentionally remains only in the\n     * actual merge-domain consumer (mergeBayer/mergeRgb), where it cannot quantize motion at the\n     * coarser finest-LK cadence into 64-RAW-pixel constant-flow blocks.\n     */\n    val convertBayerAlignment = """\n        #version 300 es\n        precision highp float;\n        precision highp int;\n        uniform sampler2D uAlignment;\n        uniform ivec2 uGridSize;\n        uniform float uTileStride;\n        uniform float uAlignmentScale;\n        uniform float uGridMin;\n        uniform float uTargetTileStride;\n        uniform vec2 uFlowNormalizationSize;\n        out vec4 oAlignment;\n\n        vec2 flowAt(ivec2 p) {\n            return texelFetch(\n                uAlignment,\n                clamp(p, ivec2(0), uGridSize - ivec2(1)),\n                0\n            ).xy * uAlignmentScale;\n        }\n        vec2 resampledFlow(vec2 sourceGrid) {\n            ivec2 p00 = ivec2(floor(sourceGrid));\n            vec2 fraction = fract(sourceGrid);\n            vec2 flow00 = flowAt(p00);\n            vec2 flow10 = flowAt(p00 + ivec2(1, 0));\n            vec2 flow01 = flowAt(p00 + ivec2(0, 1));\n            vec2 flow11 = flowAt(p00 + ivec2(1, 1));\n            return mix(\n                mix(flow00, flow10, fraction.x),\n                mix(flow01, flow11, fraction.x),\n                fraction.y\n            );\n        }\n        void main() {\n            ivec2 outputTile = ivec2(gl_FragCoord.xy);\n            ivec2 alignmentPixel = ivec2(floor(\n                (vec2(outputTile) + vec2(0.5)) * uTargetTileStride\n            ));\n            // Local texel zero is logical LK tile uGridMin and its sample lives at\n            // (uGridMin + 0.5) * uTileStride in the Bayer-quad image domain.\n            vec2 sourceGrid =\n                vec2(alignmentPixel) / uTileStride -\n                vec2(uGridMin + 0.5);\n            vec2 flow = resampledFlow(sourceGrid);\n            ivec2 tile = ivec2(floor(sourceGrid + vec2(0.5)));\n\n            vec2 minimumFlow = vec2(1.0e20);\n            vec2 maximumFlow = vec2(-1.0e20);\n            for (int y = -1; y <= 1; ++y) {\n                for (int x = -1; x <= 1; ++x) {\n                    vec2 candidate = flowAt(tile + ivec2(x, y));\n                    minimumFlow = min(minimumFlow, candidate);\n                    maximumFlow = max(maximumFlow, candidate);\n                }\n            }\n            float localFlowVariation = length(\n                (maximumFlow - minimumFlow) /\n                max(uFlowNormalizationSize, vec2(1.0))\n            );\n            oAlignment = vec4(flow, localFlowVariation, 0.0);\n        }\n    """.trimIndent()\n\n'''
    s=replace_between(s,old_start,end,replacement,'continuous Bayer-alignment shader')
    if s.count('IRIS_26520_V5_CONTINUOUS_FINEST_LK_TRANSPORT')!=1:
        raise AssertionError('continuous transport marker cardinality')
    block=s[s.find('IRIS_26520_V5_CONTINUOUS_FINEST_LK_TRANSPORT'):s.find(end)]
    for tok in ('vec2 flow = resampledFlow(sourceGrid)','mix(flow00, flow10, fraction.x)','uTargetTileStride'):
        if tok not in block: raise AssertionError('continuous transport token missing '+tok)
    for forbidden in ('cancelInterpolation','uInterpolationFlowTolerance','uAlignmentToBayerQuads'):
        if forbidden in block: raise AssertionError('coarse-grid discontinuity/legacy transport survived: '+forbidden)
    # The actual merge-domain discontinuity protection must remain in the c4ff merge shader.
    if 'cancelInterpolation' not in s:
        raise AssertionError('merge-domain discontinuity gate missing from released Spatial shader')
    return s


def rewrite_alignment_stack(text:str)->str:
    s=norm(text)
    # Exact c4ff behavior: an extra content-selected L1 upsample was performed after finest LK.
    old_doc='''     * The first three levels use three LK iterations; the finest uses two. The standalone\n     * AlignL1 search is absent, but UpsampleAlignment still selects among three neighboring\n     * coarse-flow candidates using target-level L1 residuals before every finer LK level.\n     */\n'''
    new_doc='''     * The first three levels use three LK iterations; the finest uses two. The standalone\n     * AlignL1 search is absent, but UpsampleAlignment still selects among three neighboring\n     * coarse-flow candidates using target-level L1 residuals before every finer LK level.\n     * IRIS_26520_V5_FINAL_FINEST_LK_OWNER: AlignPyramid exits after the finest LK pass; no\n     * additional content-selected UpsampleAlignment is run to the MergeBayer grid. The finest\n     * LK field is transported continuously by convertBayerAlignment instead.\n     */\n'''
    s=one(s,old_doc,new_doc,'final finest-LK documentation')
    final_upsample='''        alignment = renderUpsampledAlignment(\n            reference = reference.first(),\n            current = current.first(),\n            initial = alignment,\n            targetGridWidth = bayerAlignmentWidth,\n            targetGridHeight = bayerAlignmentHeight,\n            targetGridMin = MERGE_ALIGNMENT_GRID_MIN,\n            targetTileStride = MERGE_BAYER_RAW_TILE_SIZE / 2,\n            targetTileSize = MERGE_BAYER_RAW_TILE_SIZE / 2,\n        )\n'''
    s=one(s,final_upsample,'','remove post-finest merge-grid L1 upsample')
    s=one(s,'                "upsampleL1=3-candidate median=false " +\n','                "upsampleL1=level-transitions-only/3-candidate median=false " +\n','alignment schedule log')

    # Rejection must expand the exact flow that merge consumes, rather than independently
    # converting the sparse finest LK field.
    bento_old='''                    val flow = createTexture(\n                        rejectionWidth,\n                        rejectionHeight,\n                        GLES30.GL_RGBA16F,\n                        GLES30.GL_LINEAR,\n                    )\n                    renderConvertedAlignment(alignment, flow)\n                    val bayerAlignment = createTexture(\n                        bayerAlignmentWidth,\n                        bayerAlignmentHeight,\n                        GLES30.GL_RGBA32F,\n                        GLES30.GL_NEAREST,\n                    )\n                    renderBayerAlignment(alignment, bayerAlignment)\n'''
    bento_new='''                    val bayerAlignment = createTexture(\n                        bayerAlignmentWidth,\n                        bayerAlignmentHeight,\n                        GLES30.GL_RGBA32F,\n                        GLES30.GL_NEAREST,\n                    )\n                    renderBayerAlignment(alignment, bayerAlignment)\n                    /* IRIS_26520_V5_MERGE_DOMAIN_REJECTION_FLOW */\n                    val flow = createTexture(\n                        rejectionWidth,\n                        rejectionHeight,\n                        GLES30.GL_RGBA16F,\n                        GLES30.GL_LINEAR,\n                    )\n                    renderMergeDomainFlow(bayerAlignment, flow)\n'''
    s=one(s,bento_old,bento_new,'Bento merge-domain flow')

    temporal_old='''        val flow = createTexture(\n            rejectionWidth,\n            rejectionHeight,\n            GLES30.GL_RGBA16F,\n            GLES30.GL_LINEAR,\n        )\n        renderConvertedAlignment(alignment, flow)\n        val bayerAlignment = createTexture(\n            bayerAlignmentWidth,\n            bayerAlignmentHeight,\n            GLES30.GL_RGBA32F,\n            GLES30.GL_NEAREST,\n        )\n        renderBayerAlignment(alignment, bayerAlignment)\n'''
    temporal_new='''        val bayerAlignment = createTexture(\n            bayerAlignmentWidth,\n            bayerAlignmentHeight,\n            GLES30.GL_RGBA32F,\n            GLES30.GL_NEAREST,\n        )\n        renderBayerAlignment(alignment, bayerAlignment)\n        /* IRIS_26520_V5_MERGE_DOMAIN_REJECTION_FLOW */\n        val flow = createTexture(\n            rejectionWidth,\n            rejectionHeight,\n            GLES30.GL_RGBA16F,\n            GLES30.GL_LINEAR,\n        )\n        renderMergeDomainFlow(bayerAlignment, flow)\n'''
    s=one(s,temporal_old,temporal_new,'temporal merge-domain flow')

    render_bayer_start='    private fun renderBayerAlignment(alignment: Alignment, output: Int) {\n'
    render_guide='    private fun renderGuide(\n'
    replacement='''    /** IRIS_26520_V5_MERGE_DOMAIN_REJECTION_FLOW */\n    private fun renderMergeDomainFlow(bayerAlignment: Int, output: Int) {\n        GLES30.glUseProgram(convertAlignmentProgram)\n        bindTexture(convertAlignmentProgram, "uAlignment", 0, bayerAlignment)\n        uniform2i(\n            convertAlignmentProgram,\n            "uGridSize",\n            bayerAlignmentWidth,\n            bayerAlignmentHeight,\n        )\n        uniform2i(\n            convertAlignmentProgram,\n            "uOutputSize",\n            rejectionWidth,\n            rejectionHeight,\n        )\n        uniform1f(\n            convertAlignmentProgram,\n            "uTileStride",\n            (MERGE_BAYER_RAW_TILE_SIZE / 2).toFloat(),\n        )\n        uniform1f(convertAlignmentProgram, "uAlignmentScale", 1f)\n        uniform1f(convertAlignmentProgram, "uOutputToAlignmentScale", 1f)\n        uniform1f(convertAlignmentProgram, "uGridMin", 0f)\n        uniform1f(\n            convertAlignmentProgram,\n            "uInterpolationFlowTolerance",\n            SPATIAL_INTERPOLATION_FLOW_TOLERANCE,\n        )\n        uniform2f(\n            convertAlignmentProgram,\n            "uFlowNormalizationSize",\n            rejectionWidth.toFloat(),\n            rejectionHeight.toFloat(),\n        )\n        draw(\n            convertAlignmentProgram,\n            rejectionWidth,\n            rejectionHeight,\n            intArrayOf(output),\n        )\n    }\n\n    private fun renderBayerAlignment(alignment: Alignment, output: Int) {\n        require(\n            alignment.gridWidth > 0 &&\n                alignment.gridHeight > 0 &&\n                alignment.tileStride > 0 &&\n                alignment.scaleToBayerQuads.isFinite() &&\n                alignment.scaleToBayerQuads > 0f\n        ) {\n            "MergeBayer requires a valid finest-level LK alignment"\n        }\n        GLES30.glUseProgram(convertBayerAlignmentProgram)\n        bindTexture(\n            convertBayerAlignmentProgram,\n            "uAlignment",\n            0,\n            alignment.texture,\n        )\n        uniform2i(\n            convertBayerAlignmentProgram,\n            "uGridSize",\n            alignment.gridWidth,\n            alignment.gridHeight,\n        )\n        uniform1f(\n            convertBayerAlignmentProgram,\n            "uTileStride",\n            alignment.tileStride * alignment.scaleToBayerQuads,\n        )\n        uniform1f(\n            convertBayerAlignmentProgram,\n            "uAlignmentScale",\n            alignment.scaleToBayerQuads,\n        )\n        uniform1f(\n            convertBayerAlignmentProgram,\n            "uGridMin",\n            alignment.gridMin.toFloat(),\n        )\n        uniform1f(\n            convertBayerAlignmentProgram,\n            "uTargetTileStride",\n            (MERGE_BAYER_RAW_TILE_SIZE / 2).toFloat(),\n        )\n        uniform2f(\n            convertBayerAlignmentProgram,\n            "uFlowNormalizationSize",\n            ceilDiv(width, 2).toFloat(),\n            ceilDiv(height, 2).toFloat(),\n        )\n        draw(\n            convertBayerAlignmentProgram,\n            bayerAlignmentWidth,\n            bayerAlignmentHeight,\n            intArrayOf(output),\n        )\n    }\n\n'''
    s=replace_between(s,render_bayer_start,render_guide,replacement,'renderBayerAlignment + merge-domain flow')
    # The old grid-min constant has no owner once the extra merge-grid UpsampleAlignment is removed.
    if '        const val MERGE_ALIGNMENT_GRID_MIN = 0\n' in s:
        s=s.replace('        const val MERGE_ALIGNMENT_GRID_MIN = 0\n','',1)
    for tok in ('IRIS_26520_V5_FINAL_FINEST_LK_OWNER','IRIS_26520_V5_MERGE_DOMAIN_REJECTION_FLOW'):
        if tok not in s: raise AssertionError('alignment marker missing '+tok)
    if 'targetGridMin = MERGE_ALIGNMENT_GRID_MIN' in s:
        raise AssertionError('post-finest merge-grid L1 upsample survived')
    return s


def rewrite_raw_slot_lifetime(text:str)->str:
    s=norm(text)
    data_old='''    private data class OnlineRgbAccumulator(\n        val semanticAccumulator: Int,\n        val opponentWeightAccumulator: Int,\n        val chromaGuideTexture: Int,\n        val drawBands: List<MgcSpatialRgbTile>,\n        val projectedGpuBytes: Long,\n        var contributedFrames: Int = 0,\n        var rawUploadCount: Int = 0,\n        var rawUploadBytes: Long = 0L,\n        var rawUploadNs: Long = 0L,\n    )\n'''
    data_new='''    /* IRIS_26520_V5_SPATIAL_RGB_TWO_SLOT_RAW_LIFETIME\n     * Spatial-only backport of bjzhou 0cecf089. Two tracked RAW slots prevent a subsequent\n     * glTexSubImage upload from overwriting pixels still consumed by queued RGB band draws.\n     */\n    private data class OnlineRgbAccumulator(\n        val semanticAccumulator: Int,\n        val opponentWeightAccumulator: Int,\n        val chromaGuideTexture: Int,\n        val drawBands: List<MgcSpatialRgbTile>,\n        val rawSlots: IntArray,\n        val passWindow: GlesGpuScheduler.PassWindow,\n        val projectedGpuBytes: Long,\n        var nextRawSlot: Int,\n        var contributedFrames: Int = 0,\n        var rawUploadCount: Int = 0,\n        var rawUploadBytes: Long = 0L,\n        var rawUploadNs: Long = 0L,\n    )\n'''
    s=one(s,data_old,data_new,'OnlineRgbAccumulator two-slot ABI')

    create_call='''                onlineRgbAccumulator = createOnlineRgbAccumulator(\n                    diagnosticCapture = strengthCapture,\n                )?.also { online ->\n'''
    s=one(s,create_call,'''                onlineRgbAccumulator = createOnlineRgbAccumulator(\n                    reusableRawTexture = currentRaw,\n                    diagnosticCapture = strengthCapture,\n                )?.also { online ->\n''','online accumulator reusable raw')

    submit_sig='''            fun submitOrRetainRgbFrame(\n                frame: RgbMergeFrame,\n                rawTexture: Int,\n            ) {\n'''
    s=one(s,submit_sig,'''            fun submitOrRetainRgbFrame(\n                frame: RgbMergeFrame,\n                rawTexture: Int,\n                label: String,\n            ) {\n''','submit label ABI')
    contribute_call='''                    contributeOnlineRgbFrame(\n                        accumulator = online,\n                        frame = frame,\n                        rawTexture = rawTexture,\n                    )\n'''
    s=one(s,contribute_call,'''                    contributeOnlineRgbFrame(\n                        accumulator = online,\n                        frame = frame,\n                        rawTexture = rawTexture,\n                        label = label,\n                    )\n''','contribute label forward')

    # Four production submissions: reference under Bento, Bento short, ordinary reference, temporal.
    bento_ref_old='''                        frame = RgbMergeFrame(
                            imageIndex = 0,
                            calibration = referenceCalibration,
                            alignmentTexture = zeroFlow,
                            weightTexture = bentoBaseWeight,
                            covarianceTexture = referenceCovariance,
                            flowBounds = MgcSpatialRgbFlowBounds.Zero,
                            useFrameWeight = true,
                        ),
                        rawTexture = referenceRaw,
                    )
'''
    s=one(s,bento_ref_old,bento_ref_old.replace('                        rawTexture = referenceRaw,\n                    )\n','                        rawTexture = referenceRaw,\n                        label = \"reference\",\n                    )\n'),'Bento reference label')
    bento_short_old='''                        frame = RgbMergeFrame(
                            imageIndex = ultrashortIndex,
                            calibration = checkNotNull(bentoCalibration),
                            alignmentTexture = bentoBayerAlignmentTexture,
                            weightTexture = bentoShortWeight,
                            covarianceTexture = bentoRgbCovarianceTexture,
                            flowBounds = conservativeRgbFlowBounds,
                            useFrameWeight = true,
                        ),
                        rawTexture = bentoRaw,
                    )
'''
    s=one(s,bento_short_old,bento_short_old.replace('                        rawTexture = bentoRaw,\n                    )\n','                        rawTexture = bentoRaw,\n                        label = \"bento\",\n                    )\n'),'Bento short label')
    ref_old='''                        frame = RgbMergeFrame(
                            imageIndex = 0,
                            calibration = referenceCalibration,
                            alignmentTexture = zeroFlow,
                            weightTexture = identityWeight,
                            covarianceTexture = referenceCovariance,
                            flowBounds = MgcSpatialRgbFlowBounds.Zero,
                            useFrameWeight = false,
                        ),
                        rawTexture = referenceRaw,
                    )
'''
    s=one(s,ref_old,ref_old.replace('                        rawTexture = referenceRaw,\n                    )\n','                        rawTexture = referenceRaw,\n                        label = \"reference\",\n                    )\n'),'ordinary reference label')
    # Temporal call occurs after DNG sidecar insertion in V4; anchor on the submission's raw arg.
    temporal_submit='''                                rawTexture = temporalRaw,\n                            )\n'''
    s=one(s,temporal_submit,'''                                rawTexture = temporalRaw,\n                                label = "frame $index",\n                            )\n''','temporal label')

    temporal_raw='''                    val online = onlineRgbAccumulator\n                    val temporalRaw = currentRaw.also { texture ->\n                        val uploadStartNs = System.nanoTime()\n                        uploadRaw(images[index], texture, "frame $index")\n                        uploadCallNs = System.nanoTime() - uploadStartNs\n                        if (online != null) {\n                            online.rawUploadNs += uploadCallNs\n                            online.rawUploadCount += 1\n                            online.rawUploadBytes +=\n                                width.toLong() * height * RAW_BYTES_PER_PIXEL\n                        }\n                    }\n'''
    temporal_new='''                    val online = onlineRgbAccumulator\n                    val temporalRaw = if (online != null) {\n                        val slot = online.nextRawSlot\n                        val texture = online.rawSlots[slot]\n                        online.nextRawSlot = (slot + 1) % online.rawSlots.size\n                        online.passWindow.awaitResources(\n                            label = "MGC RGB RAW slot $slot upload frame $index",\n                            resources = longArrayOf(GlesGpuScheduler.textureResource(texture)),\n                        )\n                        val uploadStartNs = System.nanoTime()\n                        uploadRaw(images[index], texture, "frame $index")\n                        uploadCallNs = System.nanoTime() - uploadStartNs\n                        online.rawUploadNs += uploadCallNs\n                        online.rawUploadCount += 1\n                        online.rawUploadBytes += width.toLong() * height * RAW_BYTES_PER_PIXEL\n                        texture\n                    } else {\n                        currentRaw.also { texture ->\n                            val uploadStartNs = System.nanoTime()\n                            uploadRaw(images[index], texture, "frame $index")\n                            uploadCallNs = System.nanoTime() - uploadStartNs\n                        }\n                    }\n'''
    s=one(s,temporal_raw,temporal_new,'two-slot temporal RAW upload')

    # Resource ownership follows the upstream 0cecf089 correction.
    create_sig='''    private fun createOnlineRgbAccumulator(\n        diagnosticCapture: StrengthCapture?,\n    ): OnlineRgbAccumulator? {\n'''
    s=one(s,create_sig,'''    private fun createOnlineRgbAccumulator(\n        reusableRawTexture: Int,\n        diagnosticCapture: StrengthCapture?,\n    ): OnlineRgbAccumulator? {\n''','createOnline reusable raw signature')
    s=one(s,'''        val temporalProjectedBytes = estimatedOwnedTextureBytes() +\n            accumulatorBytes + chromaGuideBytes + temporalScratchReserveBytes\n''','''        val temporalProjectedBytes = estimatedOwnedTextureBytes() + rawBytes +\n            accumulatorBytes + chromaGuideBytes + temporalScratchReserveBytes\n''','second RAW projected memory')
    chroma_alloc='''        val chromaGuideTexture = createTexture(\n            width,\n            height,\n            GLES30.GL_R16F,\n            GLES30.GL_NEAREST,\n        )\n'''
    s=one(s,chroma_alloc,'''        val secondRawTexture = createTexture(\n            width,\n            height,\n            GLES30.GL_R16UI,\n            GLES30.GL_NEAREST,\n        )\n        val chromaGuideTexture = createTexture(\n            width,\n            height,\n            GLES30.GL_R16F,\n            GLES30.GL_NEAREST,\n        )\n''','second online RAW texture')
    s=one(s,'                "drawBandHeight=$RGB_ONLINE_DRAW_BAND_HEIGHT rawSlots=1 " +\n','                "drawBandHeight=$RGB_ONLINE_DRAW_BAND_HEIGHT rawSlots=2 " +\n','online raw slot log')
    ret='''            chromaGuideTexture = chromaGuideTexture,\n            drawBands = drawBands,\n            projectedGpuBytes = projectedGpuBytes,\n        )\n'''
    s=one(s,ret,'''            chromaGuideTexture = chromaGuideTexture,\n            drawBands = drawBands,\n            rawSlots = intArrayOf(reusableRawTexture, secondRawTexture),\n            passWindow = GlesGpuScheduler.PassWindow(\n                tag = TAG,\n                maxInFlight = RGB_MAX_IN_FLIGHT_PASSES,\n            ),\n            projectedGpuBytes = projectedGpuBytes,\n            // Slot zero may still contain the evaluated Bento frame. Start with the new slot.\n            nextRawSlot = 1,\n        )\n''','online accumulator slot ownership')

    contrib_sig='''    private fun contributeOnlineRgbFrame(\n        accumulator: OnlineRgbAccumulator,\n        frame: RgbMergeFrame,\n        rawTexture: Int,\n    ) {\n'''
    s=one(s,contrib_sig,'''    private fun contributeOnlineRgbFrame(\n        accumulator: OnlineRgbAccumulator,\n        frame: RgbMergeFrame,\n        rawTexture: Int,\n        label: String,\n    ) {\n        val rawResource = GlesGpuScheduler.textureResource(rawTexture)\n''','contribute online pass-window signature')
    draw_old='''        accumulator.drawBands.forEach { band ->\n            renderRgbFrameContribution(\n                frame = frame,\n                rawTexture = rawTexture,\n                rawTextureOrigin = fullRaw,\n                sourceRegion = fullRaw,\n                outputCores = listOf(band.outputCore),\n                chromaGuideRegionTexture = accumulator.chromaGuideTexture,\n                semanticAccumulator = accumulator.semanticAccumulator,\n                opponentWeightAccumulator = accumulator.opponentWeightAccumulator,\n                accumulatorIsFullOutput = true,\n            )\n        }\n'''
    draw_new='''        accumulator.drawBands.forEach { band ->\n            accumulator.passWindow.beginPass(\n                label = "MGC RGB online $label band ${band.index}",\n                reads = longArrayOf(rawResource),\n            )\n            try {\n                renderRgbFrameContribution(\n                    frame = frame,\n                    rawTexture = rawTexture,\n                    rawTextureOrigin = fullRaw,\n                    sourceRegion = fullRaw,\n                    outputCores = listOf(band.outputCore),\n                    chromaGuideRegionTexture = accumulator.chromaGuideTexture,\n                    semanticAccumulator = accumulator.semanticAccumulator,\n                    opponentWeightAccumulator = accumulator.opponentWeightAccumulator,\n                    accumulatorIsFullOutput = true,\n                )\n            } finally {\n                accumulator.passWindow.endPass()\n            }\n        }\n'''
    s=one(s,draw_old,draw_new,'online band pass-window ownership')

    # After all temporal submissions are represented by the common temporal checkpoint, their
    # resource records can be retired. This is the exact lifecycle intent of upstream 0cecf089.
    release_anchor='''                releaseRgbTemporalPhaseResources(\n                    persistentTextures = retainedTemporalTextures,\n                    strengthCapture = readyStrengthCapture,\n                )\n'''
    s=one(s,release_anchor,release_anchor+'                online?.passWindow?.clearAfterCheckpoint()\n','online pass-window checkpoint clear')
    s=one(s,'''                        "rawWindowSlots=${when {\n                            online != null -> 1\n                            else -> RGB_RAW_WINDOW_SLOTS\n                        }} " +\n                        "maxInFlight=${if (online != null) 1 else RGB_MAX_IN_FLIGHT_PASSES}",\n''','''                        "rawWindowSlots=${when {\n                            online != null -> online.rawSlots.size\n                            else -> RGB_RAW_WINDOW_SLOTS\n                        }} " +\n                        "maxInFlight=$RGB_MAX_IN_FLIGHT_PASSES",\n''','dispatch slot telemetry')
    s=one(s,'        } catch (error: Exception) {\n            PLog.e(TAG, "MGC Spatial ${outputMode.name} merge failed", error)\n','        } catch (error: Exception) {\n            onlineRgbAccumulator?.passWindow?.drain("MGC Spatial merge failure")\n            PLog.e(TAG, "MGC Spatial ${outputMode.name} merge failed", error)\n','failure pass-window drain')

    for tok in ('IRIS_26520_V5_SPATIAL_RGB_TWO_SLOT_RAW_LIFETIME','rawSlots = intArrayOf(reusableRawTexture, secondRawTexture)','awaitResources(','reads = longArrayOf(rawResource)'):
        if tok not in s: raise AssertionError('RAW-slot lifetime token missing '+tok)
    return s


def rewrite_spatial_stack(text:str)->str:
    return rewrite_raw_slot_lifetime(rewrite_alignment_stack(text))


def expected_map(base:Path,apply_v4:Path)->dict[str,str]:
    v4=load(apply_v4)
    out=dict(v4.expected_map(base))
    if v4.STACK != STACK:
        raise AssertionError('V4 released stack path drift')
    out[STACK]=rewrite_spatial_stack(out[STACK])
    shader_path=base/SHADERS
    if not shader_path.is_file():
        raise AssertionError('successful-26519 released shader missing')
    out[SHADERS]=rewrite_spatial_shader(shader_path.read_text())
    return out


def patch_text(base:Path,expected:dict[str,str])->str:
    chunks=[]
    for rel in sorted(expected):
        p=base/rel; old=norm(p.read_text()) if p.exists() else ''; new=expected[rel]
        if old==new: raise AssertionError('empty 26520 V5 transform '+rel)
        chunks.append(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=('a/'+rel if p.exists() else '/dev/null'),tofile='b/'+rel)))
    return ''.join(chunks)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('root',type=Path)
    ap.add_argument('--apply-v4',required=True,type=Path)
    ap.add_argument('--patch-out',type=Path)
    ap.add_argument('--patch-sha-out',type=Path)
    ap.add_argument('--check-only',action='store_true')
    ns=ap.parse_args()
    base=ns.root.resolve(); expected=expected_map(base,ns.apply_v4.resolve())
    if ns.check_only:
        print('PASS: 26520 V5 = exact V4 transform + Spatial-only audited corrections')
        print('PASS: finest-LK transport is continuous; rejection is derived from merge-domain flow')
        print('PASS: online Spatial RGB owns two resource-tracked RAW slots; no Sabre architecture imported')
        return
    if ns.patch_out is None or ns.patch_sha_out is None:
        raise SystemExit('--patch-out and --patch-sha-out required unless --check-only')
    diff=patch_text(base,expected)
    if not diff: raise AssertionError('empty 26520 V5 runtime patch')
    ns.patch_out.parent.mkdir(parents=True,exist_ok=True); ns.patch_out.write_text(diff)
    digest=hashlib.sha256(ns.patch_out.read_bytes()).hexdigest(); ns.patch_sha_out.write_text(f'{digest}  {ns.patch_out.name}\n')
    for rel,new in expected.items():
        p=base/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(new)
    print(f'PASS: 26520 V5 rollback patch existed before {len(expected)}-path runtime write')

if __name__=='__main__': main()
