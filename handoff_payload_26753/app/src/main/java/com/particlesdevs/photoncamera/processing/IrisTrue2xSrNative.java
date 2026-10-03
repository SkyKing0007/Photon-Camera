package com.particlesdevs.photoncamera.processing;

import java.nio.ByteBuffer;

/**
 * IRIS_26564_TRUE_2X_CPU_GPU_SEMANTIC_BRIDGE
 *
 * Native CPU reference backend for the true-2x Sabre reconstruction contract. The GLES
 * accelerator consumes the same persisted flow/covariance/rejection evidence and the same CFA
 * RBF equations. This class intentionally owns no device/manufacturer policy.
 */
public final class IrisTrue2xSrNative {
    static { System.loadLibrary("motionv2jpeg"); }
    private IrisTrue2xSrNative() {}

    /** Accumulator layout is six float32 values per output pixel: R,G,B,Rw,Gw,Bw. */
    public static native boolean accumulateCpuTileFrame(
            ByteBuffer accumulatorFloat32,
            ByteBuffer phaseMask,
            int tileWidth, int tileHeight,
            int outputOriginX, int outputOriginY,
            int fullOutputWidth, int fullOutputHeight,
            ByteBuffer raw16,
            int rawOriginX, int rawOriginY, int rawRegionWidth, int rawRegionHeight,
            int rawRowStrideSamples,
            ByteBuffer flowRgba16f,
            int flowWidth, int flowHeight,
            float flowScaleX, float flowScaleY, float flowOffsetX, float flowOffsetY,
            ByteBuffer covarianceRgb10a2,
            int covarianceOriginX, int covarianceOriginY,
            int covarianceRegionWidth, int covarianceRegionHeight,
            int covarianceFullWidth, int covarianceFullHeight,
            ByteBuffer rejectionR8,
            int rejectionOriginX, int rejectionOriginY,
            int rejectionRegionWidth, int rejectionRegionHeight,
            int rejectionFullWidth, int rejectionFullHeight,
            int fullRawWidth, int fullRawHeight,
            int cfaPattern,
            float[] gains,
            float[] blackTerms,
            float[] covarianceRangeRg,
            float[] covarianceRangeB,
            boolean useFrameWeight, float rawClipThreshold);

    /** Resolve dehomogenized camera RGB, undo calculation WB, apply lens shading, write RGB16F. */
    public static native boolean resolveCpuTile(
            ByteBuffer accumulatorFloat32,
            ByteBuffer outputRgb16f,
            int tileWidth, int tileHeight,
            int outputOriginX, int outputOriginY,
            int fullOutputWidth, int fullOutputHeight,
            float[] cameraDomainScale,
            float[] lensShading,
            int lensShadingWidth, int lensShadingHeight);

    /**
     * Transfer only the proven native Sabre/VGN low-frequency camera-chroma result onto the
     * true-2x carrier. The correction field is bilinearly interpolated on the native grid, has
     * zero 0.25/0.50/0.25 camera-luma component, and therefore cannot replace true-2x luma/detail.
     */
    public static native boolean applyNativeVgnChromaGuide(
            String true2xRgb16fPath, int true2xWidth, int true2xHeight,
            String nativeVgnRgb16fPath, int nativeWidth, int nativeHeight);

    /**
     * Build one bounded RGBA16F render tile whose RGB/chroma/highlight authority is exclusively
     * the native Sabre/VGN guide. Direct-CFA true2x contributes only a phase/support-gated scalar
     * luminance-detail factor applied equally to R/G/B. The pristine DNG source is never modified.
     */
    public static native boolean prepareVgnGuidedRenderTile(
            String true2xRgb16fPath, int true2xWidth, int true2xHeight,
            String nativeVgnRgb16fPath, int nativeWidth, int nativeHeight,
            String phaseSupportPath, int regionX, int regionY, int regionWidth, int regionHeight,
            ByteBuffer outputRgba16f, long[] detailStats);


    /** IRIS_26752_IPOL_PLAN_B_INPUT
     * Resolve one unwarped NORMAL RAW tile to scalar linear camera-luma on the native grid.
     * No flow is applied here: the paper's translation operator owns registration.
     */
    public static native boolean writePlanBLumaTile(
            String outputF32Path, int outputWidth, int outputHeight,
            int tileX, int tileY, int tileWidth, int tileHeight,
            int sampleOriginX, int sampleOriginY,
            ByteBuffer raw16, int rawOriginX, int rawOriginY, int rawRegionWidth, int rawRegionHeight,
            int rawRowStrideSamples,
            ByteBuffer covarianceRgb10a2, int covarianceOriginX, int covarianceOriginY,
            int covarianceRegionWidth, int covarianceRegionHeight, int covarianceFullWidth, int covarianceFullHeight,
            int fullRawWidth, int fullRawHeight, int cfaPattern,
            float[] gains, float[] blackTerms, float[] covarianceRangeRg, float[] covarianceRangeB,
            float[] cameraDomainScale, float[] lensShading, int lensShadingWidth, int lensShadingHeight);

    /** IRIS_26753_IPOL_PLAN_B_MOBILE_TILE
     * Solve one bounded Plan-B tile directly on its requested output grid. The native owner runs
     * exactly one direct Moore-Penrose WLS solve, then enters at most five l1-l2 IRLS updates only
     * when robust residual statistics prove an actual frame outlier. Memory and wall-clock work are
     * hard-bounded by the caller.
     */
    public static native boolean reconstructPlanBTileDirect(
            String[] lumaF32Paths, int inputWidth, int inputHeight,
            int outputWidth, int outputHeight, float[] shiftX, float[] shiftY,
            long memoryBudgetBytes, long maxDurationMs,
            String outputF32Path, float[] finalWeights, long[] stats);

    /** Feather one directly reconstructed overlapping tile into disk-backed float accumulators. */
    public static native boolean accumulatePlanBTile(
            String tileF32Path, int tileWidth, int tileHeight, int originX, int originY,
            int fullWidth, int fullHeight, int overlapPixels,
            String sumF32Path, String weightF32Path, long maxDurationMs);

    /** Normalize the bounded overlap accumulators to the final direct native-grid Plan-B luma. */
    public static native boolean finalizePlanBAccumulation(
            String sumF32Path, String weightF32Path, int fullWidth, int fullHeight,
            String outputF32Path, long maxDurationMs);

    /**
     * Convert the absolute Plan-B luma result to a bounded R16F log2 luminance sidecar against
     * the untouched native Sabre/VGN guide. Existing signal/highlight/agreement safety gates remain
     * authoritative; the modified-Tukey border is fail-closed to zero detail.
     */
    public static native boolean buildPlanBDetail(
            String reconstructedLumaF32Path, int reconstructedWidth, int reconstructedHeight,
            String nativeVgnRgb16fPath, int nativeWidth, int nativeHeight,
            float sourceOriginX, float sourceOriginY, float scaleX, float scaleY,
            float maxAbsShiftX, float maxAbsShiftY, String detailR16fPath, long[] detailStats,
            long maxDurationMs);

    /** Build a full publication RGB16F carrier from native Sabre/VGN RGB and Plan-B luma detail. */
    public static native boolean composePlanBRender(
            String nativeVgnRgb16fPath, int nativeWidth, int nativeHeight,
            String detailR16fPath, int detailWidth, int detailHeight,
            float detailOriginX, float detailOriginY, float detailScaleX, float detailScaleY,
            int outputWidth, int outputHeight, float publicationScaleX, float publicationScaleY,
            String outputRgb16fPath, long maxDurationMs);

    /** Pack the requested interior of an RGBA16F region into a disk-backed RGB16F render carrier. */
    public static native boolean writeRenderTileInterior(
            String outputRgb16fPath, int fullWidth, int fullHeight,
            ByteBuffer regionRgba16f, int regionX, int regionY, int regionWidth, int regionHeight,
            int interiorX, int interiorY, int interiorWidth, int interiorHeight);
}
