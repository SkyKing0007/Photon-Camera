package com.particlesdevs.photoncamera.spektra;

import android.hardware.camera2.CameraCharacteristics;
import android.util.Range;
import android.util.SizeF;

import java.util.ArrayDeque;
import java.util.Arrays;

/**
 * Sensor-exposure owner for Spektra mode.
 *
 * This class is intentionally independent from Iris IsoExpoSelector/Parameters. 26696 keeps the
 * audited Unspektrawesome 1.1.2 solver law, but now binds every solve to the actual ISO/shutter
 * metadata of the RAW frame whose native meter generation completed. Commanded values are never
 * treated as proof that the sensor achieved them.
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
    }

    private static final long STARTUP_NS = 1_500_000_000L;
    private static final long HISTORY_NS = 300_000_000L;
    private static final long MIN_UPDATE_NS = 16_000_000L;
    private static final double MAX_STEP_EV = 0.20;
    private static final double TARGET_LINEAR = 0.18;
    // Exact 1.1.2 help contract: automatic/priority AE defaults to about 1/30 s slowest,
    // clamped inside the lens-supported range. Full MANUAL exposure keeps the full hardware range.
    private static final long DEFAULT_AE_SLOWEST_EXPOSURE_NS = 33_333_333L;

    private final int isoMin;
    private final int isoMax;
    private final long exposureMinNs;
    private final long exposureMaxNs;
    private final int hardwareIsoMin;
    private final int hardwareIsoMax;
    private final long hardwareExposureMinNs;
    private final long hardwareExposureMaxNs;
    private final double focal35;
    private final ArrayDeque<MeterSample> history = new ArrayDeque<>();

    private Mode mode = Mode.AUTO;
    private int lockedIso;
    private long lockedExposureNs;
    private double aeBalanceEv = 0.0;
    private double exposureCompensationEv = 0.0;
    private long startNs = 0L;
    private long lastUpdateNs = 0L;
    private double meterEma = Double.NaN;
    private double correctionEma = 0.0;
    private int currentIso;
    private long currentExposureNs;

    private static final class MeterSample {
        final long t;
        final double ev;
        MeterSample(long t, double ev) { this.t = t; this.ev = ev; }
    }

    public SpektraExposureController(CameraCharacteristics c) {
        Range<Integer> iso = c.get(CameraCharacteristics.SENSOR_INFO_SENSITIVITY_RANGE);
        Range<Long> exp = c.get(CameraCharacteristics.SENSOR_INFO_EXPOSURE_TIME_RANGE);
        hardwareIsoMin = iso == null ? 50 : Math.max(1, iso.getLower());
        hardwareIsoMax = iso == null ? 6400 : Math.max(hardwareIsoMin, iso.getUpper());
        hardwareExposureMinNs = exp == null ? 100_000L : Math.max(1L, exp.getLower());
        hardwareExposureMaxNs = exp == null ? 1_000_000_000L
                : Math.max(hardwareExposureMinNs, exp.getUpper());
        // IRIS_26696_UNSPEKTRA_AE_LENS_LIMITS: 1.1.2 reads the per-lens sensitivity range
        // and defaults the slowest automatic shutter to about 1/30 s.
        isoMin = hardwareIsoMin;
        isoMax = hardwareIsoMax;
        exposureMinNs = hardwareExposureMinNs;
        exposureMaxNs = Math.min(hardwareExposureMaxNs,
                Math.max(hardwareExposureMinNs, DEFAULT_AE_SLOWEST_EXPOSURE_NS));
        focal35 = compute35mmEquivalent(c);
        currentIso = isoMin;
        long pivot = Math.round(1_000_000_000.0 / (2.0 * focal35));
        currentExposureNs = clampLong(pivot, exposureMinNs, exposureMaxNs);
        lockedIso = currentIso;
        lockedExposureNs = currentExposureNs;
    }

    public synchronized void reset(long nowNs) {
        history.clear();
        startNs = nowNs;
        lastUpdateNs = 0L;
        meterEma = Double.NaN;
        correctionEma = 0.0;
    }

    public synchronized void setMode(Mode mode, Integer iso, Long exposureNs) {
        this.mode = mode == null ? Mode.AUTO : mode;
        // 1.1.2: lens AE limits also apply in priority modes; only full MANUAL uses the
        // camera's complete supported ISO/shutter range.
        if (iso != null) {
            lockedIso = this.mode == Mode.MANUAL
                    ? clampInt(iso, hardwareIsoMin, hardwareIsoMax)
                    : clampInt(iso, isoMin, isoMax);
        }
        if (exposureNs != null) {
            lockedExposureNs = this.mode == Mode.MANUAL
                    ? clampLong(exposureNs, hardwareExposureMinNs, hardwareExposureMaxNs)
                    : clampLong(exposureNs, exposureMinNs, exposureMaxNs);
        }
    }

    public synchronized void setAeBalanceEv(double ev) {
        aeBalanceEv = clamp(ev, -1.5, 3.0);
    }

    public synchronized void setExposureCompensationEv(double ev) {
        exposureCompensationEv = clamp(ev, -8.0, 8.0);
    }

    public synchronized int getCurrentIso() { return currentIso; }
    public synchronized long getCurrentExposureNs() { return currentExposureNs; }

    /** Initial manual-sensor request used only until Camera2 reports the first actual frame. */
    public synchronized Solution initialSolution() {
        switch (mode) {
            case MANUAL:
                currentIso = lockedIso;
                currentExposureNs = lockedExposureNs;
                break;
            case ISO_PRIORITY:
                currentIso = lockedIso;
                break;
            case SHUTTER_PRIORITY:
                currentExposureNs = lockedExposureNs;
                break;
            case AUTO:
            default:
                break;
        }
        return currentSolution(0.0);
    }

    /**
     * 1.1.2 Unspektra AE solve for one generation-matched RAW frame.
     *
     * @param centerWeightedLinearMeter normalized camera-linear signal (>0), already black/white
     *                                  normalized. 0.18 is treated as the middle-gray target.
     * @param actualIso ISO reported by TotalCaptureResult for this exact metered frame.
     * @param actualExposureNs shutter reported by TotalCaptureResult for this exact metered frame.
     */
    public synchronized Solution update(long nowNs, double centerWeightedLinearMeter,
            int actualIso, long actualExposureNs) {
        if (startNs == 0L) reset(nowNs);
        if (actualIso <= 0 || actualExposureNs <= 0L) {
            return currentSolution(0.0);
        }
        // IRIS_26696_UNSPEKTRA_AE_ACTUAL_FRAME_AUTHORITY
        currentIso = clampInt(actualIso, isoMin, isoMax);
        currentExposureNs = clampLong(actualExposureNs, exposureMinNs, exposureMaxNs);
        final long previousUpdateNs = lastUpdateNs;
        if (previousUpdateNs != 0L && nowNs - previousUpdateNs < MIN_UPDATE_NS) {
            return currentSolution(0.0);
        }
        final long elapsedNs = previousUpdateNs == 0L ? MIN_UPDATE_NS : Math.max(MIN_UPDATE_NS, nowNs - previousUpdateNs);
        lastUpdateNs = nowNs;
        final boolean startup = nowNs - startNs < STARTUP_NS;
        final double dt = elapsedNs / 1e9;
        final double meter = clamp(centerWeightedLinearMeter, 1e-6, 16.0);
        final double meterTau = startup ? 0.025 : 0.100;
        final double meterAlpha = 1.0 - Math.exp(-dt / meterTau);
        meterEma = Double.isFinite(meterEma) ? meterEma + meterAlpha * (meter - meterEma) : meter;

        double rawErrorEv = log2(TARGET_LINEAR / Math.max(meterEma, 1e-8)) + exposureCompensationEv;
        history.addLast(new MeterSample(nowNs, rawErrorEv));
        while (!history.isEmpty() && nowNs - history.peekFirst().t > HISTORY_NS) history.removeFirst();
        double robustError = medianError();

        final double correctionTau = startup ? 0.050 : 0.100;
        final double correctionAlpha = 1.0 - Math.exp(-dt / correctionTau);
        correctionEma += correctionAlpha * (robustError - correctionEma);
        final double deadband = startup ? 0.025 : 0.040;
        double requestedStep = Math.abs(correctionEma) <= deadband ? 0.0 : correctionEma;
        requestedStep = clamp(requestedStep, -MAX_STEP_EV, MAX_STEP_EV);

        final double currentTotal = log2(currentIso) + log2(currentExposureNs);
        final double targetTotal = clamp(currentTotal + requestedStep,
                log2(isoMin) + log2(exposureMinNs),
                log2(isoMax) + log2(exposureMaxNs));
        allocate(targetTotal);
        double residual = robustError - requestedStep;
        return new Solution(currentIso, currentExposureNs, residual, Math.abs(residual) <= 0.08);
    }

    private void allocate(double targetTotal) {
        switch (mode) {
            case MANUAL:
                currentIso = lockedIso;
                currentExposureNs = lockedExposureNs;
                return;
            case ISO_PRIORITY: {
                currentIso = lockedIso;
                double expLog = targetTotal - log2(currentIso);
                currentExposureNs = clampLong(Math.round(pow2(expLog)), exposureMinNs, exposureMaxNs);
                return;
            }
            case SHUTTER_PRIORITY: {
                currentExposureNs = lockedExposureNs;
                double isoLog = targetTotal - log2(currentExposureNs);
                currentIso = clampInt((int)Math.round(pow2(isoLog)), isoMin, isoMax);
                return;
            }
            case AUTO:
            default:
                break;
        }

        double isoMinLog = log2(isoMin);
        double isoMaxLog = log2(isoMax);
        double expMinLog = log2(exposureMinNs);
        double expMaxLog = log2(exposureMaxNs);
        double pivotNs = clamp(1_000_000_000.0 / (2.0 * focal35), exposureMinNs, exposureMaxNs);
        double pivotTotal = isoMinLog + log2(pivotNs);
        double isoDesired = isoMinLog + Math.max(0.0, 0.5 * (targetTotal - pivotTotal))
                + clamp(aeBalanceEv, -1.5, 3.0);
        // Feasible ISO interval once shutter bounds are respected.
        double feasibleIsoLo = Math.max(isoMinLog, targetTotal - expMaxLog);
        double feasibleIsoHi = Math.min(isoMaxLog, targetTotal - expMinLog);
        isoDesired = clamp(isoDesired, feasibleIsoLo, feasibleIsoHi);
        double expDesired = clamp(targetTotal - isoDesired, expMinLog, expMaxLog);
        isoDesired = clamp(targetTotal - expDesired, isoMinLog, isoMaxLog);
        currentIso = clampInt((int)Math.round(pow2(isoDesired)), isoMin, isoMax);
        currentExposureNs = clampLong(Math.round(pow2(expDesired)), exposureMinNs, exposureMaxNs);
    }

    private Solution currentSolution(double residual) {
        return new Solution(currentIso, currentExposureNs, residual, Math.abs(residual) <= 0.08);
    }

    private double medianError() {
        if (history.isEmpty()) return 0.0;
        double[] values = new double[history.size()];
        int i = 0;
        for (MeterSample s : history) values[i++] = s.ev;
        Arrays.sort(values);
        int n = values.length;
        return (n & 1) == 1 ? values[n / 2] : 0.5 * (values[n / 2 - 1] + values[n / 2]);
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

    private static double log2(double v) { return Math.log(v) / Math.log(2.0); }
    private static double pow2(double v) { return Math.pow(2.0, v); }
    private static double clamp(double v, double lo, double hi) { return Math.max(lo, Math.min(hi, v)); }
    private static int clampInt(int v, int lo, int hi) { return Math.max(lo, Math.min(hi, v)); }
    private static long clampLong(long v, long lo, long hi) { return Math.max(lo, Math.min(hi, v)); }
}
