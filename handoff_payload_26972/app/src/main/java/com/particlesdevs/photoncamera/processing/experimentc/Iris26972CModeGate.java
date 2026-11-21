package com.particlesdevs.photoncamera.processing.experimentc;

/**
 * Experiment C-only admission firewall at shutter and RAW publication boundaries.
 *
 * Historical A/B routes must not inherit any new reconstruction rules. Until the
 * independent bjzhou 1.29.0 Sabre + RAW renderer + genuine RAISR backend is
 * complete, a stored C selection is explicitly rejected rather than mapped to
 * A or B through legacy else branches.
 *
 * This is a pure host-testable policy, not an alternate implementation of C.
 */
public final class Iris26972CModeGate {
    private Iris26972CModeGate() {}

    /** An A/B selection has no additional conditions or side effects. */
    public static boolean mustRejectAtShutter(String frozenModeId) {
        return "C".equals(frozenModeId) &&
                (!Iris26972CContract.PRODUCTION_READY ||
                 !Iris26972CContract.ACTUAL_CAMERA2_CALLBACK_WIRED);
    }

    /** Never let C slip into legacy A/B processing, even if a future UI enables it. */
    public static void requireIndependentBackend(String frozenModeId, String owner) {
        if (!"C".equals(frozenModeId)) return;
        // Once the backend exists, this guard should be replaced with an
        // explicit C-owned handoff at the caller, not removed or bypassed.
        throw new IllegalStateException("26972_C_INDEPENDENT_BACKEND_REQUIRED owner="
                + String.valueOf(owner) + " noAorBOrYuvFallback=true");
    }
}
