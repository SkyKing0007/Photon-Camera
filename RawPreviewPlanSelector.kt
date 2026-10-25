package com.unspektrawesome.preview

import com.unspektrawesome.camera.CameraDescriptor
import com.unspektrawesome.camera.RawFormat
import com.unspektrawesome.camera.RawPreviewPolicy
import com.unspektrawesome.settings.CameraPreferences
import com.unspektrawesome.settings.RawPreviewQuality

object RawPreviewPlanSelector {
    const val TARGET_FRAMES_PER_SECOND = 30

    fun select(
        camera: CameraDescriptor,
        preferences: CameraPreferences,
        candidateFormats: Set<RawFormat> = VulkanRawImportPolicy.candidateFormats,
        importCapabilities: Map<RawImportStreamKey, RawImportCapability> = emptyMap(),
    ): RawPreviewPolicy.Plan {
        require(camera.isUsable) { "Selected camera is not usable for RAW preview" }
        val selectedStream = preferences.rawPreviewStreams[camera.route.routeId]
        val selectedOutput = selectedStream?.let { selected ->
            requireNotNull(
                camera.rawOutputs.firstOrNull {
                    selected.matches(it) && !it.maximumResolutionMode
                },
            ) {
                "Saved RAW stream ${selected.format} ${selected.width} x ${selected.height} " +
                    "is not advertised by camera route ${camera.route.routeId}"
            }
        }
        selectedOutput?.let { output ->
            val capability = importCapabilities[RawImportStreamKey.from(camera.route.routeId, output)]
            require(capability?.state != RawImportCapabilityState.INCOMPATIBLE) {
                "${output.format} ${output.size.width} x ${output.size.height} cannot be imported " +
                    "by Vulkan: ${capability?.reason}"
            }
        }
        val regularOutputs = camera.rawOutputs.filterNot { it.maximumResolutionMode }
        val eligibleOutputs = regularOutputs.filter { output ->
            importCapabilities[RawImportStreamKey.from(camera.route.routeId, output)]?.state !=
                RawImportCapabilityState.INCOMPATIBLE
        }
        // IRIS_26692_UNSPEKTRAWESOME_RAW10_PREFERENCE
        // The audited 1.1.2 APK prefers RAW10 where usable, then packed alternatives, with
        // RAW_SENSOR as a real fallback. Do not pre-filter the plan to RAW_SENSOR here;
        // RawPreviewPolicy owns the format ranking for the complete eligible set.
        /* IRIS_26879_SPEKTRA_CAPTURE_MATCHED_RAW_FOV
         * The 26878 SurfaceView already has the exact 3:4 presentation ratio,
         * yet the screenshot loses its left/right field of view versus the
         * captured 4096x3072 RAW10 still. Small preview RAW streams may carry
         * HAL center crops on this camera despite identical aspect ratios.
         * Choose the same largest importable regular RAW stream as the saved
         * still when there is no explicit user stream override. Preserve the
         * standalone format order, camera identity and independent GPU quality
         * scaling, rather than stretching or cropping the final 2D surface.
         * If explicit preference exists, respect it as original code did.
         */
        val previewOutputs = selectedOutput?.let(::listOf) ?: listOf(
            RawPreviewPolicy.selectCaptureOutput(eligibleOutputs, candidateFormats),
        )
        require(previewOutputs.isNotEmpty()) {
            "No advertised RAW stream remains compatible with the Unspektrawesome RAW importer"
        }
        val allowedFormats = selectedOutput?.let { setOf(it.format) } ?: candidateFormats
        return RawPreviewPolicy.select(
            previewOutputs,
            camera.aeFpsRanges,
            when (preferences.previewQuality) {
                RawPreviewQuality.LOW -> RawPreviewPolicy.Quality.LOW
                RawPreviewQuality.MEDIUM -> RawPreviewPolicy.Quality.MEDIUM
                RawPreviewQuality.HIGH -> RawPreviewPolicy.Quality.HIGH
                RawPreviewQuality.FULL -> RawPreviewPolicy.Quality.FULL
            },
            TARGET_FRAMES_PER_SECOND,
            allowedFormats,
        )
    }
}
