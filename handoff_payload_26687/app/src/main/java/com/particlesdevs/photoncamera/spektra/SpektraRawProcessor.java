package com.particlesdevs.photoncamera.spektra;

import android.graphics.Rect;

import com.particlesdevs.photoncamera.util.Log;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;

/**
 * Spektra-owned single-frame RAW front end.
 *
 * Active-path invariant for 26687: packed Camera2 RAW -> one persistent native Vulkan owner ->
 * scene-linear RGBA16F. No Iris GLContext/GLProg/GLTexture and no Motion RCD runtime ownership.
 */
public final class SpektraRawProcessor {
    static { System.loadLibrary("spektra_iris"); }

    private static final String TAG = "SpektraRawProcessor";
    public static final float SAVED_CHROMA_DENOISE_STRENGTH = 0.75f;
    private static final float SENSOR_CLIP_THRESHOLD = 0.985f;

    public static final class LinearFrame {
        public final int width;
        public final int height;
        /** Native-order RGBA IEEE-754 half-float, scene-linear Rec.709/sRGB primaries. */
        public final ByteBuffer rgba16f;
        LinearFrame(int width, int height, ByteBuffer rgba16f) {
            this.width = width;
            this.height = height;
            this.rgba16f = rgba16f;
        }
    }

    public LinearFrame process(SpektraShot shot, boolean savedPhoto) {
        if (shot == null || shot.raw == null || shot.metadata == null) {
            throw new IllegalArgumentException("Spektra RAW recipe incomplete");
        }
        validateRecipe(shot.metadata, shot.sensorToLinearSrgb);
        if (!savedPhoto) {
            byte[] preview = shot.raw.previewLinearRgba16f;
            if (preview == null) throw new IllegalArgumentException("Spektra VF-S native linear frame missing");
            return linearFrame(shot.raw.width, shot.raw.height, preview);
        }
        if (shot.raw.packedRaw == null) {
            throw new IllegalArgumentException("Saved Spektra packed RAW missing");
        }
        ByteBuffer packed = ByteBuffer.allocateDirect(shot.raw.packedRaw.length).order(ByteOrder.nativeOrder());
        packed.put(shot.raw.packedRaw).flip();
        Rect crop = shot.metadata.sourceCrop;
        byte[] out = nativeProcessPackedRaw(packed, 0, shot.raw.packedRaw.length,
                shot.raw.sourceWidth(), shot.raw.sourceHeight(), shot.raw.rowStride, shot.raw.pixelStride,
                shot.raw.sourceFormat, rect4(shot.metadata.rawBounds), rect4(crop), rect4(shot.metadata.activeRawDomain),
                shot.metadata.cfaArrangement, shot.metadata.bayerOffset, shot.metadata.blackLevel4,
                shot.metadata.whiteLevel, shot.metadata.lensShading, shot.metadata.lensShadingRows,
                shot.metadata.lensShadingCols, shot.sensorToLinearSrgb, crop.width(), crop.height(), true,
                SAVED_CHROMA_DENOISE_STRENGTH, SENSOR_CLIP_THRESHOLD);
        if (out == null) throw new IllegalStateException("Spektra saved Vulkan RAW owner returned no frame");
        Log.d(TAG, "IRIS_26687_SPEKTRA_NATIVE_RAW_OWNER saved=true raw="
                + shot.raw.sourceWidth() + "x" + shot.raw.sourceHeight()
                + " crop=" + crop + " activeRaw=" + shot.metadata.activeRawDomain
                + " bayerOffset=" + shot.metadata.bayerOffset
                + " highlightRecovery=true chromaDenoise=" + SAVED_CHROMA_DENOISE_STRENGTH
                + " output=sceneLinearRec709 owner=Vulkan");
        return linearFrame(crop.width(), crop.height(), out);
    }

    static byte[] processLivePreview(ByteBuffer source, int sourceOffset, int sourceBytes,
            int sourceWidth, int sourceHeight, int rowStride, int pixelStride, int format,
            SpektraFrameMetadata metadata, float[] sensorToLinearSrgb, int outputWidth, int outputHeight) {
        validateRecipe(metadata, sensorToLinearSrgb);
        if (source == null || !source.isDirect()) {
            throw new IllegalArgumentException("VF-S native RAW owner requires a direct Camera2 plane");
        }
        return nativeProcessPackedRaw(source, sourceOffset, sourceBytes, sourceWidth, sourceHeight,
                rowStride, pixelStride, format, rect4(metadata.rawBounds), rect4(metadata.sourceCrop),
                rect4(metadata.activeRawDomain), metadata.cfaArrangement, metadata.bayerOffset,
                metadata.blackLevel4, metadata.whiteLevel, metadata.lensShading,
                metadata.lensShadingRows, metadata.lensShadingCols, sensorToLinearSrgb,
                outputWidth, outputHeight, false, 0.0f, SENSOR_CLIP_THRESHOLD);
    }

    static LinearFrame previewLinearFrame(SpektraRawFrame raw) {
        if (raw == null || raw.previewLinearRgba16f == null) {
            throw new IllegalArgumentException("Spektra VF-S native linear frame missing");
        }
        return linearFrame(raw.width, raw.height, raw.previewLinearRgba16f);
    }

    public static void warmUpNativeOwner() { nativeWarmUpRawOwner(); }

    public static void releaseNativeOwner() {
        nativeReleaseRawOwner();
    }

    /** Returns {previewProcessed, previewDropped, avgPreviewMicros, lastStillMicros, ownerCount, allocationCount}. */
    public static long[] nativeStats() {
        long[] stats = nativeRawOwnerStats();
        return stats == null ? new long[6] : stats;
    }

    private static void validateRecipe(SpektraFrameMetadata metadata, float[] matrix) {
        if (metadata == null || metadata.cfaArrangement < 0 || metadata.cfaArrangement > 3
                || metadata.bayerOffset < 0 || metadata.bayerOffset > 3
                || metadata.blackLevel4 == null || metadata.blackLevel4.length != 4
                || metadata.whiteLevel <= 0 || metadata.rawBounds == null || metadata.sourceCrop == null
                || metadata.activeRawDomain == null || matrix == null || matrix.length != 9) {
            throw new IllegalArgumentException("Spektra native RAW recipe incomplete");
        }
        if (!metadata.rawBounds.contains(metadata.sourceCrop)
                || !metadata.rawBounds.contains(metadata.activeRawDomain)) {
            throw new IllegalArgumentException("Spektra RAW geometry domains disagree");
        }
    }

    private static int[] rect4(Rect r) {
        return new int[]{r.left, r.top, r.right, r.bottom};
    }

    private static LinearFrame linearFrame(int width, int height, byte[] bytes) {
        long expected = (long) width * (long) height * 8L;
        if (width <= 0 || height <= 0 || expected > Integer.MAX_VALUE
                || bytes == null || bytes.length != (int) expected) {
            throw new IllegalArgumentException("Spektra native RGBA16F byte count mismatch");
        }
        ByteBuffer out = ByteBuffer.allocateDirect(bytes.length).order(ByteOrder.nativeOrder());
        out.put(bytes).flip();
        return new LinearFrame(width, height, out);
    }

    private static native byte[] nativeProcessPackedRaw(ByteBuffer source, int sourceOffset, int sourceBytes,
            int sourceWidth, int sourceHeight, int rowStride, int pixelStride, int format,
            int[] rawBounds4, int[] sourceCrop4, int[] activeRawDomain4, int cfaArrangement,
            int bayerOffset, int[] blackLevel4, int whiteLevel, float[] lensShading,
            int lensShadingRows, int lensShadingCols, float[] sensorToLinearSrgb,
            int outputWidth, int outputHeight, boolean savedPhoto, float chromaDenoiseStrength,
            float sensorClipThreshold);

    private static native void nativeWarmUpRawOwner();
    private static native void nativeReleaseRawOwner();
    private static native long[] nativeRawOwnerStats();
}
