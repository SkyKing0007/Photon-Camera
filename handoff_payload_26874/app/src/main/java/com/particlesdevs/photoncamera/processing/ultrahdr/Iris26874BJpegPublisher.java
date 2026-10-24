package com.particlesdevs.photoncamera.processing.ultrahdr;

import android.graphics.Bitmap;
import android.graphics.ColorSpace;
import android.graphics.Gainmap;
import android.os.Build;
import com.particlesdevs.photoncamera.util.Log;
import com.particlesdevs.photoncamera.util.MotionTrace;
import java.nio.file.Path;

/**
 * IRIS_26874_B_JPEG_PUBLISHER: Experiment B output-only JPEG ownership.
 * No RAW, gain-map creation, tone, white balance, ICC conversion or color math.
 * Ordinary B consumes final Display-P3 RGBA + Android gain map; true-2x consumes
 * the existing streaming renderer's full-resolution precompressed JPEG pair.
 * A, effective-A high zoom, HEIC, Night and DNG must never enter this owner.
 */
public final class Iris26874BJpegPublisher {
    private static final String TAG = "Iris26874BJpeg";
    static { System.loadLibrary("iris26874bjpeg"); }
    private Iris26874BJpegPublisher() {}

    private static boolean validP3(Bitmap b) {
        return b != null && !b.isRecycled() && b.getConfig() == Bitmap.Config.ARGB_8888
                && Build.VERSION.SDK_INT >= 26 && b.getColorSpace() != null
                && b.getColorSpace().equals(ColorSpace.get(ColorSpace.Named.DISPLAY_P3));
    }

    public static boolean writeNormal(Path output, Bitmap bitmap, int quality) {
        if (output == null || quality != 98 || !validP3(bitmap)) return false;
        Gainmap gm = Build.VERSION.SDK_INT >= 34 && bitmap.hasGainmap() ? bitmap.getGainmap() : null;
        Bitmap contents = gm != null ? gm.getGainmapContents() : null;
        if (gm != null && (contents == null || contents.isRecycled())) return false;
        long start = System.nanoTime();
        boolean ok = publishBitmapNative(bitmap, contents, output.toString(), quality,
                gm != null ? gm.getRatioMin() : null, gm != null ? gm.getRatioMax() : null,
                gm != null ? gm.getGamma() : null, gm != null ? gm.getEpsilonSdr() : null,
                gm != null ? gm.getEpsilonHdr() : null,
                gm != null ? gm.getMinDisplayRatioForHdrTransition() : 1.0f,
                gm != null ? gm.getDisplayRatioForFullHdr() : 2.0f, true);
        long ms = (System.nanoTime() - start) / 1_000_000L;
        String detail = getLastTelemetryNative();
        Log.i(TAG, "IRIS_26874_B_NATIVE_SAVE mode=normal published=" + ok
                + " gain=" + (gm != null) + " saveMs=" + ms + " " + detail);
        MotionTrace.processingState("IRIS_26874_B_JPEG_PUBLICATION",
                "mode=normal published=" + ok + " saveMs=" + ms + " exclusiveOwner=true " + detail);
        return ok;
    }

    /** Preserve the proven true-2x streaming rasterizer and full-size gain map.
     * This B-only entry point replaces only JPEG/R packaging; it never rescales
     * a bitmap, decodes/re-encodes its 50 MP SDR body, or regenerates gains.
     */
    public static boolean publishTrue2xEncoded(Path output, Path base, Path gain, Gainmap gm) {
        if (output == null || base == null || gain == null || gm == null) return false;
        long start = System.nanoTime();
        boolean ok = publishPrecompressedNative(base.toString(), gain.toString(), output.toString(),
                gm.getRatioMin(), gm.getRatioMax(), gm.getGamma(), gm.getEpsilonSdr(), gm.getEpsilonHdr(),
                gm.getMinDisplayRatioForHdrTransition(), gm.getDisplayRatioForFullHdr(), true);
        long ms = (System.nanoTime() - start) / 1_000_000L;
        String detail = getLastTelemetryNative();
        Log.i(TAG, "IRIS_26874_B_NATIVE_SAVE mode=true2x_streamed published=" + ok
                + " packageMs=" + ms + " " + detail);
        MotionTrace.processingState("IRIS_26874_B_JPEG_PUBLICATION",
                "mode=true2x_streamed published=" + ok + " packageMs=" + ms + " exclusiveOwner=true " + detail);
        return ok;
    }

    private static native String getLastTelemetryNative();
    private static native boolean publishBitmapNative(Bitmap base, Bitmap gain, String output, int quality,
            float[] min, float[] max, float[] gamma, float[] epsilonSdr, float[] epsilonHdr,
            float minHdr, float maxHdr, boolean useBase);
    private static native boolean publishPrecompressedNative(String base, String gain, String output,
            float[] min, float[] max, float[] gamma, float[] epsilonSdr, float[] epsilonHdr,
            float minHdr, float maxHdr, boolean useBase);
}
