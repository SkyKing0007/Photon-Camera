package com.hinnka.mycamera.processor.experimentc.original129.camera

/** Exact original donor preview shutter-time boundary, isolated from Iris camera state. */
internal object CameraState {
    const val MAX_PHOTO_PREVIEW_SHUTTER_SPEED_NS = 1_000_000_000L / 15
}
