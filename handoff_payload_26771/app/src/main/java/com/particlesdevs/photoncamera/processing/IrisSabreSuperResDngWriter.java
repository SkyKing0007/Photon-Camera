package com.particlesdevs.photoncamera.processing;

import android.os.Build;
import android.util.Half;

import com.particlesdevs.photoncamera.processing.render.Parameters;
import com.particlesdevs.photoncamera.util.Log;
import com.particlesdevs.photoncamera.util.SimpleStorageHelper;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.ByteArrayOutputStream;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.Date;
import java.util.List;
import java.util.Locale;

/**
 * IRIS_26564_TRUE2X_STREAMING_LINEAR_RAW_DNG
 *
 * Iris-owned DNG serializer for the direct-CFA true-2x camera-RGB result. The shared true-2x
 * carrier is RGB16F in the black-free, lens-shading-corrected normalized camera domain. DNG
 * serialization streams that half-float carrier into unsigned RGB16 [0,65535], matching the
 * LinearRaw SampleFormat/WhiteLevel contract without materializing a second whole-image buffer.
 * NORMAL frames own high-frequency SR evidence; Night long frames remain excluded from it.
 * DefaultScale is 1:1.
 */
public final class IrisSabreSuperResDngWriter {
    private static final String TAG = "Iris26562SabreSrDng";

    private static final int TYPE_BYTE = 1;
    private static final int TYPE_ASCII = 2;
    private static final int TYPE_SHORT = 3;
    private static final int TYPE_LONG = 4;
    private static final int TYPE_RATIONAL = 5;
    private static final int TYPE_SRATIONAL = 10;

    private static final int TAG_NEW_SUBFILE_TYPE = 254;
    private static final int TAG_IMAGE_WIDTH = 256;
    private static final int TAG_IMAGE_LENGTH = 257;
    private static final int TAG_BITS_PER_SAMPLE = 258;
    private static final int TAG_COMPRESSION = 259;
    private static final int TAG_PHOTOMETRIC = 262;
    private static final int TAG_DESCRIPTION = 270;
    private static final int TAG_MAKE = 271;
    private static final int TAG_MODEL = 272;
    private static final int TAG_STRIP_OFFSETS = 273;
    private static final int TAG_ORIENTATION = 274;
    private static final int TAG_SAMPLES_PER_PIXEL = 277;
    private static final int TAG_ROWS_PER_STRIP = 278;
    private static final int TAG_STRIP_BYTE_COUNTS = 279;
    private static final int TAG_PLANAR_CONFIG = 284;
    private static final int TAG_SOFTWARE = 305;
    private static final int TAG_DATETIME = 306;
    private static final int TAG_SAMPLE_FORMAT = 339;
    private static final int TAG_EXPOSURE_TIME = 33434;
    private static final int TAG_F_NUMBER = 33437;
    private static final int TAG_ISO = 34855;
    private static final int TAG_FOCAL_LENGTH = 37386;
    private static final int TAG_DNG_VERSION = 50706;
    private static final int TAG_DNG_BACKWARD_VERSION = 50707;
    private static final int TAG_UNIQUE_CAMERA_MODEL = 50708;
    private static final int TAG_BLACK_LEVEL = 50714;
    private static final int TAG_WHITE_LEVEL = 50717;
    private static final int TAG_DEFAULT_SCALE = 50718;
    private static final int TAG_DEFAULT_CROP_ORIGIN = 50719;
    private static final int TAG_DEFAULT_CROP_SIZE = 50720;
    private static final int TAG_COLOR_MATRIX_1 = 50721;
    private static final int TAG_COLOR_MATRIX_2 = 50722;
    private static final int TAG_CAMERA_CALIBRATION_1 = 50723;
    private static final int TAG_CAMERA_CALIBRATION_2 = 50724;
    private static final int TAG_ANALOG_BALANCE = 50727;
    private static final int TAG_AS_SHOT_NEUTRAL = 50728;
    private static final int TAG_BASELINE_EXPOSURE = 50730;
    private static final int TAG_CALIBRATION_ILLUMINANT_1 = 50778;
    private static final int TAG_CALIBRATION_ILLUMINANT_2 = 50779;
    private static final int TAG_ACTIVE_AREA = 50829;
    private static final int TAG_FORWARD_MATRIX_1 = 50964;
    private static final int TAG_FORWARD_MATRIX_2 = 50965;
    private static final int TAG_DEFAULT_BLACK_RENDER = 51110;

    private static final int PHOTOMETRIC_LINEAR_RAW = 34892;
    private static final int SAMPLES_PER_PIXEL = 3;
    private static final long U32_MAX = 0xffff_ffffL;

    private IrisSabreSuperResDngWriter() {}

    private static final class Entry {
        final int tag;
        final int type;
        final long count;
        final byte[] data;
        long externalOffset;

        Entry(int tag, int type, long count, byte[] data) {
            this.tag = tag;
            this.type = type;
            this.count = count;
            this.data = data;
        }
    }

    public static boolean write(
            Path output,
            Path linearRawRgb16f,
            int width,
            int height,
            Parameters p,
            int normalFrameCount,
            float supportMin,
            float supportP01,
            float supportP10,
            float supportMedian,
            float supportMean,
            float supportMax,
            float noiseEquivalentSupport) {
        if (output == null || linearRawRgb16f == null || p == null || width <= 0 || height <= 0) {
            return false;
        }
        try {
            long pixelBytes = Math.multiplyExact(Math.multiplyExact((long) width, (long) height), 6L);
            if (pixelBytes > U32_MAX || Files.size(linearRawRgb16f) != pixelBytes) {
                throw new IOException("True2x RGB16F payload size mismatch expected=" + pixelBytes
                        + " actual=" + Files.size(linearRawRgb16f));
            }
            byte[] header = buildHeader(width, height, pixelBytes, p,
                    normalFrameCount, supportMin, supportP01, supportP10, supportMedian,
                    supportMean, supportMax, noiseEquivalentSupport);
            if ((long) header.length + pixelBytes > U32_MAX) {
                throw new IOException("Classic TIFF/DNG 32-bit offset limit exceeded");
            }
            SimpleStorageHelper.deleteByAbsPath(output.toString());
            OutputStream safOutput = SimpleStorageHelper.openOutputStreamByAbsPath(output.toString());
            if (safOutput == null) throw new IOException("True2x DNG SAF output unavailable: " + output);
            try (OutputStream out = new BufferedOutputStream(safOutput, 1024 * 1024)) {
                out.write(header);
                streamRgb16fAsUnsignedRgb16(linearRawRgb16f, out, pixelBytes);
                out.flush();
            }
            long expected = (long) header.length + pixelBytes;
            long actualOutputBytes = SimpleStorageHelper.lengthByAbsPath(output.toString());
            if (actualOutputBytes != expected) {
                throw new IOException("DNG final size mismatch expected=" + expected
                        + " actual=" + actualOutputBytes);
            }
            Log.i(TAG, "IRIS_26564_TRUE2X_LINEAR_RAW_DNG saved=true size=" + width + "x" + height
                    + " payloadBytes=" + pixelBytes + " headerBytes=" + header.length
                    + " residualZoom=" + Math.max(1.0f, p.motionV2RenderResidualZoom)
                    + " defaultScale=1:1 photometric=LinearRaw");
            return true;
        } catch (Throwable t) {
            Log.e(TAG, "IRIS_26564_TRUE2X_LINEAR_RAW_DNG_FAILED", t);
            try { SimpleStorageHelper.deleteByAbsPath(output.toString()); } catch (Throwable ignored) {}
            return false;
        }
    }

    private static void streamRgb16fAsUnsignedRgb16(
            Path rgb16f, OutputStream out, long expectedBytes) throws IOException {
        // Keep conversion bounded. The source and destination are both 6 bytes/pixel; only the
        // sample encoding changes from IEEE-754 half to unsigned normalized 16-bit little-endian.
        final int chunkBytes = 6 * 32768;
        byte[] source = new byte[chunkBytes];
        byte[] encoded = new byte[chunkBytes];
        long consumed = 0L;
        try (BufferedInputStream in = new BufferedInputStream(new FileInputStream(rgb16f.toFile()), 1024 * 1024)) {
            while (consumed < expectedBytes) {
                int wanted = (int) Math.min((long) source.length, expectedBytes - consumed);
                int filled = 0;
                while (filled < wanted) {
                    int read = in.read(source, filled, wanted - filled);
                    if (read < 0) throw new IOException("Unexpected EOF in true2x RGB16F carrier");
                    filled += read;
                }
                if ((filled & 1) != 0) throw new IOException("Odd true2x RGB16F byte count");
                for (int i = 0; i < filled; i += 2) {
                    short halfBits = (short) ((source[i] & 0xff) | ((source[i + 1] & 0xff) << 8));
                    float value = Half.toFloat(halfBits);
                    if (!Float.isFinite(value)) {
                        throw new IOException("Non-finite true2x RGB16F sample at byte " + (consumed + i));
                    }
                    int u16 = Math.round(Math.max(0.0f, Math.min(1.0f, value)) * 65535.0f);
                    encoded[i] = (byte) (u16 & 0xff);
                    encoded[i + 1] = (byte) ((u16 >>> 8) & 0xff);
                }
                out.write(encoded, 0, filled);
                consumed += filled;
            }
            if (in.read() != -1) throw new IOException("Trailing bytes in true2x RGB16F carrier");
        }
        if (consumed != expectedBytes) {
            throw new IOException("True2x RGB16F conversion byte count mismatch expected="
                    + expectedBytes + " actual=" + consumed);
        }
    }

    private static byte[] buildHeader(
            int width,
            int height,
            long pixelBytes,
            Parameters p,
            int normalFrameCount,
            float supportMin,
            float supportP01,
            float supportP10,
            float supportMedian,
            float supportMean,
            float supportMax,
            float noiseEquivalentSupport) throws IOException {
        List<Entry> entries = new ArrayList<>();
        entries.add(longEntry(TAG_NEW_SUBFILE_TYPE, 0));
        entries.add(longEntry(TAG_IMAGE_WIDTH, width));
        entries.add(longEntry(TAG_IMAGE_LENGTH, height));
        entries.add(shortArray(TAG_BITS_PER_SAMPLE, new int[]{16, 16, 16}));
        entries.add(shortEntry(TAG_COMPRESSION, 1));
        entries.add(shortEntry(TAG_PHOTOMETRIC, PHOTOMETRIC_LINEAR_RAW));
        entries.add(ascii(TAG_DESCRIPTION, "Iris 26564 "
                + (p.irisNightActive ? "Night" : "Motion")
                + " true-2x direct-CFA Sabre LinearRaw; normalFrames=" + Math.max(0, normalFrameCount)
                + "; support[min,p01,p10,median,mean,max,noiseEq]="
                + supportMin + "," + supportP01 + "," + supportP10 + "," + supportMedian
                + "," + supportMean + "," + supportMax + "," + noiseEquivalentSupport
                + "; directCfa2x=true; normalFineDetail=true; nightLongFineDetail=false"
                + "; displayedZoom=" + p.motionV2GlobalZoom
                + "; residualZoom=" + p.motionV2RenderResidualZoom));
        String make = Build.BRAND != null && !Build.BRAND.isEmpty() ? Build.BRAND : Build.MANUFACTURER;
        String model = Build.MODEL != null ? Build.MODEL : "Android Camera";
        entries.add(ascii(TAG_MAKE, make));
        entries.add(ascii(TAG_MODEL, model));
        Entry stripOffset = longEntry(TAG_STRIP_OFFSETS, 0);
        entries.add(stripOffset);
        entries.add(shortEntry(TAG_ORIENTATION, exifOrientation(p.cameraRotation)));
        entries.add(shortEntry(TAG_SAMPLES_PER_PIXEL, SAMPLES_PER_PIXEL));
        entries.add(longEntry(TAG_ROWS_PER_STRIP, height));
        entries.add(longEntry(TAG_STRIP_BYTE_COUNTS, pixelBytes));
        entries.add(shortEntry(TAG_PLANAR_CONFIG, 1));
        entries.add(ascii(TAG_SOFTWARE, "Iris Camera 0.9726564 / 26564"));
        entries.add(ascii(TAG_DATETIME,
                new SimpleDateFormat("yyyy:MM:dd HH:mm:ss", Locale.US).format(new Date())));
        entries.add(shortArray(TAG_SAMPLE_FORMAT, new int[]{1, 1, 1}));

        if (p.exposureTime > 0.0 && Double.isFinite(p.exposureTime)) {
            entries.add(rationalArray(TAG_EXPOSURE_TIME, new double[]{p.exposureTime}));
        }
        if (p.aperture > 0.0f && Float.isFinite(p.aperture)) {
            entries.add(rationalArray(TAG_F_NUMBER, new double[]{p.aperture}));
        }
        if (p.iso > 0) entries.add(shortEntry(TAG_ISO, Math.min(65535, p.iso)));
        if (p.focalLength > 0.0f && Float.isFinite(p.focalLength)) {
            entries.add(rationalArray(TAG_FOCAL_LENGTH, new double[]{p.focalLength}));
        }

        entries.add(byteArray(TAG_DNG_VERSION, new byte[]{1, 4, 0, 0}));
        entries.add(byteArray(TAG_DNG_BACKWARD_VERSION, new byte[]{1, 3, 0, 0}));
        entries.add(ascii(TAG_UNIQUE_CAMERA_MODEL, model + "-" + make + "-Iris"));
        entries.add(rationalArray(TAG_BLACK_LEVEL, new double[]{0.0, 0.0, 0.0}));
        entries.add(longArray(TAG_WHITE_LEVEL, new long[]{65535, 65535, 65535}));
        entries.add(rationalArray(TAG_DEFAULT_SCALE, new double[]{1.0, 1.0}));

        double residualZoom = Float.isFinite(p.motionV2RenderResidualZoom)
                ? Math.max(1.0, p.motionV2RenderResidualZoom) : 1.0;
        double cropWidth = width / residualZoom;
        double cropHeight = height / residualZoom;
        double cropLeft = (width - cropWidth) * 0.5;
        double cropTop = (height - cropHeight) * 0.5;
        entries.add(rationalArray(TAG_DEFAULT_CROP_ORIGIN, new double[]{cropLeft, cropTop}));
        entries.add(rationalArray(TAG_DEFAULT_CROP_SIZE, new double[]{cropWidth, cropHeight}));

        addMatrix(entries, TAG_COLOR_MATRIX_1, p.ColorMatrix1);
        addMatrix(entries, TAG_COLOR_MATRIX_2, p.ColorMatrix2);
        addMatrix(entries, TAG_CAMERA_CALIBRATION_1, p.calibrationTransform1);
        addMatrix(entries, TAG_CAMERA_CALIBRATION_2, p.calibrationTransform2);
        entries.add(rationalArray(TAG_ANALOG_BALANCE, new double[]{1.0, 1.0, 1.0}));
        if (p.whitePoint != null && p.whitePoint.length >= 3
                && finitePositive(p.whitePoint[0]) && finitePositive(p.whitePoint[1])
                && finitePositive(p.whitePoint[2])) {
            entries.add(rationalArray(TAG_AS_SHOT_NEUTRAL, new double[]{
                    p.whitePoint[0], p.whitePoint[1], p.whitePoint[2]}));
        }
        entries.add(sRationalArray(TAG_BASELINE_EXPOSURE, new double[]{0.0}));
        if (p.calibrationIlluminant1 > 0) {
            entries.add(shortEntry(TAG_CALIBRATION_ILLUMINANT_1,
                    Math.min(65535, p.calibrationIlluminant1)));
        }
        if (p.calibrationIlluminant2 > 0 && validMatrix(p.ColorMatrix2)) {
            entries.add(shortEntry(TAG_CALIBRATION_ILLUMINANT_2,
                    Math.min(65535, p.calibrationIlluminant2)));
        }
        entries.add(longArray(TAG_ACTIVE_AREA, new long[]{0, 0, height, width}));
        addMatrix(entries, TAG_FORWARD_MATRIX_1, p.ForwardTransform1);
        addMatrix(entries, TAG_FORWARD_MATRIX_2, p.ForwardTransform2);
        entries.add(shortEntry(TAG_DEFAULT_BLACK_RENDER, 1));

        entries.sort(Comparator.comparingInt(e -> e.tag));
        int ifdBytes = 2 + entries.size() * 12 + 4;
        long extraCursor = 8L + ifdBytes;
        for (Entry e : entries) {
            if (e.data.length > 4) {
                extraCursor = align2(extraCursor);
                e.externalOffset = extraCursor;
                extraCursor += e.data.length;
            }
        }
        long imageOffset = align2(extraCursor);
        if (imageOffset > U32_MAX || imageOffset + pixelBytes > U32_MAX) {
            throw new IOException("DNG offset range exceeds classic TIFF");
        }
        stripOffset.data[0] = (byte) (imageOffset & 0xff);
        stripOffset.data[1] = (byte) ((imageOffset >>> 8) & 0xff);
        stripOffset.data[2] = (byte) ((imageOffset >>> 16) & 0xff);
        stripOffset.data[3] = (byte) ((imageOffset >>> 24) & 0xff);

        ByteBuffer header = ByteBuffer.allocate((int) imageOffset).order(ByteOrder.LITTLE_ENDIAN);
        header.put((byte) 'I').put((byte) 'I').putShort((short) 42).putInt(8);
        header.putShort((short) entries.size());
        for (Entry e : entries) {
            header.putShort((short) e.tag);
            header.putShort((short) e.type);
            header.putInt((int) e.count);
            if (e.data.length <= 4) {
                header.put(e.data);
                for (int i = e.data.length; i < 4; i++) header.put((byte) 0);
            } else {
                header.putInt((int) e.externalOffset);
            }
        }
        header.putInt(0);
        for (Entry e : entries) {
            if (e.data.length <= 4) continue;
            while (header.position() < e.externalOffset) header.put((byte) 0);
            header.put(e.data);
        }
        while (header.position() < imageOffset) header.put((byte) 0);
        return header.array();
    }

    private static void addMatrix(List<Entry> entries, int tag, float[] matrix) {
        if (!validMatrix(matrix)) return;
        double[] values = new double[9];
        for (int i = 0; i < 9; i++) values[i] = matrix[i];
        entries.add(sRationalArray(tag, values));
    }

    private static boolean validMatrix(float[] matrix) {
        if (matrix == null || matrix.length < 9) return false;
        boolean nonZero = false;
        for (int i = 0; i < 9; i++) {
            if (!Float.isFinite(matrix[i])) return false;
            nonZero |= Math.abs(matrix[i]) > 1.0e-9f;
        }
        return nonZero;
    }

    private static boolean finitePositive(float value) {
        return Float.isFinite(value) && value > 0.0f;
    }

    private static int exifOrientation(int rotationDegrees) {
        int r = ((rotationDegrees % 360) + 360) % 360;
        if (r == 90) return 6;
        if (r == 180) return 3;
        if (r == 270) return 8;
        return 1;
    }

    private static long align2(long value) { return (value + 1L) & ~1L; }

    private static Entry byteArray(int tag, byte[] values) {
        return new Entry(tag, TYPE_BYTE, values.length, values.clone());
    }

    private static Entry ascii(int tag, String value) {
        byte[] body = (value == null ? "" : value).getBytes(java.nio.charset.StandardCharsets.US_ASCII);
        byte[] data = new byte[body.length + 1];
        System.arraycopy(body, 0, data, 0, body.length);
        return new Entry(tag, TYPE_ASCII, data.length, data);
    }

    private static Entry shortEntry(int tag, int value) {
        return shortArray(tag, new int[]{value});
    }

    private static Entry shortArray(int tag, int[] values) {
        ByteBuffer b = ByteBuffer.allocate(values.length * 2).order(ByteOrder.LITTLE_ENDIAN);
        for (int v : values) b.putShort((short) (v & 0xffff));
        return new Entry(tag, TYPE_SHORT, values.length, b.array());
    }

    private static Entry longEntry(int tag, long value) {
        return longArray(tag, new long[]{value});
    }

    private static Entry longArray(int tag, long[] values) {
        ByteBuffer b = ByteBuffer.allocate(values.length * 4).order(ByteOrder.LITTLE_ENDIAN);
        for (long v : values) {
            if (v < 0 || v > U32_MAX) throw new IllegalArgumentException("u32 overflow tag=" + tag);
            b.putInt((int) v);
        }
        return new Entry(tag, TYPE_LONG, values.length, b.array());
    }

    private static Entry rationalArray(int tag, double[] values) {
        ByteBuffer b = ByteBuffer.allocate(values.length * 8).order(ByteOrder.LITTLE_ENDIAN);
        for (double value : values) {
            long den = 1_000_000L;
            long num = Math.round(Math.max(0.0, value) * den);
            while (num > U32_MAX && den > 1) { num /= 10; den /= 10; }
            b.putInt((int) Math.min(U32_MAX, num));
            b.putInt((int) Math.max(1L, den));
        }
        return new Entry(tag, TYPE_RATIONAL, values.length, b.array());
    }

    private static Entry sRationalArray(int tag, double[] values) {
        ByteBuffer b = ByteBuffer.allocate(values.length * 8).order(ByteOrder.LITTLE_ENDIAN);
        for (double value : values) {
            long den = 1_000_000L;
            long num = Math.round(value * den);
            while ((num > Integer.MAX_VALUE || num < Integer.MIN_VALUE) && den > 1) {
                num /= 10; den /= 10;
            }
            b.putInt((int) Math.max(Integer.MIN_VALUE, Math.min(Integer.MAX_VALUE, num)));
            b.putInt((int) Math.max(1L, den));
        }
        return new Entry(tag, TYPE_SRATIONAL, values.length, b.array());
    }

}
