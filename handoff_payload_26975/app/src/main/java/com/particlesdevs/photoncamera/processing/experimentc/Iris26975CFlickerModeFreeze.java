package com.particlesdevs.photoncamera.processing.experimentc;

/**
 * Experiment C-only Camera2 capture-metadata adapter for Iris flicker protection.
 * Copies the actual physical camera antibanding selection to C-owned RAW requests;
 * it never imports or runs Experiment A/B processing or their row-flicker filters.
 * Passing this setting while AE is OFF does NOT itself establish that a manual
 * shutter interval is flicker-safe; that remains a distinct device test gate.
 */
public final class Iris26975CFlickerModeFreeze {
    private Iris26975CFlickerModeFreeze() {}

    /** Return only a physical, actually supported request value; never invent AUTO. */
    public static Integer freeze(Integer physicalObserved, Integer irisPreviewRequest,
                                 int[] supportedModes) {
        if (supportedModes == null || supportedModes.length == 0) return null;
        if (supported(physicalObserved, supportedModes)) return physicalObserved;
        if (supported(irisPreviewRequest, supportedModes)) return irisPreviewRequest;
        return null;
    }

    private static boolean supported(Integer candidate, int[] modes) {
        if (candidate == null) return false;
        for (int value : modes) if (value == candidate.intValue()) return true;
        return false;
    }
}
