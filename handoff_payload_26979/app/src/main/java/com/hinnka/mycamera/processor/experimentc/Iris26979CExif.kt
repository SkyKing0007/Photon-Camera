package com.hinnka.mycamera.processor.experimentc

import androidx.exifinterface.media.ExifInterface
import com.hinnka.mycamera.processor.experimentc.original129.camera.CaptureInfo
import com.particlesdevs.photoncamera.api.ParseExif
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import kotlin.math.roundToInt

/** Shared Iris photographic EXIF convention, using only the C physical RAW reference.
 * The base is still private. Never rewrite the completed MPF/JPEG-R container. */
internal object Iris26979CExif {
    fun write(base: File, info: CaptureInfo) {
        val data = ParseExif.ExifData()
        data.PHOTOGRAPHIC_SENSITIVITY = requireNotNull(info.iso).toString()
        data.EXPOSURE_TIME = ParseExif.getTime(requireNotNull(info.exposureTime))
        data.F_NUMBER = info.aperture?.toString()
        data.FOCAL_LENGTH = info.focalLength?.let { "${(100.0 * it).roundToInt()}/100" }
        data.DATETIME = SimpleDateFormat("yyyy:MM:dd HH:mm:ss", Locale.US).format(Date(info.captureTime))
        val exif = checkNotNull(ParseExif.setAllAttributes(base, data))
        // Physically rotated donor output always has NORMAL orientation.
        exif.setAttribute(ExifInterface.TAG_ORIENTATION, ExifInterface.ORIENTATION_NORMAL.toString())
        exif.setAttribute(ExifInterface.TAG_IMAGE_WIDTH, info.imageWidth.toString())
        exif.setAttribute(ExifInterface.TAG_IMAGE_LENGTH, info.imageHeight.toString())
        exif.setAttribute(ExifInterface.TAG_PIXEL_X_DIMENSION, info.imageWidth.toString())
        exif.setAttribute(ExifInterface.TAG_PIXEL_Y_DIMENSION, info.imageHeight.toString())
        exif.saveAttributes()
        check(verify(base, info)) { "C shared Iris EXIF base write did not survive" }
    }
    fun verify(file: File, info: CaptureInfo): Boolean = runCatching {
        val exif=ExifInterface(file)
        val exposure=exif.getAttributeDouble(ExifInterface.TAG_EXPOSURE_TIME, -1.0)
        val expected=requireNotNull(info.exposureTime)/1_000_000_000.0
        exif.getAttribute(ExifInterface.TAG_MAKE)==android.os.Build.BRAND &&
            exif.getAttribute(ExifInterface.TAG_MODEL)==android.os.Build.MODEL &&
            exif.getAttributeInt(ExifInterface.TAG_ORIENTATION,-1)==ExifInterface.ORIENTATION_NORMAL &&
            exif.getAttributeInt(ExifInterface.TAG_PHOTOGRAPHIC_SENSITIVITY,-1)==info.iso &&
            exposure>0 && kotlin.math.abs(exposure-expected)<=kotlin.math.max(0.000001,expected*0.01) &&
            exif.getAttribute(ExifInterface.TAG_DATETIME)!=null
    }.getOrDefault(false)
}
