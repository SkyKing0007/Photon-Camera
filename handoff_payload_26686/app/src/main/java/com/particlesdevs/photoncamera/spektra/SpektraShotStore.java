package com.particlesdevs.photoncamera.spektra;

import android.content.Context;
import android.graphics.Rect;
import android.system.ErrnoException;
import android.system.Os;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.EOFException;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.util.UUID;

/** Atomic private recovery store for Spektra Process-now captures. */
public final class SpektraShotStore {
    private static final long MAGIC = 0x4953504b53485431L; // ISPKSHT1
    private static final int VERSION = 4;
    private static final int MAX_FLOAT_ARRAY = 16 * 1024 * 1024;
    private static final int MAX_DOUBLE_ARRAY = 256;
    private static final int MAX_SENSOR_PIXELS = 200_000_000;
    private static final int MAX_PACKED_RAW_BYTES = 512 * 1024 * 1024;

    private SpektraShotStore() {}

    public static File writeAtomic(Context context, SpektraShot shot) throws IOException {
        if (shot == null || shot.raw == null || shot.raw.packedRaw == null || shot.metadata == null) {
            throw new IOException("Spektra recovery requires durable packed RAW recipe");
        }
        File dir = new File(context.getFilesDir(), "spektra_recovery");
        if (!dir.exists() && !dir.mkdirs()) throw new IOException("Unable to create Spektra recovery directory");
        String stem = "spektra_" + shot.raw.timestampNs + "_" + UUID.randomUUID();
        File tmp = new File(dir, stem + ".tmp");
        File dst = new File(dir, stem + ".shot");
        try (FileOutputStream fos = new FileOutputStream(tmp);
             DataOutputStream out = new DataOutputStream(new BufferedOutputStream(fos))) {
            out.writeLong(MAGIC);
            out.writeInt(VERSION);
            out.writeLong(shot.captureWallTimeMs);
            out.writeInt(shot.raw.sourceWidth());
            out.writeInt(shot.raw.sourceHeight());
            out.writeInt(shot.raw.sourceFormat);
            out.writeInt(shot.raw.rowStride);
            out.writeInt(shot.raw.pixelStride);
            out.writeLong(shot.raw.timestampNs);
            SpektraFrameMetadata m = shot.metadata;
            out.writeLong(m.frameNumber);
            out.writeLong(m.exposureNs);
            out.writeLong(m.frameDurationNs);
            out.writeInt(m.iso);
            out.writeInt(m.requestedIso);
            out.writeInt(m.whiteLevel);
            out.writeInt(m.cfaArrangement);
            out.writeInt(m.bayerOffset);
            out.writeInt(m.geometryBayerOffsetHint);
            writeRect(out, m.rawBounds);
            writeRect(out, m.sourceCrop);
            writeRect(out, m.activeRawDomain);
            for (int i = 0; i < 4; ++i) out.writeInt(m.blackLevel4[i]);
            writeFloatArray(out, m.neutral3);
            out.writeInt(m.lensShadingRows);
            out.writeInt(m.lensShadingCols);
            writeFloatArray(out, m.lensShading);
            out.writeFloat(m.aperture);
            out.writeFloat(m.focalLengthMm);
            out.writeFloat(m.focalLength35Mm);
            writeDoubleArray(out, m.noiseProfile);
            writeFloatArray(out, shot.sensorToLinearSrgb);
            out.writeInt(shot.jpegOrientationDegrees);
            out.writeUTF(shot.cameraId);
            out.writeUTF(shot.lensModel);
            out.writeInt(shot.raw.packedRaw.length);
            out.write(shot.raw.packedRaw);
            out.flush();
            fos.getFD().sync();
        }
        try {
            Os.rename(tmp.getAbsolutePath(), dst.getAbsolutePath());
        } catch (ErrnoException e) {
            tmp.delete();
            throw new IOException("Atomic Spektra recovery rename failed", e);
        }
        return dst;
    }

    public static SpektraShot read(File file) throws IOException {
        if (file == null || !file.isFile()) throw new IOException("Spektra recovery file missing");
        try (DataInputStream in = new DataInputStream(new BufferedInputStream(new FileInputStream(file)))) {
            if (in.readLong() != MAGIC) throw new IOException("Spektra recovery magic mismatch");
            int version = in.readInt();
            if (version != VERSION) throw new IOException("Unsupported Spektra recovery version " + version);
            long captureWallTimeMs = in.readLong();
            int width = in.readInt();
            int height = in.readInt();
            int sourceFormat = in.readInt();
            int rowStride = in.readInt();
            int pixelStride = in.readInt();
            long timestampNs = in.readLong();
            long pixels = (long) width * (long) height;
            if (width <= 0 || height <= 0 || pixels <= 0 || pixels > MAX_SENSOR_PIXELS || rowStride <= 0) {
                throw new IOException("Invalid Spektra recovery RAW geometry " + width + "x" + height);
            }
            long frameNumber = in.readLong();
            long exposureNs = in.readLong();
            long frameDurationNs = in.readLong();
            int iso = in.readInt();
            int requestedIso = in.readInt();
            int whiteLevel = in.readInt();
            int cfaArrangement = in.readInt();
            int bayerOffset = in.readInt();
            int geometryBayerOffsetHint = in.readInt();
            Rect rawBounds = readRect(in, "raw bounds");
            Rect sourceCrop = readRect(in, "source crop");
            Rect activeRawDomain = readRect(in, "active RAW domain");
            int[] black = new int[4];
            for (int i = 0; i < 4; ++i) black[i] = in.readInt();
            float[] neutral = readFloatArray(in, 3, 3, "neutral");
            int lscRows = in.readInt();
            int lscCols = in.readInt();
            float[] lsc = readFloatArray(in, -1, MAX_FLOAT_ARRAY, "lens shading");
            if (lsc == null) {
                if (lscRows != 0 || lscCols != 0) throw new IOException("Spektra recovery lens shading dimensions without map");
            } else {
                long expectedLsc = (long) lscRows * (long) lscCols * 4L;
                if (lscRows <= 0 || lscCols <= 0 || expectedLsc != lsc.length) {
                    throw new IOException("Spektra recovery lens shading size mismatch");
                }
            }
            float aperture = in.readFloat();
            float focalLengthMm = in.readFloat();
            float focalLength35Mm = in.readFloat();
            double[] noise = readDoubleArray(in, MAX_DOUBLE_ARRAY, "noise profile");
            float[] sensorToLinearSrgb = readFloatArray(in, 9, 9, "sensor-to-linear-sRGB");
            int jpegOrientationDegrees = in.readInt();
            if (jpegOrientationDegrees != 0 && jpegOrientationDegrees != 90
                    && jpegOrientationDegrees != 180 && jpegOrientationDegrees != 270) {
                throw new IOException("Invalid Spektra recovery orientation " + jpegOrientationDegrees);
            }
            String cameraId = in.readUTF();
            String lensModel = in.readUTF();
            int rawLength = in.readInt();
            if (rawLength <= 0 || rawLength > MAX_PACKED_RAW_BYTES) {
                throw new IOException("Invalid Spektra recovery packed RAW length " + rawLength);
            }
            byte[] rawBytes = new byte[rawLength];
            in.readFully(rawBytes);
            if (in.read() != -1) throw new IOException("Spektra recovery has unexpected trailing data");

            SpektraRawFrame raw;
            SpektraFrameMetadata metadata;
            try {
                raw = SpektraRawFrame.restore(width, height, sourceFormat, rowStride, pixelStride,
                        timestampNs, rawBytes);
                metadata = SpektraFrameMetadata.restore(timestampNs, frameNumber, exposureNs, frameDurationNs,
                        iso, requestedIso, black, whiteLevel, neutral, lsc, lscRows, lscCols,
                        aperture, focalLengthMm, focalLength35Mm, noise, cfaArrangement, bayerOffset,
                        geometryBayerOffsetHint, rawBounds, sourceCrop, activeRawDomain);
            } catch (IllegalArgumentException e) {
                throw new IOException("Invalid frozen Spektra recovery recipe", e);
            }
            return new SpektraShot(raw, metadata, captureWallTimeMs, sensorToLinearSrgb,
                    jpegOrientationDegrees, cameraId, lensModel);
        } catch (EOFException e) {
            throw new IOException("Truncated Spektra recovery file", e);
        }
    }

    private static void writeRect(DataOutputStream out, Rect r) throws IOException {
        if (r == null) throw new IOException("Missing Spektra RAW geometry rect");
        out.writeInt(r.left); out.writeInt(r.top); out.writeInt(r.right); out.writeInt(r.bottom);
    }

    private static Rect readRect(DataInputStream in, String name) throws IOException {
        Rect r = new Rect(in.readInt(), in.readInt(), in.readInt(), in.readInt());
        if (r.width() <= 0 || r.height() <= 0) throw new IOException("Invalid Spektra recovery " + name);
        return r;
    }

    private static void writeFloatArray(DataOutputStream out, float[] values) throws IOException {
        if (values == null) { out.writeInt(-1); return; }
        out.writeInt(values.length);
        for (float v : values) out.writeFloat(v);
    }

    private static void writeDoubleArray(DataOutputStream out, double[] values) throws IOException {
        if (values == null) { out.writeInt(-1); return; }
        out.writeInt(values.length);
        for (double v : values) out.writeDouble(v);
    }

    private static float[] readFloatArray(DataInputStream in, int exactLength, int maxLength, String name) throws IOException {
        int length = in.readInt();
        if (length == -1) {
            if (exactLength >= 0) throw new IOException("Missing Spektra recovery " + name);
            return null;
        }
        if (length < 0 || length > maxLength || (exactLength >= 0 && length != exactLength)) {
            throw new IOException("Invalid Spektra recovery " + name + " length " + length);
        }
        float[] out = new float[length];
        for (int i = 0; i < length; ++i) out[i] = in.readFloat();
        return out;
    }

    private static double[] readDoubleArray(DataInputStream in, int maxLength, String name) throws IOException {
        int length = in.readInt();
        if (length == -1) return null;
        if (length < 0 || length > maxLength) throw new IOException("Invalid Spektra recovery " + name + " length " + length);
        double[] out = new double[length];
        for (int i = 0; i < length; ++i) out[i] = in.readDouble();
        return out;
    }
}
