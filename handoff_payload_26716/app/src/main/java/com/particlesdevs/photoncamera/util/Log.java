package com.particlesdevs.photoncamera.util;

import android.content.ContentResolver;
import android.content.ContentUris;
import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.os.Handler;
import android.os.HandlerThread;
import android.provider.MediaStore;

import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.text.SimpleDateFormat;
import java.util.Locale;

public class Log {
    private static boolean shouldSkipPersistentSpam(
            String tag,
            String message) {
        return "DynamicNoise".equals(tag);
    }

    /* IRIS_26716_NATIVE_MEDIASTORE_IRIS_LOG_OWNER
     * Persistent Iris logs live under DCIM/Camera/Iris Camera/Logs and are owned directly by
     * Android MediaStore.Files on Android 10+. This is intentionally independent of PhotonCamera
     * SAF/backup storage. Android does not execute app code at install time, so the directory is
     * materialized automatically on the first Iris process launch by creating today's log files.
     */
    private static final String IRIS_LOG_RELATIVE_PATH =
            Environment.DIRECTORY_DCIM + "/Camera/Iris Camera/Logs/";

    private static java.io.File logDir = null;
    private static Context logContext = null; // Application context for Iris-owned storage
    private static volatile boolean logStorageReady = false;
    private static final int LOG_RETENTION_DAYS = 10;
    private static String currentLogFileName = null;
    private static boolean logEnabled = true;

    /* IRIS_26634_RETIRE_PROCESS_LIFECYCLE_FILES
     * Keep Iris Camera/Logs/log-YYYY-MM-DD.txt and motion-trace-YYYY-MM-DD.txt. The private
     * iris-process-lifecycle files, synchronous fsync breadcrumbs and process-state persistence
     * are retired to remove capture/processing-boundary filesystem stalls. Public call sites stay
     * source-compatible: critical() routes to the normal async logger and processState() is a no-op.
     */

    // Thread-safe date formatters
    private static final ThreadLocal<SimpleDateFormat> dateFormatter =
        ThreadLocal.withInitial(() -> new SimpleDateFormat("yyyy-MM-dd", Locale.US));
    private static final ThreadLocal<SimpleDateFormat> timeFormatter =
        ThreadLocal.withInitial(() -> new SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", Locale.US));

    // Async logging
    private static HandlerThread logThread;
    private static Handler logHandler;
    private static BufferedWriter bufferedWriter = null;
    private static String currentDate = null;
    private static final int BUFFER_FLUSH_INTERVAL = 1000; // Flush every 1 second

    private static HandlerThread motionLogThread;
    private static Handler motionLogHandler;
    private static BufferedWriter motionBufferedWriter = null;
    private static String motionCurrentDate = null;
    private static String motionLogFileName = null;

    static {
        initLogThread();
    }

    private static void initLogThread() {
        logThread = new HandlerThread("LogWriterThread");
        logThread.start();
        logHandler = new Handler(logThread.getLooper());

        motionLogThread =
                new HandlerThread("MotionLogWriterThread");
        motionLogThread.start();
        motionLogHandler =
                new Handler(motionLogThread.getLooper());

        // Schedule periodic flush
        schedulePeriodicFlush();
    }

    private static void schedulePeriodicFlush() {
        logHandler.postDelayed(() -> {
            flushBuffer();
            schedulePeriodicFlush();
        }, BUFFER_FLUSH_INTERVAL);
    }

    public static void initProcessDiagnostics(Context context) {
        // IRIS_26634: dedicated lifecycle persistence intentionally retired.
    }

    public static void critical(String tag, String message) {
        i(tag, message);
    }

    public static void processState(String tag, String message) {
        // IRIS_26634: no private lifecycle file and no ActivityManager process-state summary.
    }

    /**
     * Initialize Iris-owned persistent logging. Android 10+ uses MediaStore.Files directly and
     * never depends on PhotonCamera's SAF tree. Android 9 and below retain direct-file fallback.
     */
    public static void setLogFolder(Context context) {
        if (context == null) {
            closeWriter();
            closeMotionWriter();
            logContext = null;
            logDir = null;
            logStorageReady = false;
            return;
        }

        Context appContext = context.getApplicationContext();
        if (logContext == appContext && logStorageReady) {
            return;
        }
        if (logContext != appContext) {
            closeWriter();
            closeMotionWriter();
        }
        logContext = appContext;

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            logDir = null;
            logHandler.post(() -> {
                try {
                    String today = dateFormatter.get().format(new java.util.Date());
                    Uri normal = getOrCreateMediaStoreLogUri("log-" + today + ".txt");
                    Uri motion = getOrCreateMediaStoreLogUri("motion-trace-" + today + ".txt");
                    if (normal != null && motion != null) {
                        logStorageReady = true;
                        android.util.Log.i("IrisLog",
                                "IRIS_26716_NATIVE_LOG_STORAGE_READY path=" + IRIS_LOG_RELATIVE_PATH);
                    } else {
                        logStorageReady = false;
                        android.util.Log.e("IrisLog",
                                "IRIS_26716_NATIVE_LOG_STORAGE_INIT_FAIL path=" + IRIS_LOG_RELATIVE_PATH);
                    }
                } catch (Throwable t) {
                    logStorageReady = false;
                    android.util.Log.e("IrisLog",
                            "IRIS_26716_NATIVE_LOG_STORAGE_INIT_FAIL path="
                                    + IRIS_LOG_RELATIVE_PATH, t);
                }
                cleanupOldLogs();
            });
        } else {
            java.io.File dcim = Environment.getExternalStoragePublicDirectory(
                    Environment.DIRECTORY_DCIM);
            java.io.File folder =
                    new java.io.File(dcim, "Camera/Iris Camera/Logs");
            if (!folder.exists() && !folder.mkdirs()) {
                android.util.Log.e("IrisLog",
                        "IRIS_26716_LEGACY_LOG_DIRECTORY_CREATE_FAIL path="
                                + folder.getAbsolutePath());
                logDir = null;
                logStorageReady = false;
            } else {
                logDir = folder;
                logStorageReady = true;
                logHandler.post(Log::cleanupOldLogs);
            }
        }
    }

    /** @deprecated Kept only for legacy tests/fallback callers. */
    @Deprecated
    public static void setLogFile(java.io.File folder) {
        closeWriter();
        closeMotionWriter();
        if (folder != null && folder.isDirectory()) {
            logDir = folder;
            logContext = null;
            logStorageReady = true;
            logHandler.post(Log::cleanupOldLogs);
        } else {
            logDir = null;
            logStorageReady = false;
        }
    }

    private static Uri getMediaStoreFilesCollection() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q) return null;
        return MediaStore.Files.getContentUri(MediaStore.VOLUME_EXTERNAL_PRIMARY);
    }

    /**
     * Return an app-owned text file in DCIM/Camera/Iris Camera/Logs, creating it through
     * MediaStore.Files when absent. No PhotonCamera SAF grant is consulted.
     */
    private static Uri getOrCreateMediaStoreLogUri(String fileName) {
        if (logContext == null || Build.VERSION.SDK_INT < Build.VERSION_CODES.Q) return null;

        ContentResolver resolver = logContext.getContentResolver();
        Uri collection = getMediaStoreFilesCollection();
        if (collection == null) return null;

        String[] projection = { MediaStore.MediaColumns._ID };
        String selection =
                MediaStore.MediaColumns.DISPLAY_NAME + "=? AND "
                        + MediaStore.MediaColumns.RELATIVE_PATH + "=?";
        String[] args = { fileName, IRIS_LOG_RELATIVE_PATH };

        try (Cursor cursor = resolver.query(collection, projection, selection, args, null)) {
            if (cursor != null && cursor.moveToFirst()) {
                long id = cursor.getLong(0);
                return ContentUris.withAppendedId(collection, id);
            }
        } catch (Throwable t) {
            android.util.Log.w("IrisLog",
                    "IRIS_26716_MEDIASTORE_QUERY_FAIL file=" + fileName, t);
        }

        ContentValues values = new ContentValues();
        values.put(MediaStore.MediaColumns.DISPLAY_NAME, fileName);
        values.put(MediaStore.MediaColumns.MIME_TYPE, "text/plain");
        values.put(MediaStore.MediaColumns.RELATIVE_PATH, IRIS_LOG_RELATIVE_PATH);

        try {
            return resolver.insert(collection, values);
        } catch (Throwable t) {
            android.util.Log.e("IrisLog",
                    "IRIS_26716_MEDIASTORE_INSERT_FAIL file=" + fileName
                            + " path=" + IRIS_LOG_RELATIVE_PATH, t);
            return null;
        }
    }

    private static BufferedWriter openMediaStoreWriter(String fileName, int bufferSize)
            throws java.io.IOException {
        Uri uri = getOrCreateMediaStoreLogUri(fileName);
        if (uri == null || logContext == null) return null;
        OutputStream os = logContext.getContentResolver().openOutputStream(uri, "wa");
        if (os == null) return null;
        return new BufferedWriter(new OutputStreamWriter(os), bufferSize);
    }

    private static java.io.File getLogFile() {
        if (logDir == null) return null;
        String today = dateFormatter.get().format(new java.util.Date());

        if (currentDate == null || !currentDate.equals(today)) {
            currentDate = today;
            currentLogFileName = "log-" + today + ".txt";
            closeWriter();
        }

        return new java.io.File(logDir, currentLogFileName);
    }

    private static String getCurrentLogFileName() {
        String today = dateFormatter.get().format(new java.util.Date());
        if (currentDate == null || !currentDate.equals(today)) {
            currentDate = today;
            currentLogFileName = "log-" + today + ".txt";
            closeWriter();
        }
        return currentLogFileName;
    }

    private static String getCurrentMotionLogFileName() {
        String today = dateFormatter.get().format(new java.util.Date());
        if (motionCurrentDate == null || !motionCurrentDate.equals(today)) {
            motionCurrentDate = today;
            motionLogFileName = "motion-trace-" + today + ".txt";
            closeMotionWriter();
        }
        return motionLogFileName;
    }

    private static void closeMotionWriter() {
        if (motionBufferedWriter != null) {
            try {
                motionBufferedWriter.close();
            } catch (Exception ignored) {
            }
            motionBufferedWriter = null;
        }
    }

    public static void flushMotionNow() {
        if (motionLogHandler != null) {
            motionLogHandler.post(() -> {
                if (motionBufferedWriter != null) {
                    try {
                        motionBufferedWriter.flush();
                    } catch (Exception ignored) {
                    }
                }
            });
        }
    }

    public static void writeMotionTrace(
            String level,
            String message) {

        if (!logEnabled
                || motionLogHandler == null
                || (logContext == null && logDir == null)) {
            return;
        }

        long timestamp = System.currentTimeMillis();

        motionLogHandler.post(() -> {
            try {
                if (motionBufferedWriter == null) {
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q && logContext != null) {
                        motionBufferedWriter =
                                openMediaStoreWriter(getCurrentMotionLogFileName(), 4096);
                    } else if (logDir != null) {
                        java.io.File file =
                                new java.io.File(logDir, getCurrentMotionLogFileName());
                        motionBufferedWriter =
                                new BufferedWriter(new FileWriter(file, true), 4096);
                    }
                }

                if (motionBufferedWriter == null) return;

                String time =
                        timeFormatter.get().format(
                                new java.util.Date(timestamp));

                motionBufferedWriter.write(
                        time
                                + " "
                                + level
                                + "/MotionTrace: "
                                + message);
                motionBufferedWriter.newLine();

                motionBufferedWriter.flush();
            } catch (Exception e) {
                closeMotionWriter();
                android.util.Log.w(
                        "MotionTrace",
                        "Authorized Motion trace write failed",
                        e);
            }
        });
    }

    private static void cleanupOldLogs() {
        long now = System.currentTimeMillis();
        long retentionMillis = LOG_RETENTION_DAYS * 24L * 60L * 60L * 1000L;

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q && logContext != null) {
            ContentResolver resolver = logContext.getContentResolver();
            Uri collection = getMediaStoreFilesCollection();
            if (collection == null) return;

            String[] projection = {
                    MediaStore.MediaColumns._ID,
                    MediaStore.MediaColumns.DISPLAY_NAME,
                    MediaStore.MediaColumns.DATE_MODIFIED
            };
            String selection = MediaStore.MediaColumns.RELATIVE_PATH + "=?";
            String[] args = { IRIS_LOG_RELATIVE_PATH };

            try (Cursor cursor =
                         resolver.query(collection, projection, selection, args, null)) {
                if (cursor == null) return;
                while (cursor.moveToNext()) {
                    long id = cursor.getLong(0);
                    String name = cursor.getString(1);
                    long modifiedSeconds = cursor.getLong(2);
                    boolean irisLog =
                            name != null
                                    && ((name.startsWith("log-") && name.endsWith(".txt"))
                                    || (name.startsWith("motion-trace-")
                                    && name.endsWith(".txt")));
                    if (irisLog && modifiedSeconds > 0
                            && now - (modifiedSeconds * 1000L) > retentionMillis) {
                        resolver.delete(ContentUris.withAppendedId(collection, id),
                                null, null);
                    }
                }
            } catch (Throwable t) {
                android.util.Log.w("IrisLog",
                        "IRIS_26716_MEDIASTORE_RETENTION_FAIL", t);
            }
            return;
        }

        if (logDir == null) return;
        java.io.File[] files = logDir.listFiles();
        if (files == null) return;
        for (java.io.File file : files) {
            String name = file.getName();
            boolean irisLog =
                    file.isFile()
                            && ((name.startsWith("log-") && name.endsWith(".txt"))
                            || (name.startsWith("motion-trace-") && name.endsWith(".txt")));
            if (irisLog && now - file.lastModified() > retentionMillis) {
                //noinspection ResultOfMethodCallIgnored
                file.delete();
            }
        }
    }

    private static void closeWriter() {
        if (bufferedWriter != null) {
            try {
                bufferedWriter.close();
            } catch (Exception e) {
                // Ignore
            }
            bufferedWriter = null;
        }
    }

    private static void flushBuffer() {
        if (bufferedWriter != null) {
            try {
                bufferedWriter.flush();
            } catch (Exception e) {
                // Ignore
            }
        }
    }

    public static void flushNow() {
        logHandler.post(Log::flushBuffer);
    }

    private static void writeToFile(String level, String tag, String message) {
        if (shouldSkipPersistentSpam(tag, message)) return;
        boolean useMediaStore =
                (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q && logContext != null);
        if (!logEnabled) return;
        if (!useMediaStore && logDir == null) return;

        long timestamp = System.currentTimeMillis();

        logHandler.post(() -> {
            try {
                if (useMediaStore) {
                    if (bufferedWriter == null) {
                        bufferedWriter =
                                openMediaStoreWriter(getCurrentLogFileName(), 8192);
                    }
                } else {
                    java.io.File file = getLogFile();
                    if (file == null) return;
                    if (bufferedWriter == null) {
                        bufferedWriter = new BufferedWriter(new FileWriter(file, true), 8192);
                    }
                }
                if (bufferedWriter == null) return;

                String time = timeFormatter.get().format(new java.util.Date(timestamp));
                String logEntry = time + " " + level + "/" + tag + ": " + message + "\n";
                bufferedWriter.write(logEntry);
            } catch (Exception e) {
                closeWriter();
                android.util.Log.w("IrisLog",
                        "IRIS_26716_NATIVE_LOG_WRITE_FAIL", e);
            }
        });
    }

    public static void d(String tag, String message) {
        if(!logEnabled || shouldSkipPersistentSpam(tag, message)) return;
        android.util.Log.d(tag, message);
        writeToFile("D", tag, message);
    }

    public static void w(String tag, String message) {
        if(!logEnabled) return;
        android.util.Log.w(tag, message);
        writeToFile("W", tag, message);
    }
    
    public static void w(String tag, String message, Throwable tr) {
        if(!logEnabled) return;
        android.util.Log.w(tag, message, tr);
        writeToFile("W", tag, message + "\n" + android.util.Log.getStackTraceString(tr));
    }

    public static void e(String tag, String message) {
        if(!logEnabled) return;
        android.util.Log.e(tag, message);
        writeToFile("E", tag, message);
    }
    
    public static void e(String tag, String message, Throwable tr) {
        if(!logEnabled) return;
        android.util.Log.e(tag, message, tr);
        writeToFile("E", tag, message + "\n" + android.util.Log.getStackTraceString(tr));
    }

    public static void i(String tag, String message) {
        if(!logEnabled) return;
        android.util.Log.i(tag, message);
        writeToFile("I", tag, message);
    }

    public static void v(String tag, String s) {
        if(!logEnabled || shouldSkipPersistentSpam(tag, s)) return;
        android.util.Log.v(tag, s);
        writeToFile("V", tag, s);
    }

    public static String getStackTraceString(Exception e) {
        StringBuilder sb = new StringBuilder();
        sb.append(e.toString()).append("\n");
        for (StackTraceElement element : e.getStackTrace()) {
            sb.append("\tat ").append(element).append("\n");
        }
        String stackTrace = sb.toString();
        e.printStackTrace();
        writeToFile("E", "Exception", stackTrace);
        return stackTrace;
    }
    
    public static void setLogEnabled(boolean enabled) {
        logEnabled = enabled;
    }
    
    // Cleanup method to call when app is closing
    public static void shutdown() {
        if (logHandler != null) {
            logHandler.post(() -> {
                flushBuffer();
                closeWriter();
            });
            logThread.quitSafely();
        }
    }
}
