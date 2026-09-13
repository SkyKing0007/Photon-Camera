package com.particlesdevs.photoncamera.processing.processor;

import android.graphics.Bitmap;
import android.graphics.Point;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CaptureResult;

import com.particlesdevs.photoncamera.api.ParseExif;
import com.particlesdevs.photoncamera.capture.CaptureController;
import com.particlesdevs.photoncamera.control.GyroBurst;
import com.particlesdevs.photoncamera.processing.ImageFrame;
import com.particlesdevs.photoncamera.processing.ImagePath;
import com.particlesdevs.photoncamera.processing.ImageSaver;
import com.particlesdevs.photoncamera.processing.IrisNightBatch;
import com.particlesdevs.photoncamera.processing.ProcessingEventsListener;
import com.particlesdevs.photoncamera.processing.opengl.postpipeline.PostPipeline;
import com.particlesdevs.photoncamera.processing.render.Parameters;
import com.particlesdevs.photoncamera.processing.ultrahdr.IrisNightUltraHdr;
import com.particlesdevs.photoncamera.util.Allocator;
import com.particlesdevs.photoncamera.util.Log;

import java.nio.ByteBuffer;
import java.nio.file.Path;
import java.util.ArrayList;

/**
 * IRIS_26540_NIGHT_PROCESSOR_SOLE_OWNER
 *
 * Standalone Night processor. It never enters DefaultSaver, HdrxProcessor.Run(),
 * Camera2ApiAutoFix.ApplyRes(), Parameters.FillDynamicParameters(), Photon NoiseModeler,
 * or the legacy Photon Night graph. The immutable IrisNightBatch is the complete authority.
 */
public final class IrisNightProcessor {
    private static final String TAG = "IrisNightProcessor";

    private IrisNightProcessor() {}

    public static void process(IrisNightBatch batch,
                               ProcessingEventsListener listener) {
        final long startNs = System.nanoTime();
        CaptureController.isProcessing = true;
        IrisNightUltraHdr.Prepared iris26550UltraHdr = null;
        boolean iris26550FramesReleased = false;
        String iris26564True2xLinearRgbPathForCleanup = null;
        String iris26564True2xRenderRgbPathForCleanup = null;
        Log.processState(TAG, "NIGHT_PROCESS_ENTRY");
        Log.critical(TAG, "IRIS_26544_NIGHT_PROCESS_ENTRY frames="
                + (batch == null || batch.frames == null ? -1 : batch.frames.size()));
        listener.onProcessingStarted("Iris Night");
        try {
            if (batch == null || batch.characteristics == null || batch.frames.size() < 2) {
                throw new IllegalStateException("26540 Iris Night requires immutable Camera2 batch");
            }
            final CameraCharacteristics characteristics = batch.characteristics;
            final ArrayList<ImageFrame> images = new ArrayList<>(batch.frames);
            images.sort(java.util.Comparator.comparingLong(ImageFrame::getTimestamp));
            final ImageFrame base = images.stream()
                    .filter(f -> f.motionV2FrameRole == ImageFrame.MotionV2FrameRole.NORMAL)
                    .findFirst()
                    .orElseThrow(() -> new IllegalStateException("26541 Night SHORT reference missing"));
            final int width = base.motionV2PlaneLogicalWidth;
            final int height = base.motionV2PlaneLogicalHeight;
            if (width <= 0 || height <= 0) {
                throw new IllegalStateException("26540 Night logical RAW geometry invalid " + width + "x" + height);
            }
            for (int i = 0; i < images.size(); i++) {
                ImageFrame frame = images.get(i);
                if (!frame.motionV2PlaneLayoutValid
                        || frame.motionV2PlaneLogicalWidth != width
                        || frame.motionV2PlaneLogicalHeight != height
                        || frame.irisNightExactCaptureResult == null
                        || frame.irisNightExactCaptureRequest == null
                        || frame.motionV2ResultSensorTimestampNs != frame.timestamp
                        || frame.motionV2ActualExposureNs <= 0L
                        || frame.motionV2ActualIso <= 0
                        || !frame.motionV2NoiseProfileValid
                        || !frame.motionV2BlackLevelValid
                        || !frame.motionV2WhiteLevelValid) {
                    throw new IllegalStateException("26540 Night immutable frame contract failed index=" + i);
                }
                frame.number = i;
                frame.pair = null;
                frame.irisRelativeExposureMpy = (float) (
                        base.motionV2ExposureEnergy / Math.max(1.0e-12, frame.motionV2ExposureEnergy));
                if (!Float.isFinite(frame.irisRelativeExposureMpy) || frame.irisRelativeExposureMpy <= 0.0f)
                    throw new IllegalStateException("26541 Night relative exposure invalid index=" + i);
                if (!batch.gyro.isEmpty()) {
                    frame.frameGyro = batch.gyro.get(i % batch.gyro.size());
                }
            }

            final Parameters p = new Parameters();
            p.FillIrisNightParameters(characteristics, batch.referenceResult,
                    batch.referenceRequest, new Point(width, height), batch);
            p.cameraRotation = batch.rotation;
            p.motionV2WronskiNoiseS = base.motionV2NoiseS;
            p.motionV2WronskiNoiseO = base.motionV2NoiseO;
            p.motionV2StrictWronskiSensorValid = true;
            p.motionV2GlobalZoom = 1.0f;
            p.motionV2OpticalZoomAnchor = 1.0f;
            p.motionV2OutputZoom = 1.0f;
            p.motionV2SpatialReconstructionZoom = 1.0f;
            p.motionV2RenderResidualZoom = 1.0f;
            p.motionV2SuperResOutputEnabled = batch.superResEnabled;
            p.motionV2SuperResOutputScale = batch.superResEnabled ? 2.0f : 1.0f;

            final Path dngFile = ImagePath.newDNGFilePath();
            /* IRIS_26549_NIGHT_EXPLICIT_JPEG_TARGET
             * Dedicated Night owns plain-JPEG publication and must publish to the same explicit
             * .jpg filename contract used by the proven Hdrx/Motion saver.
             */
            final Path imageFile = ImagePath.getNewImageFilePath("jpg");
            final ParseExif.ExifData exif = ParseExif.parse(batch.referenceResult, batch.referenceRequest);
            final long ref = base.getTimestamp();
            Log.i(TAG, "IRIS_26541_NIGHT_12_PLUS_3_DIRECT_PROCESS_ENTRY frames=" + images.size()
                    + " shortActual=" + batch.shortFrameCount + " longActual=" + batch.longFrameCount
                    + " shortRequested=" + batch.requestedShortFrames + " longRequested=" + batch.requestedLongFrames
                    + " frameBudget=" + batch.frameBudget + " exactReferenceTimestamp=" + ref
                    + " referenceRole=SHORT zsl=false motionRing=false preShutterRaw=false"
                    + " staticImageBuffer=false defaultSaver=false hdrxRun=false"
                    + " applyRes=false fillDynamic=false photonNoiseModeler=false"
                    + " superRes=" + batch.superResEnabled);

            final long mergeStartNs = System.nanoTime();
            Log.processState(TAG, "NIGHT_MGC_BEGIN");
            Log.critical(TAG, "IRIS_26544_NIGHT_MGC_BEGIN frames=" + images.size()
                    + " raw=" + width + "x" + height + " saveRaw=" + batch.saveRaw);
            final MotionV2Merger.Result r = PhotonMotionMgc1271Bridge.reconstruct(
                    new Point(width, height), images, ref, p, null, batch.saveRaw >= 1);
            if (r != null) {
                iris26564True2xLinearRgbPathForCleanup = r.true2xLinearRgbPath;
                iris26564True2xRenderRgbPathForCleanup = r.true2xRenderRgbPath;
            }
            final long mergeMs = (System.nanoTime() - mergeStartNs) / 1_000_000L;
            if (r == null || r.raw == null) {
                throw new IllegalStateException("26547 Night Sabre linear-RGB carrier missing");
            }
            if (p.motionV2ReconstructionOwner != Parameters.MOTION_V2_RECONSTRUCTION_SABRE) {
                throw new IllegalStateException("26548 V1.2 Night reconstruction owner is not Sabre owner="
                        + p.motionV2ReconstructionOwner);
            }
            final boolean iris26562NightSuperResRequested = batch.superResEnabled;
            final float iris26562ExpectedOutputScale = iris26562NightSuperResRequested ? 2.0f : 1.0f;
            if (Math.abs(p.motionV2ReconstructionZoom - 1.0f) > 1.0e-5f
                    || Math.abs(p.motionV2SpatialReconstructionZoom - 1.0f) > 1.0e-5f
                    || p.motionV2SuperResOutputEnabled != iris26562NightSuperResRequested
                    || Math.abs(p.motionV2SuperResOutputScale - iris26562ExpectedOutputScale) > 1.0e-5f) {
                throw new IllegalStateException("26562 Night invalid Sabre SR geometry"
                        + " reconstructionZoom=" + p.motionV2ReconstructionZoom
                        + " spatialZoom=" + p.motionV2SpatialReconstructionZoom
                        + " srEnabled=" + p.motionV2SuperResOutputEnabled
                        + " requested=" + iris26562NightSuperResRequested
                        + " outputScale=" + p.motionV2SuperResOutputScale
                        + " expectedOutputScale=" + iris26562ExpectedOutputScale);
            }
            Log.i(TAG, "IRIS_26562_NIGHT_SABRE_SR_EFFECTIVE"
                    + " requested=" + iris26562NightSuperResRequested
                    + " effective=" + p.motionV2SuperResOutputEnabled
                    + " owner=SABRE nativeGrid=true outputScale=" + p.motionV2SuperResOutputScale);
            if (r.inputFrames < images.size()) {
                throw new IllegalStateException("26540 Night MGC scheduled-frame mismatch scheduled="
                        + r.inputFrames + " expectedAtLeast=" + images.size());
            }
            ByteBuffer rgb = r.raw;
            rgb.position(0);
            final long expectedRgbBytes = (long) width * (long) height * 4L * 4L;
            if (rgb.capacity() < expectedRgbBytes) {
                throw new IllegalStateException("26540 Night RGB carrier too small bytes="
                        + rgb.capacity() + " expectedAtLeast=" + expectedRgbBytes);
            }
            if (r.stackedDngRaw16 != null && rgb == r.stackedDngRaw16) {
                throw new IllegalStateException("26540 Night RGB carrier aliases DNG sidecar");
            }
            p.motionV2EffectiveSupport = r.effectiveSupport;
            Log.processState(TAG, "NIGHT_MGC_COMPLETE");
            Log.critical(TAG, "IRIS_26544_NIGHT_MGC_COMPLETE inputFrames=" + r.inputFrames
                    + " effectiveSupport=" + r.effectiveSupport
                    + " rgba32fBytes=" + rgb.capacity());

            if (batch.saveRaw >= 1) {
                Log.processState(TAG, "NIGHT_DNG_BEGIN");
                Log.critical(TAG, "IRIS_26544_NIGHT_DNG_BEGIN path=" + dngFile);
                boolean rawSaved = false;
                try {
                    if (p.motionV2SuperResOutputEnabled && r.true2xLinearRgbPath != null
                            && r.true2xWidth > 0 && r.true2xHeight > 0) {
                        rawSaved = com.particlesdevs.photoncamera.processing.IrisSabreSuperResDngWriter.write(
                                dngFile, java.nio.file.Paths.get(r.true2xLinearRgbPath),
                                r.true2xWidth, r.true2xHeight, p,
                                r.dngStackFrames, r.dngSupportMin, r.dngSupportP01,
                                r.dngSupportP10, r.dngSupportMedian, r.dngSupportMean, r.dngSupportMax,
                                r.dngNoiseEquivalentSupport);
                    } else {
                        if (p.motionV2SuperResOutputEnabled) {
                            Log.critical(TAG, "IRIS_26564_NIGHT_TRUE2X_DNG_MISSING");
                        }
                        if (r.stackedDngRaw16 == null) {
                            throw new IllegalStateException("26540 Night normalized16 DNG sidecar missing");
                        }
                        ByteBuffer dngBayer = r.stackedDngRaw16;
                        dngBayer.position(0);
                        rawSaved = ImageSaver.Util.saveNormalized16StackedRaw(
                                dngFile, dngBayer, p, r.dngNoiseProfile, r.dngStackFrames,
                                r.dngSupportMin, r.dngSupportP01, r.dngSupportP10,
                                r.dngSupportMedian, r.dngSupportMean, r.dngSupportMax,
                                r.dngNoiseEquivalentSupport);
                    }
                } catch (Throwable rawFailure) {
                    Log.e(TAG, "IRIS_26540_NIGHT_DNG_SAVE_FAILED_CONTINUE_JPEG", rawFailure);
                    Log.critical(TAG, "IRIS_26544_NIGHT_DNG_FAILED_CONTINUE_JPEG type="
                            + rawFailure.getClass().getName() + " message="
                            + String.valueOf(rawFailure.getMessage()));
                } finally {
                    if (r.stackedDngRaw16 != null) {
                        try { Allocator.free(r.stackedDngRaw16); } catch (Throwable ignored) {}
                    }
                }
                Log.processState(TAG, "NIGHT_DNG_COMPLETE");
                Log.critical(TAG, "IRIS_26544_NIGHT_DNG_COMPLETE saved=" + rawSaved
                        + " path=" + dngFile);
                listener.notifyImageSavedStatus(rawSaved, dngFile);
                Log.critical(TAG, "IRIS_26544_NIGHT_DNG_NOTIFY_COMPLETE saved=" + rawSaved);
            } else {
                Log.critical(TAG, "IRIS_26544_NIGHT_DNG_SKIPPED saveRaw=" + batch.saveRaw);
            }

            /* IRIS_26634_PHOTOGRAPHIC_EXIF_ONLY: Night diagnostics stay in retained logs,
             * never in JPEG ImageDescription. */
            exif.IMAGE_DESCRIPTION = null;

            final PostPipeline pipeline = new PostPipeline(true);
            Log.processState(TAG, "NIGHT_POST_RGB_BEGIN");
            Log.critical(TAG, "IRIS_26544_NIGHT_POST_RGB_BEGIN dngStageComplete=true");
            final Point crop;
            Bitmap img;
            // IRIS_26546_NIGHT_POST_CARRIER_TRANSFER: PostPipeline now owns rgb before entry.
            // It frees after GPU upload or in its early-failure fallback. Caller clears its pointer
            // first so a native/Java setup failure cannot double-free the direct buffer.
            ByteBuffer postOwnedRgb = rgb;
            rgb = null;
            img = pipeline.RunIrisNightRgb(postOwnedRgb, p);
            crop = pipeline.cropSize == null ? new Point(p.rawSize) : new Point(pipeline.cropSize);
            Log.processState(TAG, "NIGHT_POST_RGB_COMPLETE");
            Log.critical(TAG, "IRIS_26546_NIGHT_POST_RGB_COMPLETE bitmap="
                    + (img == null ? "null" : (img.getWidth() + "x" + img.getHeight()))
                    + " cpuCarrierOwnership=postPipeline");
            Log.i(TAG, "IRIS_26548_NIGHT_RGBA32F_RELEASED_BEFORE_JIN bytes=" + expectedRgbBytes);
            if (android.os.Build.VERSION.SDK_INT >= 34 && img != null
                    && !img.isRecycled() && img.hasGainmap()) {
                throw new IllegalStateException("26550 Night gain map must remain detached before Jin");
            }
            if (android.os.Build.VERSION.SDK_INT >= 34 && pipeline.motionV2GainMapBitmap != null) {
                iris26550UltraHdr = IrisNightUltraHdr.prepare(
                        img, pipeline.motionV2GainMapBitmap,
                        pipeline.motionV2GainMapMaxRatio, p.cameraRotation);
                pipeline.motionV2GainMapBitmap = null;
                Log.critical(TAG, "IRIS_26550_NIGHT_UHDR_PREPARED prepared="
                        + (iris26550UltraHdr != null)
                        + " postJinAttach=true preJinAttach=false");
            }

            final String true2xLinearRgbPath = r.true2xLinearRgbPath;
            final String true2xRenderRgbPath = r.true2xRenderRgbPath;
            final int true2xWidth = r.true2xWidth;
            final int true2xHeight = r.true2xHeight;
            Log.processState(TAG, "NIGHT_BASE_JPEG_BEGIN");
            Log.critical(TAG, "IRIS_26544_NIGHT_BASE_JPEG_BEGIN path=" + imageFile);
            final boolean baseSaved = ImageSaver.Util.saveBitmapAsJPGIrisNightCheckpoint(
                    imageFile, img, ImageSaver.JPG_QUALITY, exif);
            Log.processState(TAG, "NIGHT_BASE_JPEG_COMPLETE_" + baseSaved);
            Log.critical(TAG, "IRIS_26544_NIGHT_BASE_JPEG_COMPLETE saved=" + baseSaved);
            if (baseSaved) {
                // IRIS_26554_NIGHT_CHECKPOINT_NOT_COMPLETION
                // Keep the crash-safe file, but do not scan it or update the gallery thumbnail.
                Log.critical(TAG, "IRIS_26554_NIGHT_BASE_JPEG_CHECKPOINT_ONLY saved=true"
                        + " galleryPublished=false processingComplete=false");
            } else {
                Log.w(TAG, "IRIS_26540_NIGHT_BASE_CHECKPOINT_FAILED continueFinalAttempt=true");
            }

            /* IRIS_26555_NIGHT_JIN_REFERENCE_RESIDUAL_OWNER
             * Sabre/VGN/PostPipeline remains the native-resolution reconstruction authority.
             * Jin sees that one completed RGB image at its reference 512x512 contract and returns
             * the complete learned RGB output. IrisNightNeuralEnhancer transfers only the dense
             * output-input residual back to full resolution; the rejected 32x32 ratio grid is gone.
             * Failure is non-destructive: img remains the completed multiframe base.
             */
            Log.processState(TAG, "NIGHT_JIN_BEGIN");
            final IrisNightNeuralEnhancer.True2xResidual iris26564JinResidual;
            final boolean jinApplied;
            if (true2xRenderRgbPath != null && true2xWidth > 0 && true2xHeight > 0) {
                iris26564JinResidual = IrisNightNeuralEnhancer.enhanceInPlaceForTrue2x(img);
                jinApplied = iris26564JinResidual.applied;
            } else {
                iris26564JinResidual = null;
                jinApplied = IrisNightNeuralEnhancer.enhanceInPlace(img);
            }
            Log.processState(TAG, "NIGHT_JIN_COMPLETE_" + jinApplied);
            Log.critical(TAG, "IRIS_26555_NIGHT_JIN_REFERENCE_RESIDUAL applied=" + jinApplied
                    + " input=postPipelineMergedRgb referenceInference=512x512"
                    + " coarseGrid=false ratioGain=false sabreVgnDetailAuthority=true");
            final boolean iris26550UltraHdrAttached = IrisNightUltraHdr.attachPostJin(
                    img, iris26550UltraHdr);
            iris26550UltraHdr = null;
            Log.processState(TAG, "NIGHT_POST_JIN_ULTRAHDR_" + iris26550UltraHdrAttached);
            Log.critical(TAG, "IRIS_26550_NIGHT_POST_JIN_ULTRAHDR attached="
                    + iris26550UltraHdrAttached
                    + " finalSdrAuthority="
                    + (jinApplied ? "postPipelineJinReferenceResidual" : "postPipelineJinSafeFallback")
                    + " sabreHdrAuthority=true");
            Log.processState(TAG, "NIGHT_FINAL_JPEG_BEGIN");
            Log.critical(TAG, "IRIS_26544_NIGHT_FINAL_JPEG_BEGIN path=" + imageFile);
            final boolean finalSaved = ImageSaver.Util.saveBitmapAsJPGIrisNightAtomicFinal(
                    imageFile, img, ImageSaver.JPG_QUALITY, exif,
                    true2xRenderRgbPath, true2xWidth, true2xHeight, p, crop,
                    pipeline.motionV2ToneSettingsSnapshot, pipeline.motionV2WatermarkEnabled,
                    iris26564JinResidual);
            final boolean imageSaved = finalSaved || baseSaved;
            Log.processState(TAG, "NIGHT_FINAL_JPEG_COMPLETE_" + finalSaved);
            Log.critical(TAG, "IRIS_26544_NIGHT_FINAL_JPEG_COMPLETE finalSaved=" + finalSaved
                    + " imageSaved=" + imageSaved);
            // IRIS_26554_NIGHT_SINGLE_PUBLICATION_OWNER
            // Publish exactly once, after the final attempt. If final UHDR/JPEG-R replacement
            // fails, the crash-safe base may be published only now as an explicit degraded result.
            Log.critical(TAG, "IRIS_26554_NIGHT_FINAL_PUBLICATION_BEGIN finalSaved=" + finalSaved
                    + " baseFallback=" + (!finalSaved && baseSaved) + " saved=" + imageSaved);
            listener.notifyImageSavedStatus(imageSaved, imageFile);
            Log.critical(TAG, "IRIS_26554_NIGHT_FINAL_PUBLICATION_END saved=" + imageSaved);
            if (true2xLinearRgbPath != null) {
                try { java.nio.file.Files.deleteIfExists(java.nio.file.Paths.get(true2xLinearRgbPath)); }
                catch (Throwable ignored) {}
            }
            if (true2xRenderRgbPath != null) {
                try { java.nio.file.Files.deleteIfExists(java.nio.file.Paths.get(true2xRenderRgbPath)); }
                catch (Throwable ignored) {}
            }
            Log.i(TAG, "IRIS_26540_NIGHT_PUBLICATION_OWNERSHIP baseSaved=" + baseSaved
                    + " finalSaved=" + finalSaved + " imageSaved=" + imageSaved
                    + " jinApplied=" + jinApplied + " baseCheckpointOnly=true ultraHdr=" + iris26550UltraHdrAttached
                    + " mergeMs=" + mergeMs
                    + " totalMs=" + ((System.nanoTime() - startNs) / 1_000_000L));
            Log.processState(TAG, "NIGHT_PROCESS_FINISHED_NOTIFY_BEGIN");
            releaseNightFrames(batch);
            iris26550FramesReleased = true;
            CaptureController.isProcessing = false;
            Log.critical(TAG, "IRIS_26550_NIGHT_UI_COMPLETION processing=false"
                    + " framesReleased=true beforeOnProcessingFinished=true imageSaved=" + imageSaved);
            Log.critical(TAG, "IRIS_26544_NIGHT_PROCESS_FINISHED_NOTIFY_BEGIN");
            listener.onProcessingFinished("Iris Night Processing Finished");
            Log.processState(TAG, "NIGHT_PROCESS_COMPLETE");
            Log.critical(TAG, "IRIS_26544_NIGHT_PROCESS_FINISHED_NOTIFY_END");
        } catch (Throwable failure) {
            Log.processState(TAG, "NIGHT_PROCESS_FAILED_" + failure.getClass().getSimpleName());
            Log.e(TAG, "IRIS_26540_NIGHT_PROCESS_FAILED", failure);
            Log.critical(TAG, "IRIS_26544_NIGHT_PROCESS_FAILED type="
                    + failure.getClass().getName() + " message=" + String.valueOf(failure.getMessage()));
            releaseNightFrames(batch);
            iris26550FramesReleased = true;
            CaptureController.isProcessing = false;
            Log.critical(TAG, "IRIS_26550_NIGHT_UI_COMPLETION processing=false"
                    + " framesReleased=true beforeOnProcessingError=true");
            listener.onProcessingError(failure.getClass().getSimpleName() + ": "
                    + String.valueOf(failure.getMessage()));
        } finally {
            IrisNightUltraHdr.release(iris26550UltraHdr);
            if (iris26564True2xLinearRgbPathForCleanup != null) {
                try { java.nio.file.Files.deleteIfExists(java.nio.file.Paths.get(iris26564True2xLinearRgbPathForCleanup)); }
                catch (Throwable ignored) {}
            }
            if (iris26564True2xRenderRgbPathForCleanup != null) {
                try { java.nio.file.Files.deleteIfExists(java.nio.file.Paths.get(iris26564True2xRenderRgbPathForCleanup)); }
                catch (Throwable ignored) {}
            }
            if (!iris26550FramesReleased) {
                releaseNightFrames(batch);
            }
            CaptureController.isProcessing = false;
            Log.critical(TAG, "IRIS_26544_NIGHT_FRAMES_RELEASE_END processing=false");
        }
    }

    private static void releaseNightFrames(IrisNightBatch batch) {
        Log.critical(TAG, "IRIS_26544_NIGHT_FRAMES_RELEASE_BEGIN");
        if (batch != null && batch.frames != null) {
            for (ImageFrame frame : batch.frames) {
                if (frame != null) try { frame.close(); } catch (Throwable ignored) {}
            }
        }
        Log.critical(TAG, "IRIS_26550_NIGHT_FRAMES_RELEASE_COMPLETE");
    }

}
