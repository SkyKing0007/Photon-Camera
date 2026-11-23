package com.hinnka.mycamera.processor

import android.content.Context
import android.net.Uri

import com.particlesdevs.photoncamera.processing.experimentc.Iris26975CNativeOneX
import com.particlesdevs.photoncamera.processing.experimentc.Iris26975COutputGeometry
import com.particlesdevs.photoncamera.processing.experimentc.Iris26972CContract
import com.particlesdevs.photoncamera.processing.experimentc.Iris26972CGainmap
import com.particlesdevs.photoncamera.processing.experimentc.Iris26972CJpeg444
import com.particlesdevs.photoncamera.processing.experimentc.Iris26972CMediaStorePublisher
import com.particlesdevs.photoncamera.processing.experimentc.Iris26972CUltraHdr
import java.io.File
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.UUID
import java.util.function.BooleanSupplier

/**
 * C-only bounded native-grid finishing: native 1x encoded RGB transfer,
 * original 4:4:4 JPEG95, measured HDR gainmap and atomic JPEG/R publication.
 * No intermediate 2x full frame or 50MP Kotlin Bitmap. The GL color owner stays
 * alive for every tile and is released by the caller only after the last band.
 *
 * Controlled C-only device trial: successful 26972 Android compilation is proved,
 * but physical Camera2, orientation, memory and image quality still require
 * real device validation. No A/B renderer or SDR-only fallback is permitted.
 */
internal object Iris26972CStreamingFinish {
    private const val COMPONENT = "26972 C 1x 444 JPEG-R publication"
    private const val CORE = 256
    /** Host-testable detector for the fatal all-zero output regression. */
    internal fun containsNonBlackSdrRgb(row: ByteArray): Boolean {
        require(row.isNotEmpty() && row.size % 4 == 0)
        var pixel=0
        while (pixel<row.size) {
            if (((row[pixel].toInt() or row[pixel+1].toInt() or
                    row[pixel+2].toInt()) and 255)!=0) return true
            pixel+=4 // alpha-only pixels do not prove rendered RGB exists
        }
        return false
    }
    internal class Plan(
        val output: File,
        val scratchDirectory: File,
        val physicalCameraId: String,
        val displayOrientationDegrees: Int,
        val sRgbIcc: ByteArray,
        val gainmapStrength: Float,
        val geometry: Iris26975COutputGeometry,
        /** Frozen at shutter; both SDR and UHDR must use this same choice. */
        val lutSelection: Iris26975CDonorLutSelection.Frozen =
            Iris26975CDonorLutSelection.freeze(),
    )
    internal fun validate(plan: Plan, width:Int,height:Int) {
        require(width in 16..16384 && height in 16..16384 &&
            (width and 1)==0 && (height and 1)==0 &&
            plan.physicalCameraId.isNotBlank() &&
            // Do not apply the donor APK's Standard look by default.
            // An explicit LUT requires a separate, donor-correct rendered branch.
            plan.lutSelection.isNoLut &&
            plan.displayOrientationDegrees in listOf(0,90,180,270) &&
            plan.sRgbIcc.size in 32..4_194_304 &&
            plan.gainmapStrength.isFinite() &&
            plan.gainmapStrength in Iris26972CGainmap.STRENGTH_MIN..Iris26972CGainmap.STRENGTH_MAX &&
            plan.geometry.rawWidth == width && plan.geometry.rawHeight == height &&
            plan.geometry.rotation == plan.displayOrientationDegrees &&
            plan.geometry.outputWidth > 0 && plan.geometry.outputHeight > 0 &&
            plan.output.parentFile?.isDirectory==true &&
            plan.scratchDirectory.isDirectory &&
            !plan.output.exists()) {
            "$COMPONENT requires valid shutter-frozen native metadata and exclusive output"
        }
        // EXIF orientation is injected only into the temporary base JPEG before
        // JPEG/R MPF assembly, never after gainmap attachment.
    }

    /**
     * The callback remains on the caller-owned EGL thread. It never starts a
     * background task; an aborted Java/JNI/native stage deletes temporary files.
     */
    internal fun publish(
        plan: Plan,
        image: Iris26972CColorDeveloper.Result,
        exif: Iris26975CDonorExif.Frozen,
    ): Boolean {
        image.requireOwner()
        validate(plan,image.width,image.height)
        require(exif.physicalId == plan.physicalCameraId &&
            exif.referenceTimestampNs > 0L &&
            plan.physicalCameraId == image.physicalCameraId) {
            "$COMPONENT final color source is from another physical RAW camera"
        }
        // Do not loosen this guard to speed local work. Only an independently
        // build-proven and device-tested C can publish photos.
        if (!Iris26972CContract.CONTROLLED_DEVICE_TRIAL_ENABLED) return false
        // V3 still lacks the complete pinned donor HDR reference + real LUT
        // stack. Fail closed: guided SDR alone is not permission to publish the
        // old Iris UHDR gainmap/JPEG-R path as bjzhou-equivalent.
        if (!image.donorGuidedSdrComplete || !image.donorUltraHdrComplete) return false
        val width=plan.geometry.outputWidth
        val height=plan.geometry.outputHeight
        val gainW=Iris26972CGainmap.width(width)
        val gainH=Iris26972CGainmap.height(height)
        val token=UUID.randomUUID().toString()
        val base=File(plan.scratchDirectory,".iris26972c_${token}_sdr.jpg")
        val gainJpeg=File(plan.scratchDirectory,".iris26972c_${token}_gain.jpg")
        check(!base.exists() && !gainJpeg.exists() && !plan.output.exists()) {
            "$COMPONENT scratch file collision"
        }
        try {
            val gain = Iris26972CGlReadback(image).use { reader ->
                Iris26975CGeometryResampler(plan.geometry,reader).use { geometryReader ->
                // Only the pinned donor two-stage GPU sidecar/residual may
                // encode UHDR. No legacy C 2x2 gainmap/CPU approximation.
                // This call is still BLOCKED by donorUltraHdrComplete until
                // the real RAW HDR ratio is numerically donor-verified.
                val donorGain = Iris26975CDonorTiledGainmapGpu().use { gpu ->
                    gpu.computeNoLutFromFinalizedGeometry(width,height,
                        plan.physicalCameraId,exif.referenceTimestampNs,
                        plan.gainmapStrength,plan.lutSelection,geometryReader)
                }
                check(donorGain.isDirect &&
                    donorGain.remaining()==gainW*gainH) {
                    "$COMPONENT donor UHDR gainmap missing or misaligned"
                }
                var expectedRow=0
                // An optically black RAW is a valid photo. Reject incomplete
                // output, malformed alpha and GPU errors, never all-zero RGB.
                // Tile readback and encoder boundary remain fail-closed.
                val rows: Iris26972CJpeg444.FinalizedRgbaBandSource = object: Iris26972CJpeg444.FinalizedRgbaBandSource {
                    override fun fillBand(top:Int,count:Int,destination:ByteBuffer,stride:Int):Boolean {
                        if(top!=expectedRow || count<1 || count>CORE ||
                            top+count>height || stride<width*4 ||
                            !destination.isDirect || destination.isReadOnly ||
                            destination.capacity().toLong()<(count-1L)*stride+width*4L)
                            return false
                        // No row can be committed until its native-1x SDR
                        // and pixel-matched, independently developed HDR have passed.
                        try {
                            var y=top
                            while(y<top+count) {
                                // A downscale may need wider Lanczos-3 support;
                                // shrink only the output tile, never the RAW halo.
                                var tileH=minOf(CORE,top+count-y)
                                while (tileH>1 && !geometryReader.fits(0,y,1,tileH)) tileH/=2
                                var x=0
                                while(x<width) {
                                    var tileW=minOf(CORE,width-x)
                                    while (tileW>1 && !geometryReader.fits(x,y,tileW,tileH)) tileW/=2
                                    check(geometryReader.fits(x,y,tileW,tileH)) {
                                        "$COMPONENT Lanczos support too large for bounded tile"
                                    }
                                    val sample=geometryReader.render(x,y,tileW,tileH)
                                    val packed=sample.sdr
                                    // Donor gainmap was already computed on
                                    // its GLOBAL downsample-2 grid above.
                                    // This is the SDR JPEG-only readback pass.
                                    val row=ByteArray(tileW*4)
                                    for(yy in 0 until tileH) {
                                        packed.position(yy*tileW*4)
                                        packed.get(row)
                                        for (px in row.indices step 4) {
                                            if ((row[px+3].toInt() and 255) != 255)
                                                return false // invalid finalized RGBA alpha
                                        }
                                        destination.position((y-top+yy)*stride+x*4)
                                        destination.put(row)
                                    }
                                    x+=tileW
                                }
                                y+=tileH
                            }
                        } catch (_:Throwable) {
                            return false
                        }
                        expectedRow=top+count
                        return true
                    }
                }
                if(!Iris26972CJpeg444.writeFromFinalCBands(width,height,CORE,rows,
                        base,plan.sRgbIcc) || expectedRow!=height)
                    return false // never publish a partial/broken C SDR base
                donorGain
                }
            }
            Iris26975CDonorExif.writeIntoBase(base,exif,width,height)
            // Full donor field EXIF is written into temporary JPEG444 BEFORE
            // attaching the gainmap. Never reserialize the finished JPEG/R.
            gain.position(0)
            if(!Iris26972CGainmap.encodeIntermediateJpeg(gain,width,height,gainJpeg))
                return false
            if(!Iris26972CUltraHdr.publish(base,gainJpeg,plan.output,
                    Iris26972CGainmap.jpegRMetadata())) return false
            // Native JPEG/R composition is separately required to preserve the
            // EXIF APP1 orientation. A missing/mutated tag is a hard failure.
            if(!Iris26975CDonorExif.verify(plan.output,exif,width,height)) {
                if (plan.output.exists() && !plan.output.delete())
                    throw IllegalStateException("$COMPONENT failed EXIF output cleanup")
                return false
            }
            return plan.output.isFile && plan.output.length()>0
        } finally {
            // No partially-published or temporary image may be left after a
            // failed pass. The final destination is exclusive and native-owned.
            if(base.exists()) check(base.delete()) {"$COMPONENT leaked SDR scratch"}
            if(gainJpeg.exists()) check(gainJpeg.delete()) {"$COMPONENT leaked gainmap scratch"}
        }
    }
    /**
     * C-owned final publication boundary: the encoded JPEG/R is private until
     * Android acknowledges its complete MediaStore pending-row transaction.
     * No intermediate SDR, 2x RAISR, or gainmap file is exposed. A failed or
     * disabled C always returns without a visible media row.
     *
     * The owner must call this on the color result's EGL thread. The private
     * output is removed whether publication succeeds or fails; C never alters
     * A/B's existing storage route. Real Android provider testing is pending.
     */
    internal fun publishToMediaStore(
        plan: Plan,
        image: Iris26972CColorDeveloper.Result,
        context: Context,
        displayName: String,
        shutterTimeMillis: Long,
        exif: Iris26975CDonorExif.Frozen,
        stillLive: () -> Boolean = { true },
    ): Uri? {
        image.requireOwner()
        if (!Iris26972CContract.CONTROLLED_DEVICE_TRIAL_ENABLED || !stillLive()) return null
        var committed: Uri? = null
        var primary: Throwable? = null
        try {
            if (!publish(plan, image, exif)) return null
            if (!stillLive()) return null
            committed = Iris26972CMediaStorePublisher.publish(
                context, plan.output, displayName, shutterTimeMillis,
                0, BooleanSupplier { stillLive() })
            return committed
        } catch (failure: Throwable) {
            primary = failure
            throw failure
        } finally {
            // The only durable product is the committed gallery row. If a
            // private JPEG/R cannot be deleted, revoke that C row rather than
            // reporting a false no-image failure with a visible leaked photo.
            if (plan.output.exists()) try {
                check(plan.output.delete()) {
                    "$COMPONENT leaked private finalized JPEG/R after publication"
                }
            } catch (cleanup: Throwable) {
                val row = committed
                if (row != null) try {
                    Iris26972CMediaStorePublisher.revokeCommitted(context, row)
                } catch (revoke: Throwable) { cleanup.addSuppressed(revoke) }
                if (primary != null) primary.addSuppressed(cleanup) else throw cleanup
            }
        }
    }

    /** Exact native grid: never inflate to 2x for an unused RAISR pass. */
    private fun readNativeOneXTile(
        sharpener:Iris26975CDonorSharpenTile,x:Int,y:Int,w:Int,h:Int,
    ):ByteBuffer {
        require(w in 1..CORE && h in 1..CORE)
        val source=ByteBuffer.allocateDirect(w*h*16).order(ByteOrder.nativeOrder())
        sharpener.readEncodedTile(x,y,w,h,source)
        val output=ByteBuffer.allocateDirect(w*h*4)
        check(Iris26975CNativeOneX.render(source,w,h,w*16,output,w*4)) {
            "$COMPONENT genuine 1x encoded SDR transfer failed"
        }
        return output
    }
}
