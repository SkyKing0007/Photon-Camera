package com.particlesdevs.photoncamera.spektra;

import android.hardware.camera2.CameraCharacteristics;
import android.util.Range;
import android.util.SizeF;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Collections;

/**
 * Sensor-exposure owner for Spektra mode.
 *
 * IRIS_26697_UNSPEKTRA_112_AE_SOLVER: this is a source-level translation of the
 * Unspektrawesome 1.1.2 sensor-AE contract recovered from the exact APK. The native meter input
 * is already a signed EV correction: positive means increase physical exposure, negative means
 * decrease it. The solver never converts that EV back through another middle-gray calculation.
 */
public final class SpektraExposureController {
    public enum Mode { AUTO, ISO_PRIORITY, SHUTTER_PRIORITY, MANUAL }

    public static final class Solution {
        public final int iso;
        public final long exposureNs;
        public final double residualEv;
        public final boolean settled;
        Solution(int iso, long exposureNs, double residualEv, boolean settled) {
            this.iso = iso;
            this.exposureNs = exposureNs;
            this.residualEv = residualEv;
            this.settled = settled;
        }

        @Override
        public boolean equals(Object value) {
            if (this == value) return true;
            if (!(value instanceof Solution)) return false;
            Solution other = (Solution) value;
            return iso == other.iso && exposureNs == other.exposureNs;
        }

        @Override
        public int hashCode() {
            return 31 * iso + Long.hashCode(exposureNs);
        }
    }

    private static final long STARTUP_NS = 1_500_000_000L;
    private static final long HISTORY_NS = 300_000_000L;
    private static final long MIN_UPDATE_NS = 16_000_000L;
    private static final double FIRST_DT_SECONDS = 1.0 / 30.0;
    private static final double STARTUP_TARGET_TAU_SECONDS = 0.025;
    private static final double STEADY_TARGET_TAU_SECONDS = 0.100;
    private static final double STARTUP_CORRECTION_TAU_SECONDS = 0.050;
    private static final double STEADY_CORRECTION_TAU_SECONDS = 0.100;
    private static final double STARTUP_RATE_EV_PER_SECOND = 12.0;
    private static final double STEADY_RATE_EV_PER_SECOND = 4.0;
    private static final double MAX_STEP_EV = 0.20;
    private static final double STARTUP_DEADBAND_EV = 0.025;
    private static final double STEADY_DEADBAND_EV = 0.040;
    private static final double LIMIT_TOLERANCE_EV = 0.08;
    private static final double SETTLED_METER_EV = 0.12;
    private static final double AE_BALANCE_MIN_EV = -1.5;
    private static final double AE_BALANCE_MAX_EV = 3.0;
    private static final long DEFAULT_AE_SLOWEST_EXPOSURE_NS = 33_333_333L;

    private static final class TargetSample {
        final long timestampNs;
        final double totalExposureEv;
        TargetSample(long timestampNs, double totalExposureEv) {
            this.timestampNs = timestampNs;
            this.totalExposureEv = totalExposureEv;
        }
    }

    private final int isoMin;
    private final int isoMax;
    private final long exposureMinNs;
    private final long exposureMaxNs;
    private final int hardwareIsoMin;
    private final int hardwareIsoMax;
    private final long hardwareExposureMinNs;
    private final long hardwareExposureMaxNs;
    private final int baseIso;
    private final double focal35;
    private final ArrayDeque<TargetSample> targetHistory = new ArrayDeque<>();

    private Mode mode = Mode.AUTO;
    private int lockedIso;
    private long lockedExposureNs;
    private double aeBalanceEv = 0.0;
    private double exposureCompensationEv = 0.0;
    private long exposureGeneration = 0L;
    private long resetEpoch = 0L;
    private long lastUpdateNs = 0L;
    private double currentIsoLog2;
    private double currentExposureLog2;
    private Solution lastReturned;
    private Double smoothedTargetTotalEv;
    private boolean startup = true;
    private long startupDeadlineNs = 0L;
    private double meterErrorEv = 0.0;
    private boolean exposureLimited = false;

    public SpektraExposureController(CameraCharacteristics c) {
        this(c, null);
    }

    public SpektraExposureController(CameraCharacteristics c, Float equivalentFocalLengthMm) {
        Range<Integer> iso = c.get(CameraCharacteristics.SENSOR_INFO_SENSITIVITY_RANGE);
        Range<Long> exp = c.get(CameraCharacteristics.SENSOR_INFO_EXPOSURE_TIME_RANGE);
        hardwareIsoMin = iso == null ? 50 : Math.max(1, iso.getLower());
        hardwareIsoMax = iso == null ? 6400 : Math.max(hardwareIsoMin, iso.getUpper());
        hardwareExposureMinNs = exp == null ? 100_000L : Math.max(1L, exp.getLower());
        hardwareExposureMaxNs = exp == null ? 1_000_000_000L
                : Math.max(hardwareExposureMinNs, exp.getUpper());

        // Unspektrawesome 1.1.2 uses the per-lens ISO floor as its base ISO and applies the
        // profile's automatic exposure bounds. Iris currently exposes the 1.1.2 default profile:
        // full supported ISO range and about 1/30 s as the slowest automatic shutter.
        isoMin = hardwareIsoMin;
        isoMax = hardwareIsoMax;
        baseIso = isoMin;
        exposureMinNs = hardwareExposureMinNs;
        exposureMaxNs = Math.min(hardwareExposureMaxNs,
                Math.max(hardwareExposureMinNs, DEFAULT_AE_SLOWEST_EXPOSURE_NS));
        focal35 = equivalentFocalLengthMm != null
                && Float.isFinite(equivalentFocalLengthMm) && equivalentFocalLengthMm > 0f
                ? equivalentFocalLengthMm
                : compute35mmEquivalent(c);

        int seedIso = isoMin;
        long pivot = Math.round(1_000_000_000.0 / (2.0 * focal35));
        long seedExposure = clampLong(pivot, exposureMinNs, exposureMaxNs);
        lockedIso = seedIso;
        lockedExposureNs = seedExposure;
        currentIsoLog2 = log2(seedIso);
        currentExposureLog2 = log2(seedExposure);
        lastReturned = new Solution(seedIso, seedExposure, 0.0, false);
        resetAeState();
    }

    /** Compatibility entry point retained for the dormant byte-protected legacy owner. */
    public synchronized void reset(long nowNs) {
        resetAeState();
    }

    /**
     * Match 1.1.2 mode/seed reset: clamp the current seed into the active mode's bounds, clear
     * temporal AE state, then advance the sensor-exposure generation used to reject stale frames.
     */
    public synchronized void setMode(Mode requestedMode, Integer iso, Long exposureNs) {
        mode = requestedMode == null ? Mode.AUTO : requestedMode;
        if (iso != null) {
            lockedIso = mode == Mode.MANUAL
                    ? clampInt(iso, hardwareIsoMin, hardwareIsoMax)
                    : clampInt(iso, isoMin, isoMax);
        }
        if (exposureNs != null) {
            lockedExposureNs = mode == Mode.MANUAL
                    ? clampLong(exposureNs, hardwareExposureMinNs, hardwareExposureMaxNs)
                    : clampLong(exposureNs, exposureMinNs, exposureMaxNs);
        }

        int seedIso = clampInt(currentIso(), activeIsoMin(), activeIsoMax());
        long seedExposure = clampLong(currentExposureNs(), activeExposureMinNs(), activeExposureMaxNs());
        if (locksIso()) seedIso = clampInt(lockedIso, activeIsoMin(), activeIsoMax());
        if (locksShutter()) {
            seedExposure = clampLong(lockedExposureNs, activeExposureMinNs(), activeExposureMaxNs());
        }
        currentIsoLog2 = log2(seedIso);
        currentExposureLog2 = log2(seedExposure);
        lastReturned = new Solution(seedIso, seedExposure, 0.0, false);
        resetAeState();
        exposureGeneration++;
        if (exposureGeneration <= 0L) exposureGeneration = 1L;
    }

    public synchronized void setAeBalanceEv(double ev) {
        aeBalanceEv = clamp(ev, AE_BALANCE_MIN_EV, AE_BALANCE_MAX_EV);
    }

    public synchronized void setExposureCompensationEv(double ev) {
        // 1.1.2 receives the already-bounded device-EV value from CameraControlState.
        exposureCompensationEv = ev;
    }

    public synchronized int getCurrentIso() { return currentIso(); }
    public synchronized long getCurrentExposureNs() { return currentExposureNs(); }
    public synchronized long getExposureGeneration() { return exposureGeneration; }
    public synchronized double getMeterErrorEv() { return meterErrorEv; }
    public synchronized boolean isExposureLimited() { return exposureLimited; }

    /**
     * Source-compatibility shim for the dormant SpektraCameraOwner. The active 26697 path never
     * uses this overload; it must supply frame generation + exact Camera2 request metadata below.
     */
    public synchronized Solution update(long nowNs, double signedMeterEv) {
        Solution changed = update(nowNs, signedMeterEv, currentIso(), currentExposureNs(),
                exposureGeneration, currentIso());
        return changed != null ? changed
                : new Solution(currentIso(), currentExposureNs(), meterErrorEv,
                        Math.abs(meterErrorEv) < SETTLED_METER_EV);
    }

    /** Initial request to seed the manual-sensor RAW stream before the first measured frame. */
    public synchronized Solution initialSolution() {
        return new Solution(currentIso(), currentExposureNs(), meterErrorEv,
                Math.abs(meterErrorEv) < SETTLED_METER_EV);
    }

    /**
     * Unspektrawesome 1.1.2 sensor-AE solve for one generation-matched RAW frame.
     *
     * @param signedMeterEv native Spektra AE result; positive means brighten, negative means darken.
     * @param actualIso actual SENSOR_SENSITIVITY from this RAW frame's TotalCaptureResult.
     * @param actualExposureNs actual SENSOR_EXPOSURE_TIME from this RAW frame.
     * @param frameExposureGeneration request-tagged sensor-AE generation for this exact frame.
     * @param requestedIso SENSOR_SENSITIVITY carried by the exact manual CaptureRequest, if present.
     * @return a new sensor request, or null when 1.1.2 would keep the current request unchanged.
     */
    public synchronized Solution update(long nowNs, double signedMeterEv, int actualIso,
            long actualExposureNs, long frameExposureGeneration, Integer requestedIso) {
        if (mode == Mode.MANUAL) return null;
        if (frameExposureGeneration != exposureGeneration) return null;
        if (nowNs <= lastUpdateNs || actualIso <= 0 || actualExposureNs <= 0L) return null;
        if (!Double.isFinite(signedMeterEv) || !Double.isFinite(exposureCompensationEv)) return null;
        if (lastUpdateNs != 0L && nowNs - lastUpdateNs < MIN_UPDATE_NS) return null;

        final double dtSeconds = lastUpdateNs == 0L
                ? FIRST_DT_SECONDS
                : (nowNs - lastUpdateNs) * 1.0e-9;
        lastUpdateNs = nowNs;

        if (startup) {
            if (startupDeadlineNs == 0L) startupDeadlineNs = nowNs + STARTUP_NS;
            if (nowNs >= startupDeadlineNs) startup = false;
        }
        final boolean fast = startup;
        final double targetTauSeconds = fast
                ? STARTUP_TARGET_TAU_SECONDS : STEADY_TARGET_TAU_SECONDS;
        final double correctionTauSeconds = fast
                ? STARTUP_CORRECTION_TAU_SECONDS : STEADY_CORRECTION_TAU_SECONDS;
        final double rateEvPerSecond = fast
                ? STARTUP_RATE_EV_PER_SECOND : STEADY_RATE_EV_PER_SECOND;
        final double deadbandEv = fast ? STARTUP_DEADBAND_EV : STEADY_DEADBAND_EV;

        // IRIS_26697_SIGNED_NATIVE_METER_EV: the native shader has already referenced 18.4% gray.
        // Do not reinterpret this as luminance or apply a second middle-gray conversion.
        meterErrorEv = signedMeterEv + exposureCompensationEv;

        final int modeIsoMin = activeIsoMin();
        final int modeIsoMax = activeIsoMax();
        final long modeExposureMin = activeExposureMinNs();
        final long modeExposureMax = activeExposureMaxNs();
        final int fixedIso = clampInt(lockedIso, modeIsoMin, modeIsoMax);
        final long fixedExposure = clampLong(lockedExposureNs, modeExposureMin, modeExposureMax);

        final double staticIsoMinLog = locksIso() ? log2(fixedIso) : log2(modeIsoMin);
        final double staticIsoMaxLog = locksIso() ? log2(fixedIso) : log2(modeIsoMax);
        final double staticExposureMinLog = locksShutter()
                ? log2(fixedExposure) : log2(modeExposureMin);
        final double staticExposureMaxLog = locksShutter()
                ? log2(fixedExposure) : log2(modeExposureMax);

        currentIsoLog2 = clamp(currentIsoLog2, staticIsoMinLog, staticIsoMaxLog);
        currentExposureLog2 = clamp(currentExposureLog2,
                staticExposureMinLog, staticExposureMaxLog);

        // 1.1.2 prefers request-tagged ISO for total-exposure accounting when Camera2 manual AE
        // is active, avoiding vendor-reported actual-ISO lag from old queued RAW frames.
        final int isoForTarget = requestedIso != null && requestedIso > 0
                ? requestedIso : actualIso;
        final double actualTotalEv = log2(isoForTarget) + log2(actualExposureNs);
        final double rawTargetTotalEv = actualTotalEv + meterErrorEv;
        final double minimumTotalEv = staticIsoMinLog + staticExposureMinLog;
        final double maximumTotalEv = staticIsoMaxLog + staticExposureMaxLog;
        final double boundedTargetTotalEv = clamp(rawTargetTotalEv,
                minimumTotalEv, maximumTotalEv);
        exposureLimited = Math.abs(rawTargetTotalEv - boundedTargetTotalEv) > LIMIT_TOLERANCE_EV;

        targetHistory.addLast(new TargetSample(nowNs, boundedTargetTotalEv));
        final long historyFloorNs = nowNs - HISTORY_NS;
        while (!targetHistory.isEmpty()
                && targetHistory.peekFirst().timestampNs < historyFloorNs) {
            targetHistory.removeFirst();
        }

        final double robustTargetTotalEv = fast
                ? boundedTargetTotalEv : medianTargetTotalEv();
        if (smoothedTargetTotalEv == null) {
            smoothedTargetTotalEv = robustTargetTotalEv;
        } else {
            final double targetAlpha = 1.0 - Math.exp(-dtSeconds / targetTauSeconds);
            smoothedTargetTotalEv += targetAlpha
                    * (robustTargetTotalEv - smoothedTargetTotalEv);
        }

        final double previousIsoLog = currentIsoLog2;
        final double previousExposureLog = currentExposureLog2;
        final double currentTotalEv = previousIsoLog + previousExposureLog;
        final double targetErrorEv = smoothedTargetTotalEv - currentTotalEv;
        final double maxStepEv = Math.min(MAX_STEP_EV, dtSeconds * rateEvPerSecond);

        final double totalStepEv;
        if (Math.abs(targetErrorEv) < deadbandEv) {
            totalStepEv = 0.0;
        } else {
            final double correctionAlpha = 1.0 - Math.exp(-dtSeconds / correctionTauSeconds);
            totalStepEv = clamp(correctionAlpha * targetErrorEv, -maxStepEv, maxStepEv);
        }

        final double dynamicIsoMinLog = Math.max(staticIsoMinLog, previousIsoLog - maxStepEv);
        final double dynamicIsoMaxLog = Math.min(staticIsoMaxLog, previousIsoLog + maxStepEv);
        final double dynamicExposureMinLog = Math.max(
                staticExposureMinLog, previousExposureLog - maxStepEv);
        final double dynamicExposureMaxLog = Math.min(
                staticExposureMaxLog, previousExposureLog + maxStepEv);

        final double steppedTotalEv = clamp(currentTotalEv + totalStepEv,
                dynamicIsoMinLog + dynamicExposureMinLog,
                dynamicIsoMaxLog + dynamicExposureMaxLog);
        final double feasibleIsoMinLog = Math.max(dynamicIsoMinLog,
                steppedTotalEv - dynamicExposureMaxLog);
        final double feasibleIsoMaxLog = Math.min(dynamicIsoMaxLog,
                steppedTotalEv - dynamicExposureMinLog);

        if (locksIso()) {
            currentIsoLog2 = feasibleIsoMinLog;
        } else if (locksShutter()) {
            currentIsoLog2 = clamp(steppedTotalEv - staticExposureMinLog,
                    feasibleIsoMinLog, feasibleIsoMaxLog);
        } else {
            final double validFocal35 = Double.isFinite(focal35) && focal35 > 0.0
                    ? focal35 : 50.0;
            final double baseIsoLog = log2(baseIso);
            final double pivotExposureLog = log2(1_000_000_000.0 / (2.0 * validFocal35));
            final double pivotTotalEv = baseIsoLog + pivotExposureLog;
            double desiredIsoLog = baseIsoLog
                    + Math.max(0.0, 0.5 * (steppedTotalEv - pivotTotalEv))
                    + clamp(aeBalanceEv, AE_BALANCE_MIN_EV, AE_BALANCE_MAX_EV);
            currentIsoLog2 = clamp(desiredIsoLog, feasibleIsoMinLog, feasibleIsoMaxLog);
        }
        currentExposureLog2 = clamp(steppedTotalEv - currentIsoLog2,
                dynamicExposureMinLog, dynamicExposureMaxLog);

        if (startup
                && Math.abs(targetErrorEv) < STARTUP_DEADBAND_EV
                && Math.abs(currentIsoLog2 - previousIsoLog) < STARTUP_DEADBAND_EV
                && Math.abs(currentExposureLog2 - previousExposureLog) < STARTUP_DEADBAND_EV) {
            startup = false;
        }

        final int nextIso = clampInt((int) Math.round(Math.pow(2.0, currentIsoLog2)),
                modeIsoMin, modeIsoMax);
        final long nextExposureNs = clampLong(Math.round(Math.pow(2.0, currentExposureLog2)),
                modeExposureMin, modeExposureMax);
        final Solution next = new Solution(nextIso, nextExposureNs, meterErrorEv,
                Math.abs(meterErrorEv) < SETTLED_METER_EV);
        if (lastReturned != null && next.equals(lastReturned)) return null;
        lastReturned = next;
        return next;
    }

    private void resetAeState() {
        resetEpoch++;
        smoothedTargetTotalEv = null;
        targetHistory.clear();
        startup = true;
        startupDeadlineNs = 0L;
        meterErrorEv = 0.0;
        exposureLimited = false;
        lastUpdateNs = 0L;
    }

    private double medianTargetTotalEv() {
        if (targetHistory.isEmpty()) return currentIsoLog2 + currentExposureLog2;
        ArrayList<Double> values = new ArrayList<>(targetHistory.size());
        for (TargetSample sample : targetHistory) values.add(sample.totalExposureEv);
        Collections.sort(values);
        int size = values.size();
        return 0.5 * (values.get((size - 1) / 2) + values.get(size / 2));
    }

    private boolean locksIso() {
        return mode == Mode.ISO_PRIORITY || mode == Mode.MANUAL;
    }

    private boolean locksShutter() {
        return mode == Mode.SHUTTER_PRIORITY || mode == Mode.MANUAL;
    }

    private int activeIsoMin() {
        return mode == Mode.MANUAL ? hardwareIsoMin : isoMin;
    }

    private int activeIsoMax() {
        return mode == Mode.MANUAL ? hardwareIsoMax : isoMax;
    }

    private long activeExposureMinNs() {
        return mode == Mode.MANUAL ? hardwareExposureMinNs : exposureMinNs;
    }

    private long activeExposureMaxNs() {
        return mode == Mode.MANUAL ? hardwareExposureMaxNs : exposureMaxNs;
    }

    private int currentIso() {
        return clampInt((int) Math.round(Math.pow(2.0, currentIsoLog2)),
                activeIsoMin(), activeIsoMax());
    }

    private long currentExposureNs() {
        return clampLong(Math.round(Math.pow(2.0, currentExposureLog2)),
                activeExposureMinNs(), activeExposureMaxNs());
    }

    private static double compute35mmEquivalent(CameraCharacteristics c) {
        try {
            SizeF sensor = c.get(CameraCharacteristics.SENSOR_INFO_PHYSICAL_SIZE);
            float[] focal = c.get(CameraCharacteristics.LENS_INFO_AVAILABLE_FOCAL_LENGTHS);
            if (sensor == null || focal == null || focal.length == 0 || focal[0] <= 0f) return 50.0;
            double sensorDiag = Math.hypot(sensor.getWidth(), sensor.getHeight());
            if (!(sensorDiag > 0.0)) return 50.0;
            return clamp(focal[0] * (43.2666153056 / sensorDiag), 8.0, 400.0);
        } catch (Throwable ignored) {
            return 50.0;
        }
    }

    private static double log2(double value) { return Math.log(value) / Math.log(2.0); }
    private static double clamp(double value, double lo, double hi) {
        return Math.max(lo, Math.min(hi, value));
    }
    private static int clampInt(int value, int lo, int hi) {
        return Math.max(lo, Math.min(hi, value));
    }
    private static long clampLong(long value, long lo, long hi) {
        return Math.max(lo, Math.min(hi, value));
    }
}
