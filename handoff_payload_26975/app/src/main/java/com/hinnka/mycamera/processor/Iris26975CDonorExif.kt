package com.hinnka.mycamera.processor

import android.hardware.camera2.CameraCharacteristics
import android.hardware.camera2.CameraManager
import android.hardware.camera2.CaptureResult
import android.hardware.camera2.TotalCaptureResult
import android.os.Build
import androidx.exifinterface.media.ExifInterface
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import kotlin.math.abs
import kotlin.math.ln
import kotlin.math.roundToInt

/**
 * C-only faithful EXIF field writer for bjzhou's JPEG444ExportEncoder boundary.
 * Snapshot values ONLY from the first physical RAW's timestamp-matched Camera2 result;
 * write into the temporary JPEG444 base before the donor JPEG/R MPF assembly, never
 * reserialize an assembled Ultra HDR file. No A/B or preview metadata is consulted.
 * Source field and rational formatting authority:
 * bjzhou/PhotonCamera@0a8a11defe7d932d8c8a729120a4d5f159e9d677
 * gallery/ExifWriter.kt. Missing optional physical fields stay absent.
 */
internal object Iris26975CDonorExif {
    private const val OWNER = "26975 C physical bjzhou EXIF"
    internal data class Frozen(
        val physicalId: String,
        val referenceTimestampNs: Long,
        val exposureTimeNs: Long,
        val iso: Int,
        val aperture: Float?,
        val focalLengthMm: Float?,
        val focalLength35mm: Int?,
        val exposureBiasEv: Float?,
        val whiteBalance: Int?,
        val flashState: Int?,
        val captureTimeMillis: Long,
        val make: String,
        val model: String,
        val software: String = "PhotonCamera",
    ) {
        init {
            require(physicalId.isNotBlank() && referenceTimestampNs > 0 &&
                exposureTimeNs > 0 && iso > 0 && captureTimeMillis > 0 &&
                make.isNotBlank() && model.isNotBlank() && software.isNotBlank()) {
                "$OWNER invalid frozen physical capture provenance"
            }
            require(listOfNotNull(aperture, focalLengthMm, exposureBiasEv)
                .all { it.isFinite() } &&
                (aperture == null || aperture > 0f) &&
                (focalLengthMm == null || focalLengthMm > 0f) &&
                (focalLength35mm == null || focalLength35mm > 0)) {
                "$OWNER invalid Camera2 optical or EV metadata"
            }
        }
    }

    /** Uses the same physical result as the Sabre reference and camera color freeze. */
    internal fun freeze(
        manager: CameraManager,
        logicalId: String,
        physicalId: String,
        total: TotalCaptureResult,
        reference: Iris26972CPhysicalRawMetadata.Frozen,
        shutterTimeMillis: Long,
    ): Frozen {
        require(logicalId.isNotBlank() && physicalId == reference.physicalCameraId) {
            "$OWNER wrong physical RAW lens"
        }
        val physical: CaptureResult = if (logicalId == physicalId) total else {
            require(Build.VERSION.SDK_INT >= 28)
            total.physicalCameraResults[physicalId]
                ?: error("$OWNER missing real physical CaptureResult")
        }
        require(physical.get(CaptureResult.SENSOR_TIMESTAMP) == reference.sensorTimestampNs &&
            physical.get(CaptureResult.SENSOR_EXPOSURE_TIME) == reference.exposureTimeNs &&
            physical.get(CaptureResult.SENSOR_SENSITIVITY) == reference.sensitivityIso &&
            total.frameNumber == reference.frameNumber) {
            "$OWNER wrong reference frame; EXIF must never borrow preview exposure"
        }
        val characteristics = manager.getCameraCharacteristics(physicalId)
        val fNumber = physical.get(CaptureResult.LENS_APERTURE)
            ?: characteristics.get(CameraCharacteristics.LENS_INFO_AVAILABLE_APERTURES)?.firstOrNull()
        val focal = physical.get(CaptureResult.LENS_FOCAL_LENGTH)
            ?: characteristics.get(CameraCharacteristics.LENS_INFO_AVAILABLE_FOCAL_LENGTHS)?.firstOrNull()
        // Do not invent a lens focal length or crop factor. Where available Camera2
        // physical sensor width and focal length determine the 35mm equivalent.
        val physicalSize = characteristics.get(CameraCharacteristics.SENSOR_INFO_PHYSICAL_SIZE)
        val equivalent = if (focal != null && physicalSize != null &&
            physicalSize.width.isFinite() && physicalSize.width > 0f)
            (focal * 36f / physicalSize.width).roundToInt().takeIf { it > 0 } else null
        val aeStep = characteristics.get(CameraCharacteristics.CONTROL_AE_COMPENSATION_STEP)
        val aeCode = physical.get(CaptureResult.CONTROL_AE_EXPOSURE_COMPENSATION)
        val exposureBias = if (aeStep != null && aeCode != null && aeStep.denominator != 0)
            (aeCode.toFloat() * aeStep.numerator / aeStep.denominator) else null
        val autoWhiteBalance = physical.get(CaptureResult.CONTROL_AWB_MODE)
        val wb = autoWhiteBalance?.let {
            if (it == CaptureResult.CONTROL_AWB_MODE_AUTO) 0 else 1
        }
        return Frozen(physicalId, reference.sensorTimestampNs,
            reference.exposureTimeNs, reference.sensitivityIso,
            fNumber, focal, equivalent, exposureBias, wb,
            // FLASH_STATE (HAL firing status) is not the EXIF Flash bitfield;
            // do not incorrectly serialize a status as a Flash firing tag.
            null, shutterTimeMillis, Build.MANUFACTURER, Build.MODEL)
    }

    /** Original donor EXIF field policy and rational formatting before JPEG/R packaging. */
    internal fun writeIntoBase(baseJpeg: File, frozen: Frozen, width: Int, height: Int) {
        require(baseJpeg.isFile && width > 0 && height > 0)
        val exif = ExifInterface(baseJpeg)
        exif.setAttribute(ExifInterface.TAG_MAKE, frozen.make)
        exif.setAttribute(ExifInterface.TAG_MODEL, frozen.model)
        exif.setAttribute(ExifInterface.TAG_SOFTWARE, frozen.software)
        // The donor's DeviceUtil.formatExifLensModel categorizes the true 35mm
        // equivalent as ultra-wide / wide / telephoto / ultra-telephoto.
        donorLensModel(frozen.model, frozen.focalLength35mm, frozen.aperture)?.let {
            exif.setAttribute(ExifInterface.TAG_LENS_MODEL, it)
        }
        val stamp = SimpleDateFormat("yyyy:MM:dd HH:mm:ss", Locale.US)
            .format(Date(frozen.captureTimeMillis))
        exif.setAttribute(ExifInterface.TAG_DATETIME, stamp)
        exif.setAttribute(ExifInterface.TAG_DATETIME_ORIGINAL, stamp)
        exif.setAttribute(ExifInterface.TAG_DATETIME_DIGITIZED, stamp)
        // Pixels have already been physically rotated in the output pass.
        exif.setAttribute(ExifInterface.TAG_ORIENTATION,
            ExifInterface.ORIENTATION_NORMAL.toString())
        exif.setAttribute(ExifInterface.TAG_IMAGE_WIDTH, width.toString())
        exif.setAttribute(ExifInterface.TAG_PIXEL_X_DIMENSION, width.toString())
        exif.setAttribute(ExifInterface.TAG_IMAGE_LENGTH, height.toString())
        exif.setAttribute(ExifInterface.TAG_PIXEL_Y_DIMENSION, height.toString())
        val seconds = frozen.exposureTimeNs / 1_000_000_000.0
        exif.setAttribute(ExifInterface.TAG_EXPOSURE_TIME,
            if (seconds >= 1.0) seconds.toString()
            else "1/${(1.0 / seconds).toLong()}")
        exif.setAttribute(ExifInterface.TAG_ISO_SPEED_RATINGS, frozen.iso.toString())
        exif.setAttribute(ExifInterface.TAG_PHOTOGRAPHIC_SENSITIVITY, frozen.iso.toString())
        frozen.aperture?.let {
            exif.setAttribute(ExifInterface.TAG_F_NUMBER, rational(it))
            exif.setAttribute(ExifInterface.TAG_APERTURE_VALUE,
                rational((2.0 * ln(it.toDouble()) / ln(2.0)).toFloat()))
        }
        frozen.focalLengthMm?.let {
            exif.setAttribute(ExifInterface.TAG_FOCAL_LENGTH, rational(it))
        }
        frozen.focalLength35mm?.let {
            exif.setAttribute(ExifInterface.TAG_FOCAL_LENGTH_IN_35MM_FILM, it.toString())
        }
        frozen.exposureBiasEv?.let {
            exif.setAttribute(ExifInterface.TAG_EXPOSURE_BIAS_VALUE, signedRational(it))
        }
        frozen.whiteBalance?.let {
            exif.setAttribute(ExifInterface.TAG_WHITE_BALANCE, it.toString())
        }
        frozen.flashState?.let {
            exif.setAttribute(ExifInterface.TAG_FLASH, it.toString())
        }
        exif.setAttribute(ExifInterface.TAG_COLOR_SPACE, "1")
        exif.setAttribute(ExifInterface.TAG_EXIF_VERSION, "0230")
        // The base JPEG is still temporary. AndroidX EXIF can rewrite its marker
        // headers here, BEFORE MPF/XMP/gainmap assembly, as the original donor does.
        exif.saveAttributes()
        check(verify(baseJpeg, frozen, width, height)) {
            "$OWNER original JPEG444 EXIF did not survive temporary base write"
        }
    }

    /** Fail closed if the JPEG/R packager strips the donor EXIF APP1 metadata. */
    internal fun verify(jpeg: File, frozen: Frozen, width: Int, height: Int): Boolean =
        runCatching {
            if (!jpeg.isFile || jpeg.length() <= 0) return@runCatching false
            val exif = ExifInterface(jpeg)
            exif.getAttribute(ExifInterface.TAG_MAKE) == frozen.make &&
                exif.getAttribute(ExifInterface.TAG_MODEL) == frozen.model &&
                exif.getAttribute(ExifInterface.TAG_SOFTWARE) == frozen.software &&
                exif.getAttributeInt(ExifInterface.TAG_ORIENTATION, -1) ==
                    ExifInterface.ORIENTATION_NORMAL &&
                exif.getAttributeInt(ExifInterface.TAG_PHOTOGRAPHIC_SENSITIVITY, -1) == frozen.iso &&
                exif.getAttributeInt(ExifInterface.TAG_PIXEL_X_DIMENSION, -1) == width &&
                exif.getAttributeInt(ExifInterface.TAG_PIXEL_Y_DIMENSION, -1) == height &&
                exif.getAttribute(ExifInterface.TAG_DATETIME_ORIGINAL) != null
        }.getOrDefault(false)

    internal fun donorLensModel(model: String, equivalentMm: Int?, aperture: Float?): String? {
        val focal = equivalentMm?.takeIf { it > 0 } ?: return null
        val fNumber = aperture?.takeIf { it.isFinite() && it > 0f } ?: return null
        val category = when {
            focal <= 18 -> "ultra wide camera"
            focal < 40 -> "wide camera"
            focal < 150 -> "telephoto camera"
            else -> "ultra telephoto camera"
        }
        return String.format(Locale.US, "%s %s %dmm f/%.1f", model,
            category, focal, fNumber)
    }

    private fun gcd(a: Int, b: Int): Int {
        var x = abs(a)
        var y = abs(b)
        while (y != 0) { val r = x % y; x = y; y = r }
        return if (x == 0) 1 else x
    }
    private fun rational(value: Float): String {
        val numerator = (value * 10f).toInt()
        val divisor = gcd(numerator, 10)
        return "${numerator / divisor}/${10 / divisor}"
    }
    private fun signedRational(value: Float): String {
        val denominator = 1_000_000
        val numerator = (value * denominator).roundToInt()
        val divisor = gcd(numerator, denominator)
        return "${numerator / divisor}/${denominator / divisor}"
    }
}
