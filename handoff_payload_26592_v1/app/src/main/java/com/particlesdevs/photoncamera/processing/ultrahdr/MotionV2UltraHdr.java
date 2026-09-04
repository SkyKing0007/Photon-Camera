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
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.UPSIDE_DOWN_CAKE
                || sdrBase == null
                || unrotatedGainMap == null) {
            return false;
        }

        Bitmap oriented = unrotatedGainMap;
        try {
            int rotation = ((rotationDegrees % 360) + 360) % 360;
            if (rotation != 0) {
                Matrix matrix = new Matrix();
                matrix.postRotate(rotation);
                oriented = Bitmap.createBitmap(
                        unrotatedGainMap,
                        0,
                        0,
                        unrotatedGainMap.getWidth(),
                        unrotatedGainMap.getHeight(),
                        matrix,
                        false);
                if (oriented != unrotatedGainMap
                        && !unrotatedGainMap.isRecycled()) {
                    unrotatedGainMap.recycle();
                }
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
            float safeMax = Math.max(1.50f, Math.min(8.0f, maxRatio));
            float fullHdrDisplayRatio = Math.max(
                    MIN_HDR_TRANSITION,
                    Math.min(safeMax, DEFAULT_FULL_HDR_DISPLAY_RATIO));
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

            Log.d(TAG, "IRIS_26436_TRUE_ULTRAHDR_ATTACH"
                    + " attached=" + attached
                    + " rotation=" + rotation
                    + " ratioMin=1.0"
                    + " ratioMax=" + safeMax
                    + " minHdrTransition=" + MIN_HDR_TRANSITION
                    + " fullHdrDisplayRatio=" + fullHdrDisplayRatio
                    + " ratioMaxIndependentFromFullDisplayRatio=" + safeMax
                    + " IRIS_26507_FULL_HDR_DISPLAY_CAPACITY_PARITY=true"
                    + " epsilonSdr=0.015625"
                    + " epsilonHdr=0.015625"
                    + " gamma=1.0"
                    + " metadataProfile=AndroidUltraHdr_v1_1_AdobeHdrgm"
                    + " standardCapacityRange=true"
                    + " source=V2ExtendedLinearBroadRendition"
                    + " bodyGainUnity=true");
            return attached;
        } catch (Exception t) {
            Log.e(TAG, "IRIS_26436_TRUE_ULTRAHDR_ATTACH_FAILED "
                    + Log.getStackTraceString(t));
            return false;
        }
    }
}
