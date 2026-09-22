package com.particlesdevs.photoncamera.spektra;

import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CaptureResult;
import android.hardware.camera2.params.BlackLevelPattern;
import android.hardware.camera2.params.LensShadingMap;
import android.util.Rational;

import java.util.Arrays;

/** Capture-result snapshot paired by exact SENSOR_TIMESTAMP with a Spektra RAW image. */
public final class SpektraFrameMetadata {
    public final long timestampNs;
    public final long frameNumber;
    public final long exposureNs;
    public final long frameDurationNs;
    public final int iso;
    public final int requestedIso;
    public final int[] blackLevel4;
    public final int whiteLevel;
    public final float[] neutral3;
    public final float[] lensShading;
    public final int lensShadingRows;
    public final int lensShadingCols;
    public final float aperture;
    public final float focalLengthMm;
    public final float focalLength35Mm;
    public final double[] noiseProfile;
    public final int cfaArrangement;

    private SpektraFrameMetadata(long timestampNs, long frameNumber, long exposureNs, long frameDurationNs,
            int iso, int requestedIso, int[] blackLevel4, int whiteLevel, float[] neutral3,
            float[] lensShading, int lensShadingRows, int lensShadingCols, float aperture,
            float focalLengthMm, float focalLength35Mm, double[] noiseProfile, int cfaArrangement) {
        this.timestampNs = timestampNs;
        this.frameNumber = frameNumber;
        this.exposureNs = exposureNs;
        this.frameDurationNs = frameDurationNs;
        this.iso = iso;
        this.requestedIso = requestedIso;
        this.blackLevel4 = blackLevel4;
        this.whiteLevel = whiteLevel;
        this.neutral3 = neutral3;
        this.lensShading = lensShading;
        this.lensShadingRows = lensShadingRows;
        this.lensShadingCols = lensShadingCols;
        this.aperture = aperture;
        this.focalLengthMm = focalLengthMm;
        this.focalLength35Mm = focalLength35Mm;
        this.noiseProfile = noiseProfile;
        this.cfaArrangement = cfaArrangement;
    }

    static SpektraFrameMetadata restore(long timestampNs, long frameNumber, long exposureNs,
            long frameDurationNs, int iso, int requestedIso, int[] blackLevel4, int whiteLevel,
            float[] neutral3, float[] lensShading, int lensShadingRows, int lensShadingCols,
            float aperture, float focalLengthMm, float focalLength35Mm, double[] noiseProfile,
            int cfaArrangement) {
        if (timestampNs <= 0L || frameNumber < 0L || exposureNs <= 0L || iso <= 0 || whiteLevel <= 0) {
            throw new IllegalArgumentException("Invalid frozen Spektra metadata");
        }
        if (blackLevel4 == null || blackLevel4.length != 4) {
            throw new IllegalArgumentException("Frozen Spektra black level must have four CFA values");
        }
        if (neutral3 == null || neutral3.length != 3) {
            throw new IllegalArgumentException("Frozen Spektra neutral point must have three values");
        }
        if (lensShading != null) {
            long expected = (long) lensShadingRows * (long) lensShadingCols * 4L;
            if (lensShadingRows <= 0 || lensShadingCols <= 0 || expected != lensShading.length) {
                throw new IllegalArgumentException("Frozen Spektra lens shading dimensions mismatch");
            }
        } else if (lensShadingRows != 0 || lensShadingCols != 0) {
            throw new IllegalArgumentException("Frozen Spektra lens shading metadata without map");
        }
        return new SpektraFrameMetadata(timestampNs, frameNumber, exposureNs, frameDurationNs, iso,
                requestedIso, blackLevel4.clone(), whiteLevel, neutral3.clone(),
                lensShading == null ? null : lensShading.clone(), lensShadingRows, lensShadingCols,
                aperture, focalLengthMm, focalLength35Mm,
                noiseProfile == null ? null : noiseProfile.clone(), cfaArrangement);
    }

    public static SpektraFrameMetadata from(CaptureResult result, CameraCharacteristics chars,
            long frameNumber, int requestedIso) {
        return from(result, chars, frameNumber, requestedIso, 0);
    }

    /** Apply the verified RAW-buffer origin parity before any demosaic/color owner consumes CFA data. */
    public static SpektraFrameMetadata from(CaptureResult result, CameraCharacteristics chars,
            long frameNumber, int requestedIso, int bayerOffset) {
        Long ts = result.get(CaptureResult.SENSOR_TIMESTAMP);
        Long exp = result.get(CaptureResult.SENSOR_EXPOSURE_TIME);
        Long duration = result.get(CaptureResult.SENSOR_FRAME_DURATION);
        Integer iso = result.get(CaptureResult.SENSOR_SENSITIVITY);
        Integer staticWhite = chars.get(CameraCharacteristics.SENSOR_INFO_WHITE_LEVEL);
        Integer dynamicWhite = result.get(CaptureResult.SENSOR_DYNAMIC_WHITE_LEVEL);
        int resolvedWhite = dynamicWhite != null && dynamicWhite > 0
                ? dynamicWhite : (staticWhite == null ? 0 : staticWhite);
        Integer sensorCfaBox = chars.get(CameraCharacteristics.SENSOR_INFO_COLOR_FILTER_ARRANGEMENT);
        int sensorCfa = sensorCfaBox == null ? -1 : sensorCfaBox;
        int[] sensorBlack = blackLevels(result, chars);
        final int offset = bayerOffset & 3;
        int[] black = new int[4];
        for (int q = 0; q < 4; ++q) black[q] = sensorBlack[q ^ offset];
        int cfa = sensorCfa;
        if (sensorCfa >= 0 && sensorCfa <= 3) cfa = sensorCfa ^ offset;
        float[] neutral = neutralPoint(result);
        LensShadingMap lsm = result.get(CaptureResult.STATISTICS_LENS_SHADING_CORRECTION_MAP);
        float[] lsc = null;
        int rows = 0, cols = 0;
        if (lsm != null) {
            rows = lsm.getRowCount();
            cols = lsm.getColumnCount();
            lsc = new float[rows * cols * 4];
            lsm.copyGainFactors(lsc, 0);
        }
        Float aperture = result.get(CaptureResult.LENS_APERTURE);
        Float focal = result.get(CaptureResult.LENS_FOCAL_LENGTH);
        float focal35 = focal35mm(chars, focal == null ? 0f : focal);
        android.util.Pair<Double, Double>[] noisePairs = result.get(CaptureResult.SENSOR_NOISE_PROFILE);
        double[] noise = null;
        if (noisePairs != null) {
            noise = new double[noisePairs.length * 2];
            for (int i = 0; i < noisePairs.length; ++i) {
                noise[i * 2] = noisePairs[i].first == null ? 0.0 : noisePairs[i].first;
                noise[i * 2 + 1] = noisePairs[i].second == null ? 0.0 : noisePairs[i].second;
            }
        }
        return new SpektraFrameMetadata(ts == null ? 0L : ts, frameNumber,
                exp == null ? 0L : exp, duration == null ? 0L : duration,
                iso == null ? requestedIso : iso, requestedIso, black,
                resolvedWhite, neutral, lsc, rows, cols,
                aperture == null ? 0f : aperture, focal == null ? 0f : focal, focal35,
                noise == null ? null : Arrays.copyOf(noise, noise.length), cfa);
    }

    private static float focal35mm(CameraCharacteristics chars, float focalMm) {
        if (focalMm <= 0f) return 0f;
        android.util.SizeF physical = chars.get(CameraCharacteristics.SENSOR_INFO_PHYSICAL_SIZE);
        if (physical == null || physical.getWidth() <= 0f || physical.getHeight() <= 0f) return 50f;
        double sensorDiag = Math.hypot(physical.getWidth(), physical.getHeight());
        double fullFrameDiag = Math.hypot(36.0, 24.0);
        if (!(sensorDiag > 0.0)) return 50f;
        return (float)(focalMm * fullFrameDiag / sensorDiag);
    }

    private static int[] blackLevels(CaptureResult result, CameraCharacteristics chars) {
        float[] dynamic = result.get(CaptureResult.SENSOR_DYNAMIC_BLACK_LEVEL);
        if (dynamic != null && dynamic.length >= 4) {
            return new int[] {Math.round(dynamic[0]), Math.round(dynamic[1]), Math.round(dynamic[2]), Math.round(dynamic[3])};
        }
        BlackLevelPattern p = chars.get(CameraCharacteristics.SENSOR_BLACK_LEVEL_PATTERN);
        if (p == null) return new int[] {0,0,0,0};
        int[] out = new int[4];
        out[0] = p.getOffsetForIndex(0, 0);
        out[1] = p.getOffsetForIndex(1, 0);
        out[2] = p.getOffsetForIndex(0, 1);
        out[3] = p.getOffsetForIndex(1, 1);
        return out;
    }

    private static float[] neutralPoint(CaptureResult result) {
        Rational[] neutral = result.get(CaptureResult.SENSOR_NEUTRAL_COLOR_POINT);
        if (neutral != null && neutral.length >= 3) {
            return new float[] {neutral[0].floatValue(), neutral[1].floatValue(), neutral[2].floatValue()};
        }
        android.hardware.camera2.params.RggbChannelVector gains = result.get(CaptureResult.COLOR_CORRECTION_GAINS);
        if (gains != null) {
            float g = 0.5f * (gains.getGreenEven() + gains.getGreenOdd());
            return new float[] {1f / Math.max(gains.getRed(), 1e-6f), 1f / Math.max(g, 1e-6f), 1f / Math.max(gains.getBlue(), 1e-6f)};
        }
        return null;
    }
}
