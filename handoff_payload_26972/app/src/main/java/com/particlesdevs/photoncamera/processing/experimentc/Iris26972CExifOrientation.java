package com.particlesdevs.photoncamera.processing.experimentc;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.RandomAccessFile;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.AtomicMoveNotSupportedException;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;
import java.util.Arrays;

/**
 * Isolated C-only EXIF orientation writer for the temporary original JPEG444.
 * Insert the tiny TIFF APP1 block BEFORE JPEG/R packaging (never rewrite JPEG/R:
 * ExifInterface reserialization after gainmap assembly risks stripping MPF/XMP).
 *
 * This is a byte-for-byte JPEG segment insertion: no pixels, ICC blocks, entropy,
 * or chroma sampling are touched. Atomic replacement is mandatory; failure
 * preserves the original temporary image and prevents photo publication.
 */
public final class Iris26972CExifOrientation {
    private static final byte[] EXIF = {'E','x','i','f',0,0};
    private static final long MAX_JPEG_BYTES = 256L * 1024 * 1024;
    private static final int HEADER_SCAN_LIMIT = 1_000_000;

    private Iris26972CExifOrientation() {}

    private static int code(int degrees) {
        switch (degrees) {
            case 0: return 1;
            case 90: return 6;
            case 180: return 3;
            case 270: return 8;
            default: throw new IllegalArgumentException("26972 C EXIF orientation not a right angle");
        }
    }

    private static byte[] segment(int degrees) {
        ByteBuffer data = ByteBuffer.allocate(36).order(ByteOrder.LITTLE_ENDIAN);
        data.put((byte) 0xff).put((byte) 0xe1);
        data.put((byte) 0).put((byte) 34); // 32 bytes payload + 2-byte length.
        data.put(EXIF);
        data.put((byte) 'I').put((byte) 'I');
        data.putShort((short) 42);
        data.putInt(8); // first IFD offset within the TIFF header
        data.putShort((short) 1); // exactly one IFD entry
        data.putShort((short) 0x0112); // Orientation
        data.putShort((short) 3); // SHORT
        data.putInt(1); // count
        data.putShort((short) code(degrees));
        data.putShort((short) 0);
        data.putInt(0); // no more IFDs
        return data.array();
    }

    /** Scan strictly through JPEG header markers, stopping before compressed pixels. */
    private static int exactMarkerCount(File jpeg, byte[] expected) throws IOException {
        if (jpeg == null || !jpeg.isFile() || Files.isSymbolicLink(jpeg.toPath()) ||
            jpeg.length() < 10 || jpeg.length() > MAX_JPEG_BYTES)
            throw new IOException("26972 C EXIF source is not a bounded regular JPEG");
        try (RandomAccessFile in = new RandomAccessFile(jpeg, "r")) {
            if (in.readUnsignedByte() != 0xff || in.readUnsignedByte() != 0xd8)
                throw new IOException("26972 C EXIF source lacks SOI");
            int found = 0;
            while (in.getFilePointer() < jpeg.length()) {
                long at = in.getFilePointer();
                if (at > HEADER_SCAN_LIMIT) throw new IOException("26972 C excessive JPEG headers");
                if (in.readUnsignedByte() != 0xff)
                    throw new IOException("26972 C invalid marker prefix");
                int tag;
                do { tag = in.readUnsignedByte(); } while (tag == 0xff);
                if (tag == 0xda) return found; // Start of Scan, never parse entropy
                if (tag == 0xd9 || tag == 0x00 || tag == 0xd8 ||
                    (tag >= 0xd0 && tag <= 0xd7))
                    throw new IOException("26972 C invalid JPEG header marker");
                int length = in.readUnsignedShort();
                long bodyStart = in.getFilePointer();
                if (length < 2 || bodyStart + length - 2 > jpeg.length())
                    throw new IOException("26972 C truncated JPEG marker");
                if (tag == 0xe1 && length >= 8) {
                    byte[] prefix = new byte[6];
                    in.readFully(prefix);
                    if (Arrays.equals(prefix, EXIF)) {
                        // Reject preexisting/foreign TIFF, including mismatched orientation.
                        if (length != 34 || expected == null ||
                            !matchesExact(in, bodyStart - 4, expected))
                            return -1;
                        found++;
                    }
                }
                in.seek(bodyStart + length - 2);
            }
            throw new IOException("26972 C JPEG header has no scan marker");
        }
    }

    private static boolean matchesExact(RandomAccessFile in, long start, byte[] expected)
            throws IOException {
        long position = in.getFilePointer();
        try {
            in.seek(start);
            byte[] actual = new byte[expected.length];
            in.readFully(actual);
            return Arrays.equals(actual, expected);
        } finally {
            in.seek(position);
        }
    }

    /** Exif orientation must be injected exclusively into a temporary native-1x base JPEG. */
    public static void insertIntoTemporaryBase(File baseJpeg, int degrees) throws IOException {
        byte[] marker = segment(degrees);
        int preexisting = exactMarkerCount(baseJpeg, marker);
        if (preexisting != 0)
            throw new IOException("26972 C refuses existing EXIF orientation/duplicate APP1");
        File parent = baseJpeg.getAbsoluteFile().getParentFile();
        File staging = File.createTempFile(".iris26972c-exif-", ".tmp", parent);
        boolean replaced = false;
        try {
            try (FileInputStream source = new FileInputStream(baseJpeg);
                 FileOutputStream destination = new FileOutputStream(staging)) {
                if (source.read() != 0xff || source.read() != 0xd8)
                    throw new IOException("26972 C base JPEG SOI changed");
                destination.write(0xff);
                destination.write(0xd8);
                destination.write(marker);
                byte[] buffer = new byte[64 * 1024];
                int read;
                while ((read = source.read(buffer)) != -1)
                    destination.write(buffer, 0, read);
                destination.getFD().sync();
            }
            if (exactMarkerCount(staging, marker) != 1)
                throw new IOException("26972 C staged EXIF marker failed verification");
            // Never fall back to non-atomic replacement on an unsupported filesystem.
            Files.move(staging.toPath(), baseJpeg.toPath(),
                StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
            replaced = true;
        } catch (AtomicMoveNotSupportedException failure) {
            throw new IOException("26972 C requires atomic EXIF base replacement", failure);
        } finally {
            if (!replaced && staging.exists() && !staging.delete())
                throw new IOException("26972 C EXIF temporary file cleanup failed");
        }
    }

    /** Call on the final MPF JPEG/R to prove the orientation survived packaging. */
    public static boolean finalContainsOrientation(File finalJpegR, int degrees) {
        try {
            return exactMarkerCount(finalJpegR, segment(degrees)) == 1;
        } catch (IOException | IllegalArgumentException failure) {
            return false;
        }
    }
}
