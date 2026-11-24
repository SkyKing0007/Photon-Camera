package com.particlesdevs.photoncamera.processing.experimentc;

import android.content.ContentResolver;
import android.content.ContentValues;
import android.content.Context;
import android.net.Uri;
import android.os.Build;
import android.provider.MediaStore;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.nio.file.Files;
import java.util.Objects;
import java.util.function.BooleanSupplier;

/**
 * C-only, Android Q+ pending-row publisher for a fully encoded and independently
 * EXIF-verified JPEG/R. Never exports a partial base JPEG, strips JPEG/R metadata,
 * re-encodes pixels, or uses the A/B gallery writer. The private source must be
 * deleted by its caller only AFTER a committed visible MediaStore row exists.
 *
 * Isolated, source-wired to C-only shutter processing but production disabled. Host tests establish
 * rollback semantics, NOT actual Android provider/device acceptance.
 */
public final class Iris26975CDonorMediaStorePublisher {
    private static final int COPY_CHUNK = 64 * 1024;
    private static final long MAX_ENCODED_BYTES = 256L * 1024 * 1024;
    private static final String RELATIVE_DIR = android.os.Environment.DIRECTORY_DCIM + "/Camera/";

    private Iris26975CDonorMediaStorePublisher() {}

    /** One pending-row transaction; published row remains the provider's property. */
    interface PendingStore {
        Object reserve(String displayName, long capturedAtMillis) throws IOException;
        OutputStream open(Object row) throws IOException;
        boolean commit(Object row) throws IOException;
        boolean discard(Object row) throws IOException;
    }

    private static void validateSource(File source, String name, long time) throws IOException {
        if (source == null || !source.isFile() || Files.isSymbolicLink(source.toPath()) ||
            source.length() < 64 || source.length() > MAX_ENCODED_BYTES ||
            name == null || name.length() > 95 ||
            !name.matches("[A-Za-z0-9][A-Za-z0-9_.-]*\\.jpg") || name.contains("..") ||
            time <= 0L)
            throw new IOException("26972 C invalid private finalized JPEG/R publication source");
    }

    /** Package-private test seam: exactly the same bytes and pending/commit code as Android. */
    static Object transferVerified(File source, String name, long time, PendingStore store)
            throws IOException {
        return transferVerified(source, name, time, store, () -> true);
    }

    /** Cancellation is checked before reservation, while streaming and at visibility. */
    static Object transferVerified(File source, String name, long time, PendingStore store,
                                   BooleanSupplier stillLive) throws IOException {
        Objects.requireNonNull(store, "26972 C MediaStore sink");
        Objects.requireNonNull(stillLive, "26972 C capture lifetime");
        validateSource(source, name, time);
        requireLive(stillLive);
        Object row = store.reserve(name, time);
        if (row == null) throw new IOException("26972 C MediaStore pending insert refused");
        boolean committed = false;
        Throwable pendingFailure = null;
        try {
            requireLive(stillLive);
            long copied = 0;
            try (FileInputStream input = new FileInputStream(source);
                 OutputStream output = store.open(row)) {
                if (output == null) throw new IOException("26972 C pending row output unavailable");
                byte[] buffer = new byte[COPY_CHUNK];
                int n;
                while ((n = input.read(buffer)) >= 0) {
                    requireLive(stillLive);
                    if (n == 0) continue;
                    copied += n;
                    if (copied > MAX_ENCODED_BYTES || copied > source.length())
                        throw new IOException("26972 C JPEG/R grew during publication");
                    output.write(buffer, 0, n);
                }
                output.flush();
                if (output instanceof FileOutputStream)
                    ((FileOutputStream) output).getFD().sync();
            }
            if (copied != source.length())
                throw new IOException("26972 C JPEG/R source changed during publication");
            // Provider must acknowledge visibility. We never silently accept a
            // partially written, pending, or failed metadata update.
            requireLive(stillLive);
            if (!store.commit(row)) throw new IOException("26972 C MediaStore commit failed");
            // A cancellation racing the provider update must also be removed.
            // Keep committed=false until the liveness check; finally discards it.
            requireLive(stillLive);
            committed = true;
            return row;
        } catch (IOException | RuntimeException | Error error) {
            // Even a provider runtime failure must not leak a pending row.
            pendingFailure = error;
            throw error;
        } finally {
            if (!committed) {
                try {
                    if (!store.discard(row))
                        throw new IOException("26972 C failed to delete incomplete pending row");
                } catch (IOException | RuntimeException rollbackError) {
                    if (pendingFailure != null) pendingFailure.addSuppressed(rollbackError);
                    else throw rollbackError;
                }
            }
        }
    }

    private static boolean hasOriginalNormalizedExif(File file) {
        try {
            // The donor physically rotates SDR pixels to display orientation.
            // Its ExifWriter writes NORMAL (1) plus lens/exposure/source metadata.
            androidx.exifinterface.media.ExifInterface exif =
                new androidx.exifinterface.media.ExifInterface(file);
            int orientation = exif.getAttributeInt(
                androidx.exifinterface.media.ExifInterface.TAG_ORIENTATION, -1);
            return orientation == androidx.exifinterface.media.ExifInterface.ORIENTATION_NORMAL &&
                com.hinnka.mycamera.processor.experimentc.original129.gallery
                    .Jpeg444ExportEncoder.INSTANCE.isJpegR(file);
        } catch (Exception e) {
            return false;
        }
    }

    private static void requireLive(BooleanSupplier stillLive) throws IOException {
        if (!stillLive.getAsBoolean())
            throw new IOException("26972 C capture closed before JPEG/R gallery commit");
    }

    /**
     * Returns the one visible row only on success. The caller's camera-specific
     * image owner remains responsible for its own private temporary source.
     */
    public static Uri publish(Context context, File verifiedJpegR, String displayName,
                              long shutterTimeMillis, int exifDegrees) throws IOException {
        return publish(context, verifiedJpegR, displayName, shutterTimeMillis,
                exifDegrees, () -> true);
    }

    /** The active C Camera2 session may be cancelled during encoding or transfer. */
    public static Uri publish(Context context, File verifiedJpegR, String displayName,
                              long shutterTimeMillis, int exifDegrees,
                              BooleanSupplier stillLive) throws IOException {
        if (!Iris26972CContract.CONTROLLED_DEVICE_TRIAL_ENABLED) return null;
        Objects.requireNonNull(stillLive, "26972 C capture lifetime");
        requireLive(stillLive);
        if (context == null || Build.VERSION.SDK_INT < Build.VERSION_CODES.Q)
            throw new IOException("26972 C has no safe scoped-storage JPEG/R publisher");
        validateSource(verifiedJpegR, displayName, shutterTimeMillis);
        // Original donor writes a complete EXIF APP1 before native JPEG/R packaging.
        // Do not demand the old Iris 34-byte synthetic EXIF marker: that would
        // reject legitimate bjzhou EXIF, or force duplicate EXIF blocks.
        // Read only; NEVER rewrite APP1/MPF after JPEG/R has been assembled.
        if (exifDegrees != 0 || !hasOriginalNormalizedExif(verifiedJpegR))
            throw new IOException("26975 C original donor JPEG/R has missing/invalid EXIF");
        final ContentResolver resolver = context.getContentResolver();
        final Uri collection = MediaStore.Images.Media.getContentUri(
            MediaStore.VOLUME_EXTERNAL_PRIMARY);
        PendingStore store = new PendingStore() {
            @Override public Object reserve(String name, long time) throws IOException {
                ContentValues values = new ContentValues();
                values.put(MediaStore.MediaColumns.DISPLAY_NAME, name);
                values.put(MediaStore.MediaColumns.MIME_TYPE, "image/jpeg");
                values.put(MediaStore.MediaColumns.RELATIVE_PATH, RELATIVE_DIR);
                values.put(MediaStore.MediaColumns.IS_PENDING, 1);
                values.put(MediaStore.Images.ImageColumns.DATE_TAKEN, time);
                try { return resolver.insert(collection, values); }
                catch (RuntimeException error) { throw new IOException("26972 C pending insert", error); }
            }
            @Override public OutputStream open(Object record) throws IOException {
                try { return resolver.openOutputStream((Uri) record, "w"); }
                catch (RuntimeException error) { throw new IOException("26972 C pending row open", error); }
            }
            @Override public boolean commit(Object record) throws IOException {
                ContentValues update = new ContentValues();
                update.put(MediaStore.MediaColumns.IS_PENDING, 0);
                try { return resolver.update((Uri)record, update, null, null) == 1; }
                catch (RuntimeException error) { throw new IOException("26972 C commit update", error); }
            }
            @Override public boolean discard(Object record) throws IOException {
                try { return resolver.delete((Uri)record, null, null) == 1; }
                catch (RuntimeException error) { throw new IOException("26972 C pending rollback", error); }
            }
        };
        final Uri committed = (Uri) transferVerified(verifiedJpegR, displayName,
                shutterTimeMillis, store, stillLive);
        // Last check catches a teardown immediately following the transaction.
        if (!stillLive.getAsBoolean()) {
            revokeCommitted(context, committed);
            throw new IOException("26972 C camera closed after JPEG/R commit");
        }
        return committed;
    }

    /** Only for a completed C row whose owning capture was cancelled afterward. */
    public static void revokeCommitted(Context context, Uri row) throws IOException {
        if (context == null || row == null) return;
        try {
            if (context.getContentResolver().delete(row, null, null) != 1)
                throw new IOException("26972 C cancelled output still visible");
        } catch (RuntimeException error) {
            throw new IOException("26972 C failed to revoke cancelled output", error);
        }
    }
}
