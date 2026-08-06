package com.particlesdevs.photoncamera.processing;

import android.hardware.camera2.CaptureRequest;
import android.hardware.camera2.CaptureResult;
import android.hardware.camera2.TotalCaptureResult;
import com.particlesdevs.photoncamera.control.GyroBurst;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/** Immutable ownership transfer for one finalized Motion capture. */
public final class MotionBatch {
    public final List<ImageFrame> frames;
    public final List<GyroBurst> gyro;
    public final Map<Long, Double> exposures;
    public final Map<Long, TotalCaptureResult> results;
    public final CaptureResult referenceResult;
    public final CaptureRequest referenceRequest;
    public final int imageFormat;
    public final int rotation;
    public final int candidateCount;
    public final int retainedCount;

    public MotionBatch(List<ImageFrame> frames, List<GyroBurst> gyro,
                       Map<Long, Double> exposures,
                       Map<Long, TotalCaptureResult> results,
                       CaptureResult referenceResult,
                       CaptureRequest referenceRequest,
                       int imageFormat, int rotation, int candidateCount) {
        this.frames = Collections.unmodifiableList(new ArrayList<>(frames));
        this.gyro = Collections.unmodifiableList(new ArrayList<>(gyro));
        this.exposures = Collections.unmodifiableMap(new HashMap<>(exposures));
        this.results = Collections.unmodifiableMap(new HashMap<>(results));
        this.referenceResult = referenceResult;
        this.referenceRequest = referenceRequest;
        this.imageFormat = imageFormat;
        this.rotation = rotation;
        this.candidateCount = Math.max(1, candidateCount);
        this.retainedCount = frames.size();
    }
}
