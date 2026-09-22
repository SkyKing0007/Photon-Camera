package com.particlesdevs.photoncamera.spektra;

import android.graphics.Rect;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CaptureResult;
import android.hardware.camera2.params.BlackLevelPattern;
import android.hardware.camera2.params.LensShadingMap;
import android.os.Build;
import android.util.Rational;
import android.util.Size;

import java.util.Arrays;

/** Capture-result snapshot paired by exact SENSOR_TIMESTAMP with a Spektra RAW image. */
public final class SpektraFrameMetadata {
    public final long timestampNs;
    public final long frameNumber;
    public final long exposureNs;
    public final long frameDurationNs;
    public final int iso;
    public final int requestedIso;
    /** Black levels ordered for the RAW-raster 2x2 origin after the verified Bayer offset. */
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
    /** CFA arrangement at RAW-raster coordinate (0,0) after the verified Bayer offset. */
    public final int cfaArrangement;
    /** Explicit 2x2 parity from the Camera2 CFA origin to RAW-raster origin. */
    public final int bayerOffset;
    /** Geometry-derived parity before image-statistical verification; -1 is deliberately unresolved. */
    public final int geometryBayerOffsetHint;
    /** All geometry below is normalized into RAW-raster coordinates. */
    public final Rect rawBounds;
    public final Rect sourceCrop;
    public final Rect activeRawDomain;

    private SpektraFrameMetadata(long timestampNs, long frameNumber, long exposureNs, long frameDurationNs,
            int iso, int requestedIso, int[] blackLevel4, int whiteLevel, float[] neutral3,
            float[] lensShading, int lensShadingRows, int lensShadingCols, float aperture,
            float focalLengthMm, float focalLength35Mm, double[] noiseProfile, int cfaArrangement,
            int bayerOffset, int geometryBayerOffsetHint, Rect rawBounds, Rect sourceCrop,
            Rect activeRawDomain) {
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
        this.bayerOffset = bayerOffset;
        this.geometryBayerOffsetHint = geometryBayerOffsetHint;
        this.rawBounds = new Rect(rawBounds);
        this.sourceCrop = new Rect(sourceCrop);
        this.activeRawDomain = new Rect(activeRawDomain);
    }

    static SpektraFrameMetadata restore(long timestampNs, long frameNumber, long exposureNs,
            long frameDurationNs, int iso, int requestedIso, int[] blackLevel4, int whiteLevel,
            float[] neutral3, float[] lensShading, int lensShadingRows, int lensShadingCols,
            float aperture, float focalLengthMm, float focalLength35Mm, double[] noiseProfile,
            int cfaArrangement, int bayerOffset, int geometryBayerOffsetHint, Rect rawBounds,
            Rect sourceCrop, Rect activeRawDomain) {
        validateGeometry(rawBounds, sourceCrop, activeRawDomain);
        if (timestampNs <= 0L || frameNumber < 0L || exposureNs <= 0L || iso <= 0 || whiteLevel <= 0) {
            throw new IllegalArgumentException("Invalid frozen Spektra metadata");
        }
        if (blackLevel4 == null || blackLevel4.length != 4) {
            throw new IllegalArgumentException("Frozen Spektra black level must have four CFA values");
        }
        if (neutral3 == null || neutral3.length != 3) {
            throw new IllegalArgumentException("Frozen Spektra neutral point must have three values");
        }
        if (cfaArrangement < 0 || cfaArrangement > 3 || bayerOffset < 0 || bayerOffset > 3) {
            throw new IllegalArgumentException("Frozen Spektra CFA/Bayer geometry is unresolved");
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
                noiseProfile == null ? null : noiseProfile.clone(), cfaArrangement,
                bayerOffset, geometryBayerOffsetHint, rawBounds, sourceCrop, activeRawDomain);
    }

    public static SpektraFrameMetadata from(CaptureResult result, CameraCharacteristics chars,
            long frameNumber, int requestedIso, int rawWidth, int rawHeight) {
        return from(result, chars, frameNumber, requestedIso, rawWidth, rawHeight, -1);
    }

    /**
     * Freeze one exact RAW/result geometry contract. SENSOR active-array and crop metadata begin in
     * sensor coordinates; this method is the sole Java owner that converts them to RAW-raster space.
     * Unknown Bayer origin is preserved as -1 and must never silently become phase zero.
     */
    public static SpektraFrameMetadata from(CaptureResult result, CameraCharacteristics chars,
            long frameNumber, int requestedIso, int rawWidth, int rawHeight, int verifiedBayerOffset) {
        RawGeometry geometry = RawGeometry.resolve(chars, result, rawWidth, rawHeight);
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
        final int selectedOffset = verifiedBayerOffset >= 0 && verifiedBayerOffset <= 3
                ? verifiedBayerOffset : -1;
        int[] black = sensorBlack.clone();
        int cfa = sensorCfa;
        if (selectedOffset >= 0) {
            for (int q = 0; q < 4; ++q) black[q] = sensorBlack[q ^ selectedOffset];
            if (sensorCfa >= 0 && sensorCfa <= 3) cfa = sensorCfa ^ selectedOffset;
        }
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
                noise == null ? null : Arrays.copyOf(noise, noise.length), cfa,
                selectedOffset, geometry.bayerOffsetHint,
                geometry.rawBounds, geometry.sourceCrop, geometry.activeRawDomain);
    }

    public static int geometryBayerOffsetHint(CameraCharacteristics chars, CaptureResult result,
            int rawWidth, int rawHeight) {
        return RawGeometry.resolve(chars, result, rawWidth, rawHeight).bayerOffsetHint;
    }

    private static void validateGeometry(Rect rawBounds, Rect sourceCrop, Rect activeRawDomain) {
        if (rawBounds == null || sourceCrop == null || activeRawDomain == null
                || rawBounds.width() <= 0 || rawBounds.height() <= 0
                || sourceCrop.width() <= 0 || sourceCrop.height() <= 0
                || activeRawDomain.width() < 2 || activeRawDomain.height() < 2
                || !rawBounds.contains(sourceCrop) || !rawBounds.contains(activeRawDomain)) {
            throw new IllegalArgumentException("Invalid Spektra RAW-raster geometry");
        }
    }

    private static final class RawGeometry {
        final Rect rawBounds;
        final Rect sourceCrop;
        final Rect activeRawDomain;
        final int bayerOffsetHint;

        private RawGeometry(Rect rawBounds, Rect sourceCrop, Rect activeRawDomain, int bayerOffsetHint) {
            this.rawBounds = rawBounds;
            this.sourceCrop = sourceCrop;
            this.activeRawDomain = activeRawDomain;
            this.bayerOffsetHint = bayerOffsetHint;
        }

        static RawGeometry resolve(CameraCharacteristics chars, CaptureResult result,
                int rawWidth, int rawHeight) {
            if (chars == null || rawWidth <= 0 || rawHeight <= 0) {
                throw new IllegalArgumentException("Spektra RAW geometry requires characteristics and dimensions");
            }
            Size pixelArray = chars.get(CameraCharacteristics.SENSOR_INFO_PIXEL_ARRAY_SIZE);
            Rect activeSensor = null;
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                activeSensor = chars.get(CameraCharacteristics.SENSOR_INFO_PRE_CORRECTION_ACTIVE_ARRAY_SIZE);
            }
            if (activeSensor == null) activeSensor = chars.get(CameraCharacteristics.SENSOR_INFO_ACTIVE_ARRAY_SIZE);
            if (pixelArray == null || pixelArray.getWidth() <= 0 || pixelArray.getHeight() <= 0
                    || activeSensor == null || activeSensor.width() <= 0 || activeSensor.height() <= 0) {
                throw new IllegalArgumentException("Spektra Camera2 RAW geometry metadata missing");
            }
            Rect rawBounds = new Rect(0, 0, rawWidth, rawHeight);
            Rect activeRaw = mapSensorRect(activeSensor, pixelArray, rawBounds);
            if (activeRaw.width() <= 0 || activeRaw.height() <= 0) {
                throw new IllegalArgumentException("Spektra active RAW domain collapsed during normalization");
            }

            Rect requestedSensorCrop = result == null ? null : result.get(CaptureResult.SCALER_CROP_REGION);
            Rect sourceRaw = requestedSensorCrop == null
                    ? new Rect(activeRaw)
                    : mapSensorRect(requestedSensorCrop, pixelArray, rawBounds);
            if (!sourceRaw.intersect(activeRaw)) sourceRaw.set(activeRaw);
            if (sourceRaw.width() <= 0 || sourceRaw.height() <= 0) sourceRaw.set(activeRaw);

            // Camera2 CFA is anchored to the active sensor domain. The RAW-raster origin therefore
            // needs the active-domain top-left parity only when that mapping is exact. Fractional
            // geometry remains unresolved rather than guessing a phase.
            int hint = -1;
            long leftNumerator = (long) activeSensor.left * (long) rawWidth;
            long topNumerator = (long) activeSensor.top * (long) rawHeight;
            if (leftNumerator % pixelArray.getWidth() == 0L
                    && topNumerator % pixelArray.getHeight() == 0L) {
                int activeLeftExact = (int) (leftNumerator / pixelArray.getWidth());
                int activeTopExact = (int) (topNumerator / pixelArray.getHeight());
                if (activeLeftExact == activeRaw.left && activeTopExact == activeRaw.top) {
                    hint = (activeRaw.left & 1) | ((activeRaw.top & 1) << 1);
                }
            }
            validateGeometry(rawBounds, sourceRaw, activeRaw);
            return new RawGeometry(rawBounds, sourceRaw, activeRaw, hint);
        }

        private static Rect mapSensorRect(Rect sensor, Size pixelArray, Rect rawBounds) {
            long pw = pixelArray.getWidth();
            long ph = pixelArray.getHeight();
            int left = floorDiv((long) sensor.left * rawBounds.width(), pw);
            int top = floorDiv((long) sensor.top * rawBounds.height(), ph);
            int right = ceilDiv((long) sensor.right * rawBounds.width(), pw);
            int bottom = ceilDiv((long) sensor.bottom * rawBounds.height(), ph);
            left = clamp(left, rawBounds.left, rawBounds.right);
            top = clamp(top, rawBounds.top, rawBounds.bottom);
            right = clamp(right, left, rawBounds.right);
            bottom = clamp(bottom, top, rawBounds.bottom);
            return new Rect(left, top, right, bottom);
        }

        private static int floorDiv(long numerator, long denominator) {
            if (denominator <= 0L) throw new IllegalArgumentException("Invalid Spektra geometry denominator");
            return (int) Math.floorDiv(numerator, denominator);
        }

        private static int ceilDiv(long numerator, long denominator) {
            if (denominator <= 0L) throw new IllegalArgumentException("Invalid Spektra geometry denominator");
            return (int) ((numerator + denominator - 1L) / denominator);
        }

        private static int clamp(int v, int lo, int hi) { return Math.max(lo, Math.min(hi, v)); }
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
