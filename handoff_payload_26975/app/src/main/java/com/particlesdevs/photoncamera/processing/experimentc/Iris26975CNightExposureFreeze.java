package com.particlesdevs.photoncamera.processing.experimentc;

/**
 * C-private capture-side adaptation of Iris Night's NORMAL-only exposure principle:
 * fresh post-shutter RAW, shutter-time frozen exposure, up to 100ms integration
 * before increasing ISO, and actual physical Camera2 antibanding evidence.
 * It never calls A/B Night processing, reconstructors, image merging or save paths.
 *
 * A/B Night's optional separate LONG exposure cohort is intentionally NOT applied
 * to donor Sabre's same-exposure RAW input. That remains an explicit integration
 * and device-verification requirement, not a silently coerced frame role.
 */
public final class Iris26975CNightExposureFreeze {
    private static final long NIGHT_NORMAL_SHUTTER_CEILING_NS = 100_000_000L;
    public static final int HAL_ANTIBANDING_50HZ = 1;
    public static final int HAL_ANTIBANDING_60HZ = 2;

    public static final class Plan {
        public final long exposureNs;
        public final int iso;
        public final boolean userManual;
        private Plan(long exposureNs, int iso, boolean userManual) {
            this.exposureNs = exposureNs;
            this.iso = iso;
            this.userManual = userManual;
        }
    }

    private Iris26975CNightExposureFreeze() {}

    /** Copy of the Iris Night NORMAL-only shutter-priority arithmetic, C-owned. */
    public static Plan freeze(boolean userManual,
                              long frozenIrisExposureNs, int frozenIrisIso,
                              long sensorExposureLowNs, long sensorExposureHighNs,
                              int sensorIsoLow, int sensorIsoHigh,
                              double exposureCompensationEv,
                              Integer frozenPhysicalAntibanding,
                              boolean irisHighlightProtectionActive) {
        if (frozenIrisExposureNs <= 0L || frozenIrisIso <= 0 ||
                sensorExposureLowNs <= 0L || sensorExposureHighNs < sensorExposureLowNs ||
                sensorIsoLow <= 0 || sensorIsoHigh < sensorIsoLow ||
                frozenIrisExposureNs < sensorExposureLowNs ||
                frozenIrisExposureNs > sensorExposureHighNs ||
                frozenIrisIso < sensorIsoLow || frozenIrisIso > sensorIsoHigh ||
                !Double.isFinite(exposureCompensationEv) ||
                Math.abs(exposureCompensationEv) > 10.0) {
            throw new IllegalArgumentException("C Night requires a valid frozen physical Iris exposure");
        }
        if (userManual) return new Plan(frozenIrisExposureNs, frozenIrisIso, true);
        long cap = Math.min(sensorExposureHighNs, NIGHT_NORMAL_SHUTTER_CEILING_NS);
        if (cap < sensorExposureLowNs)
            throw new IllegalArgumentException("C Night has no permissible exposure interval");
        double originalEnergy = frozenIrisExposureNs * (double) frozenIrisIso;
        double targetEnergy = originalEnergy * Math.pow(2.0, exposureCompensationEv);
        if (irisHighlightProtectionActive) {
            // A fresh Night capture may move integration time/ISO, but never defeat
            // an already-frozen Iris highlight-protection exposure budget.
            targetEnergy = Math.min(targetEnergy, originalEnergy);
        }
        if (!(targetEnergy > 0.0) || !Double.isFinite(targetEnergy))
            throw new IllegalArgumentException("C Night target energy invalid");
        long desired = Math.round(targetEnergy / Math.max(1.0, sensorIsoLow));
        long shutter = clamp(desired, sensorExposureLowNs, cap);
        // Preserves Iris Night's 50/60Hz integration periods when the physical
        // camera actually identifies one. Never invent a 60Hz period for AUTO.
        long period = frozenPhysicalAntibanding != null &&
                frozenPhysicalAntibanding == HAL_ANTIBANDING_50HZ ? 10_000_000L :
                frozenPhysicalAntibanding != null &&
                frozenPhysicalAntibanding == HAL_ANTIBANDING_60HZ ? 8_333_333L : 0L;
        if (period > 0 && shutter >= period) {
            long n = Math.max(1L, Math.round((double) shutter / period));
            while (n * period > cap && n > 1L) n--;
            shutter = clamp(n * period, sensorExposureLowNs, cap);
        }
        int iso = (int) Math.max(sensorIsoLow,
                Math.min(sensorIsoHigh, Math.round(targetEnergy / shutter)));
        if (irisHighlightProtectionActive &&
                shutter * (double) iso > originalEnergy) {
            // Antibanding rounding must not undo physical highlight protection.
            // Prefer a shorter complete mains period over increasing photons.
            long safeExposure = (long) Math.floor(originalEnergy / sensorIsoLow);
            if (period > 0L && safeExposure >= period) {
                long safePeriods = Math.max(1L, safeExposure / period);
                shutter = Math.min(shutter, safePeriods * period);
            } else {
                shutter = Math.min(shutter, safeExposure);
            }
            if (shutter < sensorExposureLowNs) {
                throw new IllegalArgumentException(
                        "C Night cannot preserve the frozen highlight energy budget");
            }
            iso = (int) Math.max(sensorIsoLow, Math.min(sensorIsoHigh,
                    (long) Math.floor(originalEnergy / shutter)));
            if (shutter * (double) iso > originalEnergy) {
                throw new IllegalArgumentException(
                        "C Night highlighted source cannot honor physical sensor bounds");
            }
        }
        return new Plan(shutter, iso, false);
    }

    private static long clamp(long value, long low, long high) {
        return Math.max(low, Math.min(high, value));
    }
}
