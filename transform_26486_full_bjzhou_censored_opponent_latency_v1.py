#!/usr/bin/env python3
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: transform_26486_full_bjzhou_censored_opponent_latency_v1.py <candidate-root>")

root = Path(sys.argv[1])
cap = root / "app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java"
batch = root / "app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java"
saver = root / "app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java"
default_saver = root / "app/src/main/java/com/particlesdevs/photoncamera/processing/DefaultSaver.java"
hdrx = root / "app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java"
recon = root / "app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
shader_dir = root / "app/src/main/assets/shaders/motionv2"
accum = shader_dir / "direct_rgb_accumulate.glsl"
refadd = shader_dir / "mfsr_low_support_reference.glsl"
finalize = shader_dir / "mfsr_finalize.glsl"
short_shader = shader_dir / "short_highlight_recover.glsl"


def read(path: Path) -> str:
    if not path.is_file():
        raise SystemExit(f"missing required source {path}")
    return path.read_text()


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def replace_once(path: Path, old: str, new: str, label: str):
    text = read(path)
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    write(path, text.replace(old, new, 1))


def regex_once(path: Path, pattern: str, replacement: str, label: str, flags=re.S):
    text = read(path)
    new, count = re.subn(pattern, replacement, text, count=1, flags=flags)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one regex match, found {count}")
    write(path, new)


def insert_before(path: Path, anchor: str, addition: str, label: str):
    text = read(path)
    count = text.count(anchor)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    write(path, text.replace(anchor, addition + anchor, 1))


def require(path: Path, token: str, label: str):
    if token not in read(path):
        raise SystemExit(f"{label}: missing {token}")


# -------------------------------------------------------------------------
# Exact 26485 lineage gates. 26486 must be a forward transform of the tested
# 26485 candidate, not a replay of an older Motion tree.
# -------------------------------------------------------------------------
for token in (
    "IRIS_26485_FULL_PREBUFFER_AUTHORITATIVE_ZSL",
    "IRIS_26485_FULL_PREBUFFER_IMMEDIATE_PROCESS",
    "IRIS_26484_IMMEDIATE_MOTION_SHUTTER_ACK",
    "IRIS_26481_EXACT_TIMESTAMP_METADATA_OWNERSHIP",
):
    require(cap, token, "26485 capture lineage")
for token in (
    "IRIS_26484_BJZHOU_COUPLED_ALIGNMENT_REJECTION_OPPONENT_MERGE",
    "IRIS_26484_BJZHOU_REFERENCE_OPPONENT_GUIDE_MATCH",
):
    require(recon if "COUPLED" in token else refadd, token, "26485 reconstruction lineage")
require(accum, "IRIS_26484_BJZHOU_COMPLETE_JOINT_OPPONENT_WEIGHTING", "26485 opponent lineage")
require(short_shader, "IRIS_26480_BJZHOU_RCD_OPPOSED_SHORT_HIGHLIGHT_SHADER_V2", "26485 short lineage")


# -------------------------------------------------------------------------
# 1) Capture: requested frame count becomes a strict MAXIMUM. No normal top-up
# wait. Two usable equal-energy RAWs are the minimum; otherwise fail promptly.
# The Motion processing lane stays serialized, but up to two immutable batches
# may be in flight (one processing + one queued).
# -------------------------------------------------------------------------
replace_once(
    cap,
    "    private boolean mMotion26485PrebufferFullAtPress = false;\n",
    "    private boolean mMotion26485PrebufferFullAtPress = false;\n"
    "\n"
    "    /* IRIS_26486_NO_WAIT_MAXIMUM_FRAME_POLICY */\n"
    "    private static final double MOTION_26486_EXPOSURE_HALF_WINDOW_EV = 0.05;\n"
    "    private static final double MOTION_26486_MAX_GROUP_SPAN_EV =\n"
    "            2.0 * MOTION_26486_EXPOSURE_HALF_WINDOW_EV;\n"
    "    private static final int MOTION_26486_MAX_INFLIGHT_BATCHES = 2;\n"
    "    private final java.util.concurrent.atomic.AtomicInteger mMotion26486InFlightBatches =\n"
    "            new java.util.concurrent.atomic.AtomicInteger(0);\n"
    "    private final java.util.concurrent.atomic.AtomicInteger mMotion26486ShortAcquisitions =\n"
    "            new java.util.concurrent.atomic.AtomicInteger(0);\n"
    "\n"
    "    /* One capture-generation ticket. Callback state is ticket-local, so a second\n"
    "     * queued Motion shot cannot overwrite the first shot's highlight metadata. */\n"
    "    private static final class Motion26486ShortTicket {\n"
    "        final com.particlesdevs.photoncamera.processing.MotionBatch.ShortHighlightSlot slot =\n"
    "                new com.particlesdevs.photoncamera.processing.MotionBatch.ShortHighlightSlot();\n"
    "        final java.util.concurrent.atomic.AtomicBoolean headroomReleased =\n"
    "                new java.util.concurrent.atomic.AtomicBoolean(false);\n"
    "        volatile boolean requested = false;\n"
    "        volatile boolean completed = false;\n"
    "        volatile long resultTimestampNs = 0L;\n"
    "        volatile long actualExposureNs = 0L;\n"
    "        volatile int actualIso = 0;\n"
    "        volatile double actualEnergy = 0.0;\n"
    "        double baselineEnergy = 0.0;\n"
    "    }\n"
    "    private volatile Motion26486ShortTicket mMotion26486CaptureShortTicket = null;\n",
    "26486 capture policy fields",
)

replace_once(
    cap,
    "        if (mZslCapturing || CaptureController.isProcessing) {\n"
    "            Log.w(TAG, \"ZSL: capture already in progress, ignoring\");\n"
    "            return;\n"
    "        }",
    "        /* IRIS_26486_BATCH_QUEUE_CAPTURE_OWNERSHIP\n"
    "         * Processing remains single-threaded, but immutable copied RAW batches no\n"
    "         * longer block the Camera2 ring. Bound the queue to one processing + one\n"
    "         * queued shot so memory cannot grow without limit.\n"
    "         */\n"
    "        if (mZslCapturing\n"
    "                || mMotion26486InFlightBatches.get() >= MOTION_26486_MAX_INFLIGHT_BATCHES) {\n"
    "            Log.w(TAG, \"ZSL: capture acquisition/queue already full, ignoring\");\n"
    "            return;\n"
    "        }",
    "26486 Motion trigger queue guard",
)

replace_once(
    cap,
    "        mMotionTopUpMinimumFrames = Math.min(\n"
    "                mMotionTopUpTargetFrames,\n"
    "                Math.max(6, Math.min(8, mMotionTopUpTargetFrames)));",
    "        /* IRIS_26486_NO_SINGLE_FRAME_FALLBACK */\n"
    "        mMotionTopUpMinimumFrames = Math.min(mMotionTopUpTargetFrames, 2);",
    "26486 two-frame minimum",
)

# Replace old short request call with per-shot ticket request.
replace_once(
    cap,
    "        final boolean iris26480ShortHighlightRequested =\n"
    "                applyMotion26480ExplicitShortCaptureIfNeeded();",
    "        final Motion26486ShortTicket iris26486ShortTicket = new Motion26486ShortTicket();\n"
    "        mMotion26486CaptureShortTicket = iris26486ShortTicket;\n"
    "        final boolean iris26480ShortHighlightRequested =\n"
    "                applyMotion26486ExplicitShortCaptureIfNeeded(iris26486ShortTicket);",
    "26486 ticket-local short request",
)

# Do not enter pollMotionTopUp at all from the active Motion shutter path.
replace_once(
    cap,
    "        pollMotionTopUp();\n"
    "    }    // IRIS_26343_GENERATION_SAFE_ZSL",
    "        /* IRIS_26486_FREEZE_BUFFER_AT_SHUTTER_NO_TOPUP_WAIT\n"
    "         * The slider is a maximum. Freeze the best qualifying exposure-energy\n"
    "         * group already in the rolling ring; do not wait for replacement RAWs.\n"
    "         */\n"
    "        int iris26486ReadyNow = countValidMotionFrames();\n"
    "        if (iris26486ReadyNow < 2) {\n"
    "            mMotionTopUpActive = false;\n"
    "            mMotion26486CaptureShortTicket = null;\n"
    "            iris26486ShortTicket.slot.sealAndClose();\n"
    "            com.particlesdevs.photoncamera.util.MotionTrace.finish(\n"
    "                    mMotionDiagnosticShotId, \"BUFFER_NOT_READY_NO_WAIT\",\n"
    "                    \"valid=\" + iris26486ReadyNow + \" minimum=2 waitMs=0\");\n"
    "            recoverMotionCaptureAfterEarlyExit(\n"
    "                    \"BUFFER_NOT_READY_NO_WAIT\", \"Motion buffer preparing\");\n"
    "            return;\n"
    "        }\n"
    "        mMotionTopUpActive = false;\n"
    "        com.particlesdevs.photoncamera.util.MotionTrace.state(\n"
    "                mMotionDiagnosticShotId, \"IRIS_26486_NO_TOP_UP_WAIT\",\n"
    "                \"validAtPress=\" + iris26486ReadyNow\n"
    "                        + \" requestedMaximum=\" + mMotionTopUpTargetFrames\n"
    "                        + \" shortNonBlocking=\" + iris26480ShortHighlightRequested\n"
    "                        + \" normalWaitMs=0\");\n"
    "        finalizeMotionZslCapture();\n"
    "    }    // IRIS_26343_GENERATION_SAFE_ZSL",
    "26486 active no-topup path",
)

# Energy-domain exposure grouping. A +/-0.05 EV representative window proves a
# <=0.10 EV whole-group span, rather than allowing independent shutter/ISO drift.
regex_once(
    cap,
    r"    private boolean motionExposurePairMatches\(\n.*?\n    \}\n\n    /\*\n     \* IRIS_26378_SHADOW_DATA_READINESS",
    "    /* IRIS_26486_EXPOSURE_ENERGY_EV_GROUPING */\n"
    "    private double motion26486ExposureEnergy(TotalCaptureResult result) {\n"
    "        if (result == null) return Double.NaN;\n"
    "        Long exposure = result.get(CaptureResult.SENSOR_EXPOSURE_TIME);\n"
    "        Integer iso = result.get(CaptureResult.SENSOR_SENSITIVITY);\n"
    "        if (exposure == null || iso == null || exposure <= 0L || iso <= 0)\n"
    "            return Double.NaN;\n"
    "        return ((double) exposure) * ((double) iso);\n"
    "    }\n"
    "\n"
    "    private double motion26486ExposureDeltaEv(TotalCaptureResult first,\n"
    "            TotalCaptureResult second) {\n"
    "        double a = motion26486ExposureEnergy(first);\n"
    "        double b = motion26486ExposureEnergy(second);\n"
    "        if (!(a > 0.0) || !(b > 0.0)) return Double.POSITIVE_INFINITY;\n"
    "        return Math.abs(Math.log(a / b) / Math.log(2.0));\n"
    "    }\n"
    "\n"
    "    private boolean motionExposurePairMatches(\n"
    "            TotalCaptureResult first, TotalCaptureResult second) {\n"
    "        return motion26486ExposureDeltaEv(first, second)\n"
    "                <= MOTION_26486_EXPOSURE_HALF_WINDOW_EV;\n"
    "    }\n"
    "\n"
    "    /*\n"
    "     * IRIS_26378_SHADOW_DATA_READINESS",
    "26486 exposure matcher replacement",
)

# Add the independent short-capture implementation immediately before the old
# historical helper. The old helper remains in source for lineage but is no
# longer called by the active shutter path.
short_ticket_code = r'''    /* IRIS_26486_NONBLOCKING_SHORT_HIGHLIGHT_TICKET
     * A short RAW is an optional asynchronous observation. It never gates the
     * normal shutter and its callback state belongs to one Motion generation.
     */
    private boolean applyMotion26486ExplicitShortCaptureIfNeeded(
            @NonNull Motion26486ShortTicket ticket) {
        if (ticket == null || !isZslMode() || mCaptureSession == null
                || mCameraDevice == null || mImageReaderRaw == null
                || mCameraCharacteristics == null || mPreviewCaptureResult == null
                || mMotion26380RawSampleCount < 64
                || Float.isNaN(mMotion26380RawHighlightFraction)) return false;

        Long previewTimestamp = mPreviewCaptureResult.get(CaptureResult.SENSOR_TIMESTAMP);
        Long baseExp = mPreviewCaptureResult.get(CaptureResult.SENSOR_EXPOSURE_TIME);
        Integer baseIso = mPreviewCaptureResult.get(CaptureResult.SENSOR_SENSITIVITY);
        long rawAgeNs = previewTimestamp == null || mMotion26380RawSignalTimestampNs <= 0L
                ? Long.MAX_VALUE : Math.abs(previewTimestamp - mMotion26380RawSignalTimestampNs);
        if (rawAgeNs > 180_000_000L
                || mMotion26380RawHighlightFraction < MOTION_26478_HIGHLIGHT_FRACTION_TRIGGER
                || baseExp == null || baseExp <= 0L || baseIso == null || baseIso <= 0) return false;

        ticket.baselineEnergy = ExposureIndex.time2sec(baseExp) * baseIso;
        try {
            CaptureRequest.Builder b = mCameraDevice.createCaptureRequest(
                    CameraDevice.TEMPLATE_STILL_CAPTURE);
            b.addTarget(mImageReaderRaw.getSurface());
            b.setTag(MOTION_26480_SHORT_TAG);
            if (mPreviewAFMode >= 0) b.set(CaptureRequest.CONTROL_AF_MODE, mPreviewAFMode);
            if (Float.isFinite(mFocus) && mFocus >= 0.0f) {
                try { b.set(CaptureRequest.LENS_FOCUS_DISTANCE, mFocus); }
                catch (IllegalArgumentException ignored) {}
            }

            boolean manual = false;
            int[] caps = mCameraCharacteristics.get(
                    CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES);
            if (caps != null) for (int c : caps) {
                if (c == CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES_MANUAL_SENSOR) {
                    manual = true; break;
                }
            }
            if (!manual) return false;

            long reqExp = Math.max(1L,
                    Math.round(baseExp / MOTION_26480_SHORT_EXPOSURE_DIVISOR));
            int reqIso = baseIso;
            android.util.Range<Long> er = mCameraCharacteristics.get(
                    CameraCharacteristics.SENSOR_INFO_EXPOSURE_TIME_RANGE);
            android.util.Range<Integer> sr = mCameraCharacteristics.get(
                    CameraCharacteristics.SENSOR_INFO_SENSITIVITY_RANGE);
            if (er != null) reqExp = Math.max(er.getLower(), Math.min(er.getUpper(), reqExp));
            if (sr != null) reqIso = Math.max(sr.getLower(), Math.min(sr.getUpper(), reqIso));
            b.set(CaptureRequest.CONTROL_AE_MODE, CaptureRequest.CONTROL_AE_MODE_OFF);
            b.set(CaptureRequest.SENSOR_EXPOSURE_TIME, reqExp);
            b.set(CaptureRequest.SENSOR_SENSITIVITY, reqIso);
            try { VendorTagUtils.builderSessionApply(b, true, useMaximumResolutionKey, physicalID); }
            catch (Throwable e) { Log.w(TAG, "26486 short vendor tags skipped "
                    + e.getClass().getSimpleName()); }

            ticket.requested = true;
            mMotion26486ShortAcquisitions.incrementAndGet();
            final long requestedExp = reqExp;
            final int requestedIso = reqIso;
            mCaptureSession.capture(b.build(), new CameraCaptureSession.CaptureCallback() {
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
                    if (ts == null || exp == null || exp <= 0L || iso == null || iso <= 0
                            || !(ticket.baselineEnergy > 0.0)) return;
                    double energy = ExposureIndex.time2sec(exp) * iso;
                    double ratio = energy / ticket.baselineEnergy;
                    boolean accepted = ratio >= MOTION_26480_SHORT_RATIO_MIN
                            && ratio <= MOTION_26480_SHORT_RATIO_MAX
                            && energy < ticket.baselineEnergy;
                    if (accepted) {
                        ticket.resultTimestampNs = ts;
                        ticket.actualExposureNs = exp;
                        ticket.actualIso = iso;
                        ticket.actualEnergy = energy;
                        Log.i(TAG, "IRIS_26486_SHORT_ACTUAL_ACCEPTED_NONBLOCKING"
                                + " requestedExposureNs=" + requestedExp
                                + " requestedIso=" + requestedIso
                                + " actualExposureNs=" + exp + " actualIso=" + iso
                                + " ratio=" + ratio + " shutterGate=false");
                        scheduleMotion26486ShortDelivery(ticket);
                    } else {
                        Log.w(TAG, "IRIS_26486_SHORT_ACTUAL_REJECTED ratio=" + ratio);
                    }
                }
                @Override public void onCaptureFailed(@NonNull CameraCaptureSession session,
                        @NonNull CaptureRequest request,
                        @NonNull android.hardware.camera2.CaptureFailure failure) {
                    ticket.completed = true;
                    Log.w(TAG, "IRIS_26486_SHORT_CAPTURE_FAILED reason=" + failure.getReason());
                }
            }, mBackgroundHandler);
            Log.i(TAG, "IRIS_26486_SHORT_CAPTURE_SUBMITTED_NONBLOCKING"
                    + " rawOnlyTarget=true shutterGate=false normalRingCleared=false");
            if (mBackgroundHandler != null) {
                mBackgroundHandler.postDelayed(() -> releaseMotion26486ShortHeadroom(ticket), 600L);
            }
            return true;
        } catch (CameraAccessException | IllegalArgumentException | IllegalStateException e) {
            ticket.completed = true;
            Log.w(TAG, "IRIS_26486_SHORT_CAPTURE skipped " + e.getClass().getSimpleName());
            releaseMotion26486ShortHeadroom(ticket);
            return false;
        }
    }

    private void releaseMotion26486ShortHeadroom(Motion26486ShortTicket ticket) {
        if (ticket != null && ticket.headroomReleased.compareAndSet(false, true)) {
            int left = mMotion26486ShortAcquisitions.decrementAndGet();
            if (left < 0) mMotion26486ShortAcquisitions.set(0);
        }
    }

    private ImageFrame copyMotion26486ShortFrame(Image img, TotalCaptureResult result) {
        if (img == null) return null;
        int rowStride = img.getPlanes()[0].getRowStride();
        int pixelStride = img.getPlanes()[0].getPixelStride();
        int width = (img.getFormat() == ImageFormat.RAW10)
                ? img.getWidth() : (pixelStride > 0 ? rowStride / pixelStride : img.getWidth());
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
        ImageFrame frame = new ImageFrame(img.getPlanes()[0].getBuffer(), img.getFormat(),
                width, rowStride, offset, bufCapacity);
        frame.timestamp = img.getTimestamp();
        frame.width = PhotonCamera.getSettings().binning ? width / 2 : width;
        frame.height = PhotonCamera.getSettings().binning ? height / 2 : height;
        long exp = 0L; int iso = 0;
        if (result != null) {
            Long e = result.get(CaptureResult.SENSOR_EXPOSURE_TIME);
            Integer s = result.get(CaptureResult.SENSOR_SENSITIVITY);
            if (e != null) exp = e;
            if (s != null) iso = s;
        }
        frame.motionV2ActualExposureNs = exp;
        frame.motionV2ActualIso = iso;
        frame.motionV2ExposureEnergy = exp > 0L && iso > 0
                ? ExposureIndex.time2sec(exp) * iso : 0.0;
        populateMotion26480FrameMetadata(frame, result, true);
        return frame;
    }

    private void tryDeliverMotion26486ShortRaw(Motion26486ShortTicket ticket) {
        if (ticket == null || ticket.slot.isSealed() || ticket.slot.hasFrame()
                || ticket.resultTimestampNs <= 0L) return;
        Image found = null;
        TotalCaptureResult result = null;
        synchronized (mZslBufferLock) {
            java.util.Iterator<Image> it = mZslRingBuffer.iterator();
            while (it.hasNext()) {
                Image im = it.next();
                if (im != null && Math.abs(im.getTimestamp() - ticket.resultTimestampNs)
                        <= MOTION_26481_SHORT_TIMESTAMP_TOLERANCE_NS) {
                    found = im; it.remove();
                    result = mZslResultMap.get(im.getTimestamp());
                    break;
                }
            }
        }
        if (found == null) return;
        try {
            ImageFrame frame = copyMotion26486ShortFrame(found, result);
            boolean accepted = ticket.slot.offer(frame);
            Log.i(TAG, "IRIS_26486_SHORT_ASYNC_DELIVERY"
                    + " accepted=" + accepted
                    + " timestamp=" + (frame == null ? -1L : frame.timestamp)
                    + " processingMayAlreadyBeRunning=true");
        } finally {
            found.close();
        }
    }

    private void scheduleMotion26486ShortDelivery(Motion26486ShortTicket ticket) {
        if (ticket == null || mBackgroundHandler == null) return;
        final long[] delays = new long[]{0L, 20L, 60L, 140L, 260L, 420L};
        for (long delay : delays) {
            mBackgroundHandler.postDelayed(() -> tryDeliverMotion26486ShortRaw(ticket), delay);
        }
    }

'''
insert_before(
    cap,
    "    private boolean applyMotion26480ExplicitShortCaptureIfNeeded() {",
    short_ticket_code,
    "26486 nonblocking short ticket helpers",
)

# Ring headroom is independent of the legacy global short flag.
replace_once(
    cap,
    "                                    + (mMotion26480ShortRequested ? 2 : 0),",
    "                                    + ((mMotion26480ShortRequested\n"
    "                                            || mMotion26486ShortAcquisitions.get() > 0) ? 2 : 0),",
    "26486 asynchronous short ring headroom",
)

# Finalization owns this acquisition ticket exactly once.
replace_once(
    cap,
    "    private void finalizeMotionZslCapture() {\n",
    "    private void finalizeMotionZslCapture() {\n"
    "        final Motion26486ShortTicket iris26486ShortTicket = mMotion26486CaptureShortTicket;\n"
    "        mMotion26486CaptureShortTicket = null;\n",
    "26486 finalization ticket transfer",
)

# Identify a short frame by its request tag as well as historical timestamp state.
replace_once(
    cap,
    "            boolean iris26480IsShort =\n"
    "                    mMotion26480ShortResultTimestampNs > 0L\n"
    "                            && Math.abs(img.getTimestamp()\n"
    "                                    - mMotion26480ShortResultTimestampNs) <= MOTION_26481_SHORT_TIMESTAMP_TOLERANCE_NS;",
    "            boolean iris26486TaggedShort = frameResult != null\n"
    "                    && frameResult.getRequest() != null\n"
    "                    && MOTION_26480_SHORT_TAG.equals(frameResult.getRequest().getTag());\n"
    "            boolean iris26480IsShort = iris26486TaggedShort\n"
    "                    || (iris26486ShortTicket != null\n"
    "                            && iris26486ShortTicket.resultTimestampNs > 0L\n"
    "                            && Math.abs(img.getTimestamp()\n"
    "                                    - iris26486ShortTicket.resultTimestampNs)\n"
    "                                    <= MOTION_26481_SHORT_TIMESTAMP_TOLERANCE_NS)\n"
    "                    || (mMotion26480ShortResultTimestampNs > 0L\n"
    "                            && Math.abs(img.getTimestamp()\n"
    "                                    - mMotion26480ShortResultTimestampNs)\n"
    "                                    <= MOTION_26481_SHORT_TIMESTAMP_TOLERANCE_NS);",
    "26486 short request-tag ownership",
)

# Enforce the whole selected normal group span and no single-frame fallback.
replace_once(
    cap,
    "        int actualCount = selected.size();\n",
    "        int actualCount = selected.size();\n"
    "        /* IRIS_26486_WHOLE_GROUP_EXPOSURE_SPAN_PROOF */\n"
    "        if (actualCount < 2) {\n"
    "            for (ImageFrame f : selected) if (f != null) f.close();\n"
    "            if (iris26480ShortFrame != null) iris26480ShortFrame.close();\n"
    "            if (iris26486ShortTicket != null) iris26486ShortTicket.slot.sealAndClose();\n"
    "            recoverMotionCaptureAfterEarlyExit(\"INSUFFICIENT_EQUAL_ENERGY_GROUP\",\n"
    "                    \"Motion buffer preparing\");\n"
    "            return;\n"
    "        }\n"
    "        double iris26486MinEnergy = Double.POSITIVE_INFINITY;\n"
    "        double iris26486MaxEnergy = 0.0;\n"
    "        for (ImageFrame f : selected) {\n"
    "            if (f != null && f.motionV2ExposureEnergy > 0.0) {\n"
    "                iris26486MinEnergy = Math.min(iris26486MinEnergy, f.motionV2ExposureEnergy);\n"
    "                iris26486MaxEnergy = Math.max(iris26486MaxEnergy, f.motionV2ExposureEnergy);\n"
    "            }\n"
    "        }\n"
    "        double iris26486SpanEv = iris26486MinEnergy > 0.0 && iris26486MaxEnergy >= iris26486MinEnergy\n"
    "                ? Math.log(iris26486MaxEnergy / iris26486MinEnergy) / Math.log(2.0)\n"
    "                : Double.POSITIVE_INFINITY;\n"
    "        com.particlesdevs.photoncamera.util.MotionTrace.state(\n"
    "                mMotionDiagnosticShotId, \"IRIS_26486_EXPOSURE_GROUP_SPAN\",\n"
    "                \"frames=\" + actualCount + \" minEnergy=\" + iris26486MinEnergy\n"
    "                        + \" maxEnergy=\" + iris26486MaxEnergy\n"
    "                        + \" spanEv=\" + iris26486SpanEv\n"
    "                        + \" maxAllowedEv=\" + MOTION_26486_MAX_GROUP_SPAN_EV);\n"
    "        if (!(iris26486SpanEv <= MOTION_26486_MAX_GROUP_SPAN_EV + 1.0e-4)) {\n"
    "            for (ImageFrame f : selected) if (f != null) f.close();\n"
    "            if (iris26480ShortFrame != null) iris26480ShortFrame.close();\n"
    "            if (iris26486ShortTicket != null) iris26486ShortTicket.slot.sealAndClose();\n"
    "            recoverMotionCaptureAfterEarlyExit(\"EXPOSURE_GROUP_SPAN_REJECTED\",\n"
    "                    \"Motion exposure changed\");\n"
    "            return;\n"
    "        }\n",
    "26486 whole-group exposure span proof",
)

# Short observation belongs to the asynchronous batch slot, never to the normal
# processing frame list and never to the Wronski equal-exposure loop.
replace_once(
    cap,
    "        List<ImageFrame> iris26480ProcessingFrames = new ArrayList<>(selected);\n"
    "        if (iris26480ShortFrame != null) {\n"
    "            iris26480ProcessingFrames.add(iris26480ShortFrame);\n"
    "        }",
    "        final com.particlesdevs.photoncamera.processing.MotionBatch.ShortHighlightSlot\n"
    "                iris26486ShortSlot = iris26486ShortTicket != null\n"
    "                        ? iris26486ShortTicket.slot\n"
    "                        : new com.particlesdevs.photoncamera.processing.MotionBatch.ShortHighlightSlot();\n"
    "        if (iris26480ShortFrame != null) {\n"
    "            long iris26486ShortTs = iris26480ShortFrame.timestamp;\n"
    "            iris26486ShortSlot.offer(iris26480ShortFrame);\n"
    "            mExposures.remove(iris26486ShortTs);\n"
    "            selectedResults.remove(iris26486ShortTs);\n"
    "            iris26480ShortFrame = null;\n"
    "        }\n"
    "        /* IRIS_26486_SHORT_NEVER_IN_NORMAL_FRAME_LIST */\n"
    "        List<ImageFrame> iris26480ProcessingFrames = new ArrayList<>(selected);",
    "26486 short slot transfer",
)

# ImageSaver is shot-local in the process lambda. Static IMAGE_BUFFER is not
# populated for Motion anymore.
regex_once(
    cap,
    r"        mImageSaver = new ImageSaver\(cameraEventsListener\);\n"
    r"        mImageSaver\.setFrameCount\(iris26480ProcessingFrames\.size\(\)\);\n"
    r"        mImageSaver\.setImageFormat\(CaptureController\.RAW_FORMAT\);\n"
    r"        mImageSaver\.implementation = ImageSaverSelector\.getImageSaver\(CaptureController\.RAW_FORMAT, mImageSaver\.implementation\);\n"
    r"        mImageSaver\.implementation\.frameCount = iris26480ProcessingFrames\.size\(\);\n\n"
    r"        SaverImplementation\.IMAGE_BUFFER\.clear\(\);\n"
    r"        SaverImplementation\.IMAGE_BUFFER\.addAll\(iris26480ProcessingFrames\);",
    "        /* IRIS_26486_MOTIONBATCH_SOLE_PROCESSING_OWNER */\n"
    "        final ImageSaver iris26486ImageSaver = new ImageSaver(cameraEventsListener);\n"
    "        iris26486ImageSaver.setFrameCount(iris26480ProcessingFrames.size());\n"
    "        iris26486ImageSaver.setImageFormat(CaptureController.RAW_FORMAT);\n"
    "        iris26486ImageSaver.implementation = ImageSaverSelector.getImageSaver(\n"
    "                CaptureController.RAW_FORMAT, iris26486ImageSaver.implementation);\n"
    "        iris26486ImageSaver.implementation.frameCount = iris26480ProcessingFrames.size();\n"
    "        mImageSaver = iris26486ImageSaver; // UI/debug compatibility only; lambda uses local owner.",
    "26486 capture static buffer removal",
)

# Batch carries the independent short slot.
replace_once(
    cap,
    "                mPreviewCaptureRequest, CaptureController.RAW_FORMAT, cameraRotation, candidateCount);",
    "                mPreviewCaptureRequest, CaptureController.RAW_FORMAT, cameraRotation, candidateCount,\n"
    "                iris26486ShortSlot);",
    "26486 batch short slot constructor",
)

# Update batch boundary trace to reflect slot state.
replace_once(
    cap,
    '                + " shortFramePresent=" + (iris26480ShortFrame != null)\n',
    '                + " shortFramePresent=" + iris26486ShortSlot.hasFrame()\n',
    "26486 batch short trace",
)

# Queue bookkeeping and asynchronous short delivery happen before serial process
# submission. A second shutter may now freeze another immutable batch.
replace_once(
    cap,
    "        mMotion26480ShortRequested = false;\n"
    "        mMotion26480ShortRequestCompleted = false;\n"
    "        mMotion26480ShortResultTimestampNs = 0L;\n"
    "        processExecutor.execute(() -> {\n",
    "        mMotion26480ShortRequested = false;\n"
    "        mMotion26480ShortRequestCompleted = false;\n"
    "        mMotion26480ShortResultTimestampNs = 0L;\n"
    "        if (iris26486ShortTicket != null) scheduleMotion26486ShortDelivery(iris26486ShortTicket);\n"
    "        int iris26486Queued = mMotion26486InFlightBatches.incrementAndGet();\n"
    "        Log.i(TAG, \"IRIS_26486_BATCH_ENQUEUED inFlight=\" + iris26486Queued\n"
    "                + \" max=\" + MOTION_26486_MAX_INFLIGHT_BATCHES\n"
    "                + \" serializedGpuExecutor=true\");\n"
    "        processExecutor.execute(() -> {\n",
    "26486 bounded batch queue increment",
)

replace_once(
    cap,
    "                mImageSaver.runMotionRaw(mCameraCharacteristics, motionBatch);",
    "                iris26486ImageSaver.runMotionRaw(mCameraCharacteristics, motionBatch);",
    "26486 shot-local saver owner",
)

# Only replace the static clear inside the Motion processing-finally block.
replace_once(
    cap,
    "                SaverImplementation.IMAGE_BUFFER.clear();\n"
    "                mBackgroundHandler.post(this::unlockFocus);",
    "                int iris26486Remaining = mMotion26486InFlightBatches.decrementAndGet();\n"
    "                if (iris26486Remaining < 0) {\n"
    "                    mMotion26486InFlightBatches.set(0);\n"
    "                    iris26486Remaining = 0;\n"
    "                }\n"
    "                Log.i(TAG, \"IRIS_26486_BATCH_FINISHED inFlight=\" + iris26486Remaining);\n"
    "                /* No SaverImplementation.IMAGE_BUFFER ownership in Motion. */\n"
    "                mBackgroundHandler.post(this::unlockFocus);",
    "26486 queue decrement/static buffer cleanup",
)

# Defer reopening the ring until every mutable per-shot object has been copied
# into the immutable batch. Otherwise a second shutter could overwrite globals
# while this first finalize method is still constructing metadata/gyro state.
replace_once(
    cap,
    "        // Ownership has transferred to the immutable processing batch.\n"
    "        // Re-open the passive ring immediately for the next scene. A second\n"
    "        // shutter is still blocked by CaptureController.isProcessing.\n"
    "        mZslCapturing = false;\n"
    "        mMotionTopUpActive = false;\n",
    "        /* IRIS_26486_CAPTURE_RELEASE_DEFERRED_UNTIL_BATCH_FROZEN */\n"
    "        mMotionTopUpActive = false;\n",
    "26486 defer capture release",
)

# Capture-time publication through global FrameNumberSelector/fullpairs would let
# the next shutter overwrite metadata needed by the batch currently processing.
# Preserve those compatibility globals, but publish them only inside the single
# serialized processing lane from MotionBatch-owned copies.
replace_once(
    cap,
    "        // Publish the actual immutable Motion batch size before processing.\n"
    "        // The existing JPEG ImageDescription/EXIF path reads this field.\n"
    "        final int motionSelectedFrameCount = selected.size();\n"
    "        com.particlesdevs.photoncamera.processing.parameters\n"
    "                .FrameNumberSelector.frameCount =\n"
    "                motionSelectedFrameCount;\n\n"
    "        com.particlesdevs.photoncamera.util.MotionTrace.state(\n"
    "                mMotionDiagnosticShotId,\n"
    "                \"JPEG_EXIF_FRAMECOUNT\",\n"
    "                \"selectedFrameCount=\" + motionSelectedFrameCount\n"
    "                        + \" publishedFrameCount=\"\n"
    "                        + com.particlesdevs.photoncamera.processing.parameters\n"
    "                                .FrameNumberSelector.frameCount);\n",
    "        final int motionSelectedFrameCount = selected.size();\n"
    "        com.particlesdevs.photoncamera.util.MotionTrace.state(\n"
    "                mMotionDiagnosticShotId, \"JPEG_EXIF_FRAMECOUNT\",\n"
    "                \"selectedFrameCount=\" + motionSelectedFrameCount\n"
    "                        + \" publication=serializedMotionBatchOwner\");\n",
    "26486 defer global frame count publication",
)

replace_once(
    cap,
    "        IsoExpoSelector.fullpairs.clear();\n"
    "        for (int i = 0; i < actualCount; i++) {\n"
    "            ImageFrame frame = selected.get(i);\n"
    "            IsoExpoSelector.fullpairs.add(IsoExpoSelector.createEqualExposureZslPair(\n"
    "                    this, selectedResults.get(frame.timestamp)));\n"
    "        }\n",
    "        /* IRIS_26486_EXPOSURE_PAIR_PUBLICATION_DEFERRED\n"
    "         * MotionBatch reconstructs per-shot ExpoPair objects from copied actual metadata.\n"
    "         * The legacy static fullpairs list is populated only on the serialized process lane.\n"
    "         */\n",
    "26486 remove capture-time static exposure pairs",
)

# Finish the gyro sequence before capture ownership is released. Calling this
# from the delayed process lambda could terminate the next shot's gyro sequence.
replace_once(
    cap,
    "        PhotonCamera.getGyro().buildZslBurstShakiness(frameTimestamps, exposureTimeNs, BurstShakiness);\n",
    "        PhotonCamera.getGyro().buildZslBurstShakiness(frameTimestamps, exposureTimeNs, BurstShakiness);\n"
    "        PhotonCamera.getGyro().CompleteSequence();\n",
    "26486 per-shot gyro completion before release",
)

# After the batch is fully frozen, increment queue ownership BEFORE reopening the
# ring. Capture the shot id and camera characteristics into locals so the next
# shutter/camera switch cannot redirect the queued process job.
replace_once(
    cap,
    "        if (iris26486ShortTicket != null) scheduleMotion26486ShortDelivery(iris26486ShortTicket);\n"
    "        int iris26486Queued = mMotion26486InFlightBatches.incrementAndGet();\n"
    "        Log.i(TAG, \"IRIS_26486_BATCH_ENQUEUED inFlight=\" + iris26486Queued\n"
    "                + \" max=\" + MOTION_26486_MAX_INFLIGHT_BATCHES\n"
    "                + \" serializedGpuExecutor=true\");\n"
    "        processExecutor.execute(() -> {\n"
    "            try {\n"
    "                PhotonCamera.getGyro().CompleteSequence();\n",
    "        if (iris26486ShortTicket != null) scheduleMotion26486ShortDelivery(iris26486ShortTicket);\n"
    "        final long iris26486ShotId = mMotionDiagnosticShotId;\n"
    "        final CameraCharacteristics iris26486Characteristics = mCameraCharacteristics;\n"
    "        int iris26486Queued = mMotion26486InFlightBatches.incrementAndGet();\n"
    "        Log.i(TAG, \"IRIS_26486_BATCH_ENQUEUED inFlight=\" + iris26486Queued\n"
    "                + \" max=\" + MOTION_26486_MAX_INFLIGHT_BATCHES\n"
    "                + \" serializedGpuExecutor=true\");\n"
    "        /* IRIS_26486_RING_REOPEN_ONLY_AFTER_IMMUTABLE_BATCH */\n"
    "        mZslCapturing = false;\n"
    "        burst = false;\n"
    "        mState = STATE_PREVIEW;\n"
    "        processExecutor.execute(() -> {\n"
    "            try {\n",
    "26486 queue ownership before ring reopen",
)

replace_once(
    cap,
    "                iris26486ImageSaver.runMotionRaw(mCameraCharacteristics, motionBatch);",
    "                iris26486ImageSaver.runMotionRaw(iris26486Characteristics, motionBatch);",
    "26486 shot-local characteristics",
)
replace_once(
    cap,
    "                        mMotionDiagnosticShotId,\n"
    "                        \"CAPTURE_OR_PROCESSING\",",
    "                        iris26486ShotId,\n"
    "                        \"CAPTURE_OR_PROCESSING\",",
    "26486 process error local shot id",
)
replace_once(
    cap,
    "                        mMotionDiagnosticShotId,\n"
    "                        \"FINALLY\",",
    "                        iris26486ShotId,\n"
    "                        \"FINALLY\",",
    "26486 process finally local shot id",
)

# Processing completion must never clear the acquisition state of a newer shot.
# The capture path already releases its own mZslCapturing flag after queueing.
replace_once(
    cap,
    "                // Do not clear mZslResultMap here: the passive ring may\n"
    "                // already contain the next scene's frames and metadata.\n"
    "                mZslCapturing = false;\n"
    "                burst = false;\n"
    "                mState = STATE_PREVIEW;\n",
    "                // Do not mutate mZslCapturing/burst/mState here: a newer Motion\n"
    "                // acquisition may already own those fields.\n",
    "26486 processing cannot clear newer capture state",
)
replace_once(
    cap,
    "                try {\n"
    "                    cameraEventsListener.onProcessingFinished(\n"
    "                            \"Motion processing ended\");\n"
    "                } catch (Exception cleanupError) {\n"
    "                    Log.e(TAG, \"Motion shutter cleanup callback failed: \"\n"
    "                            + Log.getStackTraceString(cleanupError));\n"
    "                }",
    "                if (iris26486Remaining == 0) {\n"
    "                    try {\n"
    "                        cameraEventsListener.onProcessingFinished(\n"
    "                                \"Motion processing ended\");\n"
    "                    } catch (Exception cleanupError) {\n"
    "                        Log.e(TAG, \"Motion shutter cleanup callback failed: \"\n"
    "                                + Log.getStackTraceString(cleanupError));\n"
    "                    }\n"
    "                }",
    "26486 only final queued batch ends processing UI",
)


# -------------------------------------------------------------------------
# 2) MotionBatch gets a thread-safe one-shot optional short-frame slot.
# -------------------------------------------------------------------------
require(batch, "public final int processingFrameCount;", "26485 MotionBatch lineage")
insert_before(
    batch,
    "    public final List<ImageFrame> frames;",
    r'''    /* IRIS_26486_ASYNC_SHORT_HIGHLIGHT_SLOT
     * The equal-exposure frames remain immutable. A separately exposed RAW may
     * arrive while the serialized Wronski job is running; it can be offered
     * exactly once until reconstruction reaches the highlight-recovery boundary.
     */
    public static final class ShortHighlightSlot {
        private ImageFrame frame;
        private boolean sealed = false;
        public synchronized boolean offer(ImageFrame candidate) {
            if (candidate == null) return false;
            if (sealed || frame != null) {
                try { candidate.close(); } catch (Throwable ignored) {}
                return false;
            }
            frame = candidate;
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
        public synchronized boolean hasFrame() { return frame != null; }
        public synchronized boolean isSealed() { return sealed; }
    }

''',
    "26486 ShortHighlightSlot class",
)
replace_once(
    batch,
    "    public final int processingFrameCount;\n",
    "    public final int processingFrameCount;\n"
    "    public final ShortHighlightSlot shortHighlightSlot;\n",
    "26486 MotionBatch slot field",
)

old_sig = "    public MotionBatch(List<ImageFrame> frames, List<GyroBurst> gyro,\n" \
          "                       Map<Long, Double> exposures,\n" \
          "                       Map<Long, TotalCaptureResult> results,\n" \
          "                       CaptureResult referenceResult,\n" \
          "                       CaptureRequest referenceRequest,\n" \
          "                       int imageFormat, int rotation, int candidateCount) {"
new_sig = "    public MotionBatch(List<ImageFrame> frames, List<GyroBurst> gyro,\n" \
          "                       Map<Long, Double> exposures,\n" \
          "                       Map<Long, TotalCaptureResult> results,\n" \
          "                       CaptureResult referenceResult,\n" \
          "                       CaptureRequest referenceRequest,\n" \
          "                       int imageFormat, int rotation, int candidateCount,\n" \
          "                       ShortHighlightSlot shortHighlightSlot) {"
replace_once(batch, old_sig, new_sig, "26486 MotionBatch extended constructor")
insert_before(
    batch,
    new_sig,
    "    public MotionBatch(List<ImageFrame> frames, List<GyroBurst> gyro,\n"
    "                       Map<Long, Double> exposures,\n"
    "                       Map<Long, TotalCaptureResult> results,\n"
    "                       CaptureResult referenceResult,\n"
    "                       CaptureRequest referenceRequest,\n"
    "                       int imageFormat, int rotation, int candidateCount) {\n"
    "        this(frames, gyro, exposures, results, referenceResult, referenceRequest,\n"
    "                imageFormat, rotation, candidateCount, new ShortHighlightSlot());\n"
    "    }\n\n",
    "26486 MotionBatch compatibility constructor",
)
replace_once(
    batch,
    "        this.processingFrameCount = this.frames.size();\n",
    "        this.processingFrameCount = this.frames.size();\n"
    "        this.shortHighlightSlot = shortHighlightSlot == null\n"
    "                ? new ShortHighlightSlot() : shortHighlightSlot;\n",
    "26486 MotionBatch slot assignment",
)

replace_once(
    batch,
    "import java.util.Map;\n",
    "import java.util.Map;\n"
    "import com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector;\n",
    "26486 MotionBatch exposure-pair import",
)
replace_once(
    batch,
    "    public final ShortHighlightSlot shortHighlightSlot;\n",
    "    public final ShortHighlightSlot shortHighlightSlot;\n"
    "    public final List<IsoExpoSelector.ExpoPair> exposurePairs;\n",
    "26486 MotionBatch exposure-pair field",
)
replace_once(
    batch,
    "        this.shortHighlightSlot = shortHighlightSlot == null\n"
    "                ? new ShortHighlightSlot() : shortHighlightSlot;\n",
    "        this.shortHighlightSlot = shortHighlightSlot == null\n"
    "                ? new ShortHighlightSlot() : shortHighlightSlot;\n"
    "        ArrayList<IsoExpoSelector.ExpoPair> iris26486Pairs = new ArrayList<>();\n"
    "        for (ImageFrame frame : this.frames) {\n"
    "            if (frame == null || frame.motionV2ActualExposureNs <= 0L\n"
    "                    || frame.motionV2ActualIso <= 0) {\n"
    "                throw new IllegalArgumentException(\n"
    "                        \"26486 MotionBatch frame missing exact exposure metadata\");\n"
    "            }\n"
    "            IsoExpoSelector.ExpoPair pair = new IsoExpoSelector.ExpoPair(\n"
    "                    frame.motionV2ActualExposureNs,\n"
    "                    IsoExpoSelector.getEXPLOW(), IsoExpoSelector.getEXPHIGH(),\n"
    "                    frame.motionV2ActualIso,\n"
    "                    IsoExpoSelector.getISOLOW(), IsoExpoSelector.getISOHIGH(),\n"
    "                    IsoExpoSelector.getISOAnalog());\n"
    "            pair.curlayer = IsoExpoSelector.ExpoPair.exposureLayer.Normal;\n"
    "            pair.layerMpy = 1.0f;\n"
    "            iris26486Pairs.add(pair);\n"
    "        }\n"
    "        this.exposurePairs = Collections.unmodifiableList(iris26486Pairs);\n",
    "26486 MotionBatch owned exposure pairs",
)


# -------------------------------------------------------------------------
# 3) Motion processing never round-trips through the global static IMAGE_BUFFER.
# -------------------------------------------------------------------------
regex_once(
    saver,
    r"    public void runMotionRaw\(android\.hardware\.camera2\.CameraCharacteristics characteristics,\n"
    r"                             MotionBatch batch\) \{.*?\n    \}\n\n    public void runRaw",
    "    /* IRIS_26486_MOTIONBATCH_DIRECT_SAVER_HANDOFF */\n"
    "    public void runMotionRaw(android.hardware.camera2.CameraCharacteristics characteristics,\n"
    "                             MotionBatch batch) {\n"
    "        setFrameCount(batch.processingFrameCount);\n"
    "        setImageFormat(batch.imageFormat);\n"
    "        implementation = ImageSaverSelector.getImageSaver(batch.imageFormat, implementation);\n"
    "        implementation.frameCount = batch.processingFrameCount;\n"
    "        if (!(implementation instanceof DefaultSaver)) {\n"
    "            throw new IllegalStateException(\"26486 Motion requires DefaultSaver direct batch handoff\");\n"
    "        }\n"
    "        ((DefaultSaver) implementation).runMotionBatch(characteristics, batch);\n"
    "    }\n\n"
    "    public void runRaw",
    "26486 ImageSaver direct MotionBatch method",
)

insert_before(
    default_saver,
    "    public void runRaw(int imageFormat, CameraCharacteristics characteristics, CaptureResult captureResult, CaptureRequest captureRequest, ArrayList<GyroBurst> burstShakiness, int cameraRotation, HashMap<Long, Double> exposures) {",
    r'''    /* IRIS_26486_DEFAULTSAVER_MOTIONBATCH_SOLE_OWNER
     * Motion owns copied RAWs in the immutable batch. No static IMAGE_BUFFER,
     * no busy-wait, and no cross-shot slicing/reassignment are involved.
     */
    public void runMotionBatch(CameraCharacteristics characteristics, MotionBatch batch) {
        if (batch == null || batch.frames == null || batch.frames.size() < 2) {
            throw new IllegalStateException("26486 MotionBatch requires at least two normal RAW frames");
        }
        /* IRIS_26486_SERIALIZED_LEGACY_METADATA_COMPATIBILITY
         * These globals are written only here, on the one serialized processing lane.
         * Capture of the next shot never mutates them.
         */
        com.particlesdevs.photoncamera.processing.parameters.FrameNumberSelector.frameCount =
                batch.retainedCount;
        com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector.fullpairs.clear();
        for (com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector.ExpoPair source
                : batch.exposurePairs) {
            com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector.ExpoPair copy =
                    new com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector.ExpoPair(source);
            copy.curlayer = com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector
                    .ExpoPair.exposureLayer.Normal;
            copy.layerMpy = 1.0f;
            com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector.fullpairs.add(copy);
        }
        super.runRaw(batch.imageFormat, characteristics, batch.referenceResult,
                batch.referenceRequest, new ArrayList<>(batch.gyro), batch.rotation,
                new HashMap<>(batch.exposures));
        hdrxProcessor.configure(
                PhotonCamera.getSettings().alignAlgorithm,
                PhotonCamera.getSettings().rawSaver,
                PhotonCamera.getSettings().selectedMode);
        Path dngFile = ImagePath.newDNGFilePath();
        Path imageFile = ImagePath.newImageFilePath();
        ArrayList<ImageFrame> ownedFrames = new ArrayList<>(batch.frames);
        hdrxProcessor.startMotion(
                dngFile,
                imageFile,
                ParseExif.parse(batch.referenceResult, batch.referenceRequest),
                new ArrayList<>(batch.gyro),
                ownedFrames,
                new HashMap<>(batch.exposures),
                batch.imageFormat,
                batch.rotation,
                characteristics,
                batch.referenceResult,
                batch.referenceRequest,
                batch.exposurePairs,
                batch.shortHighlightSlot,
                processingCallback);
    }

''',
    "26486 DefaultSaver direct batch path",
)


# -------------------------------------------------------------------------
# 4) Hdrx carries the one-shot slot to reconstruction. It is sealed on every
# exit path, while reconstruction takes it only immediately before highlight
# recovery so a non-blocking short RAW can arrive during the Wronski work.
# -------------------------------------------------------------------------
replace_once(
    hdrx,
    "    private HashMap<Long, Double> exposures;\n",
    "    private HashMap<Long, Double> exposures;\n"
    "    private java.util.List<com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector.ExpoPair>\n"
    "            mMotion26486ExposurePairs;\n"
    "    private com.particlesdevs.photoncamera.processing.MotionBatch.ShortHighlightSlot\n"
    "            mMotion26486ShortSlot;\n",
    "26486 Hdrx short slot field",
)

replace_once(
    hdrx,
    "        Log.d(TAG, \"HdrxProcessor called start()\");\n"
    "        Run();\n"
    "    }\n\n"
    "    public void Run() {",
    "        Log.d(TAG, \"HdrxProcessor called start()\");\n"
    "        Run();\n"
    "    }\n\n"
    "    /* IRIS_26486_HDRX_MOTIONBATCH_ENTRY */\n"
    "    public void startMotion(Path dngFile, Path imageFile,\n"
    "                      ParseExif.ExifData exifData,\n"
    "                      ArrayList<GyroBurst> BurstShakiness,\n"
    "                      ArrayList<ImageFrame> imageBuffer,\n"
    "                      HashMap<Long, Double> exposures,\n"
    "                      int imageFormat, int cameraRotation,\n"
    "                      CameraCharacteristics characteristics,\n"
    "                      CaptureResult captureResult, CaptureRequest captureRequest,\n"
    "                      java.util.List<com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector.ExpoPair> exposurePairs,\n"
    "                      com.particlesdevs.photoncamera.processing.MotionBatch.ShortHighlightSlot shortSlot,\n"
    "                      ProcessingCallback callback) {\n"
    "        this.mMotion26486ExposurePairs = new java.util.ArrayList<>();\n"
    "        if (exposurePairs != null) for (com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector.ExpoPair source : exposurePairs) {\n"
    "            com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector.ExpoPair copy =\n"
    "                    new com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector.ExpoPair(source);\n"
    "            copy.curlayer = com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector.ExpoPair.exposureLayer.Normal;\n"
    "            copy.layerMpy = 1.0f;\n"
    "            this.mMotion26486ExposurePairs.add(copy);\n"
    "        }\n"
    "        this.mMotion26486ShortSlot = shortSlot;\n"
    "        start(dngFile, imageFile, exifData, BurstShakiness, imageBuffer, exposures,\n"
    "                imageFormat, cameraRotation, characteristics, captureResult,\n"
    "                captureRequest, callback);\n"
    "    }\n\n"
    "    public void Run() {",
    "26486 Hdrx startMotion overload",
)

# Seal in Hdrx finally, after reconstruction has had a chance to take the frame.
replace_once(
    hdrx,
    "            MotionMetrics.end();\n"
    "            if(iris26480OriginalPriority!=null)",
    "            MotionMetrics.end();\n"
    "            if (mMotion26486ShortSlot != null) {\n"
    "                mMotion26486ShortSlot.sealAndClose();\n"
    "                mMotion26486ShortSlot = null;\n"
    "            }\n"
    "            mMotion26486ExposurePairs = null;\n"
    "            if(iris26480OriginalPriority!=null)",
    "26486 Hdrx short slot cleanup",
)

# Transfer any historical in-list short frame into the new slot BEFORE the
# reconstruction call, then pass the slot rather than a fixed frame object.
replace_once(
    hdrx,
    "            MotionV2Merger.Result iris26409V2 =\n"
    "                    MotionV2CfaReconstruction.reconstruct(\n"
    "                            new Point(width, height),\n"
    "                            images,\n"
    "                            iris26363ReferenceTimestamp,\n"
    "                            processingParameters,\n"
    "                            iris26480ShortHighlightFrame);\n"
    "            iris26480ShortHighlightFrame = null; // reconstruction owns/closes it",
    "            if (iris26480ShortHighlightFrame != null) {\n"
    "                if (mMotion26486ShortSlot != null)\n"
    "                    mMotion26486ShortSlot.offer(iris26480ShortHighlightFrame);\n"
    "                else iris26480ShortHighlightFrame.close();\n"
    "                iris26480ShortHighlightFrame = null;\n"
    "            }\n"
    "            MotionV2Merger.Result iris26409V2 =\n"
    "                    MotionV2CfaReconstruction.reconstruct(\n"
    "                            new Point(width, height),\n"
    "                            images,\n"
    "                            iris26363ReferenceTimestamp,\n"
    "                            processingParameters,\n"
    "                            mMotion26486ShortSlot);",
    "26486 reconstruction slot handoff",
)

replace_once(
    hdrx,
    "            frame.pair = IsoExpoSelector.fullpairs.get(i);\n",
    "            if (cameraMode == CameraMode.MOTION) {\n"
    "                if (mMotion26486ExposurePairs == null\n"
    "                        || i >= mMotion26486ExposurePairs.size()) {\n"
    "                    throw new IllegalStateException(\n"
    "                            \"26486 MotionBatch exposure-pair ownership mismatch\");\n"
    "                }\n"
    "                frame.pair = new IsoExpoSelector.ExpoPair(\n"
    "                        mMotion26486ExposurePairs.get(i));\n"
    "                frame.pair.curlayer = IsoExpoSelector.ExpoPair.exposureLayer.Normal;\n"
    "                frame.pair.layerMpy = 1.0f;\n"
    "            } else {\n"
    "                frame.pair = IsoExpoSelector.fullpairs.get(i);\n"
    "            }\n",
    "26486 Hdrx per-shot exposure-pair ownership",
)

# Update residual diagnostic wording: no IPOL MC owner remains in active Motion.
hdrx_text = read(hdrx).replace("wronskiNoiseOwner=Camera2_IPOL", "wronskiNoiseOwner=Camera2_BJZHOU_MGC")
write(hdrx, hdrx_text)


# -------------------------------------------------------------------------
# 5) Reconstruction: no per-reference/per-auxiliary IPOL Monte-Carlo table.
# Camera2 affine noise stays authoritative; analytic SNR is used only for the
# existing kernel-size/tuning selection. Full bjzhou-style rejection graph is
# GPU-side and feeds the joint opponent accumulator.
# -------------------------------------------------------------------------
replace_once(
    recon,
    "import com.particlesdevs.photoncamera.processing.ImageFrame;\n",
    "import com.particlesdevs.photoncamera.processing.ImageFrame;\n"
    "import com.particlesdevs.photoncamera.processing.MotionBatch;\n",
    "26486 MotionBatch import",
)
replace_once(recon, "    private final ImageFrame shortHighlightFrame;\n",
             "    private final MotionBatch.ShortHighlightSlot shortHighlightSlot;\n",
             "26486 reconstruction slot field")
replace_once(recon,
    "            ImageFrame referenceFrame,\n            ImageFrame shortHighlightFrame) {",
    "            ImageFrame referenceFrame,\n            MotionBatch.ShortHighlightSlot shortHighlightSlot) {",
    "26486 constructor slot parameter")
replace_once(recon, "        this.shortHighlightFrame = shortHighlightFrame;\n",
             "        this.shortHighlightSlot = shortHighlightSlot;\n",
             "26486 constructor slot assignment")
# Static reconstruct parameter is the second occurrence of the old parameter.
text = read(recon)
old_param = "            Parameters parameters,\n            ImageFrame shortHighlightFrame) {"
if text.count(old_param) != 1:
    raise SystemExit(f"26486 static reconstruct slot parameter expected one, found {text.count(old_param)}")
write(recon, text.replace(old_param,
    "            Parameters parameters,\n            MotionBatch.ShortHighlightSlot shortHighlightSlot) {", 1))
replace_once(recon,
    "                    size, ordered, referenceTimestamp, parameters, reference, shortHighlightFrame);",
    "                    size, ordered, referenceTimestamp, parameters, reference, shortHighlightSlot);",
    "26486 reconstruction constructor invocation")
replace_once(recon,
    "            if (shortHighlightFrame != null && !inputImages.contains(shortHighlightFrame)) {\n"
    "                try { shortHighlightFrame.close(); } catch (Throwable ignored) {}\n"
    "            }",
    "            if (shortHighlightSlot != null) shortHighlightSlot.sealAndClose();",
    "26486 static reconstruction slot cleanup")

# Take/seal the optional short observation at the last possible point.
replace_once(
    recon,
    "            /* IRIS_26480_BJZHOU_RCD_BENTO_SHORT_RECOVERY_V2 */\n"
    "            GLTexture iris26480ReadbackOutput=imageOutput,iris26480ShortRaw=null,iris26480ShortCfa=null;",
    "            /* IRIS_26486_LATE_NONBLOCKING_SHORT_TAKE */\n"
    "            ImageFrame shortHighlightFrame = shortHighlightSlot == null\n"
    "                    ? null : shortHighlightSlot.takeAndSeal();\n"
    "            /* IRIS_26480_BJZHOU_RCD_BENTO_SHORT_RECOVERY_V2 */\n"
    "            GLTexture iris26480ReadbackOutput=imageOutput,iris26480ShortRaw=null,iris26480ShortCfa=null;",
    "26486 late short take",
)

# Replace expensive reference MC initialization with analytic Camera2 SNR.
regex_once(
    recon,
    r"        final MotionV2IpolNoiseCurve\.Curve ipolNoiseCurve =\n"
    r"                MotionV2IpolNoiseCurve\.build\(.*?\);\n"
    r"        final float mfsrSnr = ipolNoiseCurve\.snr;",
    "        /* IRIS_26486_NO_IPOL_MONTE_CARLO_ACTIVE_PATH\n"
    "         * Camera2 affine sensor noise is already authoritative. Use the\n"
    "         * published-style analytic SNR proxy only for static kernel sizing;\n"
    "         * rejection itself is the GPU MGC graph below.\n"
    "         */\n"
    "        final float mfsrSnr = Math.max(6.0f, Math.min(30.0f,\n"
    "                0.18f / (float)Math.sqrt(Math.max(\n"
    "                        noiseS * 0.18f + noiseO, 1.0e-8f))));",
    "26486 remove reference IPOL MC",
)
# Remove texture declaration and setup block.
recon_text = read(recon).replace("        GLTexture ipolNoiseCurveTexture = null;\n", "")
write(recon, recon_text)
regex_once(
    recon,
    r"            if \(directBayer\) \{\n"
    r"                ipolNoiseCurve\.rgba32f\.position\(0\);.*?\n"
    r"            \}\n\n"
    r"            /\*\n             \* IRIS_26420_MOTION_V2_NO_LEGACY_ALIGNMENT",
    "            /* IRIS_26486_GPU_REJECTION_NO_CPU_MC_SETUP */\n\n"
    "            /*\n             * IRIS_26420_MOTION_V2_NO_LEGACY_ALIGNMENT",
    "26486 remove IPOL texture setup",
)
recon_text = read(recon).replace(
    "            if (ipolNoiseCurveTexture != null) ipolNoiseCurveTexture.close();\n", "")
recon_text = recon_text.replace("reconstructionOwner=Wronski_IPOL", "reconstructionOwner=Wronski_BJZHOU_MGC")
write(recon, recon_text)

# Add two quarter-size rejection scratch textures to the existing persistent
# per-auxiliary scratch owner.
replace_once(
    recon,
    "            GLTexture iris26480CovScratch=null,iris26480ChromaGuideScratch=null,iris26480RobustRawScratch=null,iris26480RobustMinScratch=null;",
    "            GLTexture iris26480CovScratch=null,iris26480ChromaGuideScratch=null,iris26480RobustRawScratch=null,iris26480RobustMinScratch=null;\n"
    "            GLTexture iris26486RejectSmallA=null,iris26486RejectSmallB=null;",
    "26486 rejection quarter scratch declaration",
)

# Replace robustness+erosion section while keeping the surrounding directBayer
# branch and the existing semantic accumulation/ping-pong semantics.
recon_text = read(recon)
start_token = "                            long iris26468RobustStart = System.currentTimeMillis();"
start = recon_text.find(start_token)
if start < 0:
    raise SystemExit("26486 could not find robustness block start")
end_token = "                            }\n\n                            /*"
end = recon_text.find(end_token, start)
if end < 0:
    raise SystemExit("26486 could not find robustness block end")
end += len("                            }\n")
new_rejection = r'''                            long iris26486RejectStart = System.currentTimeMillis();
                            if(iris26480RobustRawScratch==null)iris26480RobustRawScratch=new GLTexture(rawHalf,
                                    new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                            if(iris26480RobustMinScratch==null)iris26480RobustMinScratch=new GLTexture(rawHalf,
                                    new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                            Point iris26486RejectQuarter = new Point(
                                    Math.max(1,(rawHalf.x+3)/4), Math.max(1,(rawHalf.y+3)/4));
                            if(iris26486RejectSmallA==null)iris26486RejectSmallA=new GLTexture(iris26486RejectQuarter,
                                    new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                            if(iris26486RejectSmallB==null)iris26486RejectSmallB=new GLTexture(iris26486RejectQuarter,
                                    new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                            GLTexture mfsrRobustRaw=iris26480RobustRawScratch,mfsrRobustMin=iris26480RobustMinScratch;
                            try {
                                /* 1. guide/flow unblocker */
                                glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_unblocker",true);
                                glProg.setVar("rawHalf",rawHalf);glProg.setTexture("flowTexture",ownedAlignment.flowTexture);
                                glProg.setTextureCompute("outUnblocker",mfsrRobustRaw,true);glProg.computeAuto(rawHalf,1);

                                /* 2. clipping-aware affine-noise rejection evidence */
                                glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_rejection_base",true);
                                glProg.setVar("rawHalf",rawHalf);glProg.setVar("noiseS",iris26480FrameNoiseS);glProg.setVar("noiseO",iris26480FrameNoiseO);
                                glProg.setVar("physicalExposureScale",exposure);glProg.setVar("clipStart",0.985f);glProg.setVar("clipEnd",0.998f);
                                glProg.setTexture("referenceWbCfa",wronskiReferenceCfa);glProg.setTexture("alterWbCfa",wronskiAlterCfa);
                                glProg.setTexture("referencePhysicalCfa",referenceCfa);glProg.setTexture("alterPhysicalCfa",alterCfa);
                                glProg.setTexture("flowTexture",ownedAlignment.flowTexture);glProg.setTexture("unblockerTexture",mfsrRobustRaw);
                                glProg.setTextureCompute("outRejection",mfsrRobustMin,true);glProg.computeAuto(rawHalf,1);

                                /* 3. clipped Gaussian difference, separable H/V */
                                glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_clipped_gaussian_h",true);
                                glProg.setVar("size",rawHalf);glProg.setTexture("inputEvidence",mfsrRobustMin);
                                glProg.setTextureCompute("outEvidence",mfsrRobustRaw,true);glProg.computeAuto(rawHalf,1);
                                glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_clipped_gaussian_v",true);
                                glProg.setVar("size",rawHalf);glProg.setTexture("inputEvidence",mfsrRobustRaw);
                                glProg.setTextureCompute("outEvidence",mfsrRobustMin,true);glProg.computeAuto(rawHalf,1);

                                /* 4. 4x rejection reduction */
                                glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_rejection_reduce4",true);
                                glProg.setVar("inputSize",rawHalf);glProg.setTexture("inputEvidence",mfsrRobustMin);
                                glProg.setTextureCompute("outReduced",iris26486RejectSmallA,true);glProg.computeAuto(iris26486RejectQuarter,1);

                                /* 5. guide-aware bilateral rejection */
                                glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_rejection_bilateral",true);
                                glProg.setVar("smallSize",iris26486RejectQuarter);glProg.setVar("rawHalf",rawHalf);
                                glProg.setTexture("inputReduced",iris26486RejectSmallA);glProg.setTexture("referencePackedCfa",wronskiReferenceCfa);
                                glProg.setTextureCompute("outFiltered",iris26486RejectSmallB,true);glProg.computeAuto(iris26486RejectQuarter,1);

                                /* 6. full-resolution rejection postprocess */
                                glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_rejection_postprocess",true);
                                glProg.setVar("rawHalf",rawHalf);glProg.setVar("smallSize",iris26486RejectQuarter);
                                glProg.setTexture("fullEvidence",mfsrRobustMin);glProg.setTexture("smallEvidence",iris26486RejectSmallB);
                                glProg.setTextureCompute("outWeight",mfsrRobustRaw,true);glProg.computeAuto(rawHalf,1);

                                /* 7. conservative dilation of rejection = min-filter frame weight */
                                glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_bjzhou_rejection_dilate",true);
                                glProg.setVar("size",rawHalf);glProg.setTexture("inputWeight",mfsrRobustRaw);
                                glProg.setTextureCompute("outWeight",mfsrRobustMin,true);glProg.computeAuto(rawHalf,1);
                                long iris26486RejectMs=System.currentTimeMillis()-iris26486RejectStart;

                                long iris26468AccumulateStart=System.currentTimeMillis();
                                glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/direct_rgb_accumulate",true);
                                glProg.setVar("rawSize",raw);glProg.setVar("rawHalf",rawHalf);glProg.setVar("cfaPattern",(int)parameters.cfaPattern);
                                glProg.setVar("maximumSupport",(float)frameCount);
                                glProg.setVar("physicalExposureScale",exposure);glProg.setVar("physicalClipStart",0.985f);glProg.setVar("physicalClipEnd",0.998f);
                                glProg.setVar("greenNoiseS",iris26480FrameNoiseS);glProg.setVar("greenNoiseO",iris26480FrameNoiseO);
                                glProg.setTexture("flowTexture",ownedAlignment.flowTexture);glProg.setTexture("robustnessTexture",mfsrRobustMin);
                                glProg.setTexture("previousNumerator",currentDirectRgb);glProg.setTexture("previousDenominator",currentDirectSupport);
                                glProg.setTexture("previousFrameSupport",currentDirectFrameSupport);glProg.setTexture("chromaGuide",wronskiAlterChromaGuide);
                                glProg.setTexture("physicalCfa",alterCfa);
                                glProg.setTextureCompute("alterCfa",wronskiAlterCfa,false);glProg.setTextureCompute("alterCov",wronskiAlterCov,false);
                                glProg.setTextureCompute("outNumerator",nextDirectRgb,true);glProg.setTextureCompute("outDenominator",nextDirectSupport,true);
                                glProg.setTextureCompute("outFrameSupport",nextDirectFrameSupport,true);glProg.computeAuto(raw,1);
                                long iris26468AccumulateMs=System.currentTimeMillis()-iris26468AccumulateStart;
                                Log.d(TAG,"IRIS_26486_BJZHOU_REJECTION_GRAPH frame="+i
                                        +" graph=guide_clipping_unblocker_rejection_clippedGaussian_reduce4_bilateral_postprocess_dilation"
                                        +" rejectionMs="+iris26486RejectMs+" opponentAccumulateMs="+iris26468AccumulateMs
                                        +" ipolMonteCarlo=false finalWeightGpu=true");
                            } finally {
                                /* persistent full/quarter rejection scratch retained until burst end */
                            }
'''
recon_text = recon_text[:start] + new_rejection + recon_text[end:]
write(recon, recon_text)

# Close quarter scratch after the sequential loop.
replace_once(
    recon,
    "            if(iris26480RobustMinScratch!=null)iris26480RobustMinScratch.close();\n"
    "            if(iris26480RobustRawScratch!=null)iris26480RobustRawScratch.close();",
    "            if(iris26486RejectSmallB!=null)iris26486RejectSmallB.close();\n"
    "            if(iris26486RejectSmallA!=null)iris26486RejectSmallA.close();\n"
    "            if(iris26480RobustMinScratch!=null)iris26480RobustMinScratch.close();\n"
    "            if(iris26480RobustRawScratch!=null)iris26480RobustRawScratch.close();",
    "26486 quarter rejection scratch cleanup",
)

# Reference add receives physical pre-WB evidence for censored chroma authority.
replace_once(
    recon,
    "                    glProg.setTexture(\"chromaGuide\",wronskiReferenceChromaGuide);glProg.setVar(\"greenNoiseS\",noiseS);glProg.setVar(\"greenNoiseO\",noiseO);",
    "                    glProg.setTexture(\"chromaGuide\",wronskiReferenceChromaGuide);glProg.setVar(\"greenNoiseS\",noiseS);glProg.setVar(\"greenNoiseO\",noiseO);\n"
    "                    glProg.setTexture(\"physicalCfa\",referenceCfa);glProg.setVar(\"physicalExposureScale\",1.0f);\n"
    "                    glProg.setVar(\"physicalClipStart\",0.94f);glProg.setVar(\"physicalClipEnd\",0.995f);",
    "26486 reference physical clipping bindings",
)

# The old per-frame MC call must be gone after replacing the entire rejection block.
# Also remove any stale direct robustness log identity that survived outside it.
recon_text = read(recon)
if "MotionV2IpolNoiseCurve" in recon_text:
    raise SystemExit("26486 active reconstruction still contains MotionV2IpolNoiseCurve")
if 'useAssetProgram("motionv2/mfsr_robustness_half"' in recon_text:
    raise SystemExit("26486 active reconstruction still uses mfsr_robustness_half")
if 'useAssetProgram("motionv2/mfsr_robustness_erode"' in recon_text:
    raise SystemExit("26486 active reconstruction still uses old 5x5 erosion")

# Short-recovery Java bindings no longer use WB/opposed reconstruction. Flow z/w
# semantics are interpreted by the shader as variation/cancellation.
replace_once(
    recon,
    "                    glProg.setVar(\"shortToNormalScale\",shortToNormalScale);glProg.setVar(\"wbR\",r);glProg.setVar(\"wbG\",1.0f);glProg.setVar(\"wbB\",b);\n"
    "                    glProg.setVar(\"highlightClipThreshold\",0.985f);glProg.setVar(\"highlightCeiling\",8.0f);glProg.setVar(\"minimumFlowConfidence\",0.30f);",
    "                    glProg.setVar(\"shortToNormalScale\",shortToNormalScale);\n"
    "                    glProg.setVar(\"highlightClipThreshold\",0.94f);glProg.setVar(\"highlightClipEnd\",0.995f);\n"
    "                    glProg.setVar(\"highlightCeiling\",8.0f);glProg.setVar(\"minimumFlowConfidence\",0.30f);",
    "26486 short physical-domain bindings",
)

# Update current architecture trace from the intentionally pure-26478 comparison.
recon_text = read(recon).replace(
    '                        + " censoredHighlightDualEvidence=false"\n'
    '                        + " sharedSpatialClipCoherence=false"\n'
    '                        + " clippedSamplesOrdinaryObservations=false cfaPhysicalClipAuthority=true");',
    '                        + " censoredHighlightDualEvidence=true"\n'
    '                        + " sharedSpatialClipCoherence=true"\n'
    '                        + " clippedOpponentClaimsSuppressed=true cfaPhysicalClipAuthority=true");')
write(recon, recon_text)


# -------------------------------------------------------------------------
# 6) Censored opponent merge. Green/radiometric evidence remains uncensored;
# only R-G / B-G claims are gated by original physical sensor validity.
# -------------------------------------------------------------------------
write(accum, r'''#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D flowTexture;
uniform highp sampler2D robustnessTexture;
uniform highp sampler2D previousNumerator;
uniform highp sampler2D previousDenominator;
uniform highp sampler2D previousFrameSupport;
uniform highp sampler2D chromaGuide;
uniform highp sampler2D physicalCfa;
layout(rgba16f,binding=0) uniform highp readonly image2D alterCfa;
layout(rgba32f,binding=1) uniform highp readonly image2D alterCov;
layout(rgba32f,binding=2) uniform highp writeonly image2D outNumerator;
layout(rgba32f,binding=3) uniform highp writeonly image2D outDenominator;
layout(rgba32f,binding=4) uniform highp writeonly image2D outFrameSupport;
uniform ivec2 rawSize;
uniform ivec2 rawHalf;
uniform int cfaPattern;
uniform float maximumSupport;
uniform float greenNoiseS;
uniform float greenNoiseO;
uniform float physicalExposureScale;
uniform float physicalClipStart;
uniform float physicalClipEnd;
int componentIndex(ivec2 p){return ((p.y&1)<<1)|(p.x&1);}
int componentColor(int c){if(cfaPattern==0){if(c==0)return 0;if(c==3)return 2;return 1;}if(cfaPattern==1){if(c==1)return 0;if(c==2)return 2;return 1;}if(cfaPattern==2){if(c==2)return 0;if(c==1)return 2;return 1;}if(c==3)return 0;if(c==0)return 2;return 1;}
float cfaAt(ivec2 p){p=clamp(p,ivec2(0),rawSize-ivec2(1));vec4 v=imageLoad(alterCfa,p>>1);int c=componentIndex(p);return c==0?v.r:(c==1?v.g:(c==2?v.b:v.a));}
float physicalAt(ivec2 p){p=clamp(p,ivec2(0),rawSize-ivec2(1));vec4 v=texelFetch(physicalCfa,p>>1,0);int c=componentIndex(p);float x=c==0?v.r:(c==1?v.g:(c==2?v.b:v.a));return max(x/max(physicalExposureScale,1e-6),0.0);}
float siteValidity(ivec2 p){return 1.0-smoothstep(physicalClipStart,physicalClipEnd,physicalAt(p));}
float sharedChromaValidity(ivec2 p){
    float own=siteValidity(p);float same=own;float n=1.0;ivec2 d[4]=ivec2[4](ivec2(2,0),ivec2(-2,0),ivec2(0,2),ivec2(0,-2));
    for(int i=0;i<4;i++){same+=siteValidity(p+d[i]);n+=1.0;}same/=n;
    float clipMax=0.0;for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++)clipMax=max(clipMax,1.0-siteValidity(p+ivec2(x,y)));
    float sharedValidity=1.0-0.35*smoothstep(0.10,0.90,clipMax);
    return clamp((0.60*own+0.40*same)*sharedValidity,0.0,1.0);
}
float greenAt(ivec2 p){p=clamp(p,ivec2(0),rawSize-ivec2(1));return texelFetch(chromaGuide,p,0).r;}
float chromaGuideWeight(float sampleGreen,float targetGreen){float sig=max(max(sampleGreen,targetGreen),0.0);float variance=max(greenNoiseS*sig+greenNoiseO,0.0);float sigma=max(2.5*sqrt(variance),1.0/160.0);float d=(sampleGreen-targetGreen)/sigma;return exp(-0.5*d*d);}
mat2 covAt(ivec2 p){p=clamp(p,ivec2(0),rawHalf-ivec2(1));vec4 v=imageLoad(alterCov,p);return mat2(v.x,v.y,v.z,v.w);}
mat2 interpolateCov(vec2 gp){ivec2 fl=ivec2(max(floor(gp),vec2(0.0)));ivec2 ce=min(fl+ivec2(1),rawHalf-ivec2(1));vec2 f=fract(gp);mat2 c00=covAt(fl),c01=covAt(ivec2(ce.x,fl.y)),c10=covAt(ivec2(fl.x,ce.y)),c11=covAt(ce);return c00*((1.0-f.x)*(1.0-f.y))+c01*(f.x*(1.0-f.y))+c10*((1.0-f.x)*f.y)+c11*(f.x*f.y);}
mat2 invertCov(mat2 m){float d=m[0][0]*m[1][1]-m[0][1]*m[1][0];if(abs(d)<=1e-10)return mat2(1,0,0,1);return mat2(m[1][1],-m[0][1],-m[1][0],m[0][0])/d;}
/* IRIS_26486_BJZHOU_CENSORED_OPPONENT_DUAL_EVIDENCE
 * Green/radiometric evidence keeps the full robust Wronski weight. A physically
 * clipped R/B observation is a lower bound, not an exact opponent-color value;
 * only its R-G/B-G authority is attenuated using pre-WB/pre-repair sensor data.
 */
void main(){
    ivec2 outP=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(outP,rawSize)))return;
    vec2 uv=(vec2(outP)+0.5)/vec2(rawSize);vec2 rawFlow=2.0*texture(flowTexture,uv).xy;vec2 lr=vec2(outP)+0.5;vec2 lrMov=lr+rawFlow;
    if(lrMov.x<0.0||lrMov.y<0.0||lrMov.x>=float(rawSize.x)||lrMov.y>=float(rawSize.y))return;
    ivec2 robustP=clamp(outP>>1,ivec2(0),rawHalf-ivec2(1));float R=clamp(texelFetch(robustnessTexture,robustP,0).r,0.0,1.0);
    mat2 invCov=invertCov(interpolateCov(lrMov/2.0-0.5));ivec2 center=ivec2(lrMov);vec2 movTarget=lrMov-0.5;
    float gs=0.0,gw=0.0;for(int iy=-1;iy<=1;iy++)for(int ix=-1;ix<=1;ix++){ivec2 p=center+ivec2(ix,iy);if(any(lessThan(p,ivec2(0)))||any(greaterThanEqual(p,rawSize)))continue;if(componentColor(componentIndex(p))!=1)continue;vec2 d=vec2(p)-movTarget;float w=exp(-0.5*max(dot(d,invCov*d),0.0))*R;gs+=cfaAt(p)*w;gw+=w;}float targetGreen=gs/max(gw,1e-8);
    vec3 addNum=vec3(gs,0.0,0.0),addDen=vec3(gw,0.0,0.0);
    for(int iy=-1;iy<=1;iy++)for(int ix=-1;ix<=1;ix++){ivec2 p=center+ivec2(ix,iy);if(any(lessThan(p,ivec2(0)))||any(greaterThanEqual(p,rawSize)))continue;int c=componentColor(componentIndex(p));if(c==1)continue;vec2 d=vec2(p)-movTarget;float spatial=exp(-0.5*max(dot(d,invCov*d),0.0));float lg=greenAt(p);float valid=sharedChromaValidity(p);float w=spatial*R*chromaGuideWeight(lg,targetGreen)*valid;float opponent=cfaAt(p)-lg;if(c==0){addNum.y+=w*opponent;addDen.y+=w;}else{addNum.z+=w*opponent;addDen.z+=w;}}
    vec4 n=texelFetch(previousNumerator,outP,0);n.rgb+=addNum;imageStore(outNumerator,outP,n);
    vec4 d=texelFetch(previousDenominator,outP,0);d.rgb+=addDen;imageStore(outDenominator,outP,d);
    vec4 fs=texelFetch(previousFrameSupport,outP,0);fs.r=min(max(maximumSupport-1.0,0.0),max(fs.r,0.0)+R);fs.g+=addDen.y;fs.b+=addDen.z;fs.a+=0.5*(addDen.y+addDen.z);imageStore(outFrameSupport,outP,fs);
}
''')

write(refadd, r'''#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D chromaGuide;
uniform highp sampler2D physicalCfa;
layout(rgba16f,binding=0) uniform highp readonly image2D referenceCfa;
layout(rgba32f,binding=1) uniform highp readonly image2D referenceCov;
uniform highp sampler2D currentNumerator;
uniform highp sampler2D currentDenominator;
uniform highp sampler2D currentFrameSupport;
layout(rgba32f,binding=4) uniform highp writeonly image2D outNumerator;
layout(rgba32f,binding=5) uniform highp writeonly image2D outDenominator;
layout(rgba32f,binding=6) uniform highp writeonly image2D outFrameSupport;
uniform ivec2 rawSize;uniform ivec2 rawHalf;uniform int cfaPattern;
uniform float greenNoiseS;uniform float greenNoiseO;
uniform float physicalExposureScale;uniform float physicalClipStart;uniform float physicalClipEnd;
int componentIndex(ivec2 p){return ((p.y&1)<<1)|(p.x&1);}
int componentColor(int c){if(cfaPattern==0){if(c==0)return 0;if(c==3)return 2;return 1;}if(cfaPattern==1){if(c==1)return 0;if(c==2)return 2;return 1;}if(cfaPattern==2){if(c==2)return 0;if(c==1)return 2;return 1;}if(c==3)return 0;if(c==0)return 2;return 1;}
float cfaAt(ivec2 p){p=clamp(p,ivec2(0),rawSize-ivec2(1));vec4 v=imageLoad(referenceCfa,p>>1);int c=componentIndex(p);return c==0?v.r:(c==1?v.g:(c==2?v.b:v.a));}
float physicalAt(ivec2 p){p=clamp(p,ivec2(0),rawSize-ivec2(1));vec4 v=texelFetch(physicalCfa,p>>1,0);int c=componentIndex(p);float x=c==0?v.r:(c==1?v.g:(c==2?v.b:v.a));return max(x/max(physicalExposureScale,1e-6),0.0);}
float siteValidity(ivec2 p){return 1.0-smoothstep(physicalClipStart,physicalClipEnd,physicalAt(p));}
float sharedChromaValidity(ivec2 p){float own=siteValidity(p),same=own,n=1.0;ivec2 d[4]=ivec2[4](ivec2(2,0),ivec2(-2,0),ivec2(0,2),ivec2(0,-2));for(int i=0;i<4;i++){same+=siteValidity(p+d[i]);n+=1.0;}same/=n;float clipMax=0.0;for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++)clipMax=max(clipMax,1.0-siteValidity(p+ivec2(x,y)));return clamp((0.60*own+0.40*same)*(1.0-0.35*smoothstep(0.10,0.90,clipMax)),0.0,1.0);}
float greenAt(ivec2 p){p=clamp(p,ivec2(0),rawSize-ivec2(1));return texelFetch(chromaGuide,p,0).r;}
float chromaGuideWeight(float sampleGreen,float targetGreen){float sig=max(max(sampleGreen,targetGreen),0.0);float variance=max(greenNoiseS*sig+greenNoiseO,0.0);float sigma=max(2.5*sqrt(variance),1.0/160.0);float d=(sampleGreen-targetGreen)/sigma;return exp(-0.5*d*d);}
mat2 covAt(ivec2 p){p=clamp(p,ivec2(0),rawHalf-ivec2(1));vec4 v=imageLoad(referenceCov,p);return mat2(v.x,v.y,v.z,v.w);}
mat2 interpolateCov(vec2 gp){ivec2 fl=ivec2(max(floor(gp),vec2(0.0)));ivec2 ce=min(fl+ivec2(1),rawHalf-ivec2(1));vec2 f=fract(gp);mat2 c00=covAt(fl),c01=covAt(ivec2(ce.x,fl.y)),c10=covAt(ivec2(fl.x,ce.y)),c11=covAt(ce);return c00*((1.0-f.x)*(1.0-f.y))+c01*(f.x*(1.0-f.y))+c10*((1.0-f.x)*f.y)+c11*(f.x*f.y);}
mat2 invertCov(mat2 m){float d=m[0][0]*m[1][1]-m[0][1]*m[1][0];if(abs(d)<=1e-10)return mat2(1,0,0,1);return mat2(m[1][1],-m[0][1],-m[1][0],m[0][0])/d;}
/* IRIS_26486_BJZHOU_REFERENCE_CENSORED_OPPONENT_AUTHORITY */
void main(){
    ivec2 outP=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(outP,rawSize)))return;
    vec4 oldNum=texelFetch(currentNumerator,outP,0),oldDen=texelFetch(currentDenominator,outP,0),fs=texelFetch(currentFrameSupport,outP,0);
    vec2 coarse=vec2(outP);mat2 invCov=invertCov(interpolateCov((coarse-vec2(0.5))/2.0));ivec2 center=ivec2(round(coarse));
    float gs=0.0,gw=0.0;for(int iy=-1;iy<=1;iy++)for(int ix=-1;ix<=1;ix++){ivec2 p=center+ivec2(ix,iy);if(any(lessThan(p,ivec2(0)))||any(greaterThanEqual(p,rawSize)))continue;if(componentColor(componentIndex(p))!=1)continue;vec2 delta=vec2(p)-coarse;float w=exp(-0.5*max(dot(delta,invCov*delta),0.0));gs+=cfaAt(p)*w;gw+=w;}float targetGreen=gs/max(gw,1e-8);vec3 refNum=vec3(gs,0.0,0.0),refDen=vec3(gw,0.0,0.0);
    for(int iy=-1;iy<=1;iy++)for(int ix=-1;ix<=1;ix++){ivec2 p=center+ivec2(ix,iy);if(any(lessThan(p,ivec2(0)))||any(greaterThanEqual(p,rawSize)))continue;int c=componentColor(componentIndex(p));if(c==1)continue;vec2 delta=vec2(p)-coarse;float spatial=exp(-0.5*max(dot(delta,invCov*delta),0.0));float lg=greenAt(p);float w=spatial*chromaGuideWeight(lg,targetGreen)*sharedChromaValidity(p);float opp=cfaAt(p)-lg;if(c==0){refNum.y+=opp*w;refDen.y+=w;}else{refNum.z+=opp*w;refDen.z+=w;}}
    imageStore(outNumerator,outP,vec4(oldNum.rgb+refNum,0.0));imageStore(outDenominator,outP,vec4(oldDen.rgb+refDen,1.0));fs.g+=refDen.y;fs.b+=refDen.z;fs.a+=0.5*(refDen.y+refDen.z);imageStore(outFrameSupport,outP,fs);
}
''')

write(finalize, r'''#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
layout(rgba32f,binding=0) uniform highp readonly image2D currentNumerator;
layout(rgba32f,binding=1) uniform highp readonly image2D currentDenominator;
layout(rgba32f,binding=2) uniform highp readonly image2D currentFrameSupport;
layout(rgba32f,binding=3) uniform highp writeonly image2D outRgb;
uniform float wbR;uniform float wbG;uniform float wbB;
/* IRIS_26486_CENSORED_OPPONENT_FINALIZE_REFERENCE_NEUTRAL
 * Denominators are true unsaturated opponent support. When R-G/B-G evidence is
 * censored, fade only that opponent term toward the reference/common neutral
 * authority; green/radiometric brightness is never discarded.
 */
void main(){
    ivec2 p=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(p,imageSize(outRgb))))return;
    vec3 num=imageLoad(currentNumerator,p).rgb;vec3 den=max(imageLoad(currentDenominator,p).rgb,vec3(1e-12));
    float g=num.x/den.x;float rg=num.y/den.y;float bg=num.z/den.z;
    float expectedOpponent=max(0.5*den.x,1e-8);float rgAuthority=smoothstep(0.08,0.35,den.y/expectedOpponent);float bgAuthority=smoothstep(0.08,0.35,den.z/expectedOpponent);
    rg*=rgAuthority;bg*=bgAuthority;vec3 wbRgb=vec3(g+rg,g,g+bg);
    vec3 sensorRgb=wbRgb/vec3(max(wbR,1e-6),max(wbG,1e-6),max(wbB,1e-6));
    float frameSupport=1.0+max(imageLoad(currentFrameSupport,p).r,0.0);imageStore(outRgb,p,vec4(max(sensorRgb,vec3(0.0)),frameSupport));
}
''')

write(short_shader, r'''#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D normalRgb;
uniform highp sampler2D flowTexture;
layout(rgba16f,binding=0) uniform highp readonly image2D referenceCfa;
layout(rgba16f,binding=1) uniform highp readonly image2D shortCfa;
layout(rgba32f,binding=2) uniform highp writeonly image2D outRgb;
uniform ivec2 rawSize;uniform ivec2 rawHalf;uniform int cfaPattern;
uniform float shortToNormalScale;uniform float highlightClipThreshold;uniform float highlightClipEnd;uniform float highlightCeiling;uniform float minimumFlowConfidence;
int ci(ivec2 p){return ((p.y&1)<<1)|(p.x&1);}int cc(int c){if(cfaPattern==0){if(c==0)return 0;if(c==3)return 2;return 1;}if(cfaPattern==1){if(c==1)return 0;if(c==2)return 2;return 1;}if(cfaPattern==2){if(c==2)return 0;if(c==1)return 2;return 1;}if(c==3)return 0;if(c==0)return 2;return 1;}
float at(ivec2 p,bool sh){p=clamp(p,ivec2(0),rawSize-ivec2(1));vec4 v=sh?imageLoad(shortCfa,p>>1):imageLoad(referenceCfa,p>>1);int c=ci(p);return max(c==0?v.r:(c==1?v.g:(c==2?v.b:v.a)),0.0);}
float clipSeverity(ivec2 center,int color){float s=0.0,n=0.0;for(int y=-2;y<=2;y++)for(int x=-2;x<=2;x++){ivec2 q=clamp(center+ivec2(x,y),ivec2(0),rawSize-ivec2(1));if(cc(ci(q))!=color)continue;s+=smoothstep(highlightClipThreshold,highlightClipEnd,at(q,false));n+=1.0;}return s/max(n,1.0);}
vec2 shortMeasurement(ivec2 center,int color){float bestD=1e9;ivec2 best=center;for(int y=-2;y<=2;y++)for(int x=-2;x<=2;x++){ivec2 q=clamp(center+ivec2(x,y),ivec2(0),rawSize-ivec2(1));if(cc(ci(q))!=color)continue;float d=float(x*x+y*y);if(d<bestD){bestD=d;best=q;}}float sensor=at(best,true);float valid=1.0-smoothstep(highlightClipThreshold,highlightClipEnd,sensor);return vec2(min(sensor*shortToNormalScale,highlightCeiling),valid);}
/* IRIS_26486_SHORT_PHYSICAL_UP_OR_DOWN_REPLACEMENT
 * A short RAW is authoritative only if normal is clipped, short is unsaturated,
 * and the 26484 flow is coherent. The candidate may correct upward OR downward;
 * the old max(candidate,fallback) one-sided rule is forbidden.
 */
void main(){
    ivec2 p=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(p,rawSize)))return;vec4 normal=texelFetch(normalRgb,p,0);
    vec4 f=texture(flowTexture,(vec2(p)+0.5)/vec2(rawSize));float variation=max(f.z,0.0);float cancelled=step(0.5,f.w);float flowConfidence=(1.0-cancelled)*exp(-80.0*variation);vec2 sp=vec2(p)+0.5+2.0*f.xy;
    if(sp.x<0.0||sp.y<0.0||sp.x>=float(rawSize.x)||sp.y>=float(rawSize.y)||flowConfidence<minimumFlowConfidence){imageStore(outRgb,p,normal);return;}
    ivec2 sc=ivec2(sp);vec3 outc=normal.rgb;float flowGate=smoothstep(minimumFlowConfidence,0.80,flowConfidence);
    for(int c=0;c<3;c++){float normalClip=clipSeverity(p,c);if(normalClip<=0.0)continue;vec2 m=shortMeasurement(sc,c);float use=smoothstep(0.08,0.75,normalClip)*m.y*flowGate;outc[c]=mix(normal[c],m.x,use);}
    imageStore(outRgb,p,vec4(max(outc,vec3(0.0)),normal.a));
}
''')


# -------------------------------------------------------------------------
# 7) Full deterministic bjzhou-style rejection graph shader assets.
# -------------------------------------------------------------------------
write(shader_dir / "mfsr_bjzhou_unblocker.glsl", r'''#define LAYOUT //
LAYOUT
precision highp float;precision highp image2D;
uniform highp sampler2D flowTexture;
layout(r32f,binding=0) uniform highp writeonly image2D outUnblocker;
uniform ivec2 rawHalf;
/* IRIS_26486_BJZHOU_REJECTION_UNBLOCKER */
void main(){ivec2 p=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(p,rawHalf)))return;vec4 f=texelFetch(flowTexture,p,0);float variation=max(f.z,0.0);float cancelled=step(0.5,f.w);vec2 mn=f.xy,mx=f.xy;for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++){vec2 q=texelFetch(flowTexture,clamp(p+ivec2(x,y),ivec2(0),rawHalf-ivec2(1)),0).xy;mn=min(mn,q);mx=max(mx,q);}float span=length(mx-mn);float flowCoherence=(1.0-cancelled)*exp(-80.0*variation)*exp(-0.18*span);imageStore(outUnblocker,p,vec4(clamp(flowCoherence,0.0,1.0)));}
''')

write(shader_dir / "mfsr_bjzhou_rejection_base.glsl", r'''#define LAYOUT //
LAYOUT
precision highp float;precision highp image2D;
uniform highp sampler2D referenceWbCfa;uniform highp sampler2D alterWbCfa;uniform highp sampler2D referencePhysicalCfa;uniform highp sampler2D alterPhysicalCfa;uniform highp sampler2D flowTexture;uniform highp sampler2D unblockerTexture;
layout(r32f,binding=0) uniform highp writeonly image2D outRejection;
uniform ivec2 rawHalf;uniform float noiseS;uniform float noiseO;uniform float physicalExposureScale;uniform float clipStart;uniform float clipEnd;
vec4 bilinear4(sampler2D t,vec2 p){p=clamp(p,vec2(0.0),vec2(rawHalf)-vec2(1.001));ivec2 a=ivec2(floor(p));ivec2 b=min(a+ivec2(1),rawHalf-ivec2(1));vec2 f=fract(p);vec4 x=mix(texelFetch(t,a,0),texelFetch(t,ivec2(b.x,a.y),0),f.x);vec4 y=mix(texelFetch(t,ivec2(a.x,b.y),0),texelFetch(t,b,0),f.x);return mix(x,y,f.y);}
vec4 validity(vec4 sensor){return vec4(1.0)-smoothstep(vec4(clipStart),vec4(clipEnd),max(sensor,vec4(0.0)));}
/* IRIS_26486_BJZHOU_CLIPPING_AWARE_REJECTION_BASE */
void main(){ivec2 p=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(p,rawHalf)))return;vec4 flow=texelFetch(flowTexture,p,0);vec2 ap=vec2(p)+flow.xy;if(ap.x<0.0||ap.y<0.0||ap.x>=float(rawHalf.x)||ap.y>=float(rawHalf.y)){imageStore(outRejection,p,vec4(1.0));return;}vec4 r=texelFetch(referenceWbCfa,p,0),a=bilinear4(alterWbCfa,ap);vec4 rp=texelFetch(referencePhysicalCfa,p,0),apv=bilinear4(alterPhysicalCfa,ap)/max(physicalExposureScale,1e-6);vec4 v=min(validity(rp),validity(apv));float z=0.0,s=0.0;for(int c=0;c<4;c++){float vv=v[c];float sig=max(max(r[c],a[c]),0.0);float var=max(noiseS*sig+noiseO,1e-8);float d=r[c]-a[c];z+=vv*d*d/var;s+=vv;}float photo=s>0.20?1.0-exp(-0.125*z/max(s,1e-6)):0.0;float unblock=clamp(texelFetch(unblockerTexture,p,0).r,0.0,1.0);float evidence=max(photo,1.0-unblock);imageStore(outRejection,p,vec4(clamp(evidence,0.0,1.0)));}
''')

for axis, name in (("x", "mfsr_bjzhou_clipped_gaussian_h.glsl"), ("y", "mfsr_bjzhou_clipped_gaussian_v.glsl")):
    delta = "ivec2(k,0)" if axis == "x" else "ivec2(0,k)"
    write(shader_dir / name, f'''#define LAYOUT //
LAYOUT
precision highp float;precision highp image2D;
uniform highp sampler2D inputEvidence;
layout(r32f,binding=0) uniform highp writeonly image2D outEvidence;
uniform ivec2 size;
/* IRIS_26486_BJZHOU_CLIPPED_GAUSSIAN_{axis.upper()} */
void main(){{ivec2 p=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(p,size)))return;float c=texelFetch(inputEvidence,p,0).r;float w[5]=float[5](1.0,4.0,6.0,4.0,1.0);float sum=0.0,sw=0.0;for(int k=-2;k<=2;k++){{ivec2 q=clamp(p+{delta},ivec2(0),size-ivec2(1));float v=texelFetch(inputEvidence,q,0).r;v=clamp(v,c-0.22,c+0.22);float ww=w[k+2];sum+=ww*v;sw+=ww;}}imageStore(outEvidence,p,vec4(clamp(sum/max(sw,1e-6),0.0,1.0)));}}
''')

write(shader_dir / "mfsr_bjzhou_rejection_reduce4.glsl", r'''#define LAYOUT //
LAYOUT
precision highp float;precision highp image2D;
uniform highp sampler2D inputEvidence;
layout(r32f,binding=0) uniform highp writeonly image2D outReduced;
uniform ivec2 inputSize;
/* IRIS_26486_BJZHOU_REJECTION_REDUCE4 */
void main(){ivec2 q=ivec2(gl_GlobalInvocationID.xy);ivec2 os=imageSize(outReduced);if(any(greaterThanEqual(q,os)))return;float s=0.0,m=0.0,n=0.0;ivec2 b=q*4;for(int y=0;y<4;y++)for(int x=0;x<4;x++){ivec2 p=b+ivec2(x,y);if(any(greaterThanEqual(p,inputSize)))continue;float v=texelFetch(inputEvidence,p,0).r;s+=v;m=max(m,v);n+=1.0;}float e=0.65*(s/max(n,1.0))+0.35*m;imageStore(outReduced,q,vec4(clamp(e,0.0,1.0)));}
''')

write(shader_dir / "mfsr_bjzhou_rejection_bilateral.glsl", r'''#define LAYOUT //
LAYOUT
precision highp float;precision highp image2D;
uniform highp sampler2D inputReduced;uniform highp sampler2D referencePackedCfa;
layout(r32f,binding=0) uniform highp writeonly image2D outFiltered;
uniform ivec2 smallSize;uniform ivec2 rawHalf;
float guide(ivec2 q){ivec2 p=clamp(q*4+ivec2(2),ivec2(0),rawHalf-ivec2(1));vec4 v=texelFetch(referencePackedCfa,p,0);return 0.25*(v.r+v.g+v.b+v.a);}
/* IRIS_26486_BJZHOU_BILATERAL_REJECTION */
void main(){ivec2 p=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(p,smallSize)))return;float gc=guide(p),sum=0.0,sw=0.0;for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++){ivec2 q=clamp(p+ivec2(x,y),ivec2(0),smallSize-ivec2(1));float dg=guide(q)-gc;float spatial=exp(-0.65*float(x*x+y*y));float range=exp(-0.5*dg*dg/(0.015*0.015));float w=spatial*range;sum+=w*texelFetch(inputReduced,q,0).r;sw+=w;}imageStore(outFiltered,p,vec4(clamp(sum/max(sw,1e-6),0.0,1.0)));}
''')

write(shader_dir / "mfsr_bjzhou_rejection_postprocess.glsl", r'''#define LAYOUT //
LAYOUT
precision highp float;precision highp image2D;
uniform highp sampler2D fullEvidence;uniform highp sampler2D smallEvidence;
layout(r32f,binding=0) uniform highp writeonly image2D outWeight;
uniform ivec2 rawHalf;uniform ivec2 smallSize;
/* IRIS_26486_BJZHOU_REJECTION_POSTPROCESS */
void main(){ivec2 p=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(p,rawHalf)))return;float full=texelFetch(fullEvidence,p,0).r;vec2 uv=(vec2(p)+0.5)/vec2(rawHalf);float coarse=texture(smallEvidence,uv).r;float evidence=max(full,0.85*coarse);float weight=exp(-3.0*clamp(evidence,0.0,1.0));imageStore(outWeight,p,vec4(clamp(weight,0.0,1.0)));}
''')

write(shader_dir / "mfsr_bjzhou_rejection_dilate.glsl", r'''#define LAYOUT //
LAYOUT
precision highp float;precision highp image2D;
uniform highp sampler2D inputWeight;
layout(r32f,binding=0) uniform highp writeonly image2D outWeight;
uniform ivec2 size;
/* IRIS_26486_BJZHOU_REJECTION_DILATION_FINAL_WEIGHT */
void main(){ivec2 p=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(p,size)))return;float w=1.0;for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++){ivec2 q=clamp(p+ivec2(x,y),ivec2(0),size-ivec2(1));w=min(w,texelFetch(inputWeight,q,0).r);}imageStore(outWeight,p,vec4(clamp(w,0.0,1.0)));}
''')


# -------------------------------------------------------------------------
# Transform end-to-end assertions. These are deliberately semantic, not just
# marker counts, so Action failures stop before source overlay/build.
# -------------------------------------------------------------------------
cap_text = read(cap)
batch_text = read(batch)
saver_text = read(saver)
default_text = read(default_saver)
hdrx_text = read(hdrx)
recon_text = read(recon)

for marker in (
    "IRIS_26486_NO_WAIT_MAXIMUM_FRAME_POLICY",
    "IRIS_26486_FREEZE_BUFFER_AT_SHUTTER_NO_TOPUP_WAIT",
    "IRIS_26486_EXPOSURE_ENERGY_EV_GROUPING",
    "IRIS_26486_WHOLE_GROUP_EXPOSURE_SPAN_PROOF",
    "IRIS_26486_NONBLOCKING_SHORT_HIGHLIGHT_TICKET",
    "IRIS_26486_BATCH_QUEUE_CAPTURE_OWNERSHIP",
    "IRIS_26486_MOTIONBATCH_SOLE_PROCESSING_OWNER",
):
    if marker not in cap_text:
        raise SystemExit("missing capture marker " + marker)

trigger_start = cap_text.index("    private void triggerZslCapture() {")
trigger_end = cap_text.index("    }    // IRIS_26343_GENERATION_SAFE_ZSL", trigger_start)
trigger_body = cap_text[trigger_start:trigger_end]
if "CaptureController.isProcessing" in trigger_body:
    raise SystemExit("26486 Motion shutter still blocked by global isProcessing")
if "pollMotionTopUp();" in trigger_body:
    raise SystemExit("26486 active Motion shutter still enters top-up polling")
if "MOTION_26486_EXPOSURE_HALF_WINDOW_EV = 0.05" not in cap_text:
    raise SystemExit("26486 0.05 EV half-window missing")
for required_clip in ("0.985f", "0.998f"):
    if required_clip not in recon_text:
        raise SystemExit("26486 proven 26469 clip transition missing " + required_clip)
if "SaverImplementation.IMAGE_BUFFER.addAll(iris26480ProcessingFrames)" in cap_text:
    raise SystemExit("26486 capture still publishes Motion frames to static IMAGE_BUFFER")

for marker in ("IRIS_26486_ASYNC_SHORT_HIGHLIGHT_SLOT", "shortHighlightSlot"):
    if marker not in batch_text:
        raise SystemExit("missing MotionBatch slot marker " + marker)
if "IMAGE_BUFFER" in saver_text[saver_text.index("public void runMotionRaw"):saver_text.index("public void runRaw", saver_text.index("public void runMotionRaw"))]:
    raise SystemExit("26486 ImageSaver.runMotionRaw still references IMAGE_BUFFER")
if "IRIS_26486_DEFAULTSAVER_MOTIONBATCH_SOLE_OWNER" not in default_text:
    raise SystemExit("26486 direct DefaultSaver MotionBatch path missing")
# New method body itself must be static-buffer independent.
dm0=default_text.index("public void runMotionBatch")
dm1=default_text.index("public void runRaw",dm0)
if "IMAGE_BUFFER" in default_text[dm0:dm1]:
    raise SystemExit("26486 DefaultSaver.runMotionBatch references static IMAGE_BUFFER")

for marker in (
    "IRIS_26486_NO_IPOL_MONTE_CARLO_ACTIVE_PATH",
    "IRIS_26486_BJZHOU_REJECTION_GRAPH",
    "IRIS_26486_LATE_NONBLOCKING_SHORT_TAKE",
):
    if marker not in recon_text:
        raise SystemExit("missing reconstruction marker " + marker)
if "MotionV2IpolNoiseCurve" in recon_text:
    raise SystemExit("IPOL Monte-Carlo class reference survived in active reconstruction")
for old_asset in ("mfsr_robustness_half", "mfsr_robustness_erode"):
    if f'useAssetProgram("motionv2/{old_asset}"' in recon_text:
        raise SystemExit("old hybrid robustness asset still active: " + old_asset)
for asset in (
    "mfsr_bjzhou_unblocker",
    "mfsr_bjzhou_rejection_base",
    "mfsr_bjzhou_clipped_gaussian_h",
    "mfsr_bjzhou_clipped_gaussian_v",
    "mfsr_bjzhou_rejection_reduce4",
    "mfsr_bjzhou_rejection_bilateral",
    "mfsr_bjzhou_rejection_postprocess",
    "mfsr_bjzhou_rejection_dilate",
):
    if f'useAssetProgram("motionv2/{asset}"' not in recon_text:
        raise SystemExit("missing active bjzhou rejection asset " + asset)

if "max(pow(max(o,0.0),power),fallback)" in read(short_shader):
    raise SystemExit("one-sided short highlight max(candidate,fallback) survived")
if "IRIS_26486_SHORT_PHYSICAL_UP_OR_DOWN_REPLACEMENT" not in read(short_shader):
    raise SystemExit("26486 bidirectional short recovery marker missing")
if "IRIS_26486_BJZHOU_CENSORED_OPPONENT_DUAL_EVIDENCE" not in read(accum):
    raise SystemExit("26486 censored opponent shader missing")
if "physicalCfa" not in read(accum) or "sharedChromaValidity" not in read(accum):
    raise SystemExit("26486 physical saturation authority missing from opponent merge")
if "IRIS_26486_CENSORED_OPPONENT_FINALIZE_REFERENCE_NEUTRAL" not in read(finalize):
    raise SystemExit("26486 censored finalizer missing")
if "IRIS_26486_HDRX_MOTIONBATCH_ENTRY" not in hdrx_text:
    raise SystemExit("26486 Hdrx direct batch entry missing")

print("26486 transform PASS")
