package com.hinnka.mycamera.processor.experimentc

import com.hinnka.mycamera.processor.Iris26972CCaptureToGallery
import com.hinnka.mycamera.processor.experimentc.original129.processor.MgcMergeMethod
import com.hinnka.mycamera.processor.experimentc.original129.processor.MgcRawMaxMode
import com.hinnka.mycamera.processor.experimentc.original129.processor.MgcRawProcessorPipeline
import com.hinnka.mycamera.processor.experimentc.original129.processor.MgcSpatialOutputMode
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawOutputUpscaleMode
import com.particlesdevs.photoncamera.processing.experimentc.Iris26972CContract

/**
 * Immutable shutter-local route to the PINNED original bjzhou professional RAW mode.
 * This only selects original donor algorithms; it implements no image-processing math.
 *
 * Pro HDR+ Sabre fuses the native sensor Bayer grid first. Native 1x applies to the
 * RAW FINISHER (not the user's digital zoom), and the original donor Lanczos-3
 * performs any required crop/reference-grid resampling. No RAISR 2x stage is used.
 */
internal data class Iris26975CProSabre1xSelection private constructor(
    val rawMaxMode: MgcRawMaxMode,
    val processorPipeline: MgcRawProcessorPipeline,
    val mergeMethod: MgcMergeMethod,
    val stackOutputMode: MgcSpatialOutputMode,
    val outputUpscaleMode: RawOutputUpscaleMode,
    val outputScale: Float,
    val normalFrameCount: Int,
) {
    init {
        require(rawMaxMode == MgcRawMaxMode.SABRE &&
            processorPipeline == MgcRawProcessorPipeline.SABRE &&
            mergeMethod == MgcMergeMethod.SABRE &&
            stackOutputMode == MgcSpatialOutputMode.RGB &&
            rawMaxMode.mergeMethod == mergeMethod &&
            rawMaxMode.outputMode == stackOutputMode &&
            outputUpscaleMode == RawOutputUpscaleMode.LANCZOS3 &&
            outputUpscaleMode.resolveOutputScale(outputScale) == 1f &&
            outputScale == 1f && normalFrameCount in 2..30) {
            "Experiment C permits ONLY the original Pro Sabre native-1x/Lanczos-3 route"
        }
    }

    companion object {
        fun forFrozen(transaction: Iris26972CCaptureToGallery.OriginalTransaction):
            Iris26975CProSabre1xSelection {
            transaction.validate()
            val count = transaction.shutter.frameCount
            require(count == transaction.rawBurst.frames.size &&
                count in 2..Iris26972CContract.MAX_NORMAL_FRAMES &&
                Iris26972CContract.MAX_NORMAL_FRAMES == 30 &&
                Iris26972CContract.RECONSTRUCTOR == "BJZHOU_MGC_SABRE" &&
                Iris26972CContract.INTERNAL_RAISR_SCALE == 1 &&
                Iris26972CContract.FINAL_OUTPUT_SCALE == 1 &&
                !Iris26972CContract.ALLOW_ALTERNATE_RECONSTRUCTOR &&
                !Iris26972CContract.ALLOW_ALTERNATE_FINISHER) {
                "Experiment C Pro Sabre 1x output/frame slider contract violation"
            }
            // Do NOT normalize the 2..30 frame slider with the donor's unrelated
            // app-level 20-frame HDR+/denoise settings. GlesMgcRawSpatialStacker
            // consumes the full admitted frame list directly.
            return Iris26975CProSabre1xSelection(
                rawMaxMode = MgcRawMaxMode.SABRE,
                processorPipeline = MgcRawProcessorPipeline.SABRE,
                mergeMethod = MgcMergeMethod.SABRE,
                stackOutputMode = MgcSpatialOutputMode.RGB,
                outputUpscaleMode = RawOutputUpscaleMode.LANCZOS3,
                outputScale = 1f,
                normalFrameCount = count,
            )
        }
    }
}
