package com.particlesdevs.photoncamera.capture;

/**
 * IRIS_26969_RAWR_AE_FRAME_LOOP. Uses RAWR's scene-referred histogram metering,
 * critically damped temporal target, analog ISO ceiling, and optional full-
 * period flicker shutter snap. RawImage/Camera2 request ownership is kept by
 * CaptureController; this class has no Android or camera-side effects.
 *
 * Algorithm adapted from RAWR https://github.com/adityawarmanfw/rawr
 * RawrAutoExposure.h at 5b9f5cef0f03dbef2dab7fdc9d2664bbcc518078
 * (upstream GPL-3.0). Default still shutter modified to 1/14 second.
 */
public final class Iris26969RawrAeLoop {
    private final Iris26969RawrAeMetering.Filter filter =
            new Iris26969RawrAeMetering.Filter();
    private final Iris26969RawrAeMetering.Policy policy =
            new Iris26969RawrAeMetering.Policy();
    private long lastTimestamp = 0L;

    public static final class Step {
        public final Iris26969RawrAeMath.Solution request;
        /** Log2 of the intended frame brightness, including bounded postRAW gain. */
        public final double targetLogExposure;
        public final Iris26969RawrAeMetering.Reading scene;
        private Step(Iris26969RawrAeMath.Solution req, double log,
                Iris26969RawrAeMetering.Reading scene) {
            this.request = req;
            this.targetLogExposure = log;
            this.scene = scene;
        }
    }

    public synchronized void reset() {
        filter.reset();
        lastTimestamp = 0L;
    }

    public synchronized Step update(Iris26969RawrAeMetering.Frame frame,
            Iris26969RawrAeMath.Limits limits, long flickerPeriodNs,
            float shutterIsoBalanceEv, double userEv) {
        if (frame == null || limits == null || frame.timestampNs <= lastTimestamp) return null;
        if (flickerPeriodNs != 0L && !Iris26969RawrAeMath.validPeriod(flickerPeriodNs))
            return null;
        final Iris26969RawrAeMetering.Reading m =
                Iris26969RawrAeMetering.meter(frame, policy, userEv);
        if (m == null || !Double.isFinite(m.desiredLogExposure)) return null;
        // RAWR's request space is shutter(ns)*ISO; only the photo boundary
        // controls additional digital display gain. The smoother must never
        // chase a metered target that sensor + permitted gain cannot reach.
        final Iris26969RawrAeMath.Solution reachable =
                Iris26969RawrAeMath.solve(Math.pow(2.0, m.desiredLogExposure),
                        limits, shutterIsoBalanceEv, flickerPeriodNs);
        final double filteredTarget = filter.update(reachable.logTotalExposure(), frame.timestampNs);
        final Iris26969RawrAeMath.Solution request =
                Iris26969RawrAeMath.solve(Math.pow(2.0, filteredTarget),
                        limits, shutterIsoBalanceEv, flickerPeriodNs);
        lastTimestamp = frame.timestampNs;
        return new Step(request, request.logTotalExposure(), m);
    }
}
