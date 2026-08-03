package com.particlesdevs.photoncamera.settings;

import android.hardware.camera2.CameraCharacteristics;
import android.util.SizeF;

import com.particlesdevs.photoncamera.capture.CaptureController;
import com.particlesdevs.photoncamera.util.Log;

/**
 * Build 26226:
 * Selects automatic Motion noise defaults from the active physical lens.
 *
 * This never depends on vendor camera ID numbering. Classification uses the
 * physical camera's native 35 mm-equivalent focal length:
 *
 * - ultra-wide: below 20 mm
 * - standard/wide: 20 mm through below 70 mm
 * - telephoto/periscope: 70 mm and above
 *
 * A saved user value overrides the automatic profile whenever it differs from
 * the universal 26225 baseline. This preserves existing per-lens controls.
 */
public final class MotionLensNoiseProfile {
    private static final String TAG = "MotionLensNoiseProfile";

    private static final float FULL_FRAME_WIDTH_MM = 36.0f;
    private static final float ULTRAWIDE_MAX_EQUIVALENT_MM = 20.0f;
    private static final float TELEPHOTO_MIN_EQUIVALENT_MM = 70.0f;
    private static final float USER_OVERRIDE_EPSILON = 0.0005f;

    public static final float BASE_LUMA = 0.80f;
    public static final float BASE_CHROMA = 0.30f;
    public static final float BASE_TEXTURE = 1.15f;
    public static final float BASE_SPATIAL = 1.00f;
    public static final float BASE_SHADOW = 1.00f;

    private MotionLensNoiseProfile() {
    }

    public enum LensType {
        ULTRAWIDE,
        STANDARD,
        TELEPHOTO
    }

    public static final class Resolved {
        public final LensType lensType;
        public final float equivalentFocalLengthMm;
        public final float luma;
        public final float chroma;
        public final float texture;
        public final float spatial;
        public final float shadow;

        private Resolved(
                LensType lensType,
                float equivalentFocalLengthMm,
                float luma,
                float chroma,
                float texture,
                float spatial,
                float shadow
        ) {
            this.lensType = lensType;
            this.equivalentFocalLengthMm = equivalentFocalLengthMm;
            this.luma = luma;
            this.chroma = chroma;
            this.texture = texture;
            this.spatial = spatial;
            this.shadow = shadow;
        }
    }

    public static Resolved resolve(
            float storedLuma,
            float storedChroma,
            float storedTexture,
            float storedSpatial,
            float storedShadow
    ) {
        float equivalent = getNative35mmEquivalent();
        LensType type = classify(equivalent);

        float automaticLuma = BASE_LUMA;
        float automaticChroma = BASE_CHROMA;
        float automaticTexture = BASE_TEXTURE;
        float automaticSpatial = BASE_SPATIAL;
        float automaticShadow = BASE_SHADOW;

        if (type == LensType.TELEPHOTO) {
            /*
             * Build 26227 Telephoto Detail Profile v2:
             * preserve substantially more mid/high-ISO telephoto texture
             * while retaining the existing ISO-adaptive cleanup paths.
             */
            /*
             * Build 26261:
             * Safe alignment-grid mapping removed the false structural
             * residuals that the earlier telephoto profile was protecting.
             * Keep luma detail conservative, but strengthen chroma cleanup
             * and allow a little more spatial suppression of connected
             * residual noise and fabric worms.
             */
            automaticLuma = 0.58f;
            automaticChroma = 0.50f;
            automaticTexture = 1.30f;
            automaticSpatial = 0.82f;
            automaticShadow = 0.95f;} else if (type == LensType.ULTRAWIDE) {
            automaticLuma = 0.85f;
            automaticChroma = 0.42f;
            automaticTexture = 1.10f;
            automaticSpatial = 1.10f;
            automaticShadow = 1.15f;
        }

        Resolved resolved = new Resolved(
                type,
                equivalent,
                choose(storedLuma, BASE_LUMA, automaticLuma),
                choose(storedChroma, BASE_CHROMA, automaticChroma),
                choose(storedTexture, BASE_TEXTURE, automaticTexture),
                choose(storedSpatial, BASE_SPATIAL, automaticSpatial),
                choose(storedShadow, BASE_SHADOW, automaticShadow)
        );

        Log.d(
                TAG,
                "MOTION_26226_AUTO_LENS_PROFILE"
                        + " lensType=" + resolved.lensType
                        + " equivalentMm=" + resolved.equivalentFocalLengthMm
                        + " storedLuma=" + storedLuma
                        + " finalLuma=" + resolved.luma
                        + " storedChroma=" + storedChroma
                        + " finalChroma=" + resolved.chroma
                        + " storedTexture=" + storedTexture
                        + " finalTexture=" + resolved.texture
                        + " storedSpatial=" + storedSpatial
                        + " finalSpatial=" + resolved.spatial
                        + " storedShadow=" + storedShadow
                        + " finalShadow=" + resolved.shadow
        );

        return resolved;
    }

    private static float choose(
            float storedValue,
            float universalBaseline,
            float automaticValue
    ) {
        if (Math.abs(storedValue - universalBaseline)
                > USER_OVERRIDE_EPSILON) {
            return storedValue;
        }

        return automaticValue;
    }

    private static LensType classify(float equivalentFocalLengthMm) {
        if (!Float.isFinite(equivalentFocalLengthMm)) {
            return LensType.STANDARD;
        }

        if (equivalentFocalLengthMm < ULTRAWIDE_MAX_EQUIVALENT_MM) {
            return LensType.ULTRAWIDE;
        }

        if (equivalentFocalLengthMm
                >= TELEPHOTO_MIN_EQUIVALENT_MM) {
            return LensType.TELEPHOTO;
        }

        return LensType.STANDARD;
    }

    private static float getNative35mmEquivalent() {
        try {
            CameraCharacteristics characteristics =
                    CaptureController.getActiveCameraCharacteristics();

            if (characteristics == null) {
                return Float.NaN;
            }

            Integer lensFacing = characteristics.get(
                    CameraCharacteristics.LENS_FACING
            );

            if (lensFacing != null
                    && lensFacing
                    != CameraCharacteristics.LENS_FACING_BACK) {
                return Float.NaN;
            }

            SizeF sensorSize = characteristics.get(
                    CameraCharacteristics.SENSOR_INFO_PHYSICAL_SIZE
            );

            float[] focalLengths = characteristics.get(
                    CameraCharacteristics
                            .LENS_INFO_AVAILABLE_FOCAL_LENGTHS
            );

            if (sensorSize == null
                    || sensorSize.getWidth() <= 0.0f
                    || focalLengths == null
                    || focalLengths.length == 0
                    || focalLengths[0] <= 0.0f) {
                return Float.NaN;
            }

            float equivalent =
                    FULL_FRAME_WIDTH_MM
                            / sensorSize.getWidth()
                            * focalLengths[0];

            if (!Float.isFinite(equivalent)
                    || equivalent < 8.0f
                    || equivalent > 500.0f) {
                return Float.NaN;
            }

            return equivalent;
        } catch (Exception exception) {
            Log.w(
                    TAG,
                    "Unable to classify active physical lens",
                    exception
            );
            return Float.NaN;
        }
    }
}