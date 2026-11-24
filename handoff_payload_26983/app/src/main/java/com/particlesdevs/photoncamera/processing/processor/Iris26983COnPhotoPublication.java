package com.particlesdevs.photoncamera.processing.processor;

import android.content.Context;
import android.graphics.ImageFormat;
import android.hardware.camera2.CameraCharacteristics;
import com.hinnka.mycamera.processor.GlesIris26983COnMotionIngress;
import com.particlesdevs.photoncamera.api.Camera2ApiAutoFix;
import com.particlesdevs.photoncamera.api.ParseExif;
import com.particlesdevs.photoncamera.processing.ImageFrame;
import com.particlesdevs.photoncamera.processing.ImagePath;
import com.particlesdevs.photoncamera.processing.MotionBatch;
import com.particlesdevs.photoncamera.processing.ProcessingEventsListener;
import com.particlesdevs.photoncamera.util.Log;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

/** C-only Photo SR ON JPEG dispatch. A separate existing DNG owner must finish its
 * attempt before this is called for dual-output. No DNG reconstruction, DNG writer,
 * B renderer, C OFF renderer or live experiment preference is called here.
 * Camera2 shutter dispatch provides immutable admission.
 * The serialized worker owns all RAWs at entry and releases them at exit.
 */
public final class Iris26983COnPhotoPublication {
    private static final String TAG = "Iris26983COnPhoto";
    private Iris26983COnPhotoPublication() {}

    /** The B publisher adds the extension to the existing public basename and
     * resolves collisions without an experiment-specific suffix. */
    static Path uniqueJpeg(Path base) {
        final String absolute=base.toAbsolutePath().toString();
        Path output=Paths.get(absolute+".jpg");
        if(Files.exists(output)) {
            int collision=1;
            do { output=Paths.get(absolute+"_"+collision+".jpg"); collision++; }
            while(Files.exists(output));
        }
        return output;
    }

    /** JPEG dispatch is never a DNG-only route. For dual output, the original
     * independent DNG owner reports that its attempt is finished; as in B, a
     * false DNG save status does not in itself block JPEG. The original writer
     * owns that status and its output path, which are not passed to this class. */
    public static void requireJpegAdmission(MotionBatch batch, int rawSaverAtShutter,
            boolean originalDngAttempted, int expectedNormals, long referenceTimestamp) {
        if(batch==null || !batch.superResEnabled || batch.heicOutputEnabled ||
                batch.imageFormat!=ImageFormat.RAW_SENSOR || (rawSaverAtShutter!=0 && rawSaverAtShutter!=1) ||
                (rawSaverAtShutter==1)!=originalDngAttempted || expectedNormals<2 ||
                batch.frames.size()!=expectedNormals || batch.processingFrameCount!=expectedNormals ||
                batch.totalFrameCount!=expectedNormals || batch.candidateCount!=expectedNormals ||
                batch.retainedCount!=expectedNormals || batch.referenceResult==null || batch.referenceRequest==null ||
                batch.shortHighlightSlot==null || !batch.shortHighlightSlot.requiredFreezeComplete() ||
                batch.shortHighlightSlot.shortWasExpected() || batch.shortHighlightSlot.shadowWasExpected() ||
                batch.shortHighlightSlot.hasFrame() || batch.shortHighlightSlot.shadowAuxSlot.hasFrame())
            throw new IllegalArgumentException("26983 invalid C ON JPEG admission; no DNG-only or legacy fallback");
        if(batch.iris26524OwnerCameraId==null || batch.iris26524OwnerCameraId.isEmpty())
            throw new IllegalArgumentException("26983 missing C ON physical lens");
        int references=0;
        for(ImageFrame frame:batch.frames) {
            if(frame==null || !"C".equals(frame.motionV2ReconstructionExperiment26856) ||
                    !batch.iris26524OwnerCameraId.equals(frame.motionV2PhysicalCameraId) ||
                    frame.motionV2FrameRole!=ImageFrame.MotionV2FrameRole.NORMAL || frame.motionV2ShortHighlightFrame)
                throw new IllegalArgumentException("26983 foreign C ON RAW");
            if(frame.timestamp==referenceTimestamp) references++;
        }
        if(references!=1) throw new IllegalArgumentException("26983 missing or duplicate C ON shutter reference");
    }

    public static void run(Context app, CameraCharacteristics characteristics, MotionBatch batch,
            int rawSaverAtShutter, boolean originalDngAttempted, int expectedNormals, long referenceTimestamp,
            IrisMotionSettings.Snapshot tone, float clipYFloor, boolean highlightCompression,
            boolean watermark, boolean aspect169, boolean energySaving,
            ProcessingEventsListener listener, ProcessorBase.ProcessingCallback callback) {
        runPrepared(app,characteristics,batch,rawSaverAtShutter,originalDngAttempted,expectedNormals,
                referenceTimestamp,tone,clipYFloor,highlightCompression,watermark,aspect169,energySaving,
                listener,callback,null,null,false);
    }

    /** The batch owner may allocate both public paths and parse EXIF before the optional DNG.
     * The original DNG attempt is completed before entering the private JPEG engine. */
    static void runPrepared(Context app, CameraCharacteristics characteristics, MotionBatch batch,
            int rawSaverAtShutter, boolean originalDngAttempted, int expectedNormals, long referenceTimestamp,
            IrisMotionSettings.Snapshot tone, float clipYFloor, boolean highlightCompression,
            boolean watermark, boolean aspect169, boolean energySaving,
            ProcessingEventsListener listener, ProcessorBase.ProcessingCallback callback,
            Path imageBase, ParseExif.ExifData preparedExif, boolean alreadyStarted) {
        // Admission does not transfer ownership for a foreign or DNG-only batch.
        requireJpegAdmission(batch,rawSaverAtShutter,originalDngAttempted,expectedNormals,referenceTimestamp);
        Path output=null;
        boolean saved=false;
        boolean started=alreadyStarted;
        try {
            if(app==null || characteristics==null || tone==null || listener==null || callback==null ||
                    !Float.isFinite(clipYFloor) || clipYFloor<=0f)
                throw new IllegalArgumentException("26983 missing frozen JPEG context");
            // B parses EXIF before Camera2ApiAutoFix.ApplyRes, and clears the
            // ImageDescription for ON. Keep that exact photographic EXIF order.
            ParseExif.ExifData exif=preparedExif;
            if (exif==null) {
                exif=ParseExif.parse(batch.referenceResult,batch.referenceRequest);
                Camera2ApiAutoFix.ApplyRes(batch.referenceResult);
            }
            exif.IMAGE_DESCRIPTION=null;
            if(!alreadyStarted) {
                started=true;
                callback.onStarted();
                listener.onProcessingStarted("HDRX");
            }
            output=uniqueJpeg(imageBase==null?ImagePath.newImageFilePath():imageBase);
            if(!GlesIris26983COnMotionIngress.executePreparedMotion(app,characteristics,batch,
                    expectedNormals,referenceTimestamp,tone,clipYFloor,highlightCompression,watermark,
                    aspect169,energySaving,output,exif) || !Files.isRegularFile(output) || Files.size(output)<=0L)
                throw new IllegalStateException("26983 C ON private 50MP JPEG publication failed");
            saved=true;
            // A successful durable JPEG is not revoked because a detached UI listener throws.
            try { listener.notifyImageSavedStatus(true,output); }
            catch(RuntimeException detached) { Log.w(TAG,"C ON output notification failed",detached); }
            try { listener.onProcessingFinished("HdrX JPG Processing Finished"); }
            catch(RuntimeException detached) { Log.w(TAG,"C ON finish notification failed",detached); }
        } catch(Exception failure) {
            if(!saved && output!=null) try { Files.deleteIfExists(output); }
                catch(Exception cleanup) { failure.addSuppressed(cleanup); }
            throw new IllegalStateException("26983 C ON JPEG processing failed",failure);
        } catch(Error failure) {
            if(!saved && output!=null) try { Files.deleteIfExists(output); }
                catch(Exception cleanup) { failure.addSuppressed(cleanup); }
            throw failure;
        } finally {
            // No DNG pathname or carrier is owned here. Close only accepted NORMALs.
            for(ImageFrame frame:batch.frames) try { frame.close(); }
                catch(RuntimeException failure) { Log.w(TAG,"C ON RAW cleanup failed",failure); }
            try { batch.shortHighlightSlot.sealAndClose(); }
            finally { if(started) { if(saved) callback.onFinished(); else callback.onFailed(); } }
        }
    }
}
