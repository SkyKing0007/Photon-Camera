#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse

ROOT: Path

def fail(msg: str):
    raise SystemExit("ERROR: " + msg)

def one(src: str, old: str, new: str, label: str) -> str:
    n = src.count(old)
    if n != 1:
        fail(f"{label}: expected one anchor, found {n}")
    return src.replace(old, new, 1)

def edit(rel: str, fn):
    p = ROOT / rel
    if not p.is_file():
        fail(f"missing {rel}")
    before = p.read_text()
    after = fn(before)
    if after == before:
        fail(f"{rel}: transform made no change")
    p.write_text(after)
    print("CHANGED", rel)

LONG_OWNER = r'''
    /* IRIS_26505_PHYSICAL_LONG_BRACKET_OWNER
     * One intentional +EV RAW observation shares the already-existing isolated
     * ShadowAuxSlot owned by this Motion generation. It never enters the equal-
     * exposure Wronski frame list. Camera2 onCaptureStarted/result/Image timestamps
     * are the only identity authority; there is no nearest-frame borrowing.
     */
    private static final double MOTION_26505_LONG_TARGET_EV = 2.5;
    private static final double MOTION_26505_LONG_TARGET_MULTIPLIER =
            5.656854249492381;
    private static final long MOTION_26505_LONG_PREFERRED_MAX_EXPOSURE_NS =
            10_000_000L;
    private static final int MOTION_26505_LONG_FALLBACK_MAX_ISO = 800;
    private static final double MOTION_26505_LONG_MIN_ACTUAL_RATIO = 1.15;
    private static final double MOTION_26505_LONG_REQUEST_TOLERANCE_EV = 0.40;
    private static final String MOTION_26505_LONG_TAG = "IRIS_26505_SHADOW_LONG";

    private static final class Motion26505LongTicket {
        final com.particlesdevs.photoncamera.processing.MotionBatch.ShadowAuxSlot slot;
        private final java.util.ArrayDeque<ImageFrame> stagedRaw =
                new java.util.ArrayDeque<>();
        private static final int MAX_STAGED_RAW = 4;
        volatile boolean requested = false;
        volatile boolean completed = false;
        volatile long captureStartedTimestampNs = 0L;
        volatile long captureStartedFrameNumber = -1L;
        volatile long resultTimestampNs = 0L;
        volatile long actualExposureNs = 0L;
        volatile int actualIso = 0;
        volatile double actualEnergy = 0.0;
        double baselineEnergy = 0.0;

        Motion26505LongTicket(
                com.particlesdevs.photoncamera.processing.MotionBatch.ShadowAuxSlot slot) {
            this.slot = slot;
        }
        long expectedTimestampNs() {
            return resultTimestampNs > 0L
                    ? resultTimestampNs : captureStartedTimestampNs;
        }
        synchronized void stage(ImageFrame frame) {
            if (frame == null) return;
            if (slot == null || slot.isSealed() || slot.hasFrame()) {
                try { frame.close(); } catch (Throwable ignored) {}
                return;
            }
            while (stagedRaw.size() >= MAX_STAGED_RAW) {
                ImageFrame old = stagedRaw.pollFirst();
                if (old != null) try { old.close(); } catch (Throwable ignored) {}
            }
            stagedRaw.addLast(frame);
        }
        synchronized ImageFrame takeStaged(long timestampNs) {
            java.util.Iterator<ImageFrame> it = stagedRaw.iterator();
            while (it.hasNext()) {
                ImageFrame frame = it.next();
                if (frame != null && frame.timestamp == timestampNs) {
                    it.remove();
                    return frame;
                }
            }
            return null;
        }
        synchronized int stagedCount() { return stagedRaw.size(); }
        synchronized void closeStaged() {
            while (!stagedRaw.isEmpty()) {
                ImageFrame frame = stagedRaw.pollFirst();
                if (frame != null) try { frame.close(); } catch (Throwable ignored) {}
            }
        }
    }
    private volatile Motion26505LongTicket mMotion26505CaptureLongTicket = null;
    private volatile boolean mMotion26505LongRequested = false;

    private void clearMotion26505LongTicket(
            Motion26505LongTicket ticket, String reason) {
        if (ticket == null) return;
        boolean cleared = false;
        synchronized (mZslBufferLock) {
            if (mMotion26505CaptureLongTicket == ticket) {
                mMotion26505CaptureLongTicket = null;
                cleared = true;
            }
        }
        Log.d(TAG, "IRIS_26505_LONG_TICKET_CLEAR"
                + " reason=" + reason
                + " cleared=" + cleared
                + " slotHasFrame=" + (ticket.slot != null && ticket.slot.hasFrame())
                + " slotSealed=" + (ticket.slot != null && ticket.slot.isSealed()));
    }
'''

LONG_LISTENER = r'''
                /* IRIS_26505_LONG_RAW_EXACT_CALLBACK_OWNERSHIP
                 * The intentional Long-A request is physically outside the normal ZSL
                 * exposure group. CaptureStarted/Image timestamp equality owns the role.
                 * Copy/stage before the historical capture-state close just like Short-A.
                 */
                Motion26505LongTicket iris26505LongTicket = mMotion26505CaptureLongTicket;
                final long iris26505RawTimestamp = img.getTimestamp();
                final long iris26505ExpectedLongTimestamp = iris26505LongTicket == null
                        ? 0L : iris26505LongTicket.expectedTimestampNs();
                final boolean iris26505ExactLongRawOwned = iris26505LongTicket != null
                        && iris26505ExpectedLongTimestamp > 0L
                        && iris26505RawTimestamp == iris26505ExpectedLongTimestamp;
                boolean iris26505LongCandidateCopied =
                        stageMotion26505LongRawCandidate(iris26505LongTicket, img);
                if (iris26505ExactLongRawOwned) {
                    Log.i(TAG, "IRIS_26505_LONG_RAW_EXACT_CALLBACK_OWNERSHIP"
                            + " rawTimestamp=" + iris26505RawTimestamp
                            + " expectedTimestamp=" + iris26505ExpectedLongTimestamp
                            + " stagedOrDelivered=" + iris26505LongCandidateCopied
                            + " slotSealed=" + iris26505LongTicket.slot.isSealed()
                            + " normalRingAdmission=false");
                    img.close();
                    return;
                }
'''

LONG_METHODS = r'''
    private ImageFrame copyMotion26505LongFrame(
            Image img, TotalCaptureResult result) {
        if (img == null) return null;
        int rowStride = img.getPlanes()[0].getRowStride();
        int pixelStride = img.getPlanes()[0].getPixelStride();
        int width = (img.getFormat() == ImageFormat.RAW10)
                ? img.getWidth()
                : (pixelStride > 0 ? rowStride / pixelStride : img.getWidth());
        int height = img.getHeight();
        int bufCapacity = img.getPlanes()[0].getBuffer().capacity();
        int offset = 0;
        if (PhotonCamera.getSettings().aspect169 && width > height) {
            height = width * 9 / 16;
            int offsetH = (img.getHeight() - height) / 2;
            offsetH -= offsetH % 2;
            offset = rowStride * offsetH;
            bufCapacity = rowStride * height;
        }
        Allocator.binning = PhotonCamera.getSettings().binning;
        ImageFrame frame = new ImageFrame(
                img.getPlanes()[0].getBuffer(), img.getFormat(),
                width, rowStride, offset, bufCapacity);
        frame.timestamp = img.getTimestamp();
        frame.width = PhotonCamera.getSettings().binning ? width / 2 : width;
        frame.height = PhotonCamera.getSettings().binning ? height / 2 : height;
        populateMotion26480FrameMetadata(frame, result, false);
        frame.motionV2ShortHighlightFrame = false;
        frame.motionV2FrameRole = ImageFrame.MotionV2FrameRole.NORMAL;
        return frame;
    }

    private boolean tryDeliverMotion26505StagedLongRaw(
            Motion26505LongTicket ticket, TotalCaptureResult exactResult) {
        if (ticket == null || ticket.slot == null || ticket.slot.isSealed()
                || ticket.slot.hasFrame() || ticket.resultTimestampNs <= 0L) {
            if (ticket != null && ticket.slot != null && ticket.slot.isSealed()) {
                ticket.closeStaged();
            }
            return false;
        }
        ImageFrame staged = ticket.takeStaged(ticket.resultTimestampNs);
        if (staged == null) {
            Log.d(TAG, "IRIS_26505_LONG_STAGED_EXACT_MISS"
                    + " resultTimestamp=" + ticket.resultTimestampNs
                    + " staged=" + ticket.stagedCount()
                    + " nearestFallback=false");
            return false;
        }
        populateMotion26480FrameMetadata(staged, exactResult, false);
        staged.motionV2ShortHighlightFrame = false;
        staged.motionV2FrameRole = ImageFrame.MotionV2FrameRole.NORMAL;
        staged.motionV2ActualExposureNs = ticket.actualExposureNs;
        staged.motionV2ActualIso = ticket.actualIso;
        staged.motionV2ExposureEnergy = ticket.actualEnergy;
        boolean accepted = ticket.slot.offer(staged);
        ticket.closeStaged();
        if (accepted) {
            clearMotion26505LongTicket(ticket, "staged_exact_delivery");
        }
        Log.i(TAG, "IRIS_26505_LONG_STAGED_DELIVERY"
                + " accepted=" + accepted
                + " timestamp=" + ticket.resultTimestampNs
                + " exactTimestampEquality=true exactMetadata=true"
                + " normalAccumulatorAdmission=false");
        return accepted;
    }

    private boolean stageMotion26505LongRawCandidate(
            Motion26505LongTicket ticket, Image img) {
        if (ticket == null || img == null || !ticket.requested
                || ticket.slot == null || ticket.slot.isSealed()
                || ticket.slot.hasFrame()) return false;
        long ts = img.getTimestamp();
        long identityTimestamp = ticket.expectedTimestampNs();
        /* IRIS_26505_LONG_STAGE_REQUIRES_CAPTURE_STARTED_IDENTITY
         * Do not even copy an unrelated normal/Short RAW while the Long request is
         * waiting for onCaptureStarted. A Long candidate exists only after Camera2
         * has published its exact sensor timestamp and this Image equals it.
         */
        if (identityTimestamp <= 0L || ts != identityTimestamp) return false;
        if (ticket.completed && ticket.resultTimestampNs <= 0L) return false;

        TotalCaptureResult exact;
        synchronized (mZslBufferLock) { exact = mZslResultMap.get(ts); }
        ImageFrame copy;
        try {
            copy = copyMotion26505LongFrame(img, exact);
        } catch (Throwable t) {
            Log.w(TAG, "IRIS_26505_LONG_STAGE_COPY_SKIPPED timestamp=" + ts
                    + " reason=" + t.getClass().getSimpleName());
            return false;
        }
        if (copy == null) return false;

        if (ticket.resultTimestampNs > 0L
                && copy.timestamp == ticket.resultTimestampNs
                && exact != null) {
            populateMotion26480FrameMetadata(copy, exact, false);
            copy.motionV2ShortHighlightFrame = false;
            copy.motionV2FrameRole = ImageFrame.MotionV2FrameRole.NORMAL;
            copy.motionV2ActualExposureNs = ticket.actualExposureNs;
            copy.motionV2ActualIso = ticket.actualIso;
            copy.motionV2ExposureEnergy = ticket.actualEnergy;
            boolean accepted = ticket.slot.offer(copy);
            ticket.closeStaged();
            if (accepted) clearMotion26505LongTicket(ticket, "raw_callback_direct_delivery");
            Log.i(TAG, "IRIS_26505_LONG_RAW_CALLBACK_DIRECT_DELIVERY"
                    + " accepted=" + accepted
                    + " timestamp=" + ts
                    + " exactTimestampEquality=true exactResultAlreadyKnown=true"
                    + " normalAccumulatorAdmission=false");
            return true;
        }

        ticket.stage(copy);
        Log.d(TAG, "IRIS_26505_LONG_RAW_STAGED timestamp=" + ts
                + " staged=" + ticket.stagedCount()
                + " expectedTimestamp=" + ticket.expectedTimestampNs()
                + " awaitingExactResultTimestamp=" + (ticket.resultTimestampNs <= 0L)
                + " imageReaderObjectRetained=false");
        return true;
    }

    /* IRIS_26505_PHYSICAL_LONG_BRACKET
     * Bjzhou-consistency principle, adapted without replacing Wronski: request one
     * separate longer RAW around +2.5 EV in exposure energy. Prefer shutter up to
     * ~10 ms (or the already-longer base shutter), then ISO. Actual CaptureResult
     * metadata, not requested metadata, decides admission. The request never gates
     * the shutter and the frame can only enter ShadowAuxSlot.
     */
    private boolean applyMotion26505ExplicitLongCaptureIfUseful(
            @NonNull Motion26505LongTicket ticket) {
        if (ticket == null || ticket.slot == null || !isZslMode()
                || mCaptureSession == null || mCameraDevice == null
                || mImageReaderRaw == null || mCameraCharacteristics == null
                || mPreviewCaptureResult == null || mMotion26380RawSampleCount < 64) {
            return false;
        }
        Long baseExpObj = mPreviewCaptureResult.get(CaptureResult.SENSOR_EXPOSURE_TIME);
        Integer baseIsoObj = mPreviewCaptureResult.get(CaptureResult.SENSOR_SENSITIVITY);
        Long previewTs = mPreviewCaptureResult.get(CaptureResult.SENSOR_TIMESTAMP);
        if (baseExpObj == null || baseExpObj <= 0L || baseIsoObj == null || baseIsoObj <= 0
                || previewTs == null) return false;
        long rawAgeNs = mMotion26380RawSignalTimestampNs <= 0L
                ? Long.MAX_VALUE : Math.abs(previewTs - mMotion26380RawSignalTimestampNs);
        if (rawAgeNs > 180_000_000L) return false;

        boolean manual = false;
        int[] caps = mCameraCharacteristics.get(
                CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES);
        if (caps != null) for (int c : caps) {
            if (c == CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES_MANUAL_SENSOR) {
                manual = true; break;
            }
        }
        if (!manual) return false;

        final long baseExp = baseExpObj;
        final int baseIso = baseIsoObj;
        ticket.baselineEnergy = ExposureIndex.time2sec(baseExp) * baseIso;
        if (!(ticket.baselineEnergy > 0.0)) return false;

        android.util.Range<Long> er = mCameraCharacteristics.get(
                CameraCharacteristics.SENSOR_INFO_EXPOSURE_TIME_RANGE);
        android.util.Range<Integer> sr = mCameraCharacteristics.get(
                CameraCharacteristics.SENSOR_INFO_SENSITIVITY_RANGE);
        if (er == null || sr == null) return false;

        double targetEnergy = ticket.baselineEnergy * MOTION_26505_LONG_TARGET_MULTIPLIER;
        long maxLongExp = Math.min(er.getUpper(),
                Math.max(MOTION_26505_LONG_PREFERRED_MAX_EXPOSURE_NS, baseExp));
        maxLongExp = Math.max(er.getLower(), maxLongExp);
        long reqExp = Math.round(baseExp * MOTION_26505_LONG_TARGET_MULTIPLIER);
        reqExp = Math.max(er.getLower(), Math.min(maxLongExp, reqExp));

        int isoUpper = Math.min(sr.getUpper(),
                Math.max(baseIso, MOTION_26505_LONG_FALLBACK_MAX_ISO));
        int reqIso = (int)Math.round(targetEnergy
                / Math.max(ExposureIndex.time2sec(reqExp), 1.0e-12));
        reqIso = Math.max(sr.getLower(), Math.min(isoUpper, reqIso));
        long recomputedExp = Math.round(
                targetEnergy / Math.max(reqIso, 1) * 1_000_000_000.0);
        reqExp = Math.max(er.getLower(), Math.min(maxLongExp, recomputedExp));

        final double requestedEnergy = ExposureIndex.time2sec(reqExp) * reqIso;
        final double requestedRatio = requestedEnergy / ticket.baselineEnergy;
        if (!(requestedEnergy > ticket.baselineEnergy * MOTION_26505_LONG_MIN_ACTUAL_RATIO)) {
            Log.w(TAG, "IRIS_26505_LONG_REQUEST_NO_PHYSICAL_GAIN"
                    + " baselineEnergy=" + ticket.baselineEnergy
                    + " targetEnergy=" + targetEnergy
                    + " requestedEnergy=" + requestedEnergy
                    + " requestedRatio=" + requestedRatio
                    + " requestedExposureNs=" + reqExp
                    + " requestedIso=" + reqIso);
            return false;
        }

        final double tol = Math.pow(2.0, MOTION_26505_LONG_REQUEST_TOLERANCE_EV);
        final double requestedRatioMin = requestedRatio / tol;
        final double requestedRatioMax = requestedRatio * tol;
        final long requestedExp = reqExp;
        final int requestedIso = reqIso;

        try {
            CaptureRequest.Builder b = mCameraDevice.createCaptureRequest(
                    CameraDevice.TEMPLATE_STILL_CAPTURE);
            b.addTarget(mImageReaderRaw.getSurface());
            b.setTag(MOTION_26505_LONG_TAG);
            if (mPreviewAFMode >= 0) b.set(CaptureRequest.CONTROL_AF_MODE, mPreviewAFMode);
            if (Float.isFinite(mFocus) && mFocus >= 0.0f) {
                try { b.set(CaptureRequest.LENS_FOCUS_DISTANCE, mFocus); }
                catch (IllegalArgumentException ignored) {}
            }
            b.set(CaptureRequest.CONTROL_AE_MODE, CaptureRequest.CONTROL_AE_MODE_OFF);
            b.set(CaptureRequest.SENSOR_EXPOSURE_TIME, requestedExp);
            b.set(CaptureRequest.SENSOR_SENSITIVITY, requestedIso);
            try { VendorTagUtils.builderSessionApply(
                    b, true, useMaximumResolutionKey, physicalID); }
            catch (Throwable e) {
                Log.w(TAG, "IRIS_26505 long vendor tags skipped "
                        + e.getClass().getSimpleName());
            }

            ticket.requested = true;
            mMotion26505LongRequested = true;
            mCaptureSession.capture(b.build(), new CameraCaptureSession.CaptureCallback() {
                @Override public void onCaptureStarted(@NonNull CameraCaptureSession session,
                        @NonNull CaptureRequest request, long timestamp, long frameNumber) {
                    ticket.captureStartedTimestampNs = timestamp;
                    ticket.captureStartedFrameNumber = frameNumber;
                    Log.i(TAG, "IRIS_26505_LONG_CAPTURE_STARTED_IDENTITY"
                            + " sensorTimestamp=" + timestamp
                            + " frameNumber=" + frameNumber
                            + " exactImageTimestampContract=true");
                }
                @Override public void onCaptureCompleted(@NonNull CameraCaptureSession session,
                        @NonNull CaptureRequest request, @NonNull TotalCaptureResult result) {
                    Long ts = result.get(CaptureResult.SENSOR_TIMESTAMP);
                    Long exp = result.get(CaptureResult.SENSOR_EXPOSURE_TIME);
                    Integer iso = result.get(CaptureResult.SENSOR_SENSITIVITY);
                    if (ts != null) {
                        synchronized (mZslBufferLock) {
                            mZslResultMap.put(ts, result);
                            while (mZslResultMap.size() > MAX_ZSL_RESULT_METADATA) {
                                Long oldest = Collections.min(mZslResultMap.keySet());
                                mZslResultMap.remove(oldest);
                            }
                        }
                    }
                    ticket.completed = true;
                    if (ts == null || exp == null || exp <= 0L || iso == null || iso <= 0) {
                        ticket.closeStaged();
                        clearMotion26505LongTicket(ticket, "missing_actual_metadata");
                        return;
                    }
                    double energy = ExposureIndex.time2sec(exp) * iso;
                    double ratio = energy / ticket.baselineEnergy;
                    boolean accepted = energy > ticket.baselineEnergy * MOTION_26505_LONG_MIN_ACTUAL_RATIO
                            && ratio >= requestedRatioMin && ratio <= requestedRatioMax;
                    if (accepted) {
                        ticket.resultTimestampNs = ts;
                        ticket.actualExposureNs = exp;
                        ticket.actualIso = iso;
                        ticket.actualEnergy = energy;
                        double actualDeltaEv = Math.log(ratio) / Math.log(2.0);
                        Log.i(TAG, "IRIS_26505_LONG_ACTUAL_ACCEPTED"
                                + " sensorTimestamp=" + ts
                                + " requestedExposureNs=" + requestedExp
                                + " requestedIso=" + requestedIso
                                + " requestedRatio=" + requestedRatio
                                + " actualExposureNs=" + exp
                                + " actualIso=" + iso
                                + " actualRatio=" + ratio
                                + " actualDeltaEv=" + actualDeltaEv
                                + " targetDeltaEv=" + MOTION_26505_LONG_TARGET_EV
                                + " allowedAroundClampedRequest="
                                + requestedRatioMin + ".." + requestedRatioMax
                                + " normalAccumulatorAdmission=false shutterGate=false");
                        tryDeliverMotion26505StagedLongRaw(ticket, result);
                    } else {
                        ticket.closeStaged();
                        clearMotion26505LongTicket(ticket, "actual_exposure_rejected");
                        Log.w(TAG, "IRIS_26505_LONG_ACTUAL_REJECTED"
                                + " ratio=" + ratio
                                + " requestedRatio=" + requestedRatio
                                + " allowed=" + requestedRatioMin + ".." + requestedRatioMax);
                    }
                }
                @Override public void onCaptureFailed(@NonNull CameraCaptureSession session,
                        @NonNull CaptureRequest request,
                        @NonNull android.hardware.camera2.CaptureFailure failure) {
                    ticket.completed = true;
                    ticket.closeStaged();
                    clearMotion26505LongTicket(ticket, "capture_failed");
                    Log.w(TAG, "IRIS_26505_LONG_CAPTURE_FAILED reason=" + failure.getReason());
                }
            }, mBackgroundHandler);
            Log.i(TAG, "IRIS_26505_PHYSICAL_LONG_BRACKET"
                    + " submitted=true rawOnlyTarget=true"
                    + " baseExposureNs=" + baseExp
                    + " baseIso=" + baseIso
                    + " targetEv=" + MOTION_26505_LONG_TARGET_EV
                    + " requestedExposureNs=" + requestedExp
                    + " requestedIso=" + requestedIso
                    + " requestedRatio=" + requestedRatio
                    + " preferredMaxShutterNs=" + MOTION_26505_LONG_PREFERRED_MAX_EXPOSURE_NS
                    + " normalRingCleared=false previewRebuilt=false shutterGate=false");
            if (mBackgroundHandler != null) {
                mBackgroundHandler.postDelayed(() -> {
                    if (ticket.completed || ticket.slot.isSealed() || ticket.slot.hasFrame()) {
                        ticket.closeStaged();
                    }
                }, 1200L);
                mBackgroundHandler.postDelayed(() -> {
                    ticket.closeStaged();
                    clearMotion26505LongTicket(ticket, "terminal_cleanup");
                }, 2500L);
            }
            return true;
        } catch (CameraAccessException | IllegalArgumentException | IllegalStateException e) {
            ticket.completed = true;
            ticket.closeStaged();
            mMotion26505LongRequested = false;
            clearMotion26505LongTicket(ticket, "capture_submit_exception");
            Log.w(TAG, "IRIS_26505_LONG_CAPTURE skipped " + e.getClass().getSimpleName());
            return false;
        }
    }

'''

def capture_controller(src: str) -> str:
    if "IRIS_26505_PHYSICAL_LONG_BRACKET" in src:
        fail("CaptureController already contains 26505")
    anchor = "    private volatile Motion26486ShortTicket mMotion26486CaptureShortTicket = null;\n"
    src = one(src, anchor, anchor + LONG_OWNER, "long owner insertion")

    listener_anchor = (
        "                Motion26486ShortTicket iris26489ShortTicket = "
        "mMotion26486CaptureShortTicket;\n")
    src = one(src, listener_anchor, LONG_LISTENER + listener_anchor,
              "long RAW listener ownership")

    methods_anchor = "    /* IRIS_26486_NONBLOCKING_SHORT_HIGHLIGHT_TICKET\n"
    src = one(src, methods_anchor, LONG_METHODS + methods_anchor,
              "long methods before Short-A")

    trigger_old = '''        final Motion26486ShortTicket iris26486ShortTicket = new Motion26486ShortTicket();
        mMotion26486CaptureShortTicket = iris26486ShortTicket;
        final boolean iris26480ShortHighlightRequested =
                applyMotion26486ExplicitShortCaptureIfNeeded(iris26486ShortTicket);
'''
    trigger_new = '''        mMotion26505LongRequested = false;
        Motion26505LongTicket iris26505PreviousLongTicket = mMotion26505CaptureLongTicket;
        if (iris26505PreviousLongTicket != null) {
            iris26505PreviousLongTicket.closeStaged();
            clearMotion26505LongTicket(iris26505PreviousLongTicket, "new_generation");
        }
        final Motion26486ShortTicket iris26486ShortTicket = new Motion26486ShortTicket();
        mMotion26486CaptureShortTicket = iris26486ShortTicket;
        final boolean iris26480ShortHighlightRequested =
                applyMotion26486ExplicitShortCaptureIfNeeded(iris26486ShortTicket);
        final Motion26505LongTicket iris26505LongTicket = new Motion26505LongTicket(
                iris26486ShortTicket.slot.shadowAuxSlot);
        mMotion26505CaptureLongTicket = iris26505LongTicket;
        final boolean iris26505LongRequested =
                applyMotion26505ExplicitLongCaptureIfUseful(iris26505LongTicket);
        if (!iris26505LongRequested) {
            clearMotion26505LongTicket(iris26505LongTicket, "not_requested");
        }
'''
    src = one(src, trigger_old, trigger_new, "Long-A trigger")

    old = "            boolean brighter = !normalEligible && !taggedShort && exact && preShutter\n"
    new = "            boolean brighter = !mMotion26505LongRequested\n                    && !normalEligible && !taggedShort && exact && preShutter\n"
    src = one(src, old, new, "intentional long preempts opportunistic shadow scan")

    trace_old = '''                        + " iris26480ShortHighlightRequested="
                        + iris26480ShortHighlightRequested
'''
    trace_new = '''                        + " iris26480ShortHighlightRequested="
                        + iris26480ShortHighlightRequested
                        + " iris26505LongRequested="
                        + iris26505LongRequested
'''
    src = one(src, trace_old, trace_new, "top-up trace long role")
    return src

LOW_SUPPORT_SHADER = r'''precision highp float;
precision highp int;

uniform highp sampler2D referenceCfa;
uniform ivec2 rawSize;
uniform ivec2 packedSize;
uniform int cfaPattern;
uniform float wbR;
uniform float wbG;
uniform float wbB;
out vec4 Output;

/* IRIS_26505_LOW_SUPPORT_PPG_REFERENCE
 * Motion-local fallback derived from the edge-directed PPG kernel used by the
 * current bjzhou/darktable RCD path. It reads only the immutable Wronski
 * reference CFA. No alternate unaligned frame, temporal blur or generated RGB
 * is permitted. The final normalizer decides whether this observation is used
 * from true local frame-equivalent support.
 */
const int RED=0;
const int GREEN=1;
const int BLUE=2;

int colorAt(ivec2 p){
    int r=p.y&1,c=p.x&1;
    if(cfaPattern==0){
        if(r==0)return c==0?RED:GREEN;
        return c==0?GREEN:BLUE;
    }else if(cfaPattern==1){
        if(r==0)return c==0?GREEN:RED;
        return c==0?BLUE:GREEN;
    }else if(cfaPattern==2){
        if(r==0)return c==0?GREEN:BLUE;
        return c==0?RED:GREEN;
    }
    if(r==0)return c==0?BLUE:GREEN;
    return c==0?GREEN:RED;
}
float rawAt(ivec2 p){
    p=clamp(p,ivec2(0),rawSize-ivec2(1));
    ivec2 q=clamp(p/2,ivec2(0),packedSize-ivec2(1));
    int phase=((p.y&1)<<1)|(p.x&1);
    return max(texelFetch(referenceCfa,q,0)[phase],0.0);
}
float ppgGreenAt(ivec2 center){
    int ownColor=colorAt(center);
    float pc=rawAt(center);
    if(ownColor==GREEN)return pc;
    float pym=rawAt(center+ivec2(0,-1));
    float pym2=rawAt(center+ivec2(0,-2));
    float pym3=rawAt(center+ivec2(0,-3));
    float pyM=rawAt(center+ivec2(0, 1));
    float pyM2=rawAt(center+ivec2(0, 2));
    float pyM3=rawAt(center+ivec2(0, 3));
    float pxm=rawAt(center+ivec2(-1,0));
    float pxm2=rawAt(center+ivec2(-2,0));
    float pxm3=rawAt(center+ivec2(-3,0));
    float pxM=rawAt(center+ivec2( 1,0));
    float pxM2=rawAt(center+ivec2( 2,0));
    float pxM3=rawAt(center+ivec2( 3,0));
    float guessx=(pxm+pc+pxM)*2.0-pxM2-pxm2;
    float diffx=(abs(pxm2-pc)+abs(pxM2-pc)+abs(pxm-pxM))*3.0
            +(abs(pxM3-pxM)+abs(pxm3-pxm))*2.0;
    float guessy=(pym+pc+pyM)*2.0-pyM2-pym2;
    float diffy=(abs(pym2-pc)+abs(pyM2-pc)+abs(pym-pyM))*3.0
            +(abs(pyM3-pyM)+abs(pym3-pym))*2.0;
    return max(diffx>diffy
            ?clamp(guessy*0.25,min(pym,pyM),max(pym,pyM))
            :clamp(guessx*0.25,min(pxm,pxM),max(pxm,pxM)),0.0);
}
vec3 ppgColorAt(ivec2 center){
    int ownColor=colorAt(center);
    float pc=rawAt(center);
    float green=ppgGreenAt(center);
    vec3 color=vec3(0.0,green,0.0);
    if(ownColor==RED||ownColor==BLUE){
        ivec2 nw=center+ivec2(-1,-1),ne=center+ivec2(1,-1);
        ivec2 sw=center+ivec2(-1, 1),se=center+ivec2(1, 1);
        float diff1=abs(rawAt(nw)-rawAt(se))
                +abs(ppgGreenAt(nw)-green)+abs(ppgGreenAt(se)-green);
        float guess1=rawAt(nw)+rawAt(se)+2.0*green
                -ppgGreenAt(nw)-ppgGreenAt(se);
        float diff2=abs(rawAt(ne)-rawAt(sw))
                +abs(ppgGreenAt(ne)-green)+abs(ppgGreenAt(sw)-green);
        float guess2=rawAt(ne)+rawAt(sw)+2.0*green
                -ppgGreenAt(ne)-ppgGreenAt(sw);
        float other=diff1>diff2?guess2*0.5:(diff1<diff2?guess1*0.5:(guess1+guess2)*0.25);
        if(ownColor==RED){color.r=pc;color.b=other;}
        else{color.b=pc;color.r=other;}
    }else{
        color.g=pc;
        if(colorAt(center+ivec2(1,0))==RED){
            color.b=(rawAt(center+ivec2(0,-1))+rawAt(center+ivec2(0,1))
                    +2.0*color.g-ppgGreenAt(center+ivec2(0,-1))
                    -ppgGreenAt(center+ivec2(0,1)))*0.5;
            color.r=(rawAt(center+ivec2(-1,0))+rawAt(center+ivec2(1,0))
                    +2.0*color.g-ppgGreenAt(center+ivec2(-1,0))
                    -ppgGreenAt(center+ivec2(1,0)))*0.5;
        }else{
            color.r=(rawAt(center+ivec2(0,-1))+rawAt(center+ivec2(0,1))
                    +2.0*color.g-ppgGreenAt(center+ivec2(0,-1))
                    -ppgGreenAt(center+ivec2(0,1)))*0.5;
            color.b=(rawAt(center+ivec2(-1,0))+rawAt(center+ivec2(1,0))
                    +2.0*color.g-ppgGreenAt(center+ivec2(-1,0))
                    -ppgGreenAt(center+ivec2(1,0)))*0.5;
        }
    }
    return max(color,vec3(0.0));
}
void main(){
    ivec2 p=ivec2(gl_FragCoord.xy);
    if(any(greaterThanEqual(p,rawSize))){Output=vec4(0.0);return;}
    vec3 sensorRgb=ppgColorAt(p);
    vec3 calculationRgb=sensorRgb*max(vec3(wbR,wbG,wbB),vec3(1.0e-6));
    Output=vec4(max(calculationRgb,vec3(0.0)),1.0);
}
'''

def normalizer(src: str) -> str:
    if "IRIS_26504_QUAD_COHERENT_HIGHLIGHT_AUTHORITY" not in src:
        fail("26505 normalizer requires applied 26504 candidate")
    if "IRIS_26505_LOW_SUPPORT_RECONSTRUCTION_AUTHORITY" in src:
        fail("normalizer already contains 26505")
    src = one(src,
              "uniform highp sampler2D frameSupportTexture;\n",
              "uniform highp sampler2D frameSupportTexture;\n"
              "uniform highp sampler2D lowSupportReferenceRgb;\n",
              "low support texture uniform")
    old = '''    vec3 calculationRgb=max(
            vec3(green+rg,green,green+bg),vec3(0.0));

    /* IRIS_26504_POST_LSC_CHROMA_EXHAUSTION */
'''
    new = '''    vec3 calculationRgb=max(
            vec3(green+rg,green,green+bg),vec3(0.0));

    /* IRIS_26505_LOW_SUPPORT_RECONSTRUCTION_AUTHORITY
     * The windy-foliage failure has high global support but local pockets near
     * one effective frame. In those pixels only, prefer an edge-directed RGB
     * observation reconstructed from the immutable reference CFA. At >=3.5
     * effective frames the current multiframe semantic RGB remains untouched.
     */
    vec3 lowSupportReference=max(
            texelFetch(lowSupportReferenceRgb,p,0).rgb,vec3(0.0));
    float lowSupportAuthority=1.0-smoothstep(
            1.50,3.50,max(localFrameSupport,1.0));
    calculationRgb=mix(
            calculationRgb,lowSupportReference,clamp(lowSupportAuthority,0.0,1.0));

    /* IRIS_26504_POST_LSC_CHROMA_EXHAUSTION */
'''
    return one(src, old, new, "low-support authority placement")


def cfa_reconstruction(src: str) -> str:
    if "IRIS_26504_LOCAL_SUPPORT_AND_NOISE_TO_NORMALIZER" not in src:
        fail("26505 CFA host requires applied 26504 candidate")
    if "IRIS_26505_LOW_SUPPORT_PPG_FALLBACK" in src:
        fail("CFA host already contains 26505")

    src = one(src,
              "irisV13ShadowToNormal>=0.25f&&irisV13ShadowToNormal<=0.84f",
              "irisV13ShadowToNormal>=0.15f&&irisV13ShadowToNormal<=0.84f",
              "Long-A +2.5EV host eligibility")
    src = one(src,
              'glProg.setVar("shadowExposureRatio",1.0f/Math.max(irisV13ShadowToNormal,1.0e-6f));glProg.setVar("maxShadowBlend",0.20f);',
              'glProg.setVar("shadowExposureRatio",1.0f/Math.max(irisV13ShadowToNormal,1.0e-6f));glProg.setVar("maxShadowBlend",0.35f);',
              "Long-A bounded blend")

    normalizer_anchor = '                    glProg.useAssetProgram("motionv2/mfsr_spatial_rgb_normalize_26501");\n'
    prep = '''                    /* IRIS_26505_LOW_SUPPORT_PPG_FALLBACK
                     * One GPU-only edge-directed reference reconstruction. It is never a
                     * whole-photo fallback: the final normalizer receives true local frame
                     * support and grants this texture authority only below the 1.5..3.5-frame
                     * transition. The immutable Wronski reference owns all source pixels.
                     */
                    GLTexture iris26505LowSupportReference = new GLTexture(
                            raw,new GLFormat(GLFormat.DataType.FLOAT_16,4),null,
                            GL_NEAREST,GL_CLAMP_TO_EDGE);
                    glProg.useAssetProgram("motionv2/low_support_ppg_reference_26505");
                    glProg.setVar("rawSize",raw);
                    glProg.setVar("packedSize",rawHalf);
                    glProg.setVar("cfaPattern",(int)parameters.cfaPattern);
                    glProg.setVar("wbR",wronskiGlobalWbR);
                    glProg.setVar("wbG",1.0f);
                    glProg.setVar("wbB",wronskiGlobalWbB);
                    glProg.setTexture("referenceCfa",referenceCfa);
                    iris26505LowSupportReference.BufferLoad();
                    glProg.drawBlocks(raw.x,raw.y);
                    android.opengl.GLES30.glBindFramebuffer(
                            android.opengl.GLES30.GL_FRAMEBUFFER,0);
                    Log.i(TAG,"IRIS_26505_LOW_SUPPORT_PPG_FALLBACK"
                            +" source=immutableWronksiReferenceCfa"
                            +" fullFramePass=true"
                            +" visibleAuthorityLocalSupportOnly=true"
                            +" fullAuthorityAtFramesLe=1.5"
                            +" zeroAuthorityAtFramesGe=3.5"
                            +" unalignedFallback=false");
'''
    src = one(src, normalizer_anchor, prep + normalizer_anchor,
              "low-support PPG host pass")

    bind_anchor = '                    glProg.setTexture("frameSupportTexture", currentDirectFrameSupport);\n'
    src = one(src, bind_anchor,
              bind_anchor + '                    glProg.setTexture("lowSupportReferenceRgb", iris26505LowSupportReference);\n',
              "bind low-support reference")

    close_anchor = '''                    android.opengl.GLES30.glBindFramebuffer(android.opengl.GLES30.GL_FRAMEBUFFER, 0);
                    iris26480ReadbackOutput = iris26501RgbOutput;
'''
    close_new = '''                    android.opengl.GLES30.glBindFramebuffer(android.opengl.GLES30.GL_FRAMEBUFFER, 0);
                    iris26505LowSupportReference.close();
                    iris26480ReadbackOutput = iris26501RgbOutput;
'''
    src = one(src, close_anchor, close_new, "close low-support reference")
    return src


def main():
    global ROOT
    ap=argparse.ArgumentParser()
    ap.add_argument("root",type=Path)
    args=ap.parse_args()
    ROOT=args.root

    edit("app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java",
         capture_controller)
    edit("app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl",
         normalizer)
    edit("app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java",
         cfa_reconstruction)

    new_shader=ROOT/"app/src/main/assets/shaders/motionv2/low_support_ppg_reference_26505.glsl"
    if new_shader.exists():
        fail("new low-support shader already exists")
    new_shader.write_text(LOW_SUPPORT_SHADER)
    print("CREATED",new_shader.relative_to(ROOT))

if __name__=="__main__":
    main()
