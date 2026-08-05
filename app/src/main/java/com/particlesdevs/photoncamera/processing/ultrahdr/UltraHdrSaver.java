package com.particlesdevs.photoncamera.processing.ultrahdr;

import android.graphics.Bitmap;
import android.graphics.Gainmap;
import android.os.Build;

import com.particlesdevs.photoncamera.util.Log;

import java.io.OutputStream;
import java.nio.ByteBuffer;

/** Recovered from the user's working PhotonCamera APK. */
public final class UltraHdrSaver {
    private static final String TAG = "UltraHdrSaver";
    private static final float DEFAULT_FULL_HDR_RATIO = 1.8f;
    private static final int DOWNSAMPLE = 4;
    private static final float EPSILON = 1.0e-4f;
    private static final float GAIN_START_LUMA = 0.25f;
    private static final float GAIN_END_LUMA = 1.0f;
    private static final float MIN_GAIN_RATIO = 1.0f;
    private static final float MAX_GAIN_RATIO = 4.0f;
    private static final float MIN_FULL_HDR_RATIO = 1.02f;
    private static final float LUMA_RED = 0.2126f;
    private static final float LUMA_GREEN = 0.7152f;
    private static final float LUMA_BLUE = 0.0722f;

    private UltraHdrSaver() {}

    public static boolean save(Bitmap bitmap, OutputStream outputStream, int quality) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.UPSIDE_DOWN_CAKE
                || bitmap == null || outputStream == null) {
            return false;
        }

        Bitmap gainmapBitmap = null;
        Bitmap outputBitmap = null;
        try {
            gainmapBitmap = createGainmapBitmap(bitmap, DEFAULT_FULL_HDR_RATIO, 1.0f);
            if (gainmapBitmap == null) {
                Log.e(TAG, "Failed to create gainmap bitmap");
                return false;
            }

            Gainmap gainmap = new Gainmap(gainmapBitmap);
            gainmap.setRatioMin(MIN_GAIN_RATIO, MIN_GAIN_RATIO, MIN_GAIN_RATIO);
            gainmap.setRatioMax(MAX_GAIN_RATIO, MAX_GAIN_RATIO, MAX_GAIN_RATIO);
            gainmap.setGamma(1.0f, 1.0f, 1.0f);
            gainmap.setEpsilonSdr(EPSILON, EPSILON, EPSILON);
            gainmap.setEpsilonHdr(EPSILON, EPSILON, EPSILON);
            gainmap.setMinDisplayRatioForHdrTransition(MIN_FULL_HDR_RATIO);
            gainmap.setDisplayRatioForFullHdr(DEFAULT_FULL_HDR_RATIO);

            outputBitmap = bitmap.copy(Bitmap.Config.ARGB_8888, false);
            if (outputBitmap == null) return false;
            outputBitmap.setGainmap(gainmap);

            boolean saved = outputBitmap.compress(
                    Bitmap.CompressFormat.JPEG, quality, outputStream);
            outputStream.flush();
            if (saved) Log.d(TAG, "UltraHDR JPEG saved successfully");
            return saved;
        } catch (Exception e) {
            Log.e(TAG, "save failed", e);
            return false;
        } finally {
            if (outputBitmap != null && !outputBitmap.isRecycled()) outputBitmap.recycle();
            if (gainmapBitmap != null && !gainmapBitmap.isRecycled()) gainmapBitmap.recycle();
        }
    }

    private static Bitmap createGainmapBitmap(Bitmap bitmap, float fullHdrRatio, float strength) {
        int width = bitmap.getWidth();
        int height = bitmap.getHeight();
        if (width <= 0 || height <= 0) return null;

        int gainWidth = Math.max(1, width / DOWNSAMPLE);
        int gainHeight = Math.max(1, height / DOWNSAMPLE);
        byte[] gainData = new byte[gainWidth * gainHeight];
        float maxRatio = Math.max(MIN_FULL_HDR_RATIO,
                Math.min(MAX_GAIN_RATIO, fullHdrRatio));
        float safeStrength = Math.max(0.25f, Math.min(2.0f, strength));

        int index = 0;
        for (int y = 0; y < gainHeight; y++) {
            int sourceY = Math.min((int) (((y + 0.5f) * height) / gainHeight), height - 1);
            for (int x = 0; x < gainWidth; x++) {
                int sourceX = Math.min((int) (((x + 0.5f) * width) / gainWidth), width - 1);
                int pixel = bitmap.getPixel(sourceX, sourceY);
                float r = ((pixel >> 16) & 255) / 255.0f;
                float g = ((pixel >> 8) & 255) / 255.0f;
                float b = (pixel & 255) / 255.0f;
                float luma = Math.max(0.0f, Math.min(1.0f,
                        r * LUMA_RED + g * LUMA_GREEN + b * LUMA_BLUE));
                float ratio = 1.0f + (maxRatio - 1.0f)
                        * smoothstep(GAIN_START_LUMA, GAIN_END_LUMA, luma)
                        * safeStrength;
                ratio = Math.max(MIN_GAIN_RATIO, Math.min(MAX_GAIN_RATIO, ratio));
                gainData[index++] = (byte) encodeRatio(ratio, MIN_GAIN_RATIO, MAX_GAIN_RATIO);
            }
        }

        Bitmap gainmap = Bitmap.createBitmap(gainWidth, gainHeight, Bitmap.Config.ALPHA_8);
        gainmap.copyPixelsFromBuffer(ByteBuffer.wrap(gainData));
        return gainmap;
    }

    private static float smoothstep(float edge0, float edge1, float value) {
        float t = Math.max(0.0f, Math.min(1.0f, (value - edge0) / (edge1 - edge0)));
        return t * t * (3.0f - 2.0f * t);
    }

    private static int encodeRatio(float ratio, float minRatio, float maxRatio) {
        float clamped = Math.max(minRatio, Math.min(maxRatio, ratio));
        return Math.max(0, Math.min(255, (int) (
                Math.log(clamped / minRatio) / Math.log(maxRatio / minRatio) * 255.0f)));
    }
}
