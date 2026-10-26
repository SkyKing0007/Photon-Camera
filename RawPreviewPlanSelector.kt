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
        // IRIS_26880_SPEKTRA_RELIABLE_STREAM_NEGOTIATION:
        // The 26879 forced largest still-size RAW stream can be too slow or
        // unusable as a repeating Camera2/Vulkan viewfinder stream. Keep ALL
        // import-compatible regular RAW outputs available to RawPreviewPolicy:
        // it independently ranks Camera2 FPS, format and processing resolution.
        // User explicit stream preference still wins, as originally specified.
        // FULL affects the processing lattice only, not a mandatory 30fps
        // capture-stream allocation of the maximum still dimension.
        val previewOutputs = selectedOutput?.let(::listOf) ?: eligibleOutputs
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
