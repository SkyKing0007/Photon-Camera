package com.particlesdevs.photoncamera.spektra;

import android.content.ContentResolver;
import android.content.ContentValues;
import android.content.Context;
import android.graphics.Bitmap;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.provider.MediaStore;

import androidx.exifinterface.media.ExifInterface;

import com.particlesdevs.photoncamera.util.FileManager;

import java.io.File;
import java.io.FileDescriptor;
import java.io.FileOutputStream;
import java.io.OutputStream;
import java.nio.file.Path;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

/** Spektra-owned SDR sRGB JPEG publisher. No UHDR/HEIC/Motion publisher is reachable here. */
public final class SpektraJpegPublisher {
    private static final String RELATIVE = Environment.DIRECTORY_DCIM + "/PhotonCamera/Spektra";
    private final Context context;

    public SpektraJpegPublisher(Context context) { this.context = context.getApplicationContext(); }

    public Path publish(Bitmap bitmap, SpektraShot shot) throws Exception {
        if (bitmap == null || bitmap.isRecycled()) throw new IllegalArgumentException("Spektra bitmap missing");
        Date captureDate = new Date(shot.captureWallTimeMs);
        String name = "Iris_Spektra_" + new SimpleDateFormat("yyyyMMdd_HHmmss_SSS", Locale.US).format(captureDate) + ".jpg";
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            return publishMediaStore(bitmap, shot, name);
        }
        File dir = new File(FileManager.sPHOTON_DIR, "Spektra");
        if (!dir.exists() && !dir.mkdirs()) throw new IllegalStateException("Unable to create Spektra output directory");
        File out = new File(dir, name);
        try (FileOutputStream os = new FileOutputStream(out)) {
            if (!bitmap.compress(Bitmap.CompressFormat.JPEG, 100, os)) throw new IllegalStateException("Spektra JPEG encode failed");
            os.flush();
            os.getFD().sync();
        }
        ExifInterface exif = new ExifInterface(out);
        writeExif(exif, shot);
        exif.saveAttributes();
        try (FileOutputStream sync = new FileOutputStream(out, true)) {
            sync.getFD().sync();
        }
        return out.toPath();
    }

    private Path publishMediaStore(Bitmap bitmap, SpektraShot shot, String name) throws Exception {
        ContentResolver resolver = context.getContentResolver();
        ContentValues values = new ContentValues();
        values.put(MediaStore.Images.Media.DISPLAY_NAME, name);
        values.put(MediaStore.Images.Media.MIME_TYPE, "image/jpeg");
        values.put(MediaStore.Images.Media.RELATIVE_PATH, RELATIVE);
        values.put(MediaStore.Images.Media.IS_PENDING, 1);
        Uri uri = resolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values);
        if (uri == null) throw new IllegalStateException("Spektra MediaStore insert failed");
        boolean published = false;
        try {
            try (OutputStream os = resolver.openOutputStream(uri, "w")) {
                if (os == null || !bitmap.compress(Bitmap.CompressFormat.JPEG, 100, os)) {
                    throw new IllegalStateException("Spektra JPEG-100 encode failed");
                }
                os.flush();
            }
            try (android.os.ParcelFileDescriptor pfd = resolver.openFileDescriptor(uri, "rw")) {
                if (pfd == null) throw new IllegalStateException("Spektra EXIF descriptor unavailable");
                FileDescriptor fd = pfd.getFileDescriptor();
                ExifInterface exif = new ExifInterface(fd);
                writeExif(exif, shot);
                exif.saveAttributes();
                fd.sync();
            }
            ContentValues done = new ContentValues();
            done.put(MediaStore.Images.Media.IS_PENDING, 0);
            if (resolver.update(uri, done, null, null) <= 0) throw new IllegalStateException("Spektra MediaStore publish failed");
            published = true;
        } finally {
            if (!published) resolver.delete(uri, null, null);
        }
        return new File(new File(FileManager.sPHOTON_DIR, "Spektra"), name).toPath();
    }

    private static void writeExif(ExifInterface exif, SpektraShot shot) {
        Date now = new Date(shot.captureWallTimeMs);
        SimpleDateFormat dt = new SimpleDateFormat("yyyy:MM:dd HH:mm:ss", Locale.US);
        SimpleDateFormat sub = new SimpleDateFormat("SSS", Locale.US);
        SimpleDateFormat off = new SimpleDateFormat("XXX", Locale.US);
        String date = dt.format(now);
        String subSec = sub.format(now);
        String offset = off.format(now);
        exif.setAttribute(ExifInterface.TAG_DATETIME, date);
        exif.setAttribute(ExifInterface.TAG_DATETIME_ORIGINAL, date);
        exif.setAttribute(ExifInterface.TAG_DATETIME_DIGITIZED, date);
        exif.setAttribute(ExifInterface.TAG_SUBSEC_TIME, subSec);
        exif.setAttribute(ExifInterface.TAG_SUBSEC_TIME_ORIGINAL, subSec);
        exif.setAttribute(ExifInterface.TAG_SUBSEC_TIME_DIGITIZED, subSec);
        exif.setAttribute(ExifInterface.TAG_OFFSET_TIME, offset);
        exif.setAttribute(ExifInterface.TAG_OFFSET_TIME_ORIGINAL, offset);
        exif.setAttribute(ExifInterface.TAG_OFFSET_TIME_DIGITIZED, offset);
        exif.setAttribute(ExifInterface.TAG_MAKE, android.os.Build.MANUFACTURER);
        exif.setAttribute(ExifInterface.TAG_MODEL, android.os.Build.MODEL);
        exif.setAttribute(ExifInterface.TAG_SOFTWARE, "Iris Spektra 26681");
        exif.setAttribute(ExifInterface.TAG_COLOR_SPACE, "1");
        exif.setAttribute(ExifInterface.TAG_IMAGE_DESCRIPTION,
                "Iris Spektra; Kodak Portra 400; Kodak Supra Endura; filtered enlarger");
        exif.setAttribute(ExifInterface.TAG_LENS_MODEL, shot.lensModel);
        exif.setAttribute(ExifInterface.TAG_ORIENTATION, String.valueOf(ExifInterface.ORIENTATION_NORMAL));
        if (shot.metadata != null) {
            exif.setAttribute(ExifInterface.TAG_PHOTOGRAPHIC_SENSITIVITY, String.valueOf(shot.metadata.iso));
            exif.setAttribute(ExifInterface.TAG_EXPOSURE_TIME, rationalSeconds(shot.metadata.exposureNs));
            if (shot.metadata.focalLengthMm > 0f) exif.setAttribute(ExifInterface.TAG_FOCAL_LENGTH, decimalRational(shot.metadata.focalLengthMm));
            if (shot.metadata.focalLength35Mm > 0f) exif.setAttribute(ExifInterface.TAG_FOCAL_LENGTH_IN_35MM_FILM, String.valueOf(Math.round(shot.metadata.focalLength35Mm)));
            if (shot.metadata.aperture > 0f) exif.setAttribute(ExifInterface.TAG_F_NUMBER, decimalRational(shot.metadata.aperture));
        }
    }

    private static String rationalSeconds(long ns) {
        long denom = 1_000_000_000L;
        long num = Math.max(1L, ns);
        long g = gcd(num, denom);
        return (num / g) + "/" + (denom / g);
    }
    private static String decimalRational(float v) { return Math.round(v * 1000f) + "/1000"; }
    private static long gcd(long a, long b) { while (b != 0) { long t = a % b; a = b; b = t; } return Math.max(1L, a); }
}
