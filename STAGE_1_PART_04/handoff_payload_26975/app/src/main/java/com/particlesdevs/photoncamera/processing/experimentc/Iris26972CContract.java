package com.particlesdevs.photoncamera.processing.experimentc;

import java.util.List;
import java.util.Objects;

/**
 * Inert Experiment C-only immutable capture/output contract.
 *
 * The donor Sabre, physical Camera2/DNG color developer, pinned native RAISR,
 * JPEG/R and pending-row MediaStore writer now have an isolated C-only owner.
 * An isolated Camera2 source callback exists, but Android compilation and device capture are NOT proven.
 * The false production gate prevents publication and forbids A/B/YUV/Lanczos fallback.
 * It exists so the independently implemented capture and finishing components
 * have one self-contained, host-testable contract with no A/B imports.
 */
public final class Iris26972CContract {
    public static final String SOURCE_TAG = "bjzhou/PhotonCamera:1.29.0";
    public static final String MODE = "C";
    /** C safety bound covering Iris frame-slider values; never silently cap the selected count. */
    public static final int MAX_NORMAL_FRAMES = 30;
    /** Must remain false until donor Sabre, RAW development, RAISR, save & tests are complete. */
    public static final boolean PRODUCTION_READY = false;
    /** Separate explicit shutter-callback verification gate: source wiring alone is not device proof. */
    public static final boolean ACTUAL_CAMERA2_CALLBACK_WIRED = false;
    /** 26973: enable C ONLY for bounded on-device evaluation after successful 26972 Android build.
     * Do not claim production readiness or verified device image quality.
     * Existing physical RAW, frame-count, ABI, no-fallback and save guards remain. */
    public static final boolean CONTROLLED_DEVICE_TRIAL_ENABLED = true;
    public static final String RECONSTRUCTOR = "BJZHOU_MGC_SABRE";
    public static final String FINISHER = "BJZHOU_NATIVE_1X_SABRE_DENOISE_USM_PENDING_COLOR_PARITY";
    public static final float LUMA_DENOISE = 0.00f;
    public static final float CHROMA_DENOISE = 1.00f; // User-confirmed baked chroma; do not set to zero
    public static final float SHARPENING = 0.40f; // Actual MGC SharpenTo16Bit; Camera2 EDGE_MODE stays OFF
    public static final int JPEG_QUALITY = 95;
    public static final int INTERNAL_RAISR_SCALE = 1;
    public static final int FINAL_OUTPUT_SCALE = 1;
    public static final boolean JPEG_444 = true;
    public static final boolean ULTRA_HDR_ENABLED = true;
    public static final boolean HEIC_ENABLED = false;
    public static final boolean ALLOW_ALTERNATE_RECONSTRUCTOR = false;
    public static final boolean ALLOW_ALTERNATE_FINISHER = false;

    public enum Role { NORMAL, HIGHLIGHT_SHORT, SHADOW_LONG }

    public static final class Plan {
        public final String physicalLensId;
        public final int frameCount;
        public final boolean night;
        public final long referenceTimestampNs;
        private Plan(String lensId, int frameCount, boolean night, long referenceTimestampNs) {
            this.physicalLensId = lensId;
            this.frameCount = frameCount;
            this.night = night;
            this.referenceTimestampNs = referenceTimestampNs;
        }
    }

    private Iris26972CContract() {}

    /** Freeze exactly once at shutter: no additional short/long Night brackets. */
    public static Plan freeze(String physicalLensId, int frameSliderCount,
                              boolean night, long referenceTimestampNs) {
        if (physicalLensId == null || physicalLensId.trim().isEmpty())
            throw new IllegalArgumentException("26972 C requires a physical lens identity");
        if (frameSliderCount < 2 || frameSliderCount > MAX_NORMAL_FRAMES)
            throw new IllegalArgumentException("26972 C invalid frame count " + frameSliderCount);
        if (referenceTimestampNs <= 0)
            throw new IllegalArgumentException("26972 C requires timestamp-owned RAW reference");
        return new Plan(physicalLensId.trim(), frameSliderCount, night, referenceTimestampNs);
    }

    /** Fail closed: Sabre accepts same-exposure NORMAL frames, never role coercion. */
    public static void validateBurst(Plan plan, List<Role> roles,
                                     List<Long> timestamps, List<Double> exposureProducts) {
        Objects.requireNonNull(plan, "26972 C plan");
        if (roles == null || timestamps == null || exposureProducts == null ||
                roles.size() != plan.frameCount || timestamps.size() != plan.frameCount ||
                exposureProducts.size() != plan.frameCount)
            throw new IllegalArgumentException("26972 C frozen frame budget mismatch");
        // The reference is not merely present: Sabre merges the first RAW as the
        // immutable reference. Accepting a reordered burst would bind the wrong
        // frame to the shutter-frozen noise/covariance and alignment geometry.
        if (timestamps.isEmpty() || !Long.valueOf(plan.referenceTimestampNs).equals(timestamps.get(0)))
            throw new IllegalArgumentException("26972 C shutter reference must be first");
        boolean foundReference = false;
        double referenceExposure = Double.NaN;
        for (int i = 0; i < plan.frameCount; i++) {
            if (roles.get(i) != Role.NORMAL)
                throw new IllegalArgumentException("26972 C rejects auxiliary RAW frames");
            Long ts = timestamps.get(i);
            Double ev = exposureProducts.get(i);
            if (ts == null || ts <= 0 || ev == null || !Double.isFinite(ev) || ev <= 0.0)
                throw new IllegalArgumentException("26972 C invalid RAW metadata");
            for (int j = 0; j < i; j++) {
                if (ts.equals(timestamps.get(j)))
                    throw new IllegalArgumentException("26972 C repeated RAW timestamp");
            }
            if (ts == plan.referenceTimestampNs) {
                foundReference = true;
                referenceExposure = ev;
            }
        }
        if (!foundReference) throw new IllegalArgumentException("26972 C reference missing");
        // Real shutters/ISOs have normal Camera2 quantization. Reject any
        // intentional bracket; allow at most 1% exposure-product drift.
        for (Double e : exposureProducts) {
            if (Math.abs(e / referenceExposure - 1.0) > 0.01)
                throw new IllegalArgumentException("26972 C exposure brackets forbidden");
        }
    }
}
