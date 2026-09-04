package com.particlesdevs.photoncamera.processing;

import android.hardware.camera2.CaptureRequest;
import android.hardware.camera2.CaptureResult;
import android.hardware.camera2.TotalCaptureResult;
import com.particlesdevs.photoncamera.control.GyroBurst;
import com.particlesdevs.photoncamera.control.IrisZoomController;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector;

/** Immutable ownership transfer for one finalized Motion capture. */
public final class MotionBatch {
    /* IRIS_26593_GENERATION_OWNED_SHORT_HIGHLIGHT_SLOT
     * The equal-exposure NORMAL list remains immutable. A required SHORT may arrive
     * asynchronously during capture completion, but 26593 freezes this slot before
     * MotionBatch is handed to processing; reconstruction never races late delivery.
     */
    /* IRIS_26593_SEPARATE_RESERVED_SHADOW_AUX_SLOT
     * A distinct one-shot owner for the explicitly reserved LONG exposure. It is not
     * the SHORT slot and never appears in MotionBatch.frames/NORMAL reconstruction.
     */
    public static final class ShadowAuxSlot {
        private ImageFrame frame;
        private boolean sealed = false;
        public synchronized boolean offer(ImageFrame candidate) {
            if (candidate == null) return false;
            if (sealed || frame != null) {
                try { candidate.close(); } catch (Throwable ignored) {}
                return false;
            }
            frame = candidate;
            notifyAll();
            return true;
        }
        public synchronized ImageFrame takeAndSeal() {
            sealed = true;
            ImageFrame out = frame;
            frame = null;
            return out;
        }
        public synchronized void sealAndClose() {
            sealed = true;
            if (frame != null) {
                try { frame.close(); } catch (Throwable ignored) {}
                frame = null;
            }
        }
        /* IRIS_26593_IMMEDIATE_REQUIRED_AUX_FREEZE */
        private synchronized void freezePresent(boolean expected) {
            if (expected && frame == null) {
                throw new IllegalStateException("26593 expected LONG missing before immutable freeze");
            }
            sealed = true;
            notifyAll();
        }
        public synchronized boolean hasFrame() { return frame != null; }
        public synchronized boolean isSealed() { return sealed; }
    }

    public static final class ShortHighlightSlot {
        public final ShadowAuxSlot shadowAuxSlot = new ShadowAuxSlot();
        private ImageFrame frame;
        private boolean sealed = false;
        public synchronized boolean offer(ImageFrame candidate) {
            if (candidate == null) return false;
            if (sealed || frame != null) {
                try { candidate.close(); } catch (Throwable ignored) {}
                return false;
            }
            frame = candidate;
            notifyAll();
            return true;
        }
        public synchronized ImageFrame takeAndSeal() {
            sealed = true;
            ImageFrame out = frame;
            frame = null;
            return out;
        }
        public synchronized void sealAndClose() {
            sealed = true;
            if (frame != null) {
                try { frame.close(); } catch (Throwable ignored) {}
                frame = null;
            }
            shadowAuxSlot.sealAndClose();
        }
        private boolean frozenShortExpected = false;
        private boolean frozenShadowExpected = false;
        private boolean requiredFreezeComplete = false;
        /* IRIS_26593_IMMUTABLE_REQUIRED_AUX_FREEZE */
        public synchronized void freezePresentAuxiliaries(boolean shortExpected,boolean shadowExpected) {
            if (shortExpected && frame == null) {
                throw new IllegalStateException("26593 expected SHORT missing before immutable freeze");
            }
            frozenShortExpected = shortExpected;
            frozenShadowExpected = shadowExpected;
            sealed = true;
            shadowAuxSlot.freezePresent(shadowExpected);
            requiredFreezeComplete = true;
            notifyAll();
        }
        public synchronized boolean shortWasExpected() { return frozenShortExpected; }
        public synchronized boolean shadowWasExpected() { return frozenShadowExpected; }
        public synchronized boolean requiredFreezeComplete() { return requiredFreezeComplete; }
        public synchronized boolean hasFrame() { return frame != null; }
        public synchronized boolean isSealed() { return sealed; }
    }

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
    public final int processingFrameCount;
    public final int totalFrameCount;
    public final ShortHighlightSlot shortHighlightSlot;
    public final List<IsoExpoSelector.ExpoPair> exposurePairs;
    /* IRIS_26524_SHUTTER_FROZEN_ZOOM_GEOMETRY */
    public final float iris26524GlobalZoom;
    public final float iris26524OpticalZoomAnchor;
    public final float iris26524OutputLocalZoom;
    public final float iris26524HardwareLocalZoom;
    public final float iris26524ResidualSoftwareZoom;
    public final String iris26524OwnerCameraId;
    /* IRIS_26575_MOTION_SUPER_RES_IMMUTABLE_BATCH */
    public final boolean superResEnabled;

    public MotionBatch(List<ImageFrame> frames, List<GyroBurst> gyro,
                       Map<Long, Double> exposures,
                       Map<Long, TotalCaptureResult> results,
                       CaptureResult referenceResult,
                       CaptureRequest referenceRequest,
                       int imageFormat, int rotation, int candidateCount) {
        this(frames, gyro, exposures, results, referenceResult, referenceRequest,
                imageFormat, rotation, candidateCount, new ShortHighlightSlot(), false);
    }

    public MotionBatch(List<ImageFrame> frames, List<GyroBurst> gyro,
                       Map<Long, Double> exposures,
                       Map<Long, TotalCaptureResult> results,
                       CaptureResult referenceResult,
                       CaptureRequest referenceRequest,
                       int imageFormat, int rotation, int candidateCount,
                       ShortHighlightSlot shortHighlightSlot) {
        this(frames, gyro, exposures, results, referenceResult, referenceRequest,
                imageFormat, rotation, candidateCount, shortHighlightSlot, false);
    }

    public MotionBatch(List<ImageFrame> frames, List<GyroBurst> gyro,
                       Map<Long, Double> exposures,
                       Map<Long, TotalCaptureResult> results,
                       CaptureResult referenceResult,
                       CaptureRequest referenceRequest,
                       int imageFormat, int rotation, int candidateCount,
                       ShortHighlightSlot shortHighlightSlot, boolean superResEnabled) {
        this.frames = Collections.unmodifiableList(new ArrayList<>(frames));
        this.gyro = Collections.unmodifiableList(new ArrayList<>(gyro));
        this.exposures = Collections.unmodifiableMap(new HashMap<>(exposures));
        this.results = Collections.unmodifiableMap(new HashMap<>(results));
        this.referenceResult = referenceResult;
        this.referenceRequest = referenceRequest;
        this.imageFormat = imageFormat;
        this.rotation = rotation;
        this.candidateCount = Math.max(1, candidateCount);
        int normalRetained = 0;
        for (ImageFrame frame : this.frames) {
            if (frame != null && !frame.motionV2ShortHighlightFrame) normalRetained++;
        }
        this.retainedCount = normalRetained;
        this.processingFrameCount = this.frames.size();
        this.shortHighlightSlot = shortHighlightSlot == null
                ? new ShortHighlightSlot() : shortHighlightSlot;
        if (this.shortHighlightSlot.requiredFreezeComplete()) {
            int auxiliaryCount = (this.shortHighlightSlot.hasFrame() ? 1 : 0)
                    + (this.shortHighlightSlot.shadowAuxSlot.hasFrame() ? 1 : 0);
            this.totalFrameCount = this.processingFrameCount + auxiliaryCount;
            if (this.totalFrameCount != this.candidateCount) {
                throw new IllegalArgumentException(
                        "26593 exact total-frame contract mismatch requested=" + this.candidateCount
                                + " normal=" + this.processingFrameCount
                                + " auxiliaries=" + auxiliaryCount
                                + " total=" + this.totalFrameCount);
            }
        } else {
            this.totalFrameCount = this.processingFrameCount;
        }
        IrisZoomController.ZoomSnapshot iris26524Zoom = IrisZoomController.snapshot();
        this.iris26524GlobalZoom = iris26524Zoom.globalZoom;
        this.iris26524OpticalZoomAnchor = iris26524Zoom.opticalAnchor;
        this.iris26524OutputLocalZoom = iris26524Zoom.outputLocalZoom;
        this.iris26524HardwareLocalZoom = iris26524Zoom.hardwareLocalZoom;
        this.iris26524ResidualSoftwareZoom = iris26524Zoom.residualSoftwareZoom;
        this.iris26524OwnerCameraId = iris26524Zoom.ownerCameraId;
        this.superResEnabled = superResEnabled;
        ArrayList<IsoExpoSelector.ExpoPair> iris26486Pairs = new ArrayList<>();
        for (ImageFrame frame : this.frames) {
            if (frame == null || frame.motionV2ActualExposureNs <= 0L
                    || frame.motionV2ActualIso <= 0) {
                throw new IllegalArgumentException(
                        "26486 MotionBatch frame missing exact exposure metadata");
            }
            IsoExpoSelector.ExpoPair pair = new IsoExpoSelector.ExpoPair(
                    frame.motionV2ActualExposureNs,
                    IsoExpoSelector.getEXPLOW(), IsoExpoSelector.getEXPHIGH(),
                    frame.motionV2ActualIso,
                    IsoExpoSelector.getISOLOW(), IsoExpoSelector.getISOHIGH(),
                    IsoExpoSelector.getISOAnalog());
            pair.curlayer = IsoExpoSelector.ExpoPair.exposureLayer.Normal;
            pair.layerMpy = 1.0f;
            iris26486Pairs.add(pair);
        }
        this.exposurePairs = Collections.unmodifiableList(iris26486Pairs);
    }
}
