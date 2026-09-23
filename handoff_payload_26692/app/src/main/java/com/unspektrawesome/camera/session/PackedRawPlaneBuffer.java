package com.unspektrawesome.camera.session;

import com.unspektrawesome.camera.RawFormat;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Objects;

/** Prepares a direct row-stride RAW carrier for the exact Unspektrawesome native upload path. */
final class PackedRawPlaneBuffer {
    static final class Prepared {
        final ByteBuffer bytes;
        final ByteBuffer scratch;
        final boolean copied;

        Prepared(ByteBuffer bytes, ByteBuffer scratch, boolean copied) {
            this.bytes = bytes;
            this.scratch = scratch;
            this.copied = copied;
        }
    }

    private PackedRawPlaneBuffer() {}

    /* IRIS_26692_RAW_ROW_STRIDE_CARRIER
     * Android may omit the final row's padding from Image.Plane.getBuffer(). Native 1.1.2
     * requires rowStride*height bytes, so borrow only when the complete layout is present;
     * otherwise build the missing row padding in a reusable direct buffer. RAW_SENSOR remains
     * RAW_SENSOR (16-bit words); it is never converted to RAW10/RAW12.
     */
    static Prepared prepare(ByteBuffer plane, int rowStrideBytes, int width, int height,
                            RawFormat format, ByteBuffer reusableScratch) {
        Objects.requireNonNull(plane, "RAW plane is null");
        Objects.requireNonNull(format, "RAW format is null");
        if (!plane.isDirect()) {
            throw new IllegalArgumentException("RAW plane must be a direct ByteBuffer");
        }
        if (rowStrideBytes <= 0 || width <= 0 || height <= 0) {
            throw new IllegalArgumentException("RAW plane dimensions must be positive");
        }
        final int meaningfulRowBytes = meaningfulRowBytes(format, width);
        if (meaningfulRowBytes > rowStrideBytes) {
            throw new IllegalArgumentException("RAW row stride is smaller than packed row bytes");
        }
        final long requiredLong = (long) rowStrideBytes * height;
        if (requiredLong > Integer.MAX_VALUE) {
            throw new IllegalArgumentException("RAW row-stride carrier is too large");
        }
        final int required = (int) requiredLong;
        ByteBuffer source = plane.duplicate();
        final int base = source.position();
        final int available = source.remaining();
        if (available >= required) {
            source.limit(base + required);
            ByteBuffer view = source.slice().order(plane.order());
            return new Prepared(view, reusableScratch, false);
        }

        // The final meaningful pixel of every row must exist even if trailing row padding does not.
        final long minimumLong = (long) rowStrideBytes * (height - 1L) + meaningfulRowBytes;
        if (minimumLong > available) {
            throw new IllegalArgumentException(
                    "RAW plane is smaller than its row-stride layout through the final pixel");
        }

        ByteBuffer scratch = reusableScratch;
        if (scratch == null || !scratch.isDirect() || scratch.capacity() < required) {
            scratch = ByteBuffer.allocateDirect(required).order(ByteOrder.nativeOrder());
        }
        ByteBuffer destination = scratch.duplicate().order(ByteOrder.nativeOrder());
        destination.clear();
        source = plane.duplicate();
        final int sourceBase = source.position();
        for (int row = 0; row < height; row++) {
            final int sourceStart = sourceBase + row * rowStrideBytes;
            final int destinationStart = row * rowStrideBytes;
            source.position(sourceStart);
            source.limit(sourceStart + meaningfulRowBytes);
            destination.position(destinationStart);
            destination.put(source);
            for (int i = meaningfulRowBytes; i < rowStrideBytes; i++) {
                destination.put((byte) 0);
            }
            source = plane.duplicate();
        }
        destination.position(0);
        destination.limit(required);
        return new Prepared(destination.slice().order(ByteOrder.nativeOrder()), scratch, true);
    }

    static int meaningfulRowBytes(RawFormat format, int width) {
        switch (format) {
            case RAW10:
                return ((width + 3) / 4) * 5;
            case RAW12:
                return ((width + 1) / 2) * 3;
            case RAW_SENSOR:
                long bytes = (long) width * 2L;
                if (bytes > Integer.MAX_VALUE) throw new IllegalArgumentException("RAW_SENSOR row too wide");
                return (int) bytes;
            default:
                throw new IllegalArgumentException("Unsupported RAW format: " + format);
        }
    }
}
