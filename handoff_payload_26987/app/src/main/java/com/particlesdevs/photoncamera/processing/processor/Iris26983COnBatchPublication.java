package com.particlesdevs.photoncamera.processing.processor;

import android.content.Context;
import android.hardware.camera2.CameraCharacteristics;
import com.hinnka.mycamera.processor.GlesIris26983COnMotionIngress;
import com.hinnka.mycamera.processor.Iris26985CLinearOutput;
import com.particlesdevs.photoncamera.api.ParseExif;
import com.particlesdevs.photoncamera.processing.ImageFrame;
import com.particlesdevs.photoncamera.processing.ImagePath;
import com.particlesdevs.photoncamera.processing.MotionBatch;
import com.particlesdevs.photoncamera.processing.ProcessingEventsListener;
import com.particlesdevs.photoncamera.util.Log;
import java.nio.file.Files;
import java.nio.file.Path;

/** C ON single reconstruction / output transaction. Raw ownership remains here until all consumers finish. */
public final class Iris26983COnBatchPublication {
    private static final String TAG="Iris26985COnBatch";
    private Iris26983COnBatchPublication() {}
    public static void run(Context app, CameraCharacteristics characteristics, MotionBatch batch,
            int rawSaver, int expectedNormals, IrisMotionSettings.Snapshot tone, float clipYFloor,
            boolean highlightCompression, boolean watermark, boolean aspect169, boolean energySaving,
            ProcessingEventsListener listener, ProcessorBase.ProcessingCallback callback) {
        boolean started=false, savedJpeg=false, savedDng=false;
        Path jpeg=null,dng=null;
        Iris26985CLinearOutput linear=null;
        try {
            if(app==null || characteristics==null || batch==null || tone==null || listener==null || callback==null ||
                    !Float.isFinite(clipYFloor) || clipYFloor<=0f)
                throw new IllegalArgumentException("26985 missing C ON capture context");
            long reference=Iris26983COnCapturePreparation.chooseReference(batch);
            Iris26983COnPhotoPublication.requireAdmission(batch,rawSaver,expectedNormals,reference);
            String stem=ImagePath.newImageFilePath().toAbsolutePath().toString();
            String candidate=stem;int collision=0;
            while(Files.exists(java.nio.file.Paths.get(candidate+".jpg")) || Files.exists(java.nio.file.Paths.get(candidate+".dng")))
                candidate=stem+"_"+(++collision);
            dng=rawSaver>=1?java.nio.file.Paths.get(candidate+".dng"):null;
            jpeg=rawSaver!=2?java.nio.file.Paths.get(candidate+".jpg"):null;
            ParseExif.ExifData exif=ParseExif.parse(batch.referenceResult,batch.referenceRequest);
            // C ON consumes the original capture-owned metadata. ApplyRes rewrites the
            // live global CaptureResult, not this immutable reference; do not call it here.
            exif.IMAGE_DESCRIPTION=null;
            Iris26983COnCapturePreparation.Prepared prepared=Iris26983COnCapturePreparation.prepare(characteristics,batch);
            if(prepared.referenceTimestamp!=reference)throw new IllegalStateException("26985 reference changed");
            linear=new Iris26985CLinearOutput(app,characteristics,batch,dng);
            started=true;callback.onStarted();listener.onProcessingStarted("HDRX");
            boolean success=GlesIris26983COnMotionIngress.executeFrozenMotion(app,batch,expectedNormals,
                prepared.referenceTimestamp,prepared.parameters,tone,clipYFloor,highlightCompression,watermark,
                aspect169,energySaving,jpeg,exif,linear);
            savedDng=linear.getDngSaved();
            if(jpeg!=null) savedJpeg=success && Files.isRegularFile(jpeg) && Files.size(jpeg)>0L;
            if((dng!=null&&!savedDng)||(jpeg!=null&&!savedJpeg)) throw new IllegalStateException("26985 C ON output failed");
            try {listener.onProcessingFinished(rawSaver==2?"Motion stacked RAW Processing Finished":"HdrX JPG Processing Finished");}
            catch(RuntimeException detached){Log.w(TAG,"finish notification",detached);}
        } catch(Exception failure) {
            throw new IllegalStateException("26985 C ON output transaction failed",failure);
        } finally {
            if(linear!=null)savedDng=linear.getDngSaved();
            if(jpeg!=null && !savedJpeg)try{Files.deleteIfExists(jpeg);}catch(Exception failure){Log.w(TAG,"JPEG cleanup",failure);}
            if(dng!=null)try{listener.notifyImageSavedStatus(savedDng,dng);}catch(RuntimeException detached){Log.w(TAG,"DNG notification",detached);}
            if(jpeg!=null)try{listener.notifyImageSavedStatus(savedJpeg,jpeg);}catch(RuntimeException detached){Log.w(TAG,"JPEG notification",detached);}
            if(batch!=null)for(ImageFrame frame:batch.frames)try{frame.close();}catch(RuntimeException failure){Log.w(TAG,"RAW cleanup",failure);}
            try{if(batch!=null && batch.shortHighlightSlot!=null)batch.shortHighlightSlot.sealAndClose();}
            finally{if(started){if((dng==null||savedDng)&&(jpeg==null||savedJpeg))callback.onFinished();else callback.onFailed();}}
        }
    }
}
