package com.particlesdevs.photoncamera.processing.ultrahdr;

import android.graphics.Bitmap;
import android.graphics.Gainmap;
import android.graphics.Matrix;
import android.os.Build;

import com.particlesdevs.photoncamera.util.Log;

/**
 * IRIS_26436_MOTION_V2_CHROMA_SAFE_ULTRAHDR
 *
 * Motion-only helper. The gain map is already computed from V2 extended-linear
 * HDR. This class only orients it and attaches standard Android Gainmap
 * metadata. Photo/Night retain the existing UltraHdrSaver implementation.
 */
public final class MotionV2UltraHdr {
    private static final String TAG = "MotionV2UltraHdr";
    private static final float EPSILON = 0.015625f;
    private static final float MIN_RATIO = 1.0f;
    private static final float MIN_HDR_TRANSITION = 1.00f;
    /* IRIS_26507_FULL_HDR_DISPLAY_CAPACITY_PARITY */
    private static final float DEFAULT_FULL_HDR_DISPLAY_RATIO = 1.6033f;

    private MotionV2UltraHdr() {}

    public static boolean attach(
            Bitmap sdrBase,
            Bitmap unrotatedGainMap,
            int rotationDegrees,
            float maxRatio) {
        float safeMax = Math.max(1.50f, Math.min(8.0f, maxRatio));
        float frozenNightDisplayRatio = Math.max(
                MIN_HDR_TRANSITION, Math.min(safeMax, DEFAULT_FULL_HDR_DISPLAY_RATIO));
        return attachInternal(sdrBase, unrotatedGainMap, rotationDegrees, maxRatio,
                frozenNightDisplayRatio, false, false, 0, 0, 0, 0);
    }

    /** IRIS_26596_MOTION_UHDR_ACTUAL_CONTENT_CAPACITY */
    public static boolean attachMotion(
            Bitmap sdrBase,
            Bitmap unrotatedGainMap,
            int rotationDegrees,
            float maxRatio,
            float fullHdrDisplayRatio) {
        return attachMotion(sdrBase, unrotatedGainMap, rotationDegrees, maxRatio,
                fullHdrDisplayRatio, false);
    }

    /** IRIS_26945_FRONT_UHDR_FINAL_RASTER_MIRROR: SDR and gain share geometry. */
    public static boolean attachMotion(
            Bitmap sdrBase,
            Bitmap unrotatedGainMap,
            int rotationDegrees,
            float maxRatio,
            float fullHdrDisplayRatio,
            boolean mirrorFinalSdr) {
        return attachInternal(sdrBase, unrotatedGainMap, rotationDegrees, maxRatio,
                fullHdrDisplayRatio, true, mirrorFinalSdr, 0, 0, 0, 0);
    }

    /** IRIS_26946_FRONT_FINAL_SHADER_COORDINATES
     * Front Motion only: same full sensor and crop dimensions used by the
     * RotateWatermark GL shader. Rear and Night retain their prior calls.
     */
    public static boolean attachMotion(
            Bitmap sdrBase,
            Bitmap unrotatedGainMap,
            int rotationDegrees,
            float maxRatio,
            float fullHdrDisplayRatio,
            boolean mirrorFinalSdr,
            int rawWidth,
            int rawHeight,
            int cropWidth,
            int cropHeight) {
        return attachInternal(sdrBase, unrotatedGainMap, rotationDegrees, maxRatio,
                fullHdrDisplayRatio, true, mirrorFinalSdr,
                rawWidth, rawHeight, cropWidth, cropHeight);
    }

    private static boolean attachInternal(
            Bitmap sdrBase,
            Bitmap unrotatedGainMap,
            int rotationDegrees,
            float maxRatio,
            float requestedFullHdrDisplayRatio,
            boolean motionCapacityAuthority,
            boolean mirrorFinalSdr,
            int rawWidth,
            int rawHeight,
            int cropWidth,
            int cropHeight) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.UPSIDE_DOWN_CAKE
                || sdrBase == null
                || unrotatedGainMap == null) {
            return false;
        }

        Bitmap oriented = unrotatedGainMap;
        try {
            final int rotation = ((rotationDegrees % 360) + 360) % 360;
            if (rotation != 0 && rotation != 90 && rotation != 180 && rotation != 270) {
                throw new IllegalArgumentException("nonorthogonal UHDR rotation=" + rotation);
            }

            /* IRIS_26946_FRONT_FINAL_SHADER_COORDINATES
             * addwatermark_rotate.glsl uses the HIGH source Y crop for all
             * four rotations. For 180/270 it also uses HIGH source X if
             * cropWidth differs from rawWidth. Align the front gain's source
             * crop to precisely the same sensor region before rotating.
             *
             * This is exclusively front Motion. Rear and Night keep the
             * historical 26945 rotate-only path, with no changes to HDR math.
             */
            if (motionCapacityAuthority && mirrorFinalSdr
                    && rawWidth > 0 && rawHeight > 0
                    && cropWidth > 0 && cropHeight > 0) {
                if (cropWidth > rawWidth || cropHeight > rawHeight) {
                    throw new IllegalArgumentException("front gain crop exceeds sensor");
                }
                final int gainWidth = unrotatedGainMap.getWidth();
                final int gainHeight = unrotatedGainMap.getHeight();
                final int width = Math.max(1, Math.min(gainWidth,
                        (int) Math.round((double) gainWidth * cropWidth / rawWidth)));
                final int height = Math.max(1, Math.min(gainHeight,
                        (int) Math.round((double) gainHeight * cropHeight / rawHeight)));
                final int left = (rotation == 180 || rotation == 270)
                        ? gainWidth - width : 0;
                final int top = gainHeight - height;
                if (width != gainWidth || height != gainHeight) {
                    Bitmap cropped = Bitmap.createBitmap(oriented,
                            left, top, width, height);
                    if (cropped != oriented && !oriented.isRecycled()) {
                        oriented.recycle();
                    }
                    oriented = cropped;
                }
                Log.i(TAG, "IRIS_26946_FRONT_UHDR_SENSOR_CROP"
                        + " rotation=" + rotation
                        + " left=" + left + " top=" + top
                        + " width=" + width + " height=" + height
                        + " shaderCropHighY=true shaderCropHighXAt180or270=true");
            }

            if (rotation != 0) {
                Matrix matrix = new Matrix();
                matrix.postRotate(rotation);
                Bitmap rotated = Bitmap.createBitmap(
                        oriented, 0, 0, oriented.getWidth(), oriented.getHeight(),
                        matrix, false);
                if (rotated != oriented && !oriented.isRecycled()) {
                    oriented.recycle();
                }
                oriented = rotated;
            }

            /* IRIS_26946_FRONT_FINAL_SHADER_COORDINATES
             * Front GL RotateWatermark's mirrored paths are NOT the same
             * axis at every rotation:
             *   cameraRotation 0/180 -> final Y mirror
             *   cameraRotation 90/270 -> final X mirror
             * 26945 mirrored final X for all rotations. That was correct
             * in portrait (270) but displaced 180-degree landscape highlights.
             * This matches final SDR pixels; never modify the SDR bitmap.
             */
            if (motionCapacityAuthority && mirrorFinalSdr) {
                final boolean mirrorFinalY = (rotation == 0 || rotation == 180);
                Matrix frontFinalMirror = new Matrix();
                frontFinalMirror.setScale(mirrorFinalY ? 1.0f : -1.0f,
                        mirrorFinalY ? -1.0f : 1.0f);
                Bitmap matched = Bitmap.createBitmap(oriented, 0, 0,
                        oriented.getWidth(), oriented.getHeight(), frontFinalMirror, false);
                if (matched == oriented) {
                    throw new IllegalStateException("front gain map mirror not applied");
                }
                if (!oriented.isRecycled()) {
                    oriented.recycle();
                }
                oriented = matched;
                Log.i(TAG, "IRIS_26946_FRONT_UHDR_GAINMAP_SHADER_PARITY"
                        + " rotation=" + rotation
                        + " finalMirrorAxis=" + (mirrorFinalY ? "Y" : "X")
                        + " sdrBaseUnchanged=true rearGainUnaffected=true");
            }

            /* IRIS_26470_UHDR_EXACT_ORTHOGONAL_GEOMETRY */
            float baseAspect = sdrBase.getHeight() > 0
                    ? sdrBase.getWidth() / (float) sdrBase.getHeight() : 0.0f;
            float gainAspect = oriented.getHeight() > 0
                    ? oriented.getWidth() / (float) oriented.getHeight() : 0.0f;
            float aspectError = Math.abs(baseAspect - gainAspect);
            Log.d(TAG, "IRIS_26470_UHDR_ATTACH_GEOMETRY"
                    + " base=" + sdrBase.getWidth() + "x" + sdrBase.getHeight()
                    + " gain=" + oriented.getWidth() + "x" + oriented.getHeight()
                    + " rotation=" + rotation
                    + " exactOrthogonalRotation=true interpolation=false"
                    + " aspectError=" + aspectError);
            /* IRIS_26592_MOTION_UHDR_RECOVERED_HEADROOM_RANGE
             * The gain-map code itself still carries the actual per-pixel HDR/SDR quotient. Raising
             * metadata capacity does not brighten the body; it only prevents the previous 2.5x
             * ceiling from truncating valid -2.5EV SHORT recovery (5.657x physical headroom).
             */
            float safeMax = motionCapacityAuthority
                    ? Math.max(1.001f, Math.min(8.0f, maxRatio))
                    : Math.max(1.50f, Math.min(8.0f, maxRatio));
            /* IRIS_26640_UHDR_CAPACITY_EQUALS_MEASURED_STORED_RANGE
             * Motion advertises the same full-HDR display capacity as the gain-map encoding range.
             * The scene's current peak gain remains content, not metadata capacity. Night retains
             * its frozen requested-capacity policy. */
            float fullHdrDisplayRatio = motionCapacityAuthority
                    ? safeMax
                    : Math.max(1.02f, Math.min(safeMax, requestedFullHdrDisplayRatio));
            Gainmap gainmap = new Gainmap(oriented);
            gainmap.setRatioMin(MIN_RATIO, MIN_RATIO, MIN_RATIO);
            gainmap.setRatioMax(safeMax, safeMax, safeMax);
            gainmap.setGamma(1.0f, 1.0f, 1.0f);
            gainmap.setEpsilonSdr(EPSILON, EPSILON, EPSILON);
            gainmap.setEpsilonHdr(EPSILON, EPSILON, EPSILON);
            /*
             * IRIS_26438_STANDARD_ULTRAHDR_METADATA
             * GainMapMin=1.0 => HDRCapacityMin=1.0 in Android's linear API.
             * HDRCapacityMax follows GainMapMax exactly, as recommended by
             * the Android Ultra HDR specification.
             */
            gainmap.setMinDisplayRatioForHdrTransition(MIN_HDR_TRANSITION);
            gainmap.setDisplayRatioForFullHdr(fullHdrDisplayRatio);

            sdrBase.setGainmap(gainmap);
            boolean attached = sdrBase.hasGainmap();
            if (motionCapacityAuthority) {
                try {
                    com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                            "IRIS_26596_UHDR_CAPACITY_METADATA",
                            "attached=" + attached
                                    + " ratioMax=" + safeMax
                                    + " minHdrTransition=" + MIN_HDR_TRANSITION
                                    + " fullHdrDisplayRatio=" + fullHdrDisplayRatio
                                    + " capacityMatchesGainMapMax=true"
                                    + " gainOwner=HEALTHY_HDR_MASTER_VS_SDR");
                } catch (Throwable ignored) {}
            }

            Log.d(TAG, "IRIS_26436_TRUE_ULTRAHDR_ATTACH"
                    + " attached=" + attached
                    + " rotation=" + rotation
                    + " ratioMin=1.0"
                    + " ratioMax=" + safeMax
                    + " minHdrTransition=" + MIN_HDR_TRANSITION
                    + " fullHdrDisplayRatio=" + fullHdrDisplayRatio
                    + " ratioMaxIndependentFromFullDisplayRatio=" + safeMax
                    + " motionCapacityAuthority=" + motionCapacityAuthority
                    + " capacityMatchesGainMapMax=" + motionCapacityAuthority
                    + " IRIS_26640_UHDR_MEASURED_CAPACITY_AUTHORITY=" + motionCapacityAuthority
                    + " epsilonSdr=0.015625"
                    + " epsilonHdr=0.015625"
                    + " gamma=1.0"
                    + " metadataProfile=AndroidUltraHdr_v1_1_AdobeHdrgm"
                    + " standardCapacityRange=true"
                    + " source=V2MatchedSdrHdrLinearIntentQuotient"
                    + " gainOwner=HEALTHY_HDR_MASTER_VS_SDR");
            return attached;
        } catch (Exception t) {
            Log.e(TAG, "IRIS_26436_TRUE_ULTRAHDR_ATTACH_FAILED "
                    + Log.getStackTraceString(t));
            return false;
        }
    }
}
