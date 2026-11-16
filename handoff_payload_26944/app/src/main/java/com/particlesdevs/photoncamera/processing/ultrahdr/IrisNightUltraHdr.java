package com.particlesdevs.photoncamera.processing.ultrahdr;

import android.graphics.Bitmap;
import android.graphics.Matrix;
import android.os.Build;

import com.particlesdevs.photoncamera.util.Log;

import java.nio.ByteBuffer;

/**
 * IRIS_26550_NIGHT_POST_JIN_ULTRAHDR_OWNER
 *
 * Night's GL render owns the true pre-Jin relationship between Sabre extended-linear HDR and its
 * SDR rendition. Jin then modifies only the SDR bitmap. Keep that HDR authority detached, sample
 * the matching pre-Jin SDR luma on the gain-map grid, and after Jin rebase each logarithmic gain
 * against the FINAL SDR luma. This preserves the same HDR target without retaining a second
 * full-resolution SDR bitmap and without letting Jin become HDR/exposure authority.
 */
public final class IrisNightUltraHdr {
    private static final String TAG = "IrisNightUltraHdr";
    private static final float UHDR_OFFSET = 0.015625f;

    public static final class Prepared {
        Bitmap orientedGainMap;
        final float[] preJinLinearLuma;
        final float maxRatio;
        Prepared(Bitmap gainMap, float[] luma, float ratio) {
            orientedGainMap = gainMap;
            preJinLinearLuma = luma;
            maxRatio = ratio;
        }
    }

    private IrisNightUltraHdr() {}

    public static Prepared prepare(Bitmap preJinSdr, Bitmap unrotatedGainMap,
                                   float maxRatio, int rotationDegrees) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.UPSIDE_DOWN_CAKE
                || preJinSdr == null || preJinSdr.isRecycled()
                || unrotatedGainMap == null || unrotatedGainMap.isRecycled()) {
            recycle(unrotatedGainMap);
            return null;
        }
        Bitmap oriented = unrotatedGainMap;
        try {
            int rotation = ((rotationDegrees % 360) + 360) % 360;
            if (rotation != 0) {
                Matrix matrix = new Matrix();
                matrix.postRotate(rotation);
                oriented = Bitmap.createBitmap(unrotatedGainMap, 0, 0,
                        unrotatedGainMap.getWidth(), unrotatedGainMap.getHeight(), matrix, false);
                if (oriented != unrotatedGainMap) recycle(unrotatedGainMap);
            }
            float baseAspect = preJinSdr.getWidth() / (float)Math.max(1, preJinSdr.getHeight());
            float gainAspect = oriented.getWidth() / (float)Math.max(1, oriented.getHeight());
            if (Math.abs(baseAspect - gainAspect) > 0.02f) {
                throw new IllegalStateException("26550 Night UHDR aspect mismatch base="
                        + preJinSdr.getWidth() + "x" + preJinSdr.getHeight()
                        + " gain=" + oriented.getWidth() + "x" + oriented.getHeight());
            }
            float[] pre = sampleLinearLuma(preJinSdr, oriented.getWidth(), oriented.getHeight());
            float safeMax = Math.max(1.50f, Math.min(2.5f, maxRatio));
            Log.i(TAG, "IRIS_26550_NIGHT_UHDR_PREPARE gain=" + oriented.getWidth() + "x"
                    + oriented.getHeight() + " base=" + preJinSdr.getWidth() + "x"
                    + preJinSdr.getHeight() + " maxRatio=" + safeMax
                    + " rotation=" + rotation + " preJinAttached=false memoryBounded=true");
            return new Prepared(oriented, pre, safeMax);
        } catch (Throwable t) {
            Log.e(TAG, "IRIS_26550_NIGHT_UHDR_PREPARE_FAILED", t);
            recycle(oriented);
            return null;
        }
    }

    public static boolean attachPostJin(Bitmap finalSdr, Prepared prepared) {
        if (prepared == null) return false;
        Bitmap oldMap = prepared.orientedGainMap;
        prepared.orientedGainMap = null;
        Bitmap rebased = null;
        try {
            if (Build.VERSION.SDK_INT < Build.VERSION_CODES.UPSIDE_DOWN_CAKE
                    || finalSdr == null || finalSdr.isRecycled() || oldMap == null
                    || oldMap.isRecycled()) return false;
            final int w = oldMap.getWidth(), h = oldMap.getHeight();
            float[] finalLuma = sampleLinearLuma(finalSdr, w, h);
            if (prepared.preJinLinearLuma.length != w * h || finalLuma.length != w * h) {
                throw new IllegalStateException("26550 Night UHDR luma grid mismatch");
            }
            ByteBuffer codes = ByteBuffer.allocateDirect(w * h);
            oldMap.copyPixelsToBuffer(codes);
            codes.position(0);
            ByteBuffer out = ByteBuffer.allocateDirect(w * h);
            final double logMax = Math.log(prepared.maxRatio);
            int nonUnity = 0, peak = 0;
            double ratioSum = 0.0;
            for (int i = 0; i < w * h; i++) {
                int code = codes.get() & 0xff;
                double oldRatio = Math.exp((code / 255.0) * logMax);
                double pre = Math.max(0.0, prepared.preJinLinearLuma[i]);
                double fin = Math.max(0.0, finalLuma[i]);
                double ratio = oldRatio * (pre + UHDR_OFFSET) / (fin + UHDR_OFFSET);
                ratio = Math.max(1.0, Math.min(prepared.maxRatio, ratio));
                // 26944: the HDR master remains Sabre's *pre-Jin* exposure.
                // Apply the same 26941 highlight-only gain gate AFTER Jin
                // rebase so post-Jin body/shadow contrast cannot be lifted by
                // a broad gainmap. This is luminance-only, pointwise and Night
                // exclusive; no RGB, Jin or native reconstruction changes.
                double hdrIntent = Math.max(0.0, oldRatio * (pre + UHDR_OFFSET) - UHDR_OFFSET);
                double gateT = Math.max(0.0, Math.min(1.0, (hdrIntent - 0.68) / 0.28));
                double highlightGate = gateT * gateT * (3.0 - 2.0 * gateT);
                ratio = 1.0 + (ratio - 1.0) * highlightGate;
                int newCode = logMax > 1.0e-9
                        ? (int)Math.round(Math.log(ratio) / logMax * 255.0) : 0;
                newCode = Math.max(0, Math.min(255, newCode));
                if (newCode > 0) nonUnity++;
                peak = Math.max(peak, newCode);
                ratioSum += ratio;
                out.put((byte)newCode);
            }
            out.position(0);
            rebased = Bitmap.createBitmap(w, h, Bitmap.Config.ALPHA_8);
            rebased.copyPixelsFromBuffer(out);
            boolean attached = MotionV2UltraHdr.attach(finalSdr, rebased, 0, prepared.maxRatio);
            if (!attached) recycle(rebased);
            else rebased = null; // Gainmap attached to finalSdr owns contents.
            Log.i(TAG, "IRIS_26550_NIGHT_UHDR_POST_JIN_REBASE attached=" + attached
                    + " gain=" + w + "x" + h
                    + " nonUnityFraction=" + (nonUnity / (float)Math.max(1, w * h))
                    + " peakCode=" + peak
                    + " meanRatio=" + (ratioSum / Math.max(1, w * h))
                    + " hdrAuthority=SabreExtendedLinear"
                    + " finalSdrAuthority=PostJin"
                    + " jinExposureAuthority=false");
            return attached;
        } catch (Throwable t) {
            Log.e(TAG, "IRIS_26550_NIGHT_UHDR_POST_JIN_REBASE_FAILED", t);
            recycle(rebased);
            return false;
        } finally {
            recycle(oldMap);
        }
    }

    public static void release(Prepared prepared) {
        if (prepared == null) return;
        recycle(prepared.orientedGainMap);
        prepared.orientedGainMap = null;
    }

    private static float[] sampleLinearLuma(Bitmap source, int w, int h) {
        Bitmap scaled = Bitmap.createScaledBitmap(source, w, h, true);
        int[] pixels = new int[w * h];
        scaled.getPixels(pixels, 0, w, 0, 0, w, h);
        if (scaled != source) recycle(scaled);
        float[] out = new float[pixels.length];
        for (int i = 0; i < pixels.length; i++) {
            int c = pixels[i];
            float r = srgbDecode(((c >> 16) & 255) / 255.0f);
            float g = srgbDecode(((c >> 8) & 255) / 255.0f);
            float b = srgbDecode((c & 255) / 255.0f);
            out[i] = 0.2126f * r + 0.7152f * g + 0.0722f * b;
        }
        return out;
    }

    private static float srgbDecode(float x) {
        x = Math.max(0.0f, Math.min(1.0f, x));
        return x <= 0.04045f ? x / 12.92f
                : (float)Math.pow((x + 0.055f) / 1.055f, 2.4);
    }

    private static void recycle(Bitmap bitmap) {
        if (bitmap != null && !bitmap.isRecycled()) {
            try { bitmap.recycle(); } catch (Throwable ignored) {}
        }
    }
}
