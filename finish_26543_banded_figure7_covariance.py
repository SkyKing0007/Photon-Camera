from pathlib import Path
import argparse

def transform(root: Path):
    stack=root/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt'
    shader=root/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt'

    def once(s,old,new,label):
        n=s.count(old)
        if n!=1: raise SystemExit(f'{label}: expected 1 got {n}')
        return s.replace(old,new,1)

    s=stack.read_text()
    s=once(s,
    '''    private data class RgbTileFrameRegion(\n        val frame: RgbMergeFrame,\n        val sourceRegion: MgcSpatialRgbRect,\n        val uploadRegion: MgcSpatialRgbRect,\n    )\n''',
    '''    private data class RgbTileFrameRegion(\n        val frame: RgbMergeFrame,\n        val sourceRegion: MgcSpatialRgbRect,\n        val uploadRegion: MgcSpatialRgbRect,\n        val covarianceRegion: MgcSpatialRgbRect,\n    )\n''','RgbTileFrameRegion covariance')
    s=once(s,
    '''        val maximumUploadWidth: Int,\n        val maximumUploadHeight: Int,\n        val projectedGpuBytes: Long,\n''',
    '''        val maximumUploadWidth: Int,\n        val maximumUploadHeight: Int,\n        val maximumCovarianceWidth: Int,\n        val maximumCovarianceHeight: Int,\n        val projectedGpuBytes: Long,\n''','RgbBandPlan cov dims')
    # temporal fallback: do not retain a full covariance per frame
    old='''                            val retainedCovariance = copyPersistentTexture(\n                                source = currentCovariance,\n                                textureWidth = covarianceWidth,\n                                textureHeight = covarianceHeight,\n                                internalFormat = GLES30.GL_RGBA16F,\n                                filter = GLES30.GL_LINEAR,\n                                label = "MGC RGB covariance frame $index",\n                            )\n                            rgbMergeFrames += RgbMergeFrame(\n                                imageIndex = index,\n                                calibration = prepared.calibration,\n                                alignmentTexture = retainedAlignment,\n                                weightTexture = retainedWeight,\n                                covarianceTexture = retainedCovariance,\n                                flowBounds = conservativeRgbFlowBounds,\n                                useFrameWeight = true,\n                            )\n'''
    new='''                            /* IRIS_26543_BANDED_FIGURE7_BOUNDED_COVARIANCE\n                             * The low-memory/banded path must not retain one RAW/2 RGBA16F\n                             * covariance (~24 MiB at 4096x3072) per temporal frame. Alignment and\n                             * rejection remain compact persistent evidence; Figure-7 covariance is\n                             * reconstructed from the current streamed RAW band immediately before\n                             * that frame contributes, using one reusable scratch texture.\n                             */\n                            rgbMergeFrames += RgbMergeFrame(\n                                imageIndex = index,\n                                calibration = prepared.calibration,\n                                alignmentTexture = retainedAlignment,\n                                weightTexture = retainedWeight,\n                                covarianceTexture = 0,\n                                flowBounds = conservativeRgbFlowBounds,\n                                useFrameWeight = true,\n                            )\n                            PLog.d(\n                                TAG,\n                                "IRIS_26543_BANDED_COVARIANCE_FRAME frame=$index " +\n                                    "retainedFullCovariance=false",\n                            )\n'''
    s=once(s,old,new,'remove temporal covariance retention')
    # persistent texture list skip zero cov
    old='''                    rgbMergeFrames.flatMap { frame ->\n                        listOf(\n                            frame.alignmentTexture,\n                            frame.weightTexture,\n                            frame.covarianceTexture,\n                        )\n                    }.toIntArray()\n'''
    new='''                    rgbMergeFrames.flatMap { frame ->\n                        buildList {\n                            add(frame.alignmentTexture)\n                            add(frame.weightTexture)\n                            if (frame.covarianceTexture != 0) add(frame.covarianceTexture)\n                        }\n                    }.toIntArray()\n'''
    s=once(s,old,new,'skip zero retained covariance')
    # insert helper before createRgbBandPlan signature
    anchor='''    private fun createRgbBandPlan(\n        frames: List<RgbMergeFrame>,\n'''
    helper='''    /* IRIS_26543_BANDED_FIGURE7_REGION_OWNER\n     * For streamed reconstruction, compute only the RAW/2 covariance cells touched by this\n     * source band. Figure-7 cell q needs RAW support [2q-2, 2q+3], so the upload rectangle is\n     * expanded from the covariance cell rectangle rather than assuming the 3x3 merge halo is\n     * sufficient. This keeps covariance residency bounded independently of frame count.\n     */\n    private fun figure7CovarianceRegion(source: MgcSpatialRgbRect): MgcSpatialRgbRect {\n        val expandedLeft = max(0, source.left - FIGURE7_BANDED_COV_RAW_MARGIN)\n        val expandedTop = max(0, source.top - FIGURE7_BANDED_COV_RAW_MARGIN)\n        val expandedRight = minOf(width, source.right + FIGURE7_BANDED_COV_RAW_MARGIN)\n        val expandedBottom = minOf(height, source.bottom + FIGURE7_BANDED_COV_RAW_MARGIN)\n        val left = (expandedLeft / 2).coerceIn(0, covarianceWidth - 1)\n        val top = (expandedTop / 2).coerceIn(0, covarianceHeight - 1)\n        val right = ceilDiv(expandedRight, 2).coerceIn(left + 1, covarianceWidth)\n        val bottom = ceilDiv(expandedBottom, 2).coerceIn(top + 1, covarianceHeight)\n        return MgcSpatialRgbRect(left, top, right, bottom)\n    }\n\n    private fun figure7RawSupportRegion(covariance: MgcSpatialRgbRect): MgcSpatialRgbRect {\n        val left = max(0, covariance.left * 2 - FIGURE7_COV_RAW_NEGATIVE_SUPPORT)\n        val top = max(0, covariance.top * 2 - FIGURE7_COV_RAW_NEGATIVE_SUPPORT)\n        val right = minOf(width, covariance.right * 2 + FIGURE7_COV_RAW_POSITIVE_SUPPORT)\n        val bottom = minOf(height, covariance.bottom * 2 + FIGURE7_COV_RAW_POSITIVE_SUPPORT)\n        return MgcSpatialRgbRect(left, top, right, bottom)\n    }\n\n    private fun unionRawRegions(a: MgcSpatialRgbRect, b: MgcSpatialRgbRect): MgcSpatialRgbRect =\n        MgcSpatialRgbRect(\n            left = minOf(a.left, b.left),\n            top = minOf(a.top, b.top),\n            right = maxOf(a.right, b.right),\n            bottom = maxOf(a.bottom, b.bottom),\n        )\n\n'''
    if s.count(anchor)!=1: raise SystemExit('createRgbBandPlan anchor')
    s=s.replace(anchor,helper+anchor,1)
    # work construction include cov region and upload union
    old='''                RgbTileFrameRegion(\n                    frame = frame,\n                    sourceRegion = sourceRegion,\n                    uploadRegion = expandRgbRawRegion(\n                        sourceRegion,\n                        RGB_CHROMA_GUIDE_RAW_RADIUS,\n                    ),\n                )\n'''
    new='''                val covarianceRegion = figure7CovarianceRegion(sourceRegion)\n                val chromaUploadRegion = expandRgbRawRegion(\n                    sourceRegion,\n                    RGB_CHROMA_GUIDE_RAW_RADIUS,\n                )\n                val covarianceRawSupport = figure7RawSupportRegion(covarianceRegion)\n                RgbTileFrameRegion(\n                    frame = frame,\n                    sourceRegion = sourceRegion,\n                    uploadRegion = unionRawRegions(chromaUploadRegion, covarianceRawSupport),\n                    covarianceRegion = covarianceRegion,\n                )\n'''
    s=once(s,old,new,'band region construction')
    # max covariance dims and bytes
    old='''        val maximumUploadHeight = work.maxOf { (_, regions) ->\n            regions.maxOf { it.uploadRegion.height }\n        }\n        val rawWindowBytes = maximumUploadWidth.toLong() * maximumUploadHeight *\n            RAW_BYTES_PER_PIXEL * RGB_RAW_WINDOW_SLOTS\n'''
    new='''        val maximumUploadHeight = work.maxOf { (_, regions) ->\n            regions.maxOf { it.uploadRegion.height }\n        }\n        val maximumCovarianceWidth = work.maxOf { (_, regions) ->\n            regions.maxOf { it.covarianceRegion.width }\n        }\n        val maximumCovarianceHeight = work.maxOf { (_, regions) ->\n            regions.maxOf { it.covarianceRegion.height }\n        }\n        val rawWindowBytes = maximumUploadWidth.toLong() * maximumUploadHeight *\n            RAW_BYTES_PER_PIXEL * RGB_RAW_WINDOW_SLOTS\n        val covarianceScratchBytes = maximumCovarianceWidth.toLong() * maximumCovarianceHeight * 8L\n'''
    s=once(s,old,new,'band max cov dims')
    old='''        val projectedGpuBytes = estimatedOwnedTextureBytes() + rawWindowBytes +\n            chromaGuideBytes + accumulatorBytes + outputStorageBytes +\n            diagnosticTextureBytes + diagnosticPboBytes + RGB_TEXTURE_BUDGET_RESERVE_BYTES\n'''
    new='''        val projectedGpuBytes = estimatedOwnedTextureBytes() + rawWindowBytes +\n            covarianceScratchBytes + chromaGuideBytes + accumulatorBytes + outputStorageBytes +\n            diagnosticTextureBytes + diagnosticPboBytes + RGB_TEXTURE_BUDGET_RESERVE_BYTES\n'''
    s=once(s,old,new,'band budget cov scratch')
    old='''            maximumUploadWidth = maximumUploadWidth,\n            maximumUploadHeight = maximumUploadHeight,\n            projectedGpuBytes = projectedGpuBytes,\n'''
    new='''            maximumUploadWidth = maximumUploadWidth,\n            maximumUploadHeight = maximumUploadHeight,\n            maximumCovarianceWidth = maximumCovarianceWidth,\n            maximumCovarianceHeight = maximumCovarianceHeight,\n            projectedGpuBytes = projectedGpuBytes,\n'''
    s=once(s,old,new,'band plan return cov dims')
    # use plan dims and allocate scratch
    old='''        val maximumUploadWidth = bandPlan.maximumUploadWidth\n        val maximumUploadHeight = bandPlan.maximumUploadHeight\n        val rawBandTextures = List(RGB_RAW_WINDOW_SLOTS) {\n'''
    new='''        val maximumUploadWidth = bandPlan.maximumUploadWidth\n        val maximumUploadHeight = bandPlan.maximumUploadHeight\n        val maximumCovarianceWidth = bandPlan.maximumCovarianceWidth\n        val maximumCovarianceHeight = bandPlan.maximumCovarianceHeight\n        val rawBandTextures = List(RGB_RAW_WINDOW_SLOTS) {\n'''
    s=once(s,old,new,'band unpack cov dims')
    old='''        val chromaGuideRegionTexture = createTexture(\n            maximumSourceWidth,\n            maximumSourceHeight,\n            GLES30.GL_R16F,\n            GLES30.GL_NEAREST,\n        )\n'''
    new='''        val covarianceBandTexture = createTexture(\n            maximumCovarianceWidth,\n            maximumCovarianceHeight,\n            GLES30.GL_RGBA16F,\n            GLES30.GL_LINEAR,\n        )\n        val chromaGuideRegionTexture = createTexture(\n            maximumSourceWidth,\n            maximumSourceHeight,\n            GLES30.GL_R16F,\n            GLES30.GL_NEAREST,\n        )\n'''
    s=once(s,old,new,'allocate covariance band scratch')
    # log scratch
    old='''                "rawWindow=${maximumUploadWidth}x$maximumUploadHeight " +\n                "rawWindowBytes=" +\n                "${maximumUploadWidth.toLong() * maximumUploadHeight * RAW_BYTES_PER_PIXEL * rawBandTextures.size} " +\n                "maxOutput=${maximumOutputWidth}x$maximumOutputHeight " +\n'''
    new='''                "rawWindow=${maximumUploadWidth}x$maximumUploadHeight " +\n                "rawWindowBytes=" +\n                "${maximumUploadWidth.toLong() * maximumUploadHeight * RAW_BYTES_PER_PIXEL * rawBandTextures.size} " +\n                "covarianceScratch=${maximumCovarianceWidth}x$maximumCovarianceHeight " +\n                "covarianceScratchBytes=${maximumCovarianceWidth.toLong() * maximumCovarianceHeight * 8L} " +\n                "maxOutput=${maximumOutputWidth}x$maximumOutputHeight " +\n'''
    s=once(s,old,new,'band log cov scratch')
    # pass frame loop: resource and render scratch + pass merge params
    old='''                    val rawBandTexture = rawBandTextures[framePosition % rawBandTextures.size]\n                    val rawResource = GlesGpuScheduler.textureResource(rawBandTexture)\n                    passWindow.beginPass(\n                        label = "MGC RGB band ${band.index} frame $framePosition",\n                        reads = longArrayOf(rawResource),\n                        writes = longArrayOf(rawResource),\n                    )\n'''
    new='''                    val rawBandTexture = rawBandTextures[framePosition % rawBandTextures.size]\n                    val rawResource = GlesGpuScheduler.textureResource(rawBandTexture)\n                    val reconstructCovariance = frameRegion.frame.covarianceTexture == 0\n                    val covarianceScratchResource =\n                        GlesGpuScheduler.textureResource(covarianceBandTexture)\n                    passWindow.beginPass(\n                        label = "MGC RGB band ${band.index} frame $framePosition",\n                        reads = if (reconstructCovariance) {\n                            longArrayOf(rawResource, covarianceScratchResource)\n                        } else {\n                            longArrayOf(rawResource)\n                        },\n                        writes = if (reconstructCovariance) {\n                            longArrayOf(rawResource, covarianceScratchResource)\n                        } else {\n                            longArrayOf(rawResource)\n                        },\n                    )\n'''
    s=once(s,old,new,'band pass covariance resource')
    old='''                        rawBandUploadCount += 1\n                        renderRgbChromaGuide(\n                            frame = frameRegion.frame,\n                            rawTexture = rawBandTexture,\n                            rawTextureOrigin = frameRegion.uploadRegion,\n                            sourceRegion = frameRegion.sourceRegion,\n                            outputTexture = chromaGuideRegionTexture,\n                        )\n                        renderRgbFrameContribution(\n                            frame = frameRegion.frame,\n                            rawTexture = rawBandTexture,\n                            rawTextureOrigin = frameRegion.uploadRegion,\n                            sourceRegion = frameRegion.sourceRegion,\n                            outputCores = listOf(band.outputCore),\n                            chromaGuideRegionTexture = chromaGuideRegionTexture,\n                            semanticAccumulator = semanticAccumulator,\n                            opponentWeightAccumulator = opponentWeightAccumulator,\n                        )\n'''
    new='''                        rawBandUploadCount += 1\n                        val activeCovarianceTexture: Int\n                        val activeCovarianceOrigin: MgcSpatialRgbRect\n                        if (reconstructCovariance) {\n                            renderCovarianceRegion(\n                                rawTexture = rawBandTexture,\n                                rawTextureOrigin = frameRegion.uploadRegion,\n                                calibration = frameRegion.frame.calibration,\n                                kernelTuning = bayerKernelTuning,\n                                covarianceRegion = frameRegion.covarianceRegion,\n                                outputTexture = covarianceBandTexture,\n                            )\n                            activeCovarianceTexture = covarianceBandTexture\n                            activeCovarianceOrigin = frameRegion.covarianceRegion\n                        } else {\n                            activeCovarianceTexture = frameRegion.frame.covarianceTexture\n                            activeCovarianceOrigin = MgcSpatialRgbRect(\n                                0, 0, covarianceWidth, covarianceHeight,\n                            )\n                        }\n                        renderRgbChromaGuide(\n                            frame = frameRegion.frame,\n                            rawTexture = rawBandTexture,\n                            rawTextureOrigin = frameRegion.uploadRegion,\n                            sourceRegion = frameRegion.sourceRegion,\n                            outputTexture = chromaGuideRegionTexture,\n                        )\n                        renderRgbFrameContribution(\n                            frame = frameRegion.frame,\n                            rawTexture = rawBandTexture,\n                            rawTextureOrigin = frameRegion.uploadRegion,\n                            sourceRegion = frameRegion.sourceRegion,\n                            outputCores = listOf(band.outputCore),\n                            chromaGuideRegionTexture = chromaGuideRegionTexture,\n                            semanticAccumulator = semanticAccumulator,\n                            opponentWeightAccumulator = opponentWeightAccumulator,\n                            covarianceTexture = activeCovarianceTexture,\n                            covarianceRegion = activeCovarianceOrigin,\n                        )\n'''
    s=once(s,old,new,'band render covariance scratch')
    # renderCovariance generalize
    old='''    private fun renderCovariance(\n        rawTexture: Int,\n        calibration: FrameCalibration,\n        kernelTuning: BayerKernelTuning,\n        outputTexture: Int,\n    ) {\n        check(outputMode == MgcSpatialOutputMode.RGB && covarianceProgram != 0)\n        GLES30.glUseProgram(covarianceProgram)\n        bindTexture(covarianceProgram, "uRaw", 0, rawTexture)\n        uniform2i(covarianceProgram, "uRawSize", width, height)\n        uniform2i(covarianceProgram, "uCovarianceSize", covarianceWidth, covarianceHeight)\n        uniform4fv(covarianceProgram, "uBayerPhaseGains", calibration.bayerPhaseGains)\n'''
    new='''    private fun renderCovariance(\n        rawTexture: Int,\n        calibration: FrameCalibration,\n        kernelTuning: BayerKernelTuning,\n        outputTexture: Int,\n    ) {\n        renderCovarianceRegion(\n            rawTexture = rawTexture,\n            rawTextureOrigin = MgcSpatialRgbRect(0, 0, width, height),\n            calibration = calibration,\n            kernelTuning = kernelTuning,\n            covarianceRegion = MgcSpatialRgbRect(0, 0, covarianceWidth, covarianceHeight),\n            outputTexture = outputTexture,\n        )\n    }\n\n    private fun renderCovarianceRegion(\n        rawTexture: Int,\n        rawTextureOrigin: MgcSpatialRgbRect,\n        calibration: FrameCalibration,\n        kernelTuning: BayerKernelTuning,\n        covarianceRegion: MgcSpatialRgbRect,\n        outputTexture: Int,\n    ) {\n        check(outputMode == MgcSpatialOutputMode.RGB && covarianceProgram != 0)\n        GLES30.glUseProgram(covarianceProgram)\n        bindTexture(covarianceProgram, "uRaw", 0, rawTexture)\n        uniform2i(covarianceProgram, "uRawSize", width, height)\n        uniform2i(\n            covarianceProgram, "uRawTextureOrigin",\n            rawTextureOrigin.left, rawTextureOrigin.top,\n        )\n        uniform2i(\n            covarianceProgram, "uRawTextureSize",\n            rawTextureOrigin.width, rawTextureOrigin.height,\n        )\n        uniform2i(covarianceProgram, "uCovarianceSize", covarianceWidth, covarianceHeight)\n        uniform2i(\n            covarianceProgram, "uCovarianceOrigin",\n            covarianceRegion.left, covarianceRegion.top,\n        )\n        uniform2i(\n            covarianceProgram, "uCovarianceTextureSize",\n            covarianceRegion.width, covarianceRegion.height,\n        )\n        uniform4fv(covarianceProgram, "uBayerPhaseGains", calibration.bayerPhaseGains)\n'''
    s=once(s,old,new,'generalize renderCovariance')
    old='''        draw(\n            covarianceProgram,\n            covarianceWidth,\n            covarianceHeight,\n            intArrayOf(outputTexture),\n        )\n'''
    new='''        draw(\n            covarianceProgram,\n            covarianceRegion.width,\n            covarianceRegion.height,\n            intArrayOf(outputTexture),\n        )\n'''
    # This exact draw should occur only in renderCovariance region in current candidate
    if s.count(old)!=1: raise SystemExit(f'cov draw expected1 got{s.count(old)}')
    s=s.replace(old,new,1)
    # renderRgbFrameContribution signature and binding/uniforms
    old='''        semanticAccumulator: Int,\n        opponentWeightAccumulator: Int,\n        accumulatorIsFullOutput: Boolean = false,\n    ) {\n'''
    new='''        semanticAccumulator: Int,\n        opponentWeightAccumulator: Int,\n        accumulatorIsFullOutput: Boolean = false,\n        covarianceTexture: Int = frame.covarianceTexture,\n        covarianceRegion: MgcSpatialRgbRect = MgcSpatialRgbRect(\n            0, 0, covarianceWidth, covarianceHeight,\n        ),\n    ) {\n'''
    # Must apply to renderRgbFrameContribution only; but maybe other signature same. Count exact.
    if s.count(old)!=1: raise SystemExit(f'rgb contribution signature anchor {s.count(old)}')
    s=s.replace(old,new,1)
    s=once(s,
    '''        bindTexture(activeMergeProgram, "uCovariance", 4, frame.covarianceTexture)\n        uniform2i(activeMergeProgram, "uRawSize", width, height)\n''',
    '''        check(covarianceTexture != 0) { "RGB contribution has no active Figure-7 covariance" }\n        bindTexture(activeMergeProgram, "uCovariance", 4, covarianceTexture)\n        uniform2i(activeMergeProgram, "uRawSize", width, height)\n        uniform2i(\n            activeMergeProgram, "uCovarianceOrigin",\n            covarianceRegion.left, covarianceRegion.top,\n        )\n        uniform2i(\n            activeMergeProgram, "uCovarianceTextureSize",\n            covarianceRegion.width, covarianceRegion.height,\n        )\n''','merge covariance region uniforms')
    # constants
    old='''        const val RGB_CHROMA_GUIDE_RAW_RADIUS = 2\n'''
    new='''        const val RGB_CHROMA_GUIDE_RAW_RADIUS = 2\n        const val FIGURE7_BANDED_COV_RAW_MARGIN = 4\n        const val FIGURE7_COV_RAW_NEGATIVE_SUPPORT = 2\n        const val FIGURE7_COV_RAW_POSITIVE_SUPPORT = 2\n'''
    s=once(s,old,new,'Figure7 support constants')
    stack.write_text(s)

    # shader changes for region-aware covariance + merge sampling
    q=shader.read_text()
    q=once(q,
    '''        uniform ivec2 uRawSize;\n        uniform ivec2 uCovarianceSize;\n''',
    '''        uniform ivec2 uRawSize;\n        uniform ivec2 uRawTextureOrigin;\n        uniform ivec2 uRawTextureSize;\n        uniform ivec2 uCovarianceSize;\n        uniform ivec2 uCovarianceOrigin;\n        uniform ivec2 uCovarianceTextureSize;\n''','covariance region uniforms')
    q=once(q,
    '''        float sensorSample(ivec2 p) {\n            p = clamp(p, ivec2(0), uRawSize - ivec2(1));\n            int phase = phaseIndex(p);\n            return max(\n                float(texelFetch(uRaw, p, 0).r) * uBayerPhaseGains[phase] +\n                    uBayerPhaseBlackTerms[phase],\n                0.0\n            );\n        }\n''',
    '''        float sensorSample(ivec2 p) {\n            p = clamp(p, ivec2(0), uRawSize - ivec2(1));\n            int phase = phaseIndex(p);\n            ivec2 local = p - uRawTextureOrigin;\n            local = clamp(local, ivec2(0), uRawTextureSize - ivec2(1));\n            return max(\n                float(texelFetch(uRaw, local, 0).r) * uBayerPhaseGains[phase] +\n                    uBayerPhaseBlackTerms[phase],\n                0.0\n            );\n        }\n''','covariance local raw sampling')
    q=once(q,
    '''        void main() {\n            ivec2 p = ivec2(gl_FragCoord.xy);\n            if (any(greaterThanEqual(p, uCovarianceSize))) {\n                oCovariance = vec4(1.0, 1.0, 0.0, 1.0);\n                return;\n            }\n            float jxx = 0.0, jxy = 0.0, jyy = 0.0;\n''',
    '''        void main() {\n            ivec2 localP = ivec2(gl_FragCoord.xy);\n            if (any(greaterThanEqual(localP, uCovarianceTextureSize))) {\n                oCovariance = vec4(1.0, 1.0, 0.0, 1.0);\n                return;\n            }\n            ivec2 p = localP + uCovarianceOrigin;\n            if (any(greaterThanEqual(p, uCovarianceSize))) {\n                oCovariance = vec4(1.0, 1.0, 0.0, 1.0);\n                return;\n            }\n            float jxx = 0.0, jxy = 0.0, jyy = 0.0;\n''','covariance global origin')
    # merge uniforms: occurrence separate later
    q=once(q,
    '''        uniform sampler2D uCovariance;\n        uniform ivec2 uRawSize;\n        uniform ivec2 uRawTextureOrigin;\n''',
    '''        uniform sampler2D uCovariance;\n        uniform ivec2 uRawSize;\n        uniform ivec2 uCovarianceOrigin;\n        uniform ivec2 uCovarianceTextureSize;\n        uniform ivec2 uRawTextureOrigin;\n''','merge cov region uniforms')
    old='''            /* Covariance texel i represents Bayer-quad center raw=2*i+0.5 in this shader's\n             * integer-pixel-center coordinate system. GL linear sampling therefore uses\n             * u=(sourceRaw+0.5)/rawSize, equivalent to the IPOL RAW/2 covariance grid. */\n            vec2 covarianceUv = (sourceRaw + vec2(0.5)) / vec2(uRawSize);\n            vec3 covariance = texture(\n                uCovariance,\n                clamp(covarianceUv, vec2(0.0), vec2(1.0))\n            ).xyz;\n'''
    new='''            /* IPOL Bayer covariance coordinate is (sourceCenter/2 - 0.5). Our sourceRaw is\n             * integer-pixel-center coordinates, so sourceCenter=sourceRaw+0.5. Converting that\n             * texel-index coordinate to GL normalized coordinates for a possibly band-local\n             * covariance texture gives ((sourceRaw+0.5)/2-origin)/localSize. Full-frame origin=0\n             * reduces exactly to the previously audited (sourceRaw+0.5)/rawSize mapping. */\n            vec2 covarianceUv = (\n                (sourceRaw + vec2(0.5)) * 0.5 - vec2(uCovarianceOrigin)\n            ) / vec2(uCovarianceTextureSize);\n            vec3 covariance = texture(\n                uCovariance,\n                clamp(covarianceUv, vec2(0.0), vec2(1.0))\n            ).xyz;\n'''
    q=once(q,old,new,'merge local covariance uv')
    shader.write_text(q)

    capture=root/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java'
    c=capture.read_text()
    c=once(c,
        "    private volatile boolean mIrisNight26543SpoolCapacityChecked = false;\n",
        "    private volatile boolean mIrisNight26543SpoolCapacityChecked = false;\n"
        "    private volatile String mIrisNight26543SpoolFailure = null;\n",
        'Night spool failure field')
    c=once(c,
        "        mIrisNight26543SpoolCapacityChecked = false;\n"
        "        synchronized (mIrisNight26540Lock) {\n",
        "        mIrisNight26543SpoolCapacityChecked = false;\n"
        "        mIrisNight26543SpoolFailure = null;\n"
        "        synchronized (mIrisNight26540Lock) {\n",
        'Night spool failure reset')
    c=once(c,
        "                    final long generation = mIrisNight26543CaptureGeneration;\n"
        "                    mIrisNight26543PendingSpools.incrementAndGet();\n"
        "                    IRIS_NIGHT_26543_SPOOL_EXECUTOR.execute(() ->\n"
        "                            spoolIrisNight26543Raw(ownedImage, generation));\n",
        "                    final long generation = mIrisNight26543CaptureGeneration;\n"
        "                    mIrisNight26543PendingSpools.incrementAndGet();\n"
        "                    try {\n"
        "                        IRIS_NIGHT_26543_SPOOL_EXECUTOR.execute(() ->\n"
        "                                spoolIrisNight26543Raw(ownedImage, generation));\n"
        "                    } catch (Throwable submitFailure) {\n"
        "                        mIrisNight26543PendingSpools.decrementAndGet();\n"
        "                        mIrisNight26543SpoolFailure = \"submit:\"\n"
        "                                + submitFailure.getClass().getSimpleName();\n"
        "                        try { ownedImage.close(); } catch (Throwable ignored) {}\n"
        "                        throw submitFailure;\n"
        "                    }\n",
        'Night spool submit ownership')
    c=once(c,
        "            Log.e(TAG, \"IRIS_26543_NIGHT_RAW_SPOOL_FAILED bytes=\" + bytes, spoolFailure);\n",
        "            mIrisNight26543SpoolFailure = \"write:\" + spoolFailure.getClass().getSimpleName()\n"
        "                    + \":\" + String.valueOf(spoolFailure.getMessage());\n"
        "            Log.e(TAG, \"IRIS_26543_NIGHT_RAW_SPOOL_FAILED bytes=\" + bytes, spoolFailure);\n",
        'Night spool write failure ownership')
    c=once(c,
        "        try {\n"
        "            if (mIrisNight26543PendingSpools.get() != 0) return;\n"
        "            synchronized (mIrisNight26540Lock) {\n",
        "        try {\n"
        "            if (mIrisNight26543PendingSpools.get() != 0) return;\n"
        "            if (mIrisNight26543SpoolFailure != null) {\n"
        "                throw new IllegalStateException(\"26543 Night RAW spool failure: \"\n"
        "                        + mIrisNight26543SpoolFailure);\n"
        "            }\n"
        "            synchronized (mIrisNight26540Lock) {\n",
        'Night spool failure dispatch')
    old='''                for (ImageFrame frame : matched) {\n                    TotalCaptureResult exact = mIrisNight26540Results.get(frame.timestamp);\n                    CaptureRequest exactRequest = mIrisNight26540Requests.get(frame.timestamp);\n                    populateIrisNight26540FrameMetadata(frame, exact, exactRequest,\n                            mIrisNight26540Characteristics);\n                    frame.irisNightExactCaptureResult = exact;\n                    frame.irisNightExactCaptureRequest = exactRequest;\n                }\n                ArrayList<ImageFrame> unmatched = new ArrayList<>(mIrisNight26540Frames);\n'''
    new='''                for (ImageFrame frame : matched) {\n                    TotalCaptureResult exact = mIrisNight26540Results.get(frame.timestamp);\n                    CaptureRequest exactRequest = mIrisNight26540Requests.get(frame.timestamp);\n                    populateIrisNight26540FrameMetadata(frame, exact, exactRequest,\n                            mIrisNight26540Characteristics);\n                    frame.irisNightExactCaptureResult = exact;\n                    frame.irisNightExactCaptureRequest = exactRequest;\n                }\n                ImageFrame sortedReference = matched.get(0);\n                if (sortedReference.buffer == null\n                        || sortedReference.motionV2FrameRole != ImageFrame.MotionV2FrameRole.NORMAL) {\n                    throw new IllegalStateException(\n                            "26543 Night sorted first SHORT/reference is not the sole in-memory RAW");\n                }\n                Log.i(TAG, "IRIS_26543_NIGHT_REFERENCE_ORDER_PROOF timestamp="\n                        + sortedReference.timestamp + " role=SHORT inMemory=true sortedBySensorTimestamp=true");\n                ArrayList<ImageFrame> unmatched = new ArrayList<>(mIrisNight26540Frames);\n'''
    c=once(c,old,new,'Night sorted reference ownership proof')
    capture.write_text(c)
    print('PASS: 26543 bounded banded Figure-7 covariance transform')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
    if a.self_test:
        print('PASS: 26543 bounded banded covariance transformer packaged'); return
    if not a.root: ap.error('--root required')
    transform(Path(a.root).resolve())

if __name__=='__main__': main()
