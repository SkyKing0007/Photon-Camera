package com.particlesdevs.photoncamera.processing.processor;

import android.hardware.camera2.CameraCharacteristics;
import android.util.Range;

import com.particlesdevs.photoncamera.api.CameraMode;
import com.particlesdevs.photoncamera.api.ParseExif;
import com.particlesdevs.photoncamera.capture.CaptureController;
import com.particlesdevs.photoncamera.control.GyroBurst;
import com.particlesdevs.photoncamera.control.IrisZoomController;
import com.particlesdevs.photoncamera.processing.ImageFrame;
import com.particlesdevs.photoncamera.processing.ImagePath;
import com.particlesdevs.photoncamera.processing.IrisNightBatch;
import com.particlesdevs.photoncamera.processing.ProcessingEventsListener;
import com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector;
import com.particlesdevs.photoncamera.util.Log;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

/**
 * IRIS_26903_NIGHT_B_ISOLATED_SNAPSHOT_ADAPTER.
 * The selected Night B capture is a fresh post-shutter, N NORMAL, one-exposure RAW batch.
 * This class alone reuses the working Motion/B processor with an explicit immutable Night B
 * context. There is NO global mode override, no Motion ZSL takeover, no Night A mutation,
 * and no Spektra camera/session operation. All paths fail closed.
 */
public final class IrisNightBProcessor26903 {
    private static final String TAG = "IrisNightBProcessor26903";
    private IrisNightBProcessor26903() { }

    public static void process(IrisNightBatch batch, ProcessingEventsListener listener) {
        boolean handedToHdrx = false;
        CaptureController.isProcessing = true;
        try {
            if (batch == null || !batch.experimentB || batch.nightBZoom == null
                    || batch.irisSettings == null || batch.nightBDngOptions == null
                    || batch.frames.size() != batch.frameBudget || batch.frameBudget < 2
                    || batch.longFrameCount != 0 || batch.requestedLongFrames != 0
                    || batch.shortFrameCount != batch.frameBudget
                    || batch.imageFormat != CaptureController.RAW_FORMAT
                    || batch.referenceResult == null || batch.referenceRequest == null) {
                throw new IllegalStateException("26903 Night B requires frozen N NORMAL Camera2 RAWs");
            }
            final IrisZoomController.ZoomSnapshot zoom = batch.nightBZoom;
            /* The existing Night cameraId is logical for some vendor physical cameras.
             * The owner-vs-physical proof is performed at the actual shutter in
             * CaptureController, never compare physical ID to logical Camera2 ID. */
            final List<ImageFrame> frozen = batch.frames;
            final int width = frozen.get(0).motionV2PlaneLogicalWidth;
            final int height = frozen.get(0).motionV2PlaneLogicalHeight;
            if (width <= 0 || height <= 0) {
                throw new IllegalStateException("26903 invalid logical RAW dimensions");
            }
            Range<Long> expoBounds = batch.characteristics.get(
                    CameraCharacteristics.SENSOR_INFO_EXPOSURE_TIME_RANGE);
            Range<Integer> isoBounds = batch.characteristics.get(
                    CameraCharacteristics.SENSOR_INFO_SENSITIVITY_RANGE);
            Integer analogMax = batch.characteristics.get(
                    CameraCharacteristics.SENSOR_MAX_ANALOG_SENSITIVITY);
            if (expoBounds == null || isoBounds == null) {
                throw new IllegalStateException("26903 missing physical sensor exposure/ISO bounds");
            }
            long baseExposure = frozen.get(0).motionV2ActualExposureNs;
            int baseIso = frozen.get(0).motionV2ActualIso;
            if (baseExposure <= 0 || baseIso <= 0)
                throw new IllegalStateException("26903 invalid Night B exposure authority");
            ArrayList<ImageFrame> inputs = new ArrayList<>(frozen);
            ArrayList<IsoExpoSelector.ExpoPair> pairs = new ArrayList<>();
            ArrayList<GyroBurst> gyro = new ArrayList<>();
            HashMap<Long, Double> exposure = new HashMap<>();
            for (int i = 0; i < inputs.size(); i++) {
                ImageFrame frame = inputs.get(i);
                if (frame.motionV2FrameRole != ImageFrame.MotionV2FrameRole.NORMAL
                        || !"B".equals(frame.motionV2ReconstructionExperiment26856)
                        || !frame.motionV2PlaneLayoutValid
                        || frame.motionV2PlaneLogicalWidth != width
                        || frame.motionV2PlaneLogicalHeight != height
                        || frame.motionV2ActualExposureNs != baseExposure
                        || frame.motionV2ActualIso != baseIso
                        || !batch.results.containsKey(frame.timestamp)
                        || !batch.requests.containsKey(frame.timestamp)) {
                    throw new IllegalStateException("26903 Night B mixed capture/geometry/ISO/exposure " + i);
                }
                exposure.put(frame.timestamp, frame.motionV2ExposureEnergy);
                pairs.add(new IsoExpoSelector.ExpoPair(frame.motionV2ActualExposureNs,
                        expoBounds.getLower(), expoBounds.getUpper(),
                        frame.motionV2ActualIso, isoBounds.getLower(), isoBounds.getUpper(),
                        analogMax == null ? isoBounds.getLower() : analogMax));
                GyroBurst frameGyro = !batch.gyro.isEmpty()
                        ? batch.gyro.get(i % batch.gyro.size()) : frame.frameGyro;
                gyro.add(frameGyro != null ? frameGyro.clone() : new GyroBurst(1));
            }
            if (inputs.get(0).buffer == null) {
                throw new IllegalStateException("26903 reference RAW must remain in memory");
            }
            final HdrxProcessor processor = new HdrxProcessor(listener);
            processor.configure(batch.nightBAlignAlgorithm, batch.saveRaw, CameraMode.MOTION);
            processor.configureIris26903NightB(batch.irisSettings,
                    batch.watermarkEnabled, batch.aspect169, batch.energySaving);
            Log.i(TAG, "IRIS_26903_NIGHT_B_PROCESS_ENTRY n=" + inputs.size()
                    + " iso=" + baseIso + " exposureNs=" + baseExposure
                    + " localZoom=" + zoom.outputLocalZoom
                    + " sr=" + batch.superResEnabled + " raw=" + batch.saveRaw
                    + " independentDng=true jinAfterB=true");
            handedToHdrx = true;
            processor.startMotion(ImagePath.newDNGFilePath(),
                    ImagePath.newImageFilePath(),
                    ParseExif.parse(batch.referenceResult, batch.referenceRequest),
                    gyro, inputs, exposure, batch.imageFormat, batch.rotation,
                    batch.characteristics, batch.referenceResult, batch.referenceRequest,
                    pairs, null, zoom.globalZoom, zoom.opticalAnchor, zoom.outputLocalZoom,
                    zoom.hardwareLocalZoom, zoom.residualSoftwareZoom,
                    batch.superResEnabled, batch.heicOutputEnabled,
                    false, /* permanent 26704 global-tone-only policy, no live preference reread */
                    batch.nightBDngOptions,
                    new ProcessorBase.ProcessingCallback() {
                        @Override public void onStarted() { }
                        @Override public void onFailed() { }
                        @Override public void onFinished() { }
                    });
        } catch (Throwable failure) {
            Log.e(TAG, "IRIS_26903_NIGHT_B_SETUP_FAILED", failure);
            if (!handedToHdrx) listener.onProcessingError(
                    failure.getClass().getSimpleName() + ": " + String.valueOf(failure.getMessage()));
        } finally {
            // The Hdrx B normal path consumes its own carriers. RAW backing is idempotent:
            // Hdrx may already have consumed/closed some frames and this closes any spooled tail.
            if (batch != null && batch.frames != null) for (ImageFrame frame : batch.frames) {
                if (frame != null) try { frame.close(); } catch (Throwable ignored) { }
            }
            CaptureController.isProcessing = false;
        }
    }
}
