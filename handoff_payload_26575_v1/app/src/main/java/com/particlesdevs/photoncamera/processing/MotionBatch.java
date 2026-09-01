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
    /* IRIS_26486_ASYNC_SHORT_HIGHLIGHT_SLOT
     * The equal-exposure frames remain immutable. A separately exposed RAW may
     * arrive while the serialized Wronski job is running; it can be offered
     * exactly once until reconstruction reaches the highlight-recovery boundary.
     */
    /* IRIS_26498_V13_SEPARATE_SHADOW_AUX_SLOT
     * A distinct one-shot owner for one brighter pre-shutter RAW. It is not the
     * Short-A slot and never appears in MotionBatch.frames.
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
        /* IRIS_26507_IMMUTABLE_AUX_FREEZE */
        private synchronized void awaitExpectedAndSeal(boolean expected,long deadlineNs) {
            while (expected && frame == null && !sealed) {
                long remainingNs=deadlineNs-System.nanoTime();
                if(remainingNs<=0L) break;
                long millis=remainingNs/1_000_000L;
                int nanos=(int)(remainingNs%1_000_000L);
                try { wait(millis,nanos); } catch (InterruptedException e) {
                    Thread.currentThread().interrupt(); break;
                }
            }
            sealed=true;
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
        /* IRIS_26507_IMMUTABLE_AUX_FREEZE */
        private synchronized void awaitExpectedAndSeal(boolean expected,long deadlineNs) {
            while (expected && frame == null && !sealed) {
                long remainingNs=deadlineNs-System.nanoTime();
                if(remainingNs<=0L) break;
                long millis=remainingNs/1_000_000L;
                int nanos=(int)(remainingNs%1_000_000L);
                try { wait(millis,nanos); } catch (InterruptedException e) {
                    Thread.currentThread().interrupt(); break;
                }
            }
            sealed=true;
            notifyAll();
        }
        /*
         * IRIS_26507_IMMUTABLE_AUX_FREEZE
         * One processing-side deadline for auxiliaries that were actually requested.
         * Shutter acknowledgement already happened; this does not gate capture response.
         * When this returns the slot contents are permanently immutable.
         */
        public void freezeExpectedAuxiliaries(boolean shortExpected,boolean shadowExpected,long timeoutMs) {
            long safeMs=Math.max(0L,Math.min(timeoutMs,120L));
            long deadlineNs=System.nanoTime()+safeMs*1_000_000L;
            awaitExpectedAndSeal(shortExpected,deadlineNs);
            shadowAuxSlot.awaitExpectedAndSeal(shadowExpected,deadlineNs);
        }
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
