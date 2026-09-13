package com.particlesdevs.photoncamera.processing;

import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CaptureRequest;
import android.hardware.camera2.TotalCaptureResult;

import com.particlesdevs.photoncamera.control.GyroBurst;
import com.particlesdevs.photoncamera.processing.parameters.IrisNightFrameSelector;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * IRIS_26552_NIGHT_IMMUTABLE_DYNAMIC_BATCH_OWNER
 *
 * One shutter-frozen, fresh-capture Night batch. Frozen requested SHORT/LONG counts remain
 * immutable provenance, while the exact RAW/result/request pairs actually delivered by Camera2
 * own processing. Missing HAL deliveries are never fabricated and never force a single-frame
 * fallback. No Motion ZSL/ring/pre-shutter RAW, Photon static IMAGE_BUFFER, or live settings own
 * this batch.
 */
public final class IrisNightBatch {
    public final List<ImageFrame> frames;
    public final List<GyroBurst> gyro;
    public final Map<Long, Double> exposures;
    public final Map<Long, TotalCaptureResult> results;
    public final Map<Long, CaptureRequest> requests;
    public final TotalCaptureResult referenceResult;
    public final CaptureRequest referenceRequest;
    public final CameraCharacteristics characteristics;
    public final int imageFormat;
    public final int rotation;
    public final int frameBudget;
    public final int requestedShortFrames;
    public final int requestedLongFrames;
    public final int shortFrameCount;
    public final int longFrameCount;
    public final boolean degradedBracket;
    public final int saveRaw;
    public final boolean superResEnabled;
    public final boolean heicOutputEnabled;
    public final boolean aspect169;
    public final boolean energySaving;
    public final boolean watermarkEnabled;
    public final boolean binning;
    public final String cameraId;
    public final com.particlesdevs.photoncamera.processing.processor.IrisMotionSettings.Snapshot irisSettings;

    public IrisNightBatch(
            List<ImageFrame> frames,
            List<GyroBurst> gyro,
            Map<Long, Double> exposures,
            Map<Long, TotalCaptureResult> results,
            Map<Long, CaptureRequest> requests,
            CameraCharacteristics characteristics,
            int imageFormat,
            int rotation,
            int frameBudget,
            int requestedShortFrames,
            int requestedLongFrames,
            int saveRaw,
            boolean superResEnabled,
            boolean heicOutputEnabled,
            boolean aspect169,
            boolean energySaving,
            boolean watermarkEnabled,
            boolean binning,
            String cameraId,
            com.particlesdevs.photoncamera.processing.processor.IrisMotionSettings.Snapshot irisSettings) {
        if (frames == null || frames.size() < 2)
            throw new IllegalArgumentException("26541 NightBatch requires at least two exact RAW frames");
        if (results == null || requests == null || characteristics == null)
            throw new IllegalArgumentException("26541 NightBatch exact metadata/characteristics are required");
        if (frameBudget < IrisNightFrameSelector.MIN_NIGHT_FRAMES
                || frameBudget > IrisNightFrameSelector.MAX_NIGHT_FRAMES
                || frameBudget != frames.size())
            throw new IllegalArgumentException("26552 NightBatch invalid actual frame budget=" + frameBudget
                    + " frames=" + frames.size());
        if (requestedShortFrames < 2 || requestedLongFrames < 0
                || requestedShortFrames + requestedLongFrames < IrisNightFrameSelector.MIN_NIGHT_FRAMES
                || requestedShortFrames + requestedLongFrames > IrisNightFrameSelector.MAX_NIGHT_FRAMES)
            throw new IllegalArgumentException("26552 NightBatch invalid requested role plan short="
                    + requestedShortFrames + " long=" + requestedLongFrames);

        ArrayList<ImageFrame> ordered = new ArrayList<>(frames);
        ordered.sort(java.util.Comparator.comparingLong(ImageFrame::getTimestamp));
        HashMap<Long, Double> expoCopy = new HashMap<>();
        HashMap<Long, TotalCaptureResult> resultCopy = new HashMap<>();
        HashMap<Long, CaptureRequest> requestCopy = new HashMap<>();
        int shortCount = 0;
        int longCount = 0;
        ImageFrame reference = null;
        for (ImageFrame frame : ordered) {
            if (frame == null || !frame.motionV2PlaneLayoutValid)
                throw new IllegalArgumentException("26541 NightBatch RAW layout missing");
            TotalCaptureResult result = results.get(frame.timestamp);
            CaptureRequest request = requests.get(frame.timestamp);
            if (result == null || request == null)
                throw new IllegalArgumentException("26541 NightBatch exact metadata missing timestamp=" + frame.timestamp);
            Long resultTimestamp = result.get(android.hardware.camera2.CaptureResult.SENSOR_TIMESTAMP);
            if (resultTimestamp == null || resultTimestamp.longValue() != frame.timestamp)
                throw new IllegalArgumentException("26541 NightBatch timestamp mismatch image=" + frame.timestamp
                        + " result=" + resultTimestamp);
            if (frame.motionV2ActualExposureNs <= 0L || frame.motionV2ActualIso <= 0
                    || !frame.motionV2NoiseProfileValid || !frame.motionV2BlackLevelValid
                    || !frame.motionV2WhiteLevelValid)
                throw new IllegalArgumentException("26541 NightBatch exact radiometric metadata missing timestamp=" + frame.timestamp);
            if (frame.motionV2FrameRole == ImageFrame.MotionV2FrameRole.HIGHLIGHT_SHORT)
                throw new IllegalArgumentException("26541 Night never admits Motion HIGHLIGHT_SHORT role");
            if (frame.motionV2FrameRole == ImageFrame.MotionV2FrameRole.SHADOW_LONG) {
                longCount++;
            } else if (frame.motionV2FrameRole == ImageFrame.MotionV2FrameRole.NORMAL) {
                shortCount++;
                if (reference == null) reference = frame;
            } else {
                throw new IllegalArgumentException("26541 Night unknown frame role=" + frame.motionV2FrameRole);
            }
            expoCopy.put(frame.timestamp, frame.motionV2ExposureEnergy);
            resultCopy.put(frame.timestamp, result);
            requestCopy.put(frame.timestamp, request);
        }
        if (shortCount < 2 || reference == null)
            throw new IllegalArgumentException("26554 Night requires at least two exact delivered SHORT/reference frames; got=" + shortCount);
        if (shortCount + longCount != frameBudget)
            throw new IllegalArgumentException("26554 Night delivered role total mismatch short="
                    + shortCount + " long=" + longCount + " budget=" + frameBudget);
        if (shortCount > requestedShortFrames || longCount > requestedLongFrames)
            throw new IllegalArgumentException("26554 Night delivered roles exceed frozen request: short="
                    + shortCount + "/" + requestedShortFrames + " long=" + longCount + "/" + requestedLongFrames);
        final double referenceEnergy = reference.motionV2ExposureEnergy;
        for (ImageFrame frame : ordered) {
            if (frame.motionV2FrameRole == ImageFrame.MotionV2FrameRole.SHADOW_LONG
                    && !(frame.motionV2ExposureEnergy > referenceEnergy))
                throw new IllegalArgumentException("26541 Night SHADOW_LONG is not above SHORT reference energy");
        }

        this.frames = Collections.unmodifiableList(ordered);
        this.gyro = Collections.unmodifiableList(new ArrayList<>(gyro == null ? Collections.emptyList() : gyro));
        this.exposures = Collections.unmodifiableMap(expoCopy);
        this.results = Collections.unmodifiableMap(resultCopy);
        this.requests = Collections.unmodifiableMap(requestCopy);
        this.referenceResult = resultCopy.get(reference.timestamp);
        this.referenceRequest = requestCopy.get(reference.timestamp);
        this.characteristics = characteristics;
        this.imageFormat = imageFormat;
        this.rotation = rotation;
        this.frameBudget = frameBudget;
        this.requestedShortFrames = requestedShortFrames;
        this.requestedLongFrames = requestedLongFrames;
        this.shortFrameCount = shortCount;
        this.longFrameCount = longCount;
        this.degradedBracket = shortCount != requestedShortFrames || longCount != requestedLongFrames;
        this.saveRaw = saveRaw;
        this.superResEnabled = superResEnabled;
        if (superResEnabled && heicOutputEnabled)
            throw new IllegalArgumentException("26636 Night HEIC must never coexist with Super Res");
        this.heicOutputEnabled = heicOutputEnabled;
        this.aspect169 = aspect169;
        this.energySaving = energySaving;
        this.watermarkEnabled = watermarkEnabled;
        this.binning = binning;
        this.cameraId = cameraId == null ? "0" : cameraId;
        if (irisSettings == null || irisSettings.customNoiseModelEnabled)
            throw new IllegalArgumentException("26541 NightBatch requires exact-Camera2 Iris settings");
        this.irisSettings = irisSettings;
    }
}
