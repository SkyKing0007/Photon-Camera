package com.particlesdevs.photoncamera.util;

import android.content.ContentResolver;
import android.content.ContentUris;
import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.os.ParcelFileDescriptor;
import android.provider.DocumentsContract;
import android.provider.MediaStore;

import androidx.documentfile.provider.DocumentFile;

import com.anggrayudi.storage.file.DocumentFileCompat;
import com.anggrayudi.storage.file.StorageId;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.ArrayList;
import java.util.Locale;

/**
 * IRIS_26772_SELECTED_STORAGE_ROOT_OWNER
 *
 * One Iris storage owner sits above two Android-supported backends on Android 11+:
 * an arbitrary persisted SAF tree chosen by the user, or the platform Downloads collection when
 * the user explicitly chooses Download (whose root Android does not grant through ACTION_OPEN_DOCUMENT_TREE).
 * FileManager's historical Photon-named fields are routing aliases only. Normal camera JPG/HEIC and
 * still DNG output remain owned by DCIM/Camera; Raw is reserved for RAW Video.
 */
public final class SimpleStorageHelper {
    private static final String TAG = "SimpleStorageHelper";
    private static final String PREFS = "iris_storage_access";
    private static final String KEY_TREE_URI = "selected_tree_uri";
    private static final String KEY_BACKEND = "storage_backend";
    private static final String BACKEND_SAF = "saf";
    private static final String BACKEND_DOWNLOADS = "downloads";

    public static final String IRIS_CAMERA_DIR_NAME = "Iris Camera";
    public static final String IRIS_TUNING_DIR_NAME = "Tuning";
    public static final String IRIS_SPEKTRA_DIR_NAME = "Spektra";
    public static final String IRIS_RAW_DIR_NAME = "Raw";
    public static final String IRIS_LOGS_DIR_NAME = "Logs";

    private static Context sContext;

    private SimpleStorageHelper() {}

    public static void init(Context context) {
        sContext = context == null ? null : context.getApplicationContext();
        if (sContext != null && hasStorageAccess(sContext)) updateFileManagerPaths(sContext);
    }

    /** Persist an arbitrary user-selected SAF tree. */
    public static boolean setStorageRoot(Context context, DocumentFile root) {
        if (context == null || root == null || root.getUri() == null || !root.exists() || !root.canWrite()) {
            return false;
        }
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
                .putString(KEY_TREE_URI, root.getUri().toString())
                .putString(KEY_BACKEND, BACKEND_SAF)
                .apply();
        Log.i(TAG, "IRIS_26772_STORAGE_ROOT_SELECTED backend=saf uri=" + root.getUri());
        return true;
    }

    /** Use Android's supported Downloads collection instead of requesting the blocked Download SAF root. */
    public static boolean setDownloadsRoot(Context context) {
        if (context == null || Build.VERSION.SDK_INT < Build.VERSION_CODES.Q) return false;
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
                .remove(KEY_TREE_URI)
                .putString(KEY_BACKEND, BACKEND_DOWNLOADS)
                .apply();
        Log.i(TAG, "IRIS_26772_STORAGE_ROOT_SELECTED backend=downloads");
        return true;
    }

    public static boolean isDownloadsBackend(Context context) {
        if (context == null || Build.VERSION.SDK_INT < Build.VERSION_CODES.Q) return false;
        return BACKEND_DOWNLOADS.equals(context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .getString(KEY_BACKEND, ""));
    }

    public static Uri getStorageRootUri(Context context) {
        if (context == null || isDownloadsBackend(context)) return null;
        String raw = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getString(KEY_TREE_URI, null);
        if (raw == null || raw.isEmpty()) return null;
        try {
            return Uri.parse(raw);
        } catch (Throwable t) {
            Log.e(TAG, "getStorageRootUri: " + t.getMessage());
            return null;
        }
    }

    public static DocumentFile getStorageRoot(Context context) {
        Uri uri = getStorageRootUri(context);
        if (uri == null) return null;
        try {
            DocumentFile root = DocumentFile.fromTreeUri(context, uri);
            return root != null && root.exists() && root.canRead() && root.canWrite() ? root : null;
        } catch (Throwable t) {
            Log.e(TAG, "getStorageRoot: " + t.getMessage());
            return null;
        }
    }

    /** Any valid selected tree or the explicit Downloads backend satisfies storage ownership. */
    public static boolean hasStorageAccess(Context context) {
        if (context == null) return false;
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.R) return true;
        if (isDownloadsBackend(context)) return true;
        if (getStorageRoot(context) == null) return false;
        return getSelectedRootAbsoluteFile(context) != null;
    }

    /** Create Iris Camera/Tuning, Spektra, Raw and Logs under the selected backend. */
    public static boolean ensureIrisStorageHierarchy(Context context) {
        if (context == null) return false;
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.R) {
            File base = new File(Environment.getExternalStorageDirectory(), IRIS_CAMERA_DIR_NAME);
            File tuning = new File(base, IRIS_TUNING_DIR_NAME);
            File spektra = new File(base, IRIS_SPEKTRA_DIR_NAME);
            File raw = new File(base, IRIS_RAW_DIR_NAME);
            File logs = new File(base, IRIS_LOGS_DIR_NAME);
            boolean ok = (base.isDirectory() || base.mkdirs())
                    && (tuning.isDirectory() || tuning.mkdirs())
                    && (spektra.isDirectory() || spektra.mkdirs())
                    && (raw.isDirectory() || raw.mkdirs())
                    && (logs.isDirectory() || logs.mkdirs());
            configureFileManager(base);
            return ok;
        }

        if (isDownloadsBackend(context)) {
            boolean ok = ensureDownloadsDirectory(context, IRIS_TUNING_DIR_NAME)
                    && ensureDownloadsDirectory(context, IRIS_SPEKTRA_DIR_NAME)
                    && ensureDownloadsDirectory(context, IRIS_RAW_DIR_NAME)
                    && ensureDownloadsDirectory(context, IRIS_LOGS_DIR_NAME);
            if (ok) {
                File physical = new File(Environment.getExternalStoragePublicDirectory(
                        Environment.DIRECTORY_DOWNLOADS), IRIS_CAMERA_DIR_NAME);
                configureFileManager(physical);
                Log.i(TAG, "IRIS_26772_STORAGE_HIERARCHY_READY backend=downloads root=" + physical);
            }
            return ok;
        }

        DocumentFile selected = getStorageRoot(context);
        if (selected == null) return false;
        File physical = getIrisCameraAbsoluteFile(context);
        if (physical == null) {
            Log.e(TAG, "IRIS_26772_STORAGE_ROOT_PHYSICAL_PATH_UNRESOLVED uri=" + selected.getUri());
            return false;
        }
        DocumentFile iris = findOrCreateDirectory(selected, IRIS_CAMERA_DIR_NAME);
        if (iris == null) return false;
        if (findOrCreateDirectory(iris, IRIS_TUNING_DIR_NAME) == null) return false;
        if (findOrCreateDirectory(iris, IRIS_SPEKTRA_DIR_NAME) == null) return false;
        if (findOrCreateDirectory(iris, IRIS_RAW_DIR_NAME) == null) return false;
        if (findOrCreateDirectory(iris, IRIS_LOGS_DIR_NAME) == null) return false;
        configureFileManager(physical);
        Log.i(TAG, "IRIS_26772_STORAGE_HIERARCHY_READY backend=saf root=" + physical);
        return true;
    }

    private static boolean ensureDownloadsDirectory(Context context, String child) {
        // MediaStore materializes RELATIVE_PATH when an app-owned entry is inserted. A hidden marker
        // keeps an otherwise-empty folder present without exposing a fake user document.
        return getOrCreateDownloadsUri(context, child + "/.iris", "application/octet-stream", false) != null;
    }

    private static void configureFileManager(File irisRoot) {
        FileManager.sPHOTON_DIR = irisRoot;
        FileManager.sPHOTON_TUNING_DIR = new File(irisRoot, IRIS_TUNING_DIR_NAME);
        FileManager.sPHOTON_RAW_DIR = new File(irisRoot, IRIS_RAW_DIR_NAME);
        FileManager.sIRIS_SPEKTRA_DIR = new File(irisRoot, IRIS_SPEKTRA_DIR_NAME);
        // sDCIM_CAMERA deliberately remains the real system DCIM/Camera owner.
    }

    public static void updateFileManagerPaths(Context context) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.R) {
            configureFileManager(new File(Environment.getExternalStorageDirectory(), IRIS_CAMERA_DIR_NAME));
            return;
        }
        File iris = getIrisCameraAbsoluteFile(context);
        if (iris != null) configureFileManager(iris);
    }

    public static File getIrisCameraAbsoluteFile(Context context) {
        if (context == null) return null;
        if (isDownloadsBackend(context)) {
            return new File(Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS),
                    IRIS_CAMERA_DIR_NAME);
        }
        File selected = getSelectedRootAbsoluteFile(context);
        return selected == null ? null : new File(selected, IRIS_CAMERA_DIR_NAME);
    }

    public static String getIrisRelativePath(Context context, String relativeInsideIris) {
        String selected = getSelectedRootRelativePath(context);
        if (selected == null) return null;
        StringBuilder out = new StringBuilder();
        if (!selected.isEmpty()) out.append(trimSlashes(selected)).append('/');
        out.append(IRIS_CAMERA_DIR_NAME);
        String child = trimSlashes(relativeInsideIris);
        if (!child.isEmpty()) out.append('/').append(child);
        return out.toString();
    }

    public static String getIrisMediaStoreLikePattern(String relativeInsideIris) {
        return sContext == null ? null : getIrisMediaStoreLikePattern(sContext, relativeInsideIris);
    }

    public static String getIrisMediaStoreLikePattern(Context context, String relativeInsideIris) {
        String p = getIrisRelativePath(context, relativeInsideIris);
        return p == null ? null : "%" + trimSlashes(p) + "/%";
    }

    private static String getSelectedRootRelativePath(Context context) {
        if (isDownloadsBackend(context)) return Environment.DIRECTORY_DOWNLOADS;
        Uri uri = getStorageRootUri(context);
        if (uri == null) return null;
        try {
            String authority = uri.getAuthority();
            if (authority != null && authority.contains("downloads")) return Environment.DIRECTORY_DOWNLOADS;
            String id = DocumentsContract.getTreeDocumentId(uri);
            if (id == null) return null;
            int colon = id.indexOf(':');
            if (colon >= 0) return trimSlashes(id.substring(colon + 1));
            if ("downloads".equalsIgnoreCase(id)) return Environment.DIRECTORY_DOWNLOADS;
        } catch (Throwable t) {
            Log.e(TAG, "getSelectedRootRelativePath: " + t.getMessage());
        }
        return null;
    }

    private static String getSelectedStorageId(Context context) {
        if (isDownloadsBackend(context)) return StorageId.PRIMARY;
        Uri uri = getStorageRootUri(context);
        if (uri == null) return null;
        try {
            String authority = uri.getAuthority();
            if (authority != null && authority.contains("downloads")) return StorageId.PRIMARY;
            String id = DocumentsContract.getTreeDocumentId(uri);
            if (id == null) return null;
            int colon = id.indexOf(':');
            if (colon >= 0) return id.substring(0, colon);
            if ("downloads".equalsIgnoreCase(id)) return StorageId.PRIMARY;
        } catch (Throwable t) {
            Log.e(TAG, "getSelectedStorageId: " + t.getMessage());
        }
        return null;
    }

    private static File getSelectedRootAbsoluteFile(Context context) {
        String relative = getSelectedRootRelativePath(context);
        String storageId = getSelectedStorageId(context);
        if (relative == null || storageId == null) return null;
        File volumeRoot = StorageId.PRIMARY.equalsIgnoreCase(storageId)
                ? Environment.getExternalStorageDirectory() : new File("/storage", storageId);
        return relative.isEmpty() ? volumeRoot : new File(volumeRoot, relative);
    }

    private static String irisRelativeFromAbsolutePath(Context context, String absolutePath) {
        if (context == null || absolutePath == null) return null;
        File iris = getIrisCameraAbsoluteFile(context);
        if (iris == null) return null;
        String root = iris.getAbsolutePath();
        String target = new File(absolutePath).getAbsolutePath();
        if (target.equals(root)) return "";
        String prefix = root.endsWith(File.separator) ? root : root + File.separator;
        if (!target.startsWith(prefix)) return null;
        return target.substring(prefix.length()).replace(File.separatorChar, '/');
    }

    private static String dcimCameraRelativeFromAbsolutePath(String absolutePath) {
        if (absolutePath == null || FileManager.sDCIM_CAMERA == null) return null;
        String root = FileManager.sDCIM_CAMERA.getAbsolutePath();
        String target = new File(absolutePath).getAbsolutePath();
        String prefix = root.endsWith(File.separator) ? root : root + File.separator;
        if (!target.startsWith(prefix)) return null;
        String rel = target.substring(prefix.length()).replace(File.separatorChar, '/');
        return rel.contains("/") ? null : rel;
    }

    public static DocumentFile getIrisCameraFolder(Context context) {
        if (isDownloadsBackend(context)) return null;
        DocumentFile selected = getStorageRoot(context);
        if (selected == null) return null;
        DocumentFile iris = selected.findFile(IRIS_CAMERA_DIR_NAME);
        return iris != null && iris.isDirectory() ? iris : null;
    }

    public static String[] listBackupFileNames(Context context) {
        if (context == null) return new String[0];
        ArrayList<String> names = new ArrayList<>();
        if (isDownloadsBackend(context)) {
            String relative = downloadsRelativeDirectory("");
            Uri collection = downloadsCollection();
            if (collection == null) return new String[0];
            String[] projection = {MediaStore.MediaColumns.DISPLAY_NAME};
            try (Cursor cursor = context.getContentResolver().query(collection, projection,
                    MediaStore.MediaColumns.RELATIVE_PATH + "=?", new String[]{relative}, null)) {
                if (cursor != null) while (cursor.moveToNext()) {
                    String name = cursor.getString(0);
                    if (name != null && (name.endsWith(".json") || name.endsWith(".xml"))) names.add(name);
                }
            } catch (Throwable t) {
                Log.e(TAG, "listBackupFileNames downloads: " + t.getMessage());
            }
        } else {
            DocumentFile folder = getIrisCameraFolder(context);
            if (folder == null || !folder.exists()) return new String[0];
            for (DocumentFile f : folder.listFiles()) {
                if (f == null || f.isDirectory()) continue;
                String name = f.getName();
                if (name != null && (name.endsWith(".json") || name.endsWith(".xml"))) names.add(name);
            }
        }
        names.sort(String::compareToIgnoreCase);
        return names.toArray(new String[0]);
    }

    public static OutputStream openOutputStream(Context context, String fileName) throws Exception {
        OutputStream os = openIrisOutputStream(context, fileName, "application/json", false);
        if (os == null) throw new IOException("Failed to open output stream for: " + fileName);
        return os;
    }

    public static InputStream openInputStream(Context context, String fileName) throws Exception {
        InputStream is = openIrisInputStream(context, fileName);
        if (is == null) throw new FileNotFoundException("Iris file not found: " + fileName);
        return is;
    }

    public static boolean irisFileExists(String relativeInsideIris) {
        return sContext != null && irisFileExists(sContext, relativeInsideIris);
    }

    public static boolean irisFileExists(Context context, String relativeInsideIris) {
        return getIrisFileUri(context, relativeInsideIris) != null;
    }

    public static InputStream openIrisInputStream(String relativeInsideIris) throws Exception {
        return sContext == null ? null : openIrisInputStream(sContext, relativeInsideIris);
    }

    public static InputStream openIrisInputStream(Context context, String relativeInsideIris) throws Exception {
        Uri uri = getIrisFileUri(context, relativeInsideIris);
        return uri == null ? null : context.getContentResolver().openInputStream(uri);
    }

    public static OutputStream openIrisOutputStream(String relativeInsideIris, String mime) throws Exception {
        return sContext == null ? null : openIrisOutputStream(sContext, relativeInsideIris, mime, false);
    }

    public static OutputStream openIrisAppendOutputStream(Context context, String relativeInsideIris, String mime)
            throws Exception {
        return openIrisOutputStream(context, relativeInsideIris, mime, true);
    }

    private static OutputStream openIrisOutputStream(Context context, String relativeInsideIris, String mime,
                                                     boolean append) throws Exception {
        Uri uri = getOrCreateIrisFileUri(context, relativeInsideIris, mime, !append);
        if (uri == null) return null;
        return context.getContentResolver().openOutputStream(uri, append ? "wa" : "w");
    }

    /** URI-level owner used by Spektra and the logger so both SAF and Downloads backends are valid. */
    public static Uri getOrCreateIrisFileUri(Context context, String relativeInsideIris, String mime,
                                             boolean replace) {
        if (context == null) return null;
        if (isDownloadsBackend(context)) {
            return getOrCreateDownloadsUri(context, relativeInsideIris, mime, replace);
        }
        DocumentFile file = resolveIrisDocument(context, relativeInsideIris, true, mime, replace);
        return file == null ? null : file.getUri();
    }

    private static Uri getIrisFileUri(Context context, String relativeInsideIris) {
        if (context == null) return null;
        if (isDownloadsBackend(context)) return findDownloadsUri(context, relativeInsideIris);
        DocumentFile file = resolveIrisDocument(context, relativeInsideIris, false, null, false);
        return file == null || file.isDirectory() ? null : file.getUri();
    }

    /** SAF-only compatibility API retained for old callers; new code should use URI/stream APIs above. */
    public static DocumentFile createOrReplaceIrisFile(Context context, String relativeInsideIris, String mime) {
        if (isDownloadsBackend(context)) return null;
        return resolveIrisDocument(context, relativeInsideIris, true, mime, true);
    }

    private static DocumentFile resolveIrisDocument(Context context, String relativeInsideIris,
                                                     boolean createParents, String mime, boolean replaceFile) {
        if (context == null || isDownloadsBackend(context)) return null;
        DocumentFile iris = getIrisCameraFolder(context);
        if (iris == null) return null;
        String clean = trimSlashes(relativeInsideIris);
        if (clean.isEmpty()) return iris;
        String[] parts = clean.split("/");
        DocumentFile current = iris;
        for (int i = 0; i < parts.length - 1; i++) {
            if (parts[i].isEmpty()) continue;
            DocumentFile next = current.findFile(parts[i]);
            if (next == null && createParents) next = current.createDirectory(parts[i]);
            if (next == null || !next.isDirectory()) return null;
            current = next;
        }
        String leaf = parts[parts.length - 1];
        DocumentFile existing = current.findFile(leaf);
        if (mime == null) return existing;
        if (existing != null && replaceFile && !existing.delete()) return null;
        if (existing != null && !replaceFile) return existing;
        return current.createFile(mime, leaf);
    }

    private static DocumentFile findOrCreateDirectory(DocumentFile parent, String name) {
        DocumentFile existing = parent.findFile(name);
        if (existing != null) return existing.isDirectory() ? existing : null;
        return parent.createDirectory(name);
    }

    private static String trimSlashes(String value) {
        if (value == null) return "";
        return value.replaceAll("^/+|/+$", "");
    }

    private static Uri downloadsCollection() {
        return Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q
                ? MediaStore.Downloads.getContentUri(MediaStore.VOLUME_EXTERNAL_PRIMARY) : null;
    }

    private static String downloadsRelativeDirectory(String relativeInsideIris) {
        String clean = trimSlashes(relativeInsideIris);
        int slash = clean.lastIndexOf('/');
        String folder = slash >= 0 ? clean.substring(0, slash) : "";
        StringBuilder out = new StringBuilder(Environment.DIRECTORY_DOWNLOADS)
                .append('/').append(IRIS_CAMERA_DIR_NAME).append('/');
        if (!folder.isEmpty()) out.append(folder).append('/');
        return out.toString();
    }

    private static String leafName(String relativeInsideIris) {
        String clean = trimSlashes(relativeInsideIris);
        int slash = clean.lastIndexOf('/');
        return slash >= 0 ? clean.substring(slash + 1) : clean;
    }

    private static Uri findDownloadsUri(Context context, String relativeInsideIris) {
        Uri collection = downloadsCollection();
        String leaf = leafName(relativeInsideIris);
        if (collection == null || leaf.isEmpty()) return null;
        String[] projection = {MediaStore.MediaColumns._ID};
        String selection = MediaStore.MediaColumns.DISPLAY_NAME + "=? AND "
                + MediaStore.MediaColumns.RELATIVE_PATH + "=?";
        String[] args = {leaf, downloadsRelativeDirectory(relativeInsideIris)};
        try (Cursor cursor = context.getContentResolver().query(collection, projection, selection, args, null)) {
            if (cursor != null && cursor.moveToFirst()) {
                return ContentUris.withAppendedId(collection, cursor.getLong(0));
            }
        } catch (Throwable t) {
            Log.e(TAG, "findDownloadsUri: " + t.getMessage());
        }
        return null;
    }

    private static Uri getOrCreateDownloadsUri(Context context, String relativeInsideIris, String mime,
                                               boolean replace) {
        Uri existing = findDownloadsUri(context, relativeInsideIris);
        if (existing != null && !replace) return existing;
        if (existing != null) {
            try { context.getContentResolver().delete(existing, null, null); }
            catch (Throwable t) { Log.e(TAG, "delete Downloads replacement: " + t.getMessage()); return null; }
        }
        Uri collection = downloadsCollection();
        String leaf = leafName(relativeInsideIris);
        if (collection == null || leaf.isEmpty()) return null;
        ContentValues values = new ContentValues();
        values.put(MediaStore.MediaColumns.DISPLAY_NAME, leaf);
        values.put(MediaStore.MediaColumns.MIME_TYPE, mime == null ? guessMime(leaf) : mime);
        values.put(MediaStore.MediaColumns.RELATIVE_PATH, downloadsRelativeDirectory(relativeInsideIris));
        try {
            return context.getContentResolver().insert(collection, values);
        } catch (Throwable t) {
            Log.e(TAG, "getOrCreateDownloadsUri: " + t.getMessage());
            return null;
        }
    }

    /** Delete old Iris normal/MotionTrace log files without changing logger threading or formatting. */
    public static void cleanupIrisLogFiles(Context context, long cutoffMillis) {
        if (context == null) return;
        if (isDownloadsBackend(context)) {
            Uri collection = downloadsCollection();
            if (collection == null) return;
            String[] projection = {MediaStore.MediaColumns._ID, MediaStore.MediaColumns.DISPLAY_NAME,
                    MediaStore.MediaColumns.DATE_MODIFIED};
            String selection = MediaStore.MediaColumns.RELATIVE_PATH + "=?";
            String[] args = {downloadsRelativeDirectory(IRIS_LOGS_DIR_NAME + "/x")};
            try (Cursor cursor = context.getContentResolver().query(collection, projection, selection, args, null)) {
                if (cursor == null) return;
                while (cursor.moveToNext()) {
                    String name = cursor.getString(1);
                    long modified = cursor.getLong(2) * 1000L;
                    if (isIrisLogName(name) && modified > 0 && modified < cutoffMillis) {
                        context.getContentResolver().delete(
                                ContentUris.withAppendedId(collection, cursor.getLong(0)), null, null);
                    }
                }
            } catch (Throwable t) {
                Log.e(TAG, "cleanupIrisLogFiles downloads: " + t.getMessage());
            }
            return;
        }
        DocumentFile logs = resolveIrisDocument(context, IRIS_LOGS_DIR_NAME, false, null, false);
        if (logs == null || !logs.isDirectory()) return;
        for (DocumentFile file : logs.listFiles()) {
            if (file == null || file.isDirectory()) continue;
            if (isIrisLogName(file.getName()) && file.lastModified() > 0 && file.lastModified() < cutoffMillis) {
                file.delete();
            }
        }
    }

    private static boolean isIrisLogName(String name) {
        return name != null && ((name.startsWith("log-") && name.endsWith(".txt"))
                || (name.startsWith("motion-trace-") && name.endsWith(".txt")));
    }

    /** Generic compatibility helper for callers that already hold a primary-storage relative path. */
    public static boolean fileExistsByPath(Context context, String relativePath) {
        try {
            DocumentFile file = DocumentFileCompat.INSTANCE.fromSimplePath(context, StorageId.PRIMARY, relativePath);
            return file != null && file.exists();
        } catch (Throwable t) {
            Log.e(TAG, "fileExistsByPath: " + t.getMessage());
            return false;
        }
    }

    public static InputStream openInputStreamByPath(Context context, String relativePath) throws Exception {
        DocumentFile file = DocumentFileCompat.INSTANCE.fromSimplePath(context, StorageId.PRIMARY, relativePath);
        if (file == null || !file.exists()) throw new FileNotFoundException("File not found: " + relativePath);
        InputStream is = context.getContentResolver().openInputStream(file.getUri());
        if (is == null) throw new IOException("Failed to open stream for: " + relativePath);
        return is;
    }

    public static int openFdForWrite(String absolutePath) {
        if (sContext == null || absolutePath == null) return -1;
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.R) {
            try {
                File target = new File(absolutePath);
                File parent = target.getParentFile();
                if (parent != null && !parent.isDirectory() && !parent.mkdirs()) return -1;
                ParcelFileDescriptor pfd = ParcelFileDescriptor.open(target,
                        ParcelFileDescriptor.MODE_CREATE | ParcelFileDescriptor.MODE_TRUNCATE
                                | ParcelFileDescriptor.MODE_READ_WRITE);
                return pfd.detachFd();
            } catch (Exception e) {
                Log.e(TAG, "openFdForWrite legacy: " + e.getMessage());
                return -1;
            }
        }
        try {
            Uri uri = createOrReplaceUriForAbsolutePath(absolutePath);
            if (uri == null) return -1;
            ParcelFileDescriptor pfd = sContext.getContentResolver().openFileDescriptor(uri, "rw");
            return pfd == null ? -1 : pfd.detachFd();
        } catch (Exception e) {
            Log.e(TAG, "openFdForWrite: " + e.getMessage());
            return -1;
        }
    }

    public static OutputStream openOutputStreamByAbsPath(String absolutePath) {
        if (sContext == null || absolutePath == null) return null;
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.R) {
            try {
                File target = new File(absolutePath);
                File parent = target.getParentFile();
                if (parent != null && !parent.isDirectory() && !parent.mkdirs()) return null;
                return new FileOutputStream(target, false);
            } catch (Exception e) {
                Log.e(TAG, "openOutputStreamByAbsPath legacy: " + e.getMessage());
                return null;
            }
        }
        try {
            Uri uri = createOrReplaceUriForAbsolutePath(absolutePath);
            return uri == null ? null : sContext.getContentResolver().openOutputStream(uri, "w");
        } catch (Exception e) {
            Log.e(TAG, "openOutputStreamByAbsPath: " + e.getMessage());
            return null;
        }
    }

    public static boolean deleteByAbsPath(String absolutePath) {
        if (sContext == null || absolutePath == null) return false;
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.R) {
            File f = new File(absolutePath);
            return !f.exists() || f.delete();
        }
        Uri uri = findUriForAbsolutePath(absolutePath);
        if (uri == null) return true;
        try { return sContext.getContentResolver().delete(uri, null, null) >= 0; }
        catch (Throwable t) { Log.e(TAG, "deleteByAbsPath: " + t.getMessage()); return false; }
    }

    public static long lengthByAbsPath(String absolutePath) {
        if (sContext == null || absolutePath == null) return -1L;
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.R) return new File(absolutePath).length();
        Uri uri = findUriForAbsolutePath(absolutePath);
        if (uri == null) return -1L;
        try (ParcelFileDescriptor pfd = sContext.getContentResolver().openFileDescriptor(uri, "r")) {
            return pfd == null ? -1L : pfd.getStatSize();
        } catch (Exception e) {
            Log.e(TAG, "lengthByAbsPath: " + e.getMessage());
            return -1L;
        }
    }

    private static Uri createOrReplaceUriForAbsolutePath(String absolutePath) {
        String dcimLeaf = dcimCameraRelativeFromAbsolutePath(absolutePath);
        if (dcimLeaf != null) return getOrCreateDcimCameraUri(sContext, dcimLeaf, true);
        String relative = irisRelativeFromAbsolutePath(sContext, absolutePath);
        if (relative == null || relative.isEmpty()) {
            Log.e(TAG, "target outside Iris/DCIM owners: " + absolutePath);
            return null;
        }
        return getOrCreateIrisFileUri(sContext, relative, guessMime(new File(absolutePath).getName()), true);
    }

    private static Uri findUriForAbsolutePath(String absolutePath) {
        String dcimLeaf = dcimCameraRelativeFromAbsolutePath(absolutePath);
        if (dcimLeaf != null) return findDcimCameraUri(sContext, dcimLeaf);
        String relative = irisRelativeFromAbsolutePath(sContext, absolutePath);
        return relative == null || relative.isEmpty() ? null : getIrisFileUri(sContext, relative);
    }

    private static Uri dcimImagesCollection() {
        return Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q
                ? MediaStore.Images.Media.getContentUri(MediaStore.VOLUME_EXTERNAL_PRIMARY) : null;
    }

    private static Uri findDcimCameraUri(Context context, String displayName) {
        Uri collection = dcimImagesCollection();
        if (context == null || collection == null || displayName == null) return null;
        String[] projection = {MediaStore.MediaColumns._ID};
        String relative = Environment.DIRECTORY_DCIM + "/Camera/";
        String selection = MediaStore.MediaColumns.DISPLAY_NAME + "=? AND "
                + MediaStore.MediaColumns.RELATIVE_PATH + "=?";
        try (Cursor cursor = context.getContentResolver().query(collection, projection, selection,
                new String[]{displayName, relative}, null)) {
            if (cursor != null && cursor.moveToFirst()) {
                return ContentUris.withAppendedId(collection, cursor.getLong(0));
            }
        } catch (Throwable t) {
            Log.e(TAG, "findDcimCameraUri: " + t.getMessage());
        }
        return null;
    }

    private static Uri getOrCreateDcimCameraUri(Context context, String displayName, boolean replace) {
        Uri existing = findDcimCameraUri(context, displayName);
        if (existing != null && !replace) return existing;
        if (existing != null) {
            try { context.getContentResolver().delete(existing, null, null); }
            catch (Throwable t) { Log.e(TAG, "delete DCIM replacement: " + t.getMessage()); return null; }
        }
        Uri collection = dcimImagesCollection();
        if (context == null || collection == null) return null;
        ContentValues values = new ContentValues();
        values.put(MediaStore.MediaColumns.DISPLAY_NAME, displayName);
        values.put(MediaStore.MediaColumns.MIME_TYPE, "image/x-adobe-dng");
        values.put(MediaStore.MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_DCIM + "/Camera/");
        try { return context.getContentResolver().insert(collection, values); }
        catch (Throwable t) { Log.e(TAG, "getOrCreateDcimCameraUri: " + t.getMessage()); return null; }
    }

    private static String guessMime(String fileName) {
        String lower = fileName.toLowerCase(Locale.US);
        if (lower.endsWith(".flac")) return "audio/flac";
        if (lower.endsWith(".csv") || lower.endsWith(".gcsv")) return "text/csv";
        if (lower.endsWith(".txt") || lower.endsWith(".ini")) return "text/plain";
        if (lower.endsWith(".json")) return "application/json";
        if (lower.endsWith(".jpg") || lower.endsWith(".jpeg")) return "image/jpeg";
        if (lower.endsWith(".png")) return "image/png";
        if (lower.endsWith(".dng")) return "image/x-adobe-dng";
        if (lower.endsWith(".zip")) return "application/zip";
        return "application/octet-stream";
    }
}
