package com.particlesdevs.photoncamera.capture;

import com.particlesdevs.photoncamera.processing.ProcessingEventsListener;
import com.particlesdevs.photoncamera.util.Log;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Locale;

/** Only the frozen C/SR-ON ImageSaver receives this per-shot listener. */
public final class Iris26983COnProcessingRelay implements ProcessingEventsListener {
    private final ProcessingEventsListener delegate;
    private final long token;
    private final boolean expectedHeic;
    private boolean published;
    private boolean terminal;

    public Iris26983COnProcessingRelay(ProcessingEventsListener delegate) {
        this(delegate, false);
    }
    public Iris26983COnProcessingRelay(ProcessingEventsListener delegate, boolean heicAtShutter) {
        if (delegate == null) throw new IllegalArgumentException("no processing listener");
        this.delegate = delegate;
        expectedHeic = heicAtShutter;
        token = Iris26983COnSession.arm();
        Log.i("Iris26983COnRelay", "IRIS_26983_C_ON_ARM token=" + token
                + " output=" + (expectedHeic ? "HEIC" : "JPEG")
                + " immutable15RawLkr=true");
    }
    public long token() { return token; }

    @Override public void onProcessingStarted(String name) {
        Log.i("Iris26983COnRelay", "IRIS_26983_C_ON_PROCESS_START token=" + token
                + " monoNs=" + System.nanoTime());
        delegate.onProcessingStarted(name);
    }
    @Override public void onProcessingChanged(Object obj) { delegate.onProcessingChanged(obj); }
    @Override public void notifyImageSavedStatus(boolean saved, Path path) {
        // Preserve gallery, DNG, notification and media scan exactly as before.
        delegate.notifyImageSavedStatus(saved, path);
        if (!saved || path == null || published || terminal) return;
        String filename = path.getFileName().toString().toLowerCase(Locale.ROOT);
        final boolean expected = expectedHeic
                ? (filename.endsWith(".heic") || filename.endsWith(".heif"))
                : (filename.endsWith(".jpg") || filename.endsWith(".jpeg"));
        if (!expected) return;
        try {
            if (!Files.isRegularFile(path) || Files.size(path) <= 0L) {
                Log.w("Iris26983COnRelay", "IRIS_26935_JPEG_NOT_PUBLISHED token=" + token);
                return;
            }
            published = true;
            terminal = true;
            Iris26983COnSession.complete(token, true, "saved_output_file_verified");
            Log.i("Iris26983COnRelay", "IRIS_26935_OUTPUT_PUBLICATION_SUCCESS token="
                    + token + " monoNs=" + System.nanoTime());
        } catch (Exception exception) {
            Log.w("Iris26983COnRelay", "IRIS_26935_JPEG_FILE_VERIFICATION_FAILED token=" + token, exception);
        }
    }
    @Override public void onProcessingFinished(Object obj) {
        // HdrX may finish before other callbacks; Motion also sends a second
        // terminal callback. Neither is a substitute for actual JPG publication.
        if (!published && !terminal) {
            Log.w("Iris26983COnRelay", "IRIS_26935_FINISHED_WITHOUT_OUTPUT token=" + token
                    + " event=" + obj + " terminalReleaseDeferred=true");
            return;
        }
        delegate.onProcessingFinished(obj);
    }
    @Override public void onProcessingError(Object error) {
        if (terminal) return;
        terminal = true;
        // Let CameraFragment finish its failure UI path while shutter remains
        // locked; only then publish the terminal release, even if UI throws.
        try { delegate.onProcessingError(error); }
        finally { Iris26983COnSession.complete(token, false, "processing_exception"); }
    }
    /** Called from the immutable Motion batch executor's finally, not the UI thread. */
    public void finishIfMissing() {
        if (terminal) return;
        terminal = true;
        Log.w("Iris26983COnRelay", "IRIS_26935_TERMINAL_NO_OUTPUT token=" + token);
        try { delegate.onProcessingFinished("C ON processing terminal without saved output"); }
        finally { Iris26983COnSession.complete(token, false, "terminal_without_output"); }
    }
}
