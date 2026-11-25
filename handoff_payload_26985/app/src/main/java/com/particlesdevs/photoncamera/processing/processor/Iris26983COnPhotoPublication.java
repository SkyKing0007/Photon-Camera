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
    static void requireAdmission(MotionBatch batch, int rawSaverAtShutter, int expectedNormals, long referenceTimestamp) {
        if(batch==null || !batch.superResEnabled || batch.heicOutputEnabled ||
                batch.imageFormat!=ImageFormat.RAW_SENSOR || (rawSaverAtShutter<0 || rawSaverAtShutter>2) || expectedNormals<2 ||
                batch.frames.size()!=expectedNormals || batch.processingFrameCount!=expectedNormals ||
                batch.totalFrameCount!=expectedNormals || batch.candidateCount!=expectedNormals ||
                batch.retainedCount!=expectedNormals || batch.referenceResult==null || batch.referenceRequest==null ||
                batch.shortHighlightSlot==null || !batch.shortHighlightSlot.requiredFreezeComplete() ||
                batch.shortHighlightSlot.shortWasExpected() || batch.shortHighlightSlot.shadowWasExpected() ||
                batch.shortHighlightSlot.hasFrame() || batch.shortHighlightSlot.shadowAuxSlot.hasFrame())
            throw new IllegalArgumentException("26983 invalid C ON JPEG admission; no DNG-only or legacy fallback");
        if(batch.iris26524OwnerCameraId==null || batch.iris26524OwnerCameraId.isEmpty())
            throw new IllegalArgumentException("26983 missing C ON physical lens");
        int references=0, zero=0, shorts=0, longs=0;
        for(ImageFrame frame:batch.frames) {
            if(frame==null || !"C".equals(frame.motionV2ReconstructionExperiment26856) ||
                    !batch.iris26524OwnerCameraId.equals(frame.motionV2PhysicalCameraId) ||
                    frame.motionV2FrameRole!=ImageFrame.MotionV2FrameRole.NORMAL || frame.motionV2ShortHighlightFrame)
                throw new IllegalArgumentException("26983 foreign C ON RAW");
            if(frame.iris26985CBracketEv==0f)zero++;
            else if(frame.iris26985CBracketEv==-2f)shorts++;
            else if(frame.iris26985CBracketEv==1.5f)longs++;
            else throw new IllegalArgumentException("26985 invalid planned HDR exposure");
            if(frame.timestamp==referenceTimestamp && frame.iris26985CBracketEv==0f) references++;
        }
        if(references!=1 || zero<2 || shorts>2 || longs>1) throw new IllegalArgumentException("26983 missing or duplicate C ON shutter reference");
    }

    /** Legacy JPEG-only entry is retained for binary/source compatibility, never a second dual-output solve. */
    public static void requireJpegAdmission(MotionBatch batch,int rawSaverAtShutter,
            boolean originalDngAttempted,int expectedNormals,long referenceTimestamp) {
        if(rawSaverAtShutter!=0 || originalDngAttempted)
            throw new IllegalArgumentException("26985 dual/DNG must use single C ON batch owner");
        requireAdmission(batch,rawSaverAtShutter,expectedNormals,referenceTimestamp);
    }
    public static void run(Context app, CameraCharacteristics characteristics, MotionBatch batch,
            int rawSaverAtShutter, boolean originalDngAttempted, int expectedNormals, long referenceTimestamp,
            IrisMotionSettings.Snapshot tone, float clipYFloor, boolean highlightCompression,
            boolean watermark, boolean aspect169, boolean energySaving,
            ProcessingEventsListener listener, ProcessorBase.ProcessingCallback callback) {
        requireJpegAdmission(batch,rawSaverAtShutter,originalDngAttempted,expectedNormals,referenceTimestamp);
        Iris26983COnBatchPublication.run(app,characteristics,batch,0,expectedNormals,tone,
                clipYFloor,highlightCompression,watermark,aspect169,energySaving,listener,callback);
    }
}
