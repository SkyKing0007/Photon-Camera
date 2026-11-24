package com.particlesdevs.photoncamera.processing.experimentc;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;

/**
 * Experiment C native 1x output: do not synthesize a 2x RAISR image only to
 * downsample it. The original bjzhou RAW finisher selects RAISR for 2x
 * magnification, not for native 1x output. Input is already finalized,
 * encoded sRGB RGBA32F at the precise output pixel coordinates.
 *
 * This bounded transfer has no fallback to RAW, Bayer, A/B or YUV processing.
 * It does not replace the still-required donor RAW/color/denoise/sharpen chain.
 */
public final class Iris26975CNativeOneX {
    private Iris26975CNativeOneX() {}

    public static boolean render(final ByteBuffer encodedRgba32f,
                                 final int width, final int height,
                                 final int srcStrideBytes,
                                 final ByteBuffer outputRgba8,
                                 final int dstStrideBytes) {
        if (encodedRgba32f == null || outputRgba8 == null ||
                !encodedRgba32f.isDirect() || !outputRgba8.isDirect() ||
                outputRgba8.isReadOnly() ||
                width <= 0 || height <= 0 || width > 16384 || height > 16384 ||
                srcStrideBytes < 16L * width || srcStrideBytes % 4 != 0 ||
                dstStrideBytes < 4L * width ||
                (long)(height - 1) * srcStrideBytes + (long)width * 16 > encodedRgba32f.capacity() ||
                (long)(height - 1) * dstStrideBytes + (long)width * 4 > outputRgba8.capacity())
            return false;
        final ByteBuffer sourceView = encodedRgba32f.duplicate().order(ByteOrder.nativeOrder());
        sourceView.clear();
        final FloatBuffer input = sourceView.asFloatBuffer();
        final ByteBuffer out = outputRgba8.duplicate();
        final int inStride = srcStrideBytes / 4;
        // Pass one checks the entire tile, so a bad last pixel cannot cause a
        // partially written gallery band. The caller owns publication rollback.
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                int p = y * inStride + x * 4;
                for (int channel = 0; channel < 3; channel++) {
                    if (!Float.isFinite(input.get(p + channel))) return false;
                }
            }
        }
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                final int p = y * inStride + x * 4;
                final int target = y * dstStrideBytes + x * 4;
                for (int channel = 0; channel < 3; channel++) {
                    final float c = input.get(p + channel);
                    final int byteValue = Math.max(0, Math.min(255, Math.round(c * 255f)));
                    out.put(target + channel, (byte)byteValue);
                }
                out.put(target + 3, (byte)255);
            }
        }
        return true;
    }
}
