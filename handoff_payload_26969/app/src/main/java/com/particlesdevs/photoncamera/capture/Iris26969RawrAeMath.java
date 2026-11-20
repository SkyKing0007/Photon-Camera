package com.particlesdevs.photoncamera.capture;

/**
 * IRIS_26969_RAWR_AE_MATH — pure host-testable exposure allocation.
 * Algorithm adapted from RAWR RawrAutoExposure.h, GPL-3.0, upstream
 * https://github.com/adityawarmanfw/rawr (commit 5b9f5cef0f03dbef2dab7fdc9d2664bbcc518078).
 * Camera2 ownership and scene-specific gain are managed separately by CaptureController.
 */
public final class Iris26969RawrAeMath {
    public static final long DEFAULT_MAX_STILL_SHUTTER_NS = 71_428_571L; // 1/14s, user specified
    public static final long DEFAULT_START_SHUTTER_NS = 33_333_333L; // 1/30s
    public static final long PERIOD_50_HZ_NS = 10_000_000L;
    public static final long PERIOD_60_HZ_NS = 8_333_333L;
    public static final double CAP_RAMP_EV = 4.0;
    private Iris26969RawrAeMath() {}

    public static final class Limits {
        public int isoMin = 50, isoMax = 6400, isoAnalogMax = 1600;
        public long shutterMinNs = 100_000L;
        public long shutterMaxNs = DEFAULT_MAX_STILL_SHUTTER_NS;
        public long shutterStartNs = DEFAULT_START_SHUTTER_NS;
        public float maxDigitalGainEv = 2.0f;
    }
    public static final class Solution {
        public final long shutterNs;
        public final int iso;
        public final float digitalGainEv;
        public final boolean underexposed, overexposed;
        public final double requestedEnergy;
        private Solution(long t, int i, float d, boolean u, boolean o, double e) {
            shutterNs=t; iso=i; digitalGainEv=d; underexposed=u; overexposed=o; requestedEnergy=e;
        }
        public double logTotalExposure() {
            return Math.log(shutterNs*(double)iso)/Math.log(2.0) + digitalGainEv;
        }
    }
    static double clamp(double v, double lo, double hi) { return Math.max(lo, Math.min(hi,v)); }
    static long clamp(long v, long lo, long hi) { return Math.max(lo, Math.min(hi,v)); }
    public static boolean validPeriod(long p) {
        return p==PERIOD_50_HZ_NS || p==PERIOD_60_HZ_NS;
    }
    /** RAWR uses whole exposure-cycle multiples, rounding DOWN to avoid added blur. */
    public static long snapDown(long t, long period, long min, long max) {
        if (period==0 || t<period) return clamp(t,min,max);
        if (!validPeriod(period) || min<=0 || max<min) throw new IllegalArgumentException("unverified period");
        long count=Math.max(1,t/period);
        while(count>1 && count*period>max) count--;
        return clamp(count*period,min,max);
    }
    /**
     * RAWR Auto solver with 1/14s still cap. Sensor ISO is bounded by its *analog*
     * ceiling. Residual exposure is returned as digitalGainEv and MUST be
     * implemented on a frame-matched, camera-linear display + photo path
     * before this math may control the camera. It must not be silently ignored.
     */
    public static Solution solve(double exposureNsTimesIso, Limits l,
                                 float balanceEv, long verifiedFlickerPeriodNs) {
        if (l==null || l.isoMin<1 || l.isoMax<l.isoMin || l.isoAnalogMax<l.isoMin ||
                l.shutterMinNs<=0 || l.shutterMaxNs<l.shutterMinNs ||
                l.shutterStartNs<=0 || !Double.isFinite(exposureNsTimesIso) ||
                exposureNsTimesIso<=0 || !Float.isFinite(balanceEv) ||
                (verifiedFlickerPeriodNs!=0 && !validPeriod(verifiedFlickerPeriodNs)))
            throw new IllegalArgumentException("invalid AE input");
        final int analog=Math.min(l.isoMax,l.isoAnalogMax);
        final double e=Math.max(1.0,exposureNsTimesIso);
        final long start=clamp(Math.round(l.shutterStartNs *
                Math.pow(2.0,Math.max(0.0,-(double)balanceEv))),l.shutterMinNs,l.shutterMaxNs);
        double cap=start;
        double eStart=start*(double)l.isoMin;
        if (e>eStart && l.shutterMaxNs>start) {
            double ramp=clamp(Math.log(e/eStart)/Math.log(2.0)/CAP_RAMP_EV,0,1);
            cap=start*Math.pow(l.shutterMaxNs/(double)start,ramp);
        }
        double shutter=clamp(e/l.isoMin,l.shutterMinNs,cap);
        shutter=clamp(shutter*Math.pow(2.0,-Math.max(0.0,(double)balanceEv)),l.shutterMinNs,cap);
        shutter=Math.min(shutter,Math.max(l.shutterMinNs,e/l.isoMin));
        long t=snapDown(Math.round(shutter),verifiedFlickerPeriodNs,
                l.shutterMinNs,(long)cap);
        double rawIso=e/t;
        if (rawIso<l.isoMin) {
            t=clamp(Math.round(e/l.isoMin),l.shutterMinNs,l.shutterMaxNs);
            rawIso=e/t;
        }
        int iso=(int)Math.round(clamp(rawIso,l.isoMin,analog));
        double remainder=Math.log(e/(t*(double)iso))/Math.log(2.0);
        float digital=(float)clamp(remainder,0,Math.max(0,l.maxDigitalGainEv));
        return new Solution(t,iso,digital,remainder-digital>1.0/16.0,
                remainder< -1.0/16.0,e);
    }
}
