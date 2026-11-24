package com.hinnka.mycamera.processor.experimentc

import android.util.Size
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawDigitalZoomResampling
import com.hinnka.mycamera.processor.experimentc.original129.camera.RawBlackBorderCrop
import android.hardware.camera2.CameraCharacteristics
import android.hardware.camera2.CaptureResult
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawPhysicalCrop
import com.hinnka.mycamera.processor.experimentc.original129.utils.RawProcessor
import com.particlesdevs.photoncamera.processing.experimentc.Iris26975COutputGeometry

object Iris26977CPhysicalGeometry {
    class Frozen internal constructor(val geometry: Iris26975COutputGeometry, internal val physicalCrop: RawPhysicalCrop, internal val nativeOutputSize: Size?)
    @JvmStatic fun freeze(width: Int, height: Int, characteristics: CameraCharacteristics,
                         result: CaptureResult, rotation: Int): Frozen {
        val crop = RawProcessor.resolveCameraRawPhysicalCrop(width, height, characteristics, result)
        val nativeSize = RawDigitalZoomResampling.readPhysicalSize(
            RawDigitalZoomResampling.resolveCaptureProperties(
                RawDigitalZoomResampling.captureProperties(true), crop, RawBlackBorderCrop(),
            ),
        )
        val nativeWidth = nativeSize?.width ?: crop.width
        val nativeHeight = nativeSize?.height ?: crop.height
        val quarter = rotation == 90 || rotation == 270
        require(nativeWidth >= 16 && nativeHeight >= 16 && crop.width >= 16 && crop.height >= 16)
        val r = crop.sourceBounds
        return Frozen(Iris26975COutputGeometry(width,height,r.left,r.top,r.right,r.bottom,rotation,
            if (quarter) nativeHeight else nativeWidth, if (quarter) nativeWidth else nativeHeight), crop, nativeSize)
    }
}
