package com.particlesdevs.photoncamera.spektra;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Matrix;

import com.particlesdevs.photoncamera.util.Log;

import java.io.File;
import java.nio.file.Path;

/** One-shot Spektra processing owner: RAW front end -> public SPEKTRA -> JPEG-100 publication. */
public final class SpektraProcessor {
    private static final String TAG = "SpektraProcessor";
    private final Context context;

    public static final class Result {
        public final boolean saved;
        public final Path path;
        public final String error;
        Result(boolean saved, Path path, String error) { this.saved = saved; this.path = path; this.error = error; }
    }

    public SpektraProcessor(Context context) { this.context = context.getApplicationContext(); }

    public Result process(SpektraShot shot, File recovery) {
        Bitmap rendered = null;
        Bitmap oriented = null;
        try {
            SpektraRawProcessor.LinearFrame linear = new SpektraRawProcessor().process(shot, true);
            try (SpektraFilmRenderer film = new SpektraFilmRenderer(context)) {
                rendered = film.render(linear, false, 0.0);
            }
            if (shot.jpegOrientationDegrees != 0) {
                Matrix matrix = new Matrix();
                matrix.postRotate(shot.jpegOrientationDegrees);
                oriented = Bitmap.createBitmap(rendered, 0, 0, rendered.getWidth(), rendered.getHeight(), matrix, true);
                if (oriented != rendered) rendered.recycle();
            } else {
                oriented = rendered;
            }
            Path path = new SpektraJpegPublisher(context).publish(oriented, shot);
            oriented.recycle();
            Log.d(TAG, "IRIS_26681_SPEKTRA_SAVED path=" + path
                    + " recovery=" + recovery
                    + " film=kodak_portra_400 paper=kodak_supra_endura jpegQuality=100");
            return new Result(true, path, null);
        } catch (Throwable t) {
            if (oriented != null && !oriented.isRecycled()) oriented.recycle();
            else if (rendered != null && !rendered.isRecycled()) rendered.recycle();
            Log.e(TAG, "IRIS_26681_SPEKTRA_PROCESSOR_FAILED recovery=" + recovery, t);
            return new Result(false, null, t.getMessage());
        }
    }
}
