package com.particlesdevs.photoncamera.processing.experimentc;

import java.nio.ByteBuffer;

/**
 * C-owned native finishing bridge. This NEVER replaces Sabre or runs RAISR:
 * the input must already be genuine bjzhou/MGC 2x RAISR RGBA8 pixels.
 * No A/B/YUV/Lanczos reconstruction fallback exists in this class.
 *
 * Input tile coordinates are in the global 2x output grid; destination
 * coordinates and dimensions are in the global native 1x grid. The entire
 * interpolation halo must be present, otherwise the native function fails.
 */
public final class Iris26972CNativeDownsample {
    private Iris26972CNativeDownsample() {}

    static { System.loadLibrary("iris26972c"); }

    public static boolean fromGenuineRaisr2x(
            ByteBuffer raisrTileRGBA8,
            int tileWidth2x, int tileHeight2x, int tileRowStrideBytes,
            int tileGlobalX2x, int tileGlobalY2x,
            int fullWidth2x, int fullHeight2x,
            int targetNativeX, int targetNativeY,
            int targetNativeWidth, int targetNativeHeight,
            ByteBuffer outputNativeRGBA8, int outputRowStrideBytes) {
        if (raisrTileRGBA8 == null || outputNativeRGBA8 == null ||
                !raisrTileRGBA8.isDirect() || !outputNativeRGBA8.isDirect() ||
                raisrTileRGBA8.isReadOnly() || outputNativeRGBA8.isReadOnly()) return false;
        return downsampleNative(
                raisrTileRGBA8, tileWidth2x, tileHeight2x, tileRowStrideBytes,
                tileGlobalX2x, tileGlobalY2x, fullWidth2x, fullHeight2x,
                targetNativeX, targetNativeY,
                targetNativeWidth, targetNativeHeight,
                outputNativeRGBA8, outputRowStrideBytes);
    }

    private static native boolean downsampleNative(
            ByteBuffer input, int tileWidth, int tileHeight, int tileStride,
            int tileX, int tileY, int fullWidth, int fullHeight,
            int outputX, int outputY, int outputWidth, int outputHeight,
            ByteBuffer output, int outputStride);
}
