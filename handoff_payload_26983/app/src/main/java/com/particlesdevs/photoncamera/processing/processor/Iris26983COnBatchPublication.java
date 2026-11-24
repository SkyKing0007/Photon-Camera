package com.particlesdevs.photoncamera.processing.processor;

import android.content.Context;
import android.graphics.Point;
import android.hardware.camera2.CameraCharacteristics;
import com.particlesdevs.photoncamera.api.Camera2ApiAutoFix;
import com.particlesdevs.photoncamera.api.ParseExif;
import com.particlesdevs.photoncamera.processing.ImageFrame;
import com.particlesdevs.photoncamera.processing.ImagePath;
import com.particlesdevs.photoncamera.processing.IrisSabreSuperResDngWriter;
import com.particlesdevs.photoncamera.processing.MotionBatch;
import com.particlesdevs.photoncamera.processing.ProcessingEventsListener;
import com.particlesdevs.photoncamera.processing.render.Parameters;
import com.particlesdevs.photoncamera.util.Log;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;

/** Explicit C ON batch owner. DNG borrows immutable NORMAL bytes, never starts B JPEG,
 * and uses the existing shared historical Sabre producer and unchanged writer. */
public final class Iris26983COnBatchPublication {
    private static final String TAG="Iris26983COnBatch";
    private Iris26983COnBatchPublication() {}
    public static void run(Context app, CameraCharacteristics characteristics, MotionBatch batch,
            int rawSaver, int expectedNormals, IrisMotionSettings.Snapshot tone, float clipYFloor,
            boolean highlightCompression, boolean watermark, boolean aspect169, boolean energySaving,
            ProcessingEventsListener listener, ProcessorBase.ProcessingCallback callback) {
        boolean delegated=false, started=false, savedDng=false;
        try {
            if(batch==null || rawSaver<0 || rawSaver>2 || !batch.superResEnabled || batch.heicOutputEnabled ||
                    expectedNormals<1 || batch.candidateCount!=expectedNormals ||
                    batch.frames.size()!=expectedNormals || batch.totalFrameCount!=expectedNormals ||
                    batch.retainedCount!=expectedNormals || batch.shortHighlightSlot==null ||
                    !batch.shortHighlightSlot.requiredFreezeComplete() || batch.shortHighlightSlot.hasFrame() ||
                    batch.shortHighlightSlot.shadowAuxSlot.hasFrame() || batch.shortHighlightSlot.shortWasExpected() ||
                    batch.shortHighlightSlot.shadowWasExpected())
                throw new IllegalArgumentException("26983 invalid C ON frozen batch");
            // B allocates both names before reconstruction, and EXIF before ApplyRes.
            Path dngFile=ImagePath.newDNGFilePath();
            Path imageBase=ImagePath.newImageFilePath();
            ParseExif.ExifData exif=ParseExif.parse(batch.referenceResult,batch.referenceRequest);
            Camera2ApiAutoFix.ApplyRes(batch.referenceResult);
            Iris26983COnCapturePreparation.Prepared prepared=Iris26983COnCapturePreparation.prepare(characteristics,batch);
            started=true; callback.onStarted(); listener.onProcessingStarted("HDRX");
            if(rawSaver>=1) {
                ArrayList<ImageFrame> ordered=new ArrayList<>();
                ImageFrame reference=prepared.frames.get(0).frame;
                for(Iris26983COnCapturePreparation.OrderedFrame entry:prepared.frames) {
                    ImageFrame f=entry.frame;
                    f.frameGyro=entry.gyro;
                    // Preserve B's fallback provenance. The unchanged DNG producer rejects
                    // anything other than per-frame Camera2 noise unless custom model is selected.
                    if(!f.motionV2NoiseProfileValid && reference.motionV2NoiseProfileValid) {
                        System.arraycopy(entry.noise,0,f.motionV2NoiseProfile,0,f.motionV2NoiseProfile.length);
                        f.motionV2NoiseProfileValid=true; f.motionV2NoiseProfileSource="CAMERA2_BASE_FRAME";
                        f.motionV2NoiseS=reference.motionV2NoiseS; f.motionV2NoiseO=reference.motionV2NoiseO;
                    } else if(!f.motionV2NoiseProfileValid) f.motionV2NoiseProfileSource="WRONSKI_EXISTING_FALLBACK";
                    ordered.add(f);
                }
                Parameters p=prepared.parameters;
                savedDng=PhotonMotionMgc1271Bridge.publishCOnDng(new Point(p.rawSize.x,p.rawSize.y),
                    ordered,prepared.referenceTimestamp,p,batch.shortHighlightSlot,originalDng -> {
                        boolean saved=false;
                        try {
                            saved=IrisSabreSuperResDngWriter.write(dngFile,Paths.get(originalDng.getTrue2xLinearRgbPath()),
                                originalDng.getTrue2xWidth(),originalDng.getTrue2xHeight(),p,
                                originalDng.getNormalStackedDngFrameCount(),originalDng.getNormalStackedDngSupportMin(),
                                originalDng.getNormalStackedDngSupportP01(),originalDng.getNormalStackedDngSupportP10(),
                                originalDng.getNormalStackedDngSupportMedian(),originalDng.getNormalStackedDngSupportMean(),
                                originalDng.getNormalStackedDngSupportMax(),originalDng.getNormalStackedDngNoiseEquivalentSupport());
                        } catch(Exception failure) { Log.e(TAG,"C ON shared DNG write failed",failure); }
                        listener.notifyImageSavedStatus(saved,dngFile);
                        return saved;
                    });
                if(rawSaver==2) {
                    if(!savedDng) throw new IllegalStateException("26983 C ON DNG-only write failed");
                    listener.onProcessingFinished("Motion stacked RAW Processing Finished");
                    return;
                }
            }
            Iris26983COnPhotoPublication.requireJpegAdmission(batch,rawSaver,rawSaver==1,
                    expectedNormals,prepared.referenceTimestamp);
            delegated=true;
            Iris26983COnPhotoPublication.runPrepared(app,characteristics,batch,rawSaver,rawSaver==1,
                    expectedNormals,prepared.referenceTimestamp,tone,clipYFloor,highlightCompression,watermark,
                    aspect169,energySaving,listener,callback,imageBase,exif,true);
        } finally {
            if(!delegated) {
                if(batch!=null) for(ImageFrame f:batch.frames) if(f!=null) try{f.close();}catch(RuntimeException e){Log.w(TAG,"RAW cleanup",e);}
                if(batch!=null && batch.shortHighlightSlot!=null) batch.shortHighlightSlot.sealAndClose();
                if(started) { if(rawSaver==2 && savedDng) callback.onFinished(); else callback.onFailed(); }
            }
        }
    }
}
