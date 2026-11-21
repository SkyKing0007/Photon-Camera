package com.hinnka.mycamera.processor

import android.content.Context
import android.net.Uri

import com.particlesdevs.photoncamera.processing.experimentc.Iris26972CActualRaisr
import com.particlesdevs.photoncamera.processing.experimentc.Iris26972CContract
import com.particlesdevs.photoncamera.processing.experimentc.Iris26972CExifOrientation
import com.particlesdevs.photoncamera.processing.experimentc.Iris26972CGainmap
import com.particlesdevs.photoncamera.processing.experimentc.Iris26972CJpeg444
import com.particlesdevs.photoncamera.processing.experimentc.Iris26972CMediaStorePublisher
import com.particlesdevs.photoncamera.processing.experimentc.Iris26972CRaisrTilePlan
import com.particlesdevs.photoncamera.processing.experimentc.Iris26972CUltraHdr
import java.io.File
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.UUID
import java.util.function.BooleanSupplier

/**
 * C-only bounded native-grid finishing: pinned donor RAISR 2x, real 2x -> 1x,
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
    )
    internal fun validate(plan: Plan, width:Int,height:Int) {
        require(width in 16..16384 && height in 16..16384 &&
            (width and 1)==0 && (height and 1)==0 &&
            plan.physicalCameraId.isNotBlank() &&
            plan.displayOrientationDegrees in listOf(0,90,180,270) &&
            plan.sRgbIcc.size in 32..4_194_304 &&
            plan.gainmapStrength.isFinite() && plan.gainmapStrength in 0f..1f &&
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
    ): Boolean {
        image.requireOwner()
        validate(plan,image.width,image.height)
        require(plan.physicalCameraId == image.physicalCameraId) {
            "$COMPONENT final color source is from another physical RAW camera"
        }
        // Do not loosen this guard to speed local work. Only an independently
        // build-proven and device-tested C can publish photos.
        if (!Iris26972CContract.CONTROLLED_DEVICE_TRIAL_ENABLED) return false
        val width=image.width
        val height=image.height
        val gainW=Iris26972CGainmap.width(width)
        val gainH=Iris26972CGainmap.height(height)
        val gain=ByteBuffer.allocateDirect(gainW*gainH)
        val token=UUID.randomUUID().toString()
        val base=File(plan.scratchDirectory,".iris26972c_${token}_sdr.jpg")
        val gainJpeg=File(plan.scratchDirectory,".iris26972c_${token}_gain.jpg")
        check(!base.exists() && !gainJpeg.exists() && !plan.output.exists()) {
            "$COMPONENT scratch file collision"
        }
        try {
            Iris26972CGlReadback(image).use { reader ->
                var expectedRow=0
                // Non-black output is a *necessary*, not sufficient, signal of
                // a valid image. A lost/zeroed RAISR or GL color target must
                // raise an explicit capture failure; never publish a black
                // placeholder as if a real C JPEG-R photograph was produced.
                // Genuine completely-black scenes will also fail closed.
                var hasNonBlackSdrPixel=false
                val rows = object: Iris26972CJpeg444.FinalizedRgbaBandSource {
                    override fun fillBand(top:Int,count:Int,destination:ByteBuffer,stride:Int):Boolean {
                        if(top!=expectedRow || count<1 || count>CORE ||
                            top+count>height || stride<width*4 ||
                            !destination.isDirect || destination.isReadOnly ||
                            destination.capacity().toLong()<(count-1L)*stride+width*4L)
                            return false
                        // No row can be committed until its genuine donor RAISR
                        // and pixel-matched, independently developed HDR have passed.
                        try {
                            var y=top
                            while(y<top+count) {
                                val tileH=minOf(CORE,top+count-y)
                                var x=0
                                while(x<width) {
                                    val tileW=minOf(CORE,width-x)
                                    val geometry=Iris26972CRaisrTilePlan.create(
                                        width,height,x,y,x+tileW,y+tileH)
                                    val packed=readDonorTile(reader,geometry)
                                    val hdr=readHdrRgbTile(reader,x,y,tileW,tileH)
                                    val okay=Iris26972CGainmap.writeTile(packed,hdr,gain,
                                        width,height,x,y,tileW,tileH,tileW*4,tileW*12,gainW,
                                        plan.gainmapStrength)
                                    if(!okay)return false
                                    val row=ByteArray(tileW*4)
                                    for(yy in 0 until tileH) {
                                        packed.position(yy*tileW*4)
                                        packed.get(row)
                                        if (!hasNonBlackSdrPixel)
                                            hasNonBlackSdrPixel=containsNonBlackSdrRgb(row)
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
                        base,plan.sRgbIcc) || expectedRow!=height || !hasNonBlackSdrPixel)
                    return false // never publish an all-zero C SDR base
            }
            Iris26972CExifOrientation.insertIntoTemporaryBase(
                base, plan.displayOrientationDegrees)
            gain.position(0)
            if(!Iris26972CGainmap.encodeIntermediateJpeg(gain,width,height,gainJpeg))
                return false
            if(!Iris26972CUltraHdr.publish(base,gainJpeg,plan.output,
                    Iris26972CGainmap.jpegRMetadata())) return false
            // Native JPEG/R composition is separately required to preserve the
            // EXIF APP1 orientation. A missing/mutated tag is a hard failure.
            if(!Iris26972CExifOrientation.finalContainsOrientation(
                    plan.output, plan.displayOrientationDegrees)) {
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
        stillLive: () -> Boolean = { true },
    ): Uri? {
        image.requireOwner()
        if (!Iris26972CContract.CONTROLLED_DEVICE_TRIAL_ENABLED || !stillLive()) return null
        var committed: Uri? = null
        var primary: Throwable? = null
        try {
            if (!publish(plan, image)) return null
            if (!stillLive()) return null
            committed = Iris26972CMediaStorePublisher.publish(
                context, plan.output, displayName, shutterTimeMillis,
                plan.displayOrientationDegrees, BooleanSupplier { stillLive() })
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

    private fun readDonorTile(
        reader:Iris26972CGlReadback,
        plan:Iris26972CRaisrTilePlan,
    ):ByteBuffer {
        val w=plan.donorInputWidth()
        val h=plan.donorInputHeight()
        require(w in 16..1024 && h in 16..1024 &&
            plan.finalWidth() in 1..CORE && plan.finalHeight() in 1..CORE)
        val source=ByteBuffer.allocateDirect(w*h*16).order(ByteOrder.nativeOrder())
        reader.readSdr(plan.donorInputLeft,plan.donorInputTop,w,h,source)
        val result=ByteBuffer.allocateDirect(plan.finalWidth()*plan.finalHeight()*4)
        check(Iris26972CActualRaisr.render(source,plan.nativeWidth,plan.nativeHeight,
            plan.donorInputLeft,plan.donorInputTop,w,h,w*16,
            plan.coreLeft,plan.coreTop,plan.finalWidth(),plan.finalHeight(),
            result,plan.finalWidth()*4)) {
            "$COMPONENT genuine ARM64 RAISR AOT failed; no fallback"
        }
        return result
    }
    private fun readHdrRgbTile(
        reader:Iris26972CGlReadback,x:Int,y:Int,w:Int,h:Int,
    ):ByteBuffer {
        val rgba=ByteBuffer.allocateDirect(w*h*16).order(ByteOrder.nativeOrder())
        reader.readHdr(x,y,w,h,rgba)
        val input=rgba.asFloatBuffer()
        val output=ByteBuffer.allocateDirect(w*h*12).order(ByteOrder.nativeOrder())
        val rgb=output.asFloatBuffer()
        for(index in 0 until w*h) {
            rgb.put(input.get(index*4))
            rgb.put(input.get(index*4+1))
            rgb.put(input.get(index*4+2))
        }
        return output
    }
}
