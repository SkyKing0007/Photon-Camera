#!/usr/bin/env python3
from pathlib import Path
import re, sys, math

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")

def p(rel): return root / rel

def read(rel): return p(rel).read_text()

def write(rel, text):
    path = p(rel); path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text)

def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{label} anchor count={n}")
    return text.replace(old, new, 1)

def regex_once(text, pattern, repl, label, flags=re.S):
    out, n = re.subn(pattern, repl, text, count=1, flags=flags)
    if n != 1:
        raise SystemExit(f"{label} regex count={n}")
    return out

CAP = "app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java"
FRAME = "app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java"
BATCH = "app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java"
SAVER = "app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java"
HDRX = "app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java"
RECON = "app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
RENDER = "app/src/main/assets/shaders/motionv2/render.glsl"
SHORT_SHADER = "app/src/main/assets/shaders/motionv2/short_highlight_recover.glsl"
VER = "app/version.properties"

# -------------------------------------------------------------------------
# ImageFrame: explicit role + actual Camera2 metadata for the short frame.
# -------------------------------------------------------------------------
t = read(FRAME)
anchor = "    public IsoExpoSelector.ExpoPair pair;\n"
insert = anchor + """

    /* IRIS_26480_SHORT_HIGHLIGHT_FRAME_ROLE_V1
     * This frame is transported beside the normal equal-exposure Motion group.
     * HdrxProcessor removes it before any Wronski alignment/fusion loop.
     */
    public boolean motionV2ShortHighlightFrame = false;
    public long motionV2ActualExposureNs = 0L;
    public int motionV2ActualIso = 0;
    public double motionV2ExposureEnergy = 0.0;
    public float motionV2NoiseS = Float.NaN;
    public float motionV2NoiseO = Float.NaN;
"""
t = replace_once(t, anchor, insert, "ImageFrame role")
write(FRAME, t)

# -------------------------------------------------------------------------
# MotionBatch/ImageSaver: retainedCount remains the normal Wronski count,
# while processingFrameCount transports the optional short frame as well.
# -------------------------------------------------------------------------
t = read(BATCH)
t = replace_once(t,
    "    public final int retainedCount;\n",
    "    public final int retainedCount;\n    public final int processingFrameCount;\n",
    "MotionBatch processing count field")
t = replace_once(t,
    "        this.retainedCount = frames.size();\n",
    """        int normalRetained = 0;
        for (ImageFrame frame : this.frames) {
            if (frame != null && !frame.motionV2ShortHighlightFrame) normalRetained++;
        }
        this.retainedCount = normalRetained;
        this.processingFrameCount = this.frames.size();
""",
    "MotionBatch retained count")
write(BATCH, t)

t = read(SAVER)
old = """        setFrameCount(batch.retainedCount);
        setImageFormat(batch.imageFormat);
        implementation = ImageSaverSelector.getImageSaver(batch.imageFormat, implementation);
        implementation.frameCount = batch.retainedCount;
        SaverImplementation.IMAGE_BUFFER.clear();
        SaverImplementation.IMAGE_BUFFER.addAll(batch.frames);
        implementation.bufferLock = false;
        updateFrameCount(batch.retainedCount);
"""
new = """        /* IRIS_26480_SHORT_HIGHLIGHT_TRANSPORT_V1
         * DefaultSaver must slice the normal frames plus the one role-tagged
         * short frame. HdrxProcessor removes the short frame before Wronski.
         */
        setFrameCount(batch.processingFrameCount);
        setImageFormat(batch.imageFormat);
        implementation = ImageSaverSelector.getImageSaver(batch.imageFormat, implementation);
        implementation.frameCount = batch.processingFrameCount;
        SaverImplementation.IMAGE_BUFFER.clear();
        SaverImplementation.IMAGE_BUFFER.addAll(batch.frames);
        implementation.bufferLock = false;
        updateFrameCount(batch.processingFrameCount);
"""
t = replace_once(t, old, new, "ImageSaver Motion transport")
write(SAVER, t)

# -------------------------------------------------------------------------
# CaptureController: replace 26478 whole-group recollection with a separate
# ~1/3 exposure HAL-AE short probe while preserving the existing normal ZSL ring.
# -------------------------------------------------------------------------
t = read(CAP)
fields_anchor = """    private boolean mMotion26478HighlightSafeBiasApplied = false;
    private int mMotion26478HighlightSafeBaseSteps = 0;
    private int mMotion26478HighlightSafeTargetSteps = 0;
"""
fields_new = fields_anchor + """

    /* IRIS_26480_BJZHOU_STYLE_SEPARATE_SHORT_HIGHLIGHT_V1
     * Architecture borrowed from bjzhou/PhotonCamera: one short frame is a
     * separate highlight-recovery observation, never a normal fusion frame.
     * Exposure role is determined from ACTUAL Camera2 exposure*ISO metadata.
     */
    private static final double MOTION_26480_SHORT_EXPOSURE_DIVISOR = 3.0;
    private static final float MOTION_26480_SHORT_PROTECTION_EV = 1.5849625f; // log2(3)
    private static final long MOTION_26480_SHORT_WAIT_MS = 650L;
    private static final double MOTION_26480_SHORT_RATIO_MAX = 0.60;
    private static final double MOTION_26480_SHORT_RATIO_MIN = 0.10;
    private boolean mMotion26480ShortRequested = false;
    private long mMotion26480ShortBaselineExposureNs = 0L;
    private int mMotion26480ShortBaselineIso = 0;
    private double mMotion26480ShortBaselineEnergy = 0.0;
    private volatile long mMotion26480ShortResultTimestampNs = 0L;
    private volatile long mMotion26480ShortActualExposureNs = 0L;
    private volatile int mMotion26480ShortActualIso = 0;
    private volatile double mMotion26480ShortActualEnergy = 0.0;
"""
t = replace_once(t, fields_anchor, fields_new, "26480 capture fields")

# Preserve more than the slider count only while the separate short frame is pending.
t = replace_once(t,
    """                    int maxFrames = Math.min(PhotonCamera.getSettings().frameCount, 37);
                    while (mZslRingBuffer.size() > maxFrames) {
""",
    """                    /* IRIS_26480_SHORT_RING_HEADROOM_V1
                     * ImageReader already owns frameCount+3 buffers in Motion.
                     * Keep up to two extra acquired Images only while the short
                     * highlight observation is pending, so normal ZSL frames
                     * are not evicted by the short probe.
                     */
                    int maxFrames = Math.min(
                            PhotonCamera.getSettings().frameCount
                                    + (mMotion26480ShortRequested ? 2 : 0),
                            39);
                    while (mZslRingBuffer.size() > maxFrames) {
""",
    "26480 ring headroom")

# Replace the 26478 apply method wholesale, but keep the restore function name
# out of the old body so all old whole-group semantics are removed.
pattern = r"    private boolean applyMotion26478HighlightSafeBurstBiasIfNeeded\(\) \{.*?\n    \}\n\n    private void restoreMotion26478HighlightSafeBurstBias\(\) \{.*?\n    \}\n"
new_methods = r'''    private boolean applyMotion26480ShortHighlightBiasIfNeeded() {
        if (!isZslMode()
                || mPreviewRequestBuilder == null
                || mCaptureSession == null
                || mCameraCharacteristics == null
                || mPreviewCaptureResult == null
                || mMotion26380RawSampleCount < 64
                || Float.isNaN(mMotion26380RawHighlightFraction)) {
            return false;
        }

        Long previewTimestamp = mPreviewCaptureResult.get(CaptureResult.SENSOR_TIMESTAMP);
        Long baselineExposure = mPreviewCaptureResult.get(CaptureResult.SENSOR_EXPOSURE_TIME);
        Integer baselineIso = mPreviewCaptureResult.get(CaptureResult.SENSOR_SENSITIVITY);
        long rawAgeNs = previewTimestamp == null || mMotion26380RawSignalTimestampNs <= 0L
                ? Long.MAX_VALUE
                : Math.abs(previewTimestamp - mMotion26380RawSignalTimestampNs);
        boolean rawFresh = rawAgeNs <= 180_000_000L;
        if (!rawFresh
                || mMotion26380RawHighlightFraction < MOTION_26478_HIGHLIGHT_FRACTION_TRIGGER
                || baselineExposure == null || baselineExposure <= 0L
                || baselineIso == null || baselineIso <= 0) {
            return false;
        }

        android.util.Range<Integer> range = mCameraCharacteristics.get(
                CameraCharacteristics.CONTROL_AE_COMPENSATION_RANGE);
        android.util.Rational step = mCameraCharacteristics.get(
                CameraCharacteristics.CONTROL_AE_COMPENSATION_STEP);
        if (range == null || step == null || step.floatValue() <= 0.0f) {
            Log.w(TAG, "IRIS_26480_SHORT_HIGHLIGHT unavailable reason=noAeCompensationRange");
            return false;
        }

        Integer current = mPreviewRequestBuilder.get(
                CaptureRequest.CONTROL_AE_EXPOSURE_COMPENSATION);
        int baseSteps = current != null ? current : 0;
        baseSteps = Math.max(range.getLower(), Math.min(range.getUpper(), baseSteps));
        int protectionSteps = Math.max(1, Math.round(
                MOTION_26480_SHORT_PROTECTION_EV / step.floatValue()));
        int targetSteps = Math.max(range.getLower(), Math.min(
                range.getUpper(), baseSteps - protectionSteps));
        if (targetSteps >= baseSteps) return false;

        try {
            mMotion26480ShortRequested = true;
            mMotion26480ShortBaselineExposureNs = baselineExposure;
            mMotion26480ShortBaselineIso = baselineIso;
            mMotion26480ShortBaselineEnergy = ExposureIndex.time2sec(baselineExposure) * baselineIso;
            mMotion26480ShortResultTimestampNs = 0L;
            mMotion26480ShortActualExposureNs = 0L;
            mMotion26480ShortActualIso = 0;
            mMotion26480ShortActualEnergy = 0.0;

            mPreviewRequestBuilder.set(
                    CaptureRequest.CONTROL_AE_EXPOSURE_COMPENSATION, targetSteps);
            mMotion26478HighlightSafeBiasApplied = true;
            mMotion26478HighlightSafeBaseSteps = baseSteps;
            mMotion26478HighlightSafeTargetSteps = targetSteps;

            /* Crucial 26480 boundary: DO NOT clear the normal ZSL ring. */
            rebuildPreviewBuilder();

            Log.i(TAG, "IRIS_26480_SHORT_HIGHLIGHT_REQUESTED"
                    + " rawHighlightFraction=" + mMotion26380RawHighlightFraction
                    + " rawAgeNs=" + rawAgeNs
                    + " divisor=" + MOTION_26480_SHORT_EXPOSURE_DIVISOR
                    + " requestedProtectionEv=" + MOTION_26480_SHORT_PROTECTION_EV
                    + " baselineExposureNs=" + baselineExposure
                    + " baselineIso=" + baselineIso
                    + " baselineEnergy=" + mMotion26480ShortBaselineEnergy
                    + " baseSteps=" + baseSteps
                    + " targetSteps=" + targetSteps
                    + " halAeRemainsOn=true"
                    + " normalRingPreserved=true"
                    + " normalWronskiExposureGroupUnchanged=true");
            return true;
        } catch (IllegalArgumentException | IllegalStateException error) {
            mMotion26480ShortRequested = false;
            mMotion26478HighlightSafeBiasApplied = false;
            Log.w(TAG, "IRIS_26480_SHORT_HIGHLIGHT skipped "
                    + error.getClass().getSimpleName());
            return false;
        }
    }

    private void restoreMotion26480ShortHighlightBias() {
        if (!mMotion26478HighlightSafeBiasApplied
                || mPreviewRequestBuilder == null
                || mCaptureSession == null) {
            mMotion26478HighlightSafeBiasApplied = false;
            return;
        }
        int restoreSteps = mMotion26478HighlightSafeBaseSteps;
        int usedSteps = mMotion26478HighlightSafeTargetSteps;
        try {
            mPreviewRequestBuilder.set(
                    CaptureRequest.CONTROL_AE_EXPOSURE_COMPENSATION, restoreSteps);
            rebuildPreviewBuilder();
            Log.i(TAG, "IRIS_26480_SHORT_HIGHLIGHT_BIAS_RESTORED"
                    + " usedSteps=" + usedSteps
                    + " restoredSteps=" + restoreSteps
                    + " halAeRemainsOn=true");
        } catch (IllegalArgumentException | IllegalStateException error) {
            Log.w(TAG, "IRIS_26480_SHORT_HIGHLIGHT_RESTORE skipped "
                    + error.getClass().getSimpleName());
        } finally {
            mMotion26478HighlightSafeBiasApplied = false;
        }
    }
'''
t = regex_once(t, pattern, new_methods, "replace 26478 capture methods")

# Trigger uses the new short probe, not whole-group recollection.
t = replace_once(t,
    """        final boolean iris26478HighlightSafeBurst =
                applyMotion26478HighlightSafeBurstBiasIfNeeded();
""",
    """        final boolean iris26480ShortHighlightRequested =
                applyMotion26480ShortHighlightBiasIfNeeded();
""",
    "26480 trigger call")
t = t.replace("iris26478HighlightSafeBurst=\"\n                        + iris26478HighlightSafeBurst",
              "iris26480ShortHighlightRequested=\"\n                        + iris26480ShortHighlightRequested")
t = t.replace("iris26478RawHighlightFraction=", "iris26480RawHighlightFraction=")
t = t.replace("iris26478AeTargetSteps=", "iris26480ShortAeTargetSteps=")

# Capture-result recognition: actual exposure*ISO decides whether the requested
# observation really is short enough. This is deliberately after result-map insert.
result_anchor = """                    mZslResultMap.put(sensorTimestamp, result);
                    while (mZslResultMap.size() > MAX_ZSL_RESULT_METADATA) {
"""
result_insert = """                    mZslResultMap.put(sensorTimestamp, result);

                    /* IRIS_26480_SHORT_ACTUAL_METADATA_MATCH_V1 */
                    if (mMotion26480ShortRequested
                            && mMotion26478HighlightSafeBiasApplied
                            && mMotion26480ShortResultTimestampNs == 0L
                            && mMotion26480ShortBaselineEnergy > 0.0) {
                        Long shortExp = result.get(CaptureResult.SENSOR_EXPOSURE_TIME);
                        Integer shortIso = result.get(CaptureResult.SENSOR_SENSITIVITY);
                        if (shortExp != null && shortExp > 0L
                                && shortIso != null && shortIso > 0) {
                            double shortEnergy = ExposureIndex.time2sec(shortExp) * shortIso;
                            double ratio = shortEnergy / mMotion26480ShortBaselineEnergy;
                            if (ratio >= MOTION_26480_SHORT_RATIO_MIN
                                    && ratio <= MOTION_26480_SHORT_RATIO_MAX) {
                                mMotion26480ShortResultTimestampNs = sensorTimestamp;
                                mMotion26480ShortActualExposureNs = shortExp;
                                mMotion26480ShortActualIso = shortIso;
                                mMotion26480ShortActualEnergy = shortEnergy;
                                Log.i(TAG, "IRIS_26480_SHORT_ACTUAL_ACCEPTED"
                                        + " timestamp=" + sensorTimestamp
                                        + " actualExposureNs=" + shortExp
                                        + " actualIso=" + shortIso
                                        + " actualEnergy=" + shortEnergy
                                        + " energyRatioToNormal=" + ratio
                                        + " targetRatio=" + (1.0 / MOTION_26480_SHORT_EXPOSURE_DIVISOR));
                                restoreMotion26480ShortHighlightBias();
                            }
                        }
                    }
                    while (mZslResultMap.size() > MAX_ZSL_RESULT_METADATA) {
"""
t = replace_once(t, result_anchor, result_insert, "short result metadata")

# Poll gate: if requested, wait briefly until the accepted result has a matching RAW Image.
poll_anchor = """        boolean targetReady = validBuffered >= mMotionTopUpTargetFrames;
        boolean timedOut = elapsed >= MOTION_TOP_UP_TIMEOUT_MS;
"""
poll_insert = """        boolean targetReady = validBuffered >= mMotionTopUpTargetFrames;
        boolean timedOut = elapsed >= MOTION_TOP_UP_TIMEOUT_MS;

        boolean iris26480ShortRawReady = false;
        if (mMotion26480ShortRequested && mMotion26480ShortResultTimestampNs > 0L) {
            synchronized (mZslBufferLock) {
                for (Image iris26480Image : mZslRingBuffer) {
                    if (iris26480Image != null
                            && Math.abs(iris26480Image.getTimestamp()
                                    - mMotion26480ShortResultTimestampNs) <= 40_000_000L) {
                        iris26480ShortRawReady = true;
                        break;
                    }
                }
            }
        }
        boolean iris26480ShortExpired = mMotion26480ShortRequested
                && !iris26480ShortRawReady
                && elapsed >= MOTION_26480_SHORT_WAIT_MS;
        if (iris26480ShortExpired) {
            restoreMotion26480ShortHighlightBias();
            Log.w(TAG, "IRIS_26480_SHORT_HIGHLIGHT_TIMEOUT"
                    + " elapsedMs=" + elapsed
                    + " acceptedResultTimestamp=" + mMotion26480ShortResultTimestampNs
                    + " normalWronskiStillAvailable=true");
            mMotion26480ShortRequested = false;
        }
        boolean iris26480ShortGateReady = !mMotion26480ShortRequested
                || iris26480ShortRawReady;
"""
t = replace_once(t, poll_anchor, poll_insert, "short poll gate")

t = replace_once(t,
    """        if (iris26379TargetReady
                || iris26383TimeoutMinimumReady) {
""",
    """        if ((iris26379TargetReady
                || iris26383TimeoutMinimumReady)
                && iris26480ShortGateReady) {
""",
    "short completion gate")

# Restore on any early exit / before normal finalization.
t = t.replace("restoreMotion26478HighlightSafeBurstBias();", "restoreMotion26480ShortHighlightBias();")

# Final drain: transport the accepted short frame separately instead of rejecting it as
# a different exposure group. The existing drain window was exactly frameCount;
# include one extra slot when a short result exists so the short frame cannot evict
# one normal Wronski observation before role separation.
t = replace_once(t,
    """        int take = Math.min(rawImages.size(), frameCount);
        int skip = rawImages.size() - take;
""",
    """        /* IRIS_26480_SHORT_DRAIN_HEADROOM_V1 */
        int iris26480DrainTarget = frameCount
                + (mMotion26480ShortResultTimestampNs > 0L ? 1 : 0);
        int take = Math.min(rawImages.size(), iris26480DrainTarget);
        int skip = rawImages.size() - take;
""",
    "26480 short drain headroom")

sel_anchor = """        List<ImageFrame> selected = new ArrayList<>();
        HashMap<Long, TotalCaptureResult> selectedResults = new HashMap<>();
"""
sel_new = sel_anchor + """        ImageFrame iris26480ShortFrame = null;
        TotalCaptureResult iris26480ShortResult = null;
"""
t = replace_once(t, sel_anchor, sel_new, "short drain declarations")

loop_anchor = """            boolean exposureAccepted =
                    motionExposurePairMatches(
                            frameResult,
                            bestExposureGroup);
            if (!exposureAccepted) {
                img.close();
                continue;
            }
"""
short_branch = """            boolean iris26480IsShort =
                    mMotion26480ShortResultTimestampNs > 0L
                            && Math.abs(img.getTimestamp()
                                    - mMotion26480ShortResultTimestampNs) <= 40_000_000L;
            if (iris26480IsShort && iris26480ShortFrame == null) {
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
                ImageFrame shortFrame = new ImageFrame(
                        img.getPlanes()[0].getBuffer(), img.getFormat(),
                        width, rowStride, offset, bufCapacity);
                shortFrame.timestamp = img.getTimestamp();
                shortFrame.width = width;
                shortFrame.height = height;
                if (PhotonCamera.getSettings().binning) {
                    shortFrame.width /= 2;
                    shortFrame.height /= 2;
                }
                long shortExpNs = mMotion26480ShortActualExposureNs;
                int shortIso = mMotion26480ShortActualIso;
                if (frameResult != null) {
                    Long e = frameResult.get(CaptureResult.SENSOR_EXPOSURE_TIME);
                    Integer s = frameResult.get(CaptureResult.SENSOR_SENSITIVITY);
                    if (e != null) shortExpNs = e;
                    if (s != null) shortIso = s;
                }
                shortFrame.motionV2ShortHighlightFrame = true;
                shortFrame.motionV2ActualExposureNs = shortExpNs;
                shortFrame.motionV2ActualIso = shortIso;
                shortFrame.motionV2ExposureEnergy =
                        ExposureIndex.time2sec(shortExpNs) * shortIso;
                if (frameResult != null) {
                    android.util.Pair<Double, Double>[] np =
                            frameResult.get(CaptureResult.SENSOR_NOISE_PROFILE);
                    if (np != null && np.length > 0) {
                        double sSum = 0.0, oSum = 0.0;
                        int n = 0;
                        for (android.util.Pair<Double, Double> pair : np) {
                            if (pair != null && pair.first != null && pair.second != null
                                    && Double.isFinite(pair.first)
                                    && Double.isFinite(pair.second)) {
                                sSum += pair.first;
                                oSum += pair.second;
                                n++;
                            }
                        }
                        if (n > 0) {
                            shortFrame.motionV2NoiseS = (float)(sSum / n);
                            shortFrame.motionV2NoiseO = (float)(oSum / n);
                        }
                    }
                    selectedResults.put(shortFrame.timestamp, frameResult);
                }
                mExposures.put(shortFrame.timestamp, shortFrame.motionV2ExposureEnergy);
                iris26480ShortFrame = shortFrame;
                iris26480ShortResult = frameResult;
                img.close();
                Log.i(TAG, "IRIS_26480_SHORT_FRAME_TRANSPORTED"
                        + " timestamp=" + shortFrame.timestamp
                        + " exposureNs=" + shortFrame.motionV2ActualExposureNs
                        + " iso=" + shortFrame.motionV2ActualIso
                        + " energy=" + shortFrame.motionV2ExposureEnergy
                        + " noiseS=" + shortFrame.motionV2NoiseS
                        + " noiseO=" + shortFrame.motionV2NoiseO
                        + " excludedFromNormalExposureGroup=true");
                continue;
            }

            boolean exposureAccepted =
                    motionExposurePairMatches(frameResult, bestExposureGroup);
            if (!exposureAccepted) {
                img.close();
                continue;
            }
"""
t = replace_once(t, loop_anchor, short_branch, "short drain branch")

# Add actual per-frame metadata fields to normal frames too; this lets reconstruction
# derive the exact short/reference energy scale after reference ownership is resolved.
normal_meta_anchor = """            mExposures.put(frame.timestamp, ExposureIndex.time2sec(actualExposureNs) * actualIso);
            selected.add(frame);
"""
normal_meta_new = """            frame.motionV2ActualExposureNs = actualExposureNs;
            frame.motionV2ActualIso = actualIso;
            frame.motionV2ExposureEnergy = ExposureIndex.time2sec(actualExposureNs) * actualIso;
            mExposures.put(frame.timestamp, frame.motionV2ExposureEnergy);
            selected.add(frame);
"""
t = replace_once(t, normal_meta_anchor, normal_meta_new, "normal frame metadata")

# Create a processing list containing the normal group plus optional short frame.
t = replace_once(t,
    """        int actualCount = selected.size();

        mImageSaver = new ImageSaver(cameraEventsListener);
        mImageSaver.setFrameCount(actualCount);
""",
    """        int actualCount = selected.size();
        List<ImageFrame> iris26480ProcessingFrames = new ArrayList<>(selected);
        if (iris26480ShortFrame != null) {
            iris26480ProcessingFrames.add(iris26480ShortFrame);
        }

        mImageSaver = new ImageSaver(cameraEventsListener);
        mImageSaver.setFrameCount(iris26480ProcessingFrames.size());
""",
    "processing list")
t = replace_once(t,
    """        mImageSaver.implementation.frameCount = actualCount;

        SaverImplementation.IMAGE_BUFFER.clear();
        SaverImplementation.IMAGE_BUFFER.addAll(selected);
""",
    """        mImageSaver.implementation.frameCount = iris26480ProcessingFrames.size();

        SaverImplementation.IMAGE_BUFFER.clear();
        SaverImplementation.IMAGE_BUFFER.addAll(iris26480ProcessingFrames);
""",
    "processing buffer")

# MotionBatch gets both, but retainedCount remains normal count by role.
t = replace_once(t,
    """        final MotionBatch motionBatch = new MotionBatch(
                selected, new ArrayList<>(BurstShakiness), mExposures, selectedResults,
""",
    """        final MotionBatch motionBatch = new MotionBatch(
                iris26480ProcessingFrames, new ArrayList<>(BurstShakiness), mExposures, selectedResults,
""",
    "MotionBatch short transport")

# Reset request state only after the processing-owned copy exists.
mb_anchor = """                mPreviewCaptureRequest, CaptureController.RAW_FORMAT, cameraRotation, candidateCount);
        processExecutor.execute(() -> {
"""
mb_new = """                mPreviewCaptureRequest, CaptureController.RAW_FORMAT, cameraRotation, candidateCount);
        Log.i(TAG, "IRIS_26480_SHORT_BATCH_BOUNDARY"
                + " normalWronskiFrames=" + motionBatch.retainedCount
                + " processingFrames=" + motionBatch.processingFrameCount
                + " shortFramePresent=" + (iris26480ShortFrame != null)
                + " shortNeverNormalFusion=true");
        mMotion26480ShortRequested = false;
        mMotion26480ShortResultTimestampNs = 0L;
        processExecutor.execute(() -> {
"""
t = replace_once(t, mb_anchor, mb_new, "batch boundary")
write(CAP, t)

# -------------------------------------------------------------------------
# HdrxProcessor: strip the role-tagged short frame before all normal exposure,
# gyro, reference-selection and Wronski logic. Pass it only to reconstruction.
# -------------------------------------------------------------------------
t = read(HDRX)
apply_anchor = """        Log.d(TAG, "ApplyHdrX() mImageFramesToProcess.size():" + mImageFramesToProcess.size());
        int width = mImageFramesToProcess.get(0).width;
"""
apply_new = """        Log.d(TAG, "ApplyHdrX() mImageFramesToProcess.size():" + mImageFramesToProcess.size());

        /* IRIS_26480_SHORT_FRAME_SPLIT_BEFORE_WRONSKI_V1 */
        ImageFrame iris26480ShortHighlightFrame = null;
        if (cameraMode == CameraMode.MOTION) {
            for (int i = mImageFramesToProcess.size() - 1; i >= 0; i--) {
                ImageFrame candidate = mImageFramesToProcess.get(i);
                if (candidate != null && candidate.motionV2ShortHighlightFrame) {
                    if (iris26480ShortHighlightFrame == null) {
                        iris26480ShortHighlightFrame = candidate;
                    } else {
                        candidate.close();
                    }
                    mImageFramesToProcess.remove(i);
                }
            }
            if (mImageFramesToProcess.isEmpty()) {
                if (iris26480ShortHighlightFrame != null) iris26480ShortHighlightFrame.close();
                throw new IllegalStateException("26480 short frame cannot replace normal Wronski group");
            }
            Log.d(TAG, "IRIS_26480_SHORT_FRAME_SPLIT_BEFORE_WRONSKI"
                    + " normalFrames=" + mImageFramesToProcess.size()
                    + " shortPresent=" + (iris26480ShortHighlightFrame != null)
                    + " shortInWronskiList=false");
        }
        int width = mImageFramesToProcess.get(0).width;
"""
t = replace_once(t, apply_anchor, apply_new, "Hdrx short split")

# Raw-only early return must close the detached short frame.
raw_return_anchor = """                    processingEventsListener.onProcessingFinished(
                            "Motion RAW Processing Finished");
                    callback.onFinished();
                    return;
"""
raw_return_new = """                    if (iris26480ShortHighlightFrame != null) {
                        iris26480ShortHighlightFrame.close();
                        iris26480ShortHighlightFrame = null;
                    }
                    processingEventsListener.onProcessingFinished(
                            "Motion RAW Processing Finished");
                    callback.onFinished();
                    return;
"""
t = replace_once(t, raw_return_anchor, raw_return_new, "raw-only short cleanup")

call_anchor = """                    MotionV2CfaReconstruction.reconstruct(
                            new Point(width, height),
                            images,
                            iris26363ReferenceTimestamp,
                            processingParameters);
"""
call_new = """                    MotionV2CfaReconstruction.reconstruct(
                            new Point(width, height),
                            images,
                            iris26363ReferenceTimestamp,
                            processingParameters,
                            iris26480ShortHighlightFrame);
            iris26480ShortHighlightFrame = null; // reconstruction owns/closes it
"""
t = replace_once(t, call_anchor, call_new, "reconstruct short argument")
write(HDRX, t)

# -------------------------------------------------------------------------
# Reconstruction: optional short path is aligned with the SAME prepared Wronski
# reference but written to a separate recovery texture. It never touches normal
# currentNumerator/currentDenominator/currentFrameSupport.
# -------------------------------------------------------------------------
t = read(RECON)
# Method signature: tolerate whitespace but require exactly one public reconstruct.
t = regex_once(t,
    r"public static MotionV2Merger\.Result reconstruct\(\s*Point size,\s*List<ImageFrame> inputImages,\s*long referenceTimestamp,\s*Parameters parameters\) \{",
    """public static MotionV2Merger.Result reconstruct(
            Point size,
            List<ImageFrame> inputImages,
            long referenceTimestamp,
            Parameters parameters,
            ImageFrame shortHighlightFrame) {""",
    "reconstruct signature")

# Disable 26478 speaker edge correlation call. Existing general support telemetry remains.
t = regex_once(t,
    r"\n\s*if \(directBayer && output != null\) \{\s*/\*\s*\* IRIS_26478_SPEAKER_SUPPORT_DIAGNOSTIC.*?iris26478LogSpeakerSupportEdges\(.*?\);\s*\}\n",
    "\n            /* IRIS_26480_DISABLE_SPEAKER_EDGE_DIAGNOSTIC_V1\n"
    "             * The 26478 scene-specific CPU edge/color correlation is retired.\n"
    "             * Existing support summary remains logging-only.\n"
    "             */\n",
    "disable speaker diagnostic")

# Insert recovery between normal Wronski finalization and required FLOAT32 bridge readback.
readback_anchor = """            imageOutput.BufferLoad();
            output = imageOutput.textureBuffer(
                    new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                    true);
"""
recovery = """            /* IRIS_26480_ALIGNED_SHORT_SENSOR_HIGHLIGHT_RECOVERY_V1
             * Normal Wronski reconstruction is already complete. The short frame
             * is aligned against the same cached reference, reconstructed into a
             * SEPARATE RGBA32F texture, and consulted only where reference CFA
             * evidence is clipped and the short observation remains unsaturated.
             * No write ever targets Wronski numerator/denominator/support.
             */
            GLTexture iris26480ReadbackOutput = imageOutput;
            GLTexture iris26480ShortRaw = null;
            GLTexture iris26480ShortCfa = null;
            GLTexture iris26480ShortWbCfa = null;
            GLTexture iris26480Recovered = null;
            MotionV2Alignment.Result iris26480ShortAlignment = null;
            try {
                if (directBayer
                        && shortHighlightFrame != null
                        && shortHighlightFrame.buffer != null
                        && reference != null
                        && reference.motionV2ExposureEnergy > 0.0
                        && shortHighlightFrame.motionV2ExposureEnergy > 0.0
                        && wronskiPreparedAlignment != null) {
                    float shortToNormalScale = (float)Math.max(
                            1.0,
                            Math.min(8.0,
                                    reference.motionV2ExposureEnergy
                                            / shortHighlightFrame.motionV2ExposureEnergy));

                    iris26480ShortRaw = new GLTexture(
                            raw,
                            new GLFormat(GLFormat.DataType.UNSIGNED_16, 1),
                            shortHighlightFrame.buffer,
                            GL_NEAREST,
                            GL_CLAMP_TO_EDGE);
                    iris26480ShortCfa = new GLTexture(
                            rawHalf,
                            new GLFormat(GLFormat.DataType.FLOAT_16, 4),
                            null,
                            GL_NEAREST,
                            GL_CLAMP_TO_EDGE);
                    glProg.setLayout(tile, tile, 1);
                    glProg.useAssetProgram("motionv2/raw_to_cfa", true);
                    glProg.setVar("whiteLevel", (float) parameters.whiteLevel);
                    glProg.setVar("blackLevel", blackLevel);
                    glProg.setVar("exposure", shortToNormalScale);
                    glProg.setTexture("inTexture", iris26480ShortRaw);
                    glProg.setTextureCompute("outTexture", iris26480ShortCfa, true);
                    glProg.computeAuto(rawHalf, 1);

                    final float iris26480WbR = directSensorGains[0]
                            / Math.max(directSensorGains[1], 1.0e-6f);
                    final float iris26480WbB = directSensorGains[2]
                            / Math.max(directSensorGains[1], 1.0e-6f);
                    iris26480ShortWbCfa = new GLTexture(
                            rawHalf,
                            new GLFormat(GLFormat.DataType.FLOAT_16, 4),
                            null,
                            GL_NEAREST,
                            GL_CLAMP_TO_EDGE);
                    glProg.setLayout(tile, tile, 1);
                    glProg.useAssetProgram("motionv2/mfsr_wb_cfa", true);
                    glProg.setVar("cfaPattern", (int) parameters.cfaPattern);
                    glProg.setVar("wbR", iris26480WbR);
                    glProg.setVar("wbG", 1.0f);
                    glProg.setVar("wbB", iris26480WbB);
                    glProg.setTextureCompute("inputCfa", iris26480ShortCfa, false);
                    glProg.setTextureCompute("outputCfa", iris26480ShortWbCfa, true);
                    glProg.computeAuto(rawHalf, 1);

                    iris26480ShortAlignment = MotionV2WronskiAlignment.alignPrepared(
                            wronskiPreparedAlignment,
                            glProg,
                            iris26480ShortWbCfa);

                    iris26480Recovered = new GLTexture(
                            raw,
                            new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                            null,
                            GL_NEAREST,
                            GL_CLAMP_TO_EDGE);
                    glProg.setLayout(tile, tile, 1);
                    glProg.useAssetProgram("motionv2/short_highlight_recover", true);
                    glProg.setVar("rawSize", raw);
                    glProg.setVar("rawHalf", rawHalf);
                    glProg.setVar("cfaPattern", (int) parameters.cfaPattern);
                    glProg.setVar("shortToNormalScale", shortToNormalScale);
                    glProg.setVar("referenceClipThreshold", 0.985f);
                    glProg.setVar("shortNativeClipThreshold", 0.970f);
                    glProg.setVar("minimumFlowConfidence", 0.35f);
                    glProg.setTexture("normalRgb", imageOutput);
                    glProg.setTexture("flowTexture", iris26480ShortAlignment.flowTexture);
                    glProg.setTextureCompute("referenceCfa", referenceCfa, false);
                    glProg.setTextureCompute("shortCfa", iris26480ShortCfa, false);
                    glProg.setTextureCompute("outRgb", iris26480Recovered, true);
                    glProg.computeAuto(raw, 1);
                    iris26480ReadbackOutput = iris26480Recovered;

                    Log.d(TAG, "IRIS_26480_ALIGNED_SHORT_SENSOR_HIGHLIGHT_RECOVERY"
                            + " shortToNormalScale=" + shortToNormalScale
                            + " shortExposureNs=" + shortHighlightFrame.motionV2ActualExposureNs
                            + " shortIso=" + shortHighlightFrame.motionV2ActualIso
                            + " shortNoiseS=" + shortHighlightFrame.motionV2NoiseS
                            + " shortNoiseO=" + shortHighlightFrame.motionV2NoiseO
                            + " alignMeanConfidence=" + iris26480ShortAlignment.meanConfidence
                            + " alignLowConfidenceFraction=" + iris26480ShortAlignment.lowConfidenceFraction
                            + " normalWronskiNumDenUnchanged=true"
                            + " recoveryDomain=sensorRGB_beforeCamera2Color"
                            + " sharpening=false");
                }

                iris26480ReadbackOutput.BufferLoad();
                output = iris26480ReadbackOutput.textureBuffer(
                        new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                        true);
            } finally {
                if (iris26480ShortAlignment != null) iris26480ShortAlignment.close();
                if (iris26480ShortWbCfa != null) iris26480ShortWbCfa.close();
                if (iris26480ShortCfa != null) iris26480ShortCfa.close();
                if (iris26480ShortRaw != null) iris26480ShortRaw.close();
                if (iris26480Recovered != null) iris26480Recovered.close();
                if (shortHighlightFrame != null) shortHighlightFrame.close();
            }
"""
t = replace_once(t, readback_anchor, recovery, "short recovery insertion")
write(RECON, t)

# -------------------------------------------------------------------------
# Sensor-domain recovery shader. Uses actual aligned short RAW only where the
# reference CFA has channel-specific clipping; flow confidence is a soft gate.
# -------------------------------------------------------------------------
shader = r'''#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D normalRgb;
uniform highp sampler2D flowTexture;
layout(rgba16f,binding=0) uniform highp readonly image2D referenceCfa;
layout(rgba16f,binding=1) uniform highp readonly image2D shortCfa;
layout(rgba32f,binding=2) uniform highp writeonly image2D outRgb;
uniform ivec2 rawSize;
uniform ivec2 rawHalf;
uniform int cfaPattern;
uniform float shortToNormalScale;
uniform float referenceClipThreshold;
uniform float shortNativeClipThreshold;
uniform float minimumFlowConfidence;

/* IRIS_26480_ALIGNED_SHORT_SENSOR_HIGHLIGHT_RECOVERY_SHADER_V1 */
int componentIndex(ivec2 p){return ((p.y&1)<<1)|(p.x&1);}
int componentColor(int c){
    if(cfaPattern==0){if(c==0)return 0;if(c==3)return 2;return 1;}
    if(cfaPattern==1){if(c==1)return 0;if(c==2)return 2;return 1;}
    if(cfaPattern==2){if(c==2)return 0;if(c==1)return 2;return 1;}
    if(c==3)return 0;if(c==0)return 2;return 1;
}
float referenceAt(ivec2 p){
    p=clamp(p,ivec2(0),rawSize-ivec2(1));
    vec4 v=imageLoad(referenceCfa,p>>1);
    int c=componentIndex(p);
    return c==0?v.r:(c==1?v.g:(c==2?v.b:v.a));
}
float shortAt(ivec2 p){
    p=clamp(p,ivec2(0),rawSize-ivec2(1));
    vec4 v=imageLoad(shortCfa,p>>1);
    int c=componentIndex(p);
    return c==0?v.r:(c==1?v.g:(c==2?v.b:v.a));
}

void main(){
    ivec2 outP=ivec2(gl_GlobalInvocationID.xy);
    if(any(greaterThanEqual(outP,rawSize))) return;

    vec4 normal=texelFetch(normalRgb,outP,0);
    vec2 uv=(vec2(outP)+0.5)/vec2(rawSize);
    vec4 flow=texture(flowTexture,uv);
    float flowConfidence=clamp(flow.z,0.0,1.0);
    vec2 shortPos=vec2(outP)+0.5+2.0*flow.xy;

    if(shortPos.x<0.0||shortPos.y<0.0
            ||shortPos.x>=float(rawSize.x)||shortPos.y>=float(rawSize.y)
            ||flowConfidence<minimumFlowConfidence){
        imageStore(outRgb,outP,normal);
        return;
    }

    ivec2 refCenter=outP;
    ivec2 shortCenter=ivec2(shortPos);
    vec2 shortTarget=shortPos-0.5;
    vec3 refSum=vec3(0.0), refW=vec3(0.0), refClipW=vec3(0.0);
    vec3 shortSum=vec3(0.0), shortW=vec3(0.0), shortValidW=vec3(0.0);

    for(int iy=-1;iy<=1;iy++)for(int ix=-1;ix<=1;ix++){
        ivec2 rp=refCenter+ivec2(ix,iy);
        if(all(greaterThanEqual(rp,ivec2(0)))&&all(lessThan(rp,rawSize))){
            int c=componentColor(componentIndex(rp));
            vec2 d=vec2(rp)-vec2(refCenter);
            float w=exp(-0.5*dot(d,d));
            float s=referenceAt(rp);
            refSum[c]+=w*s;
            refW[c]+=w;
            refClipW[c]+=w*smoothstep(referenceClipThreshold,0.9995,s);
        }

        ivec2 sp=shortCenter+ivec2(ix,iy);
        if(all(greaterThanEqual(sp,ivec2(0)))&&all(lessThan(sp,rawSize))){
            int c=componentColor(componentIndex(sp));
            vec2 d=vec2(sp)-shortTarget;
            float w=exp(-0.5*dot(d,d));
            float scaled=shortAt(sp);
            float nativeSample=scaled/max(shortToNormalScale,1.0e-6);
            shortSum[c]+=w*scaled;
            shortW[c]+=w;
            shortValidW[c]+=w*(1.0-smoothstep(shortNativeClipThreshold,0.995,nativeSample));
        }
    }

    vec3 recovered=normal.rgb;
    for(int c=0;c<3;c++){
        float rw=max(refW[c],1.0e-6);
        float sw=max(shortW[c],1.0e-6);
        float refClip=clamp(refClipW[c]/rw,0.0,1.0);
        float shortValid=clamp(shortValidW[c]/sw,0.0,1.0);
        float alignedShort=max(shortSum[c]/sw,0.0);

        /* Channel-specific sensor clipping + short validity + local alignment.
         * No neighborhood hard switch and no reference overwrite boundary.
         */
        float clipGate=smoothstep(0.15,0.72,refClip);
        float validGate=smoothstep(0.45,0.85,shortValid);
        float flowGate=smoothstep(minimumFlowConfidence,0.80,flowConfidence);
        float useShort=clipGate*validGate*flowGate;
        recovered[c]=mix(normal[c],alignedShort,useShort);
    }

    imageStore(outRgb,outP,vec4(max(recovered,vec3(0.0)),normal.a));
}
'''
write(SHORT_SHADER, shader)

# -------------------------------------------------------------------------
# Max-RGB protected tone guide: keep channel ratios, but use the largest channel
# to decide shoulder compression so a saturated channel cannot hide behind luma.
# -------------------------------------------------------------------------
t = read(RENDER)
old = """    float y=max(luminance(rgb),0.0);
    if(y<=1.0e-7) return rgb;

    float mappedY=mapHeadroomLuminance(y);
    return rgb*(mappedY/y);
"""
new = """    float y=max(luminance(rgb),0.0);
    float peak=max3(rgb);
    float guide=max(y,peak);
    if(guide<=1.0e-7) return rgb;

    /* IRIS_26480_MAX_RGB_HIGHLIGHT_TONE_GUIDE_V1
     * Saturated channels participate in the shoulder decision directly.
     * Uniform scaling preserves hue/channel ratios.
     */
    float mappedGuide=mapHeadroomLuminance(guide);
    return rgb*(mappedGuide/guide);
"""
t = replace_once(t, old, new, "max-RGB tone guide")
write(RENDER, t)

# -------------------------------------------------------------------------
# Version/build in same transform consumed by guarded build wrapper.
# -------------------------------------------------------------------------
t = read(VER)
t = regex_once(t, r"^VERSION_NAME=.*$", "VERSION_NAME=0.9726480", "version name", flags=re.M)
t = regex_once(t, r"^VERSION_BUILD=.*$", "VERSION_BUILD=26480", "version build", flags=re.M)
write(VER, t)

# Hard post-transform semantic guards.
checks = {
    CAP: [
        "IRIS_26480_BJZHOU_STYLE_SEPARATE_SHORT_HIGHLIGHT_V1",
        "normalRingPreserved=true",
        "IRIS_26480_SHORT_ACTUAL_ACCEPTED",
        "IRIS_26480_SHORT_FRAME_TRANSPORTED",
        "shortNeverNormalFusion=true",
    ],
    HDRX: [
        "IRIS_26480_SHORT_FRAME_SPLIT_BEFORE_WRONSKI_V1",
        "shortInWronskiList=false",
        "iris26480ShortHighlightFrame",
    ],
    RECON: [
        "IRIS_26480_ALIGNED_SHORT_SENSOR_HIGHLIGHT_RECOVERY_V1",
        "normalWronskiNumDenUnchanged=true",
        "short_highlight_recover",
        "IRIS_26480_DISABLE_SPEAKER_EDGE_DIAGNOSTIC_V1",
    ],
    RENDER: ["IRIS_26480_MAX_RGB_HIGHLIGHT_TONE_GUIDE_V1"],
    SHORT_SHADER: [
        "IRIS_26480_ALIGNED_SHORT_SENSOR_HIGHLIGHT_RECOVERY_SHADER_V1",
        "float referenceAt(ivec2 p)",
        "float shortAt(ivec2 p)",
    ],
}
for rel, markers in checks.items():
    text = read(rel)
    for marker in markers:
        if marker not in text:
            raise SystemExit(f"missing marker {marker} in {rel}")
if "readonly image2D tex" in read(SHORT_SHADER):
    raise SystemExit("Adreno-risk image2D function parameter remains in short recovery shader")

# Ensure the legacy whole-group destructive action is gone from the 26478 block.
cap = read(CAP)
start = cap.find("private boolean applyMotion26480ShortHighlightBiasIfNeeded")
end = cap.find("private void triggerZslCapture", start)
block = cap[start:end]
if "clearMotionUnifiedBuffer();" in block:
    raise SystemExit("26480 short-capture block must not clear normal ZSL ring")

# Capture guards for stale 26478 local names and role-drain correctness.
if "iris26478HighlightSafeBurst" in cap:
    raise SystemExit("stale iris26478HighlightSafeBurst variable remains after 26480 transform")
if "IRIS_26480_SHORT_DRAIN_HEADROOM_V1" not in cap:
    raise SystemExit("26480 short drain headroom marker missing")
if cap.count("iris26480ShortHighlightRequested") < 2:
    raise SystemExit("26480 short request trigger/log wiring incomplete")

# Ensure no call to the scene-specific speaker helper remains.
recon = read(RECON)
if "iris26478LogSpeakerSupportEdges(" in recon:
    # method definition is allowed; an invocation has 24 spaces in the old block.
    calls = len(re.findall(r"(?m)^\s{12,}iris26478LogSpeakerSupportEdges\(", recon))
    if calls:
        raise SystemExit(f"speaker diagnostic invocation remains: {calls}")

print("26480 candidate/source validation PASS")
print("26480 short frame excluded from normal Wronski list PASS")
print("26480 normal Wronski num/den shaders untouched by transform PASS")
print("26480 aligned sensor-domain short recovery marker PASS")
print("26480 max-RGB tone guide PASS")
