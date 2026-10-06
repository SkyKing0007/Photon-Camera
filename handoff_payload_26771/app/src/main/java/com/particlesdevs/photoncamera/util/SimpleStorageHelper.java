package com.particlesdevs.photoncamera.util;

import android.content.Context;
import android.content.SharedPreferences;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.os.ParcelFileDescriptor;
import android.provider.DocumentsContract;

import androidx.documentfile.provider.DocumentFile;

import com.anggrayudi.storage.file.DocumentFileCompat;
import com.anggrayudi.storage.file.DocumentFileType;
import com.anggrayudi.storage.file.StorageId;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;

/**
 * IRIS_26771_SELECTED_STORAGE_ROOT_OWNER
 *
 * One persisted SAF tree selected by the user owns Iris Camera/Tuning, Spektra and Raw on
 * Android 11+. FileManager's historical Photon-named fields remain compatibility aliases only;
 * they no longer choose or create storage. Persistent Iris logs intentionally remain owned by
 * the independent MediaStore.Downloads logger in {@link Log}.
 */
public final class SimpleStorageHelper {
    private static final String TAG = "SimpleStorageHelper";
    private static final String PREFS = "iris_storage_access";
    private static final String KEY_TREE_URI = "selected_tree_uri";

    public static final String IRIS_CAMERA_DIR_NAME = "Iris Camera";
    public static final String IRIS_TUNING_DIR_NAME = "Tuning";
    public static final String IRIS_SPEKTRA_DIR_NAME = "Spektra";
    public static final String IRIS_RAW_DIR_NAME = "Raw";

    private static Context sContext;

    private SimpleStorageHelper() {}

    public static void init(Context context) {
        sContext = context == null ? null : context.getApplicationContext();
        if (sContext != null && hasStorageAccess(sContext)) {
            // Restore compatibility aliases immediately on process restart without creating folders.
            updateFileManagerPaths(sContext);
        }
    }

    /** Persist the exact tree returned by RequestStorageAccessContract. */
    public static boolean setStorageRoot(Context context, DocumentFile root) {
        if (context == null || root == null || root.getUri() == null || !root.exists() || !root.canWrite()) {
            return false;
        }
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .edit().putString(KEY_TREE_URI, root.getUri().toString()).apply();
        Log.i(TAG, "IRIS_26771_STORAGE_ROOT_SELECTED uri=" + root.getUri());
        return true;
    }

    public static Uri getStorageRootUri(Context context) {
        if (context == null) return null;
        String raw = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .getString(KEY_TREE_URI, null);
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

    /** Any still-valid device-storage tree is accepted; there is no DCIM/path-name gate. */
    public static boolean hasStorageAccess(Context context) {
        if (getStorageRoot(context) == null) return false;
        return Build.VERSION.SDK_INT < Build.VERSION_CODES.R || getSelectedRootAbsoluteFile(context) != null;
    }

    /**
     * Create the Iris-owned hierarchy under the selected SAF tree. Photon FileManager is not
     * allowed to create these folders. Logs are intentionally excluded: Log.java owns them.
     */
    public static boolean ensureIrisStorageHierarchy(Context context) {
        if (context == null) return false;
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.R) {
            File base = new File(Environment.getExternalStorageDirectory(), IRIS_CAMERA_DIR_NAME);
            File tuning = new File(base, IRIS_TUNING_DIR_NAME);
            File spektra = new File(base, IRIS_SPEKTRA_DIR_NAME);
            File raw = new File(base, IRIS_RAW_DIR_NAME);
            boolean ok = (base.isDirectory() || base.mkdirs())
                    && (tuning.isDirectory() || tuning.mkdirs())
                    && (spektra.isDirectory() || spektra.mkdirs())
                    && (raw.isDirectory() || raw.mkdirs());
            configureFileManager(base);
            return ok;
        }

        DocumentFile selected = getStorageRoot(context);
        if (selected == null) return false;
        File physical = getIrisCameraAbsoluteFile(context);
        if (physical == null) {
            Log.e(TAG, "IRIS_26771_STORAGE_ROOT_PHYSICAL_PATH_UNRESOLVED uri=" + selected.getUri());
            return false;
        }
        DocumentFile iris = findOrCreateDirectory(selected, IRIS_CAMERA_DIR_NAME);
        if (iris == null) return false;
        if (findOrCreateDirectory(iris, IRIS_TUNING_DIR_NAME) == null) return false;
        if (findOrCreateDirectory(iris, IRIS_SPEKTRA_DIR_NAME) == null) return false;
        if (findOrCreateDirectory(iris, IRIS_RAW_DIR_NAME) == null) return false;
        configureFileManager(physical);
        Log.i(TAG, "IRIS_26771_STORAGE_HIERARCHY_READY root=" + physical);
        return true;
    }

    private static void configureFileManager(File irisRoot) {
        FileManager.sPHOTON_DIR = irisRoot;
        FileManager.sPHOTON_TUNING_DIR = new File(irisRoot, IRIS_TUNING_DIR_NAME);
        FileManager.sPHOTON_RAW_DIR = new File(irisRoot, IRIS_RAW_DIR_NAME);
        FileManager.sIRIS_SPEKTRA_DIR = new File(irisRoot, IRIS_SPEKTRA_DIR_NAME);
        // sDCIM_CAMERA deliberately remains the real system DCIM/Camera owner.
    }

    /** Refresh compatibility aliases from the persisted selected root without creating folders. */
    public static void updateFileManagerPaths(Context context) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.R) {
            configureFileManager(new File(Environment.getExternalStorageDirectory(), IRIS_CAMERA_DIR_NAME));
            return;
        }
        File iris = getIrisCameraAbsoluteFile(context);
        if (iris != null) configureFileManager(iris);
    }

    public static File getIrisCameraAbsoluteFile(Context context) {
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
        Uri uri = getStorageRootUri(context);
        if (uri == null) return null;
        try {
            String authority = uri.getAuthority();
            if (authority != null && authority.contains("downloads")) {
                return Environment.DIRECTORY_DOWNLOADS;
            }
            String id = DocumentsContract.getTreeDocumentId(uri);
            if (id == null) return null;
            int colon = id.indexOf(':');
            if (colon >= 0) {
                return trimSlashes(id.substring(colon + 1));
            }
            if ("downloads".equalsIgnoreCase(id)) return Environment.DIRECTORY_DOWNLOADS;
        } catch (Throwable t) {
            Log.e(TAG, "getSelectedRootRelativePath: " + t.getMessage());
        }
        return null;
    }

    private static String getSelectedStorageId(Context context) {
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
        File volumeRoot;
        if (StorageId.PRIMARY.equalsIgnoreCase(storageId)) {
            volumeRoot = Environment.getExternalStorageDirectory();
        } else {
            volumeRoot = new File("/storage", storageId);
        }
        return relative.isEmpty() ? volumeRoot : new File(volumeRoot, relative);
    }

    /**
     * Convert the compatibility absolute path used by existing RAW/DNG/native call sites back into
     * the persisted Iris SAF tree. The absolute path is a routing token only on Android 11+; file
     * creation/writes still go through ContentResolver and the selected tree grant.
     */
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

    public static DocumentFile getIrisCameraFolder(Context context) {
        DocumentFile selected = getStorageRoot(context);
        if (selected == null) return null;
        DocumentFile iris = selected.findFile(IRIS_CAMERA_DIR_NAME);
        return iris != null && iris.isDirectory() ? iris : null;
    }

    public static String[] listBackupFileNames(Context context) {
        DocumentFile folder = getIrisCameraFolder(context);
        if (folder == null || !folder.exists()) return new String[0];
        java.util.ArrayList<String> names = new java.util.ArrayList<>();
        for (DocumentFile f : folder.listFiles()) {
            if (f == null || f.isDirectory()) continue;
            String name = f.getName();
            if (name != null && (name.endsWith(".json") || name.endsWith(".xml"))) names.add(name);
        }
        names.sort(String::compareToIgnoreCase);
        return names.toArray(new String[0]);
    }

    public static OutputStream openOutputStream(Context context, String fileName) throws Exception {
        DocumentFile file = createOrReplaceIrisFile(context, fileName, "application/json");
        if (file == null) throw new IOException("Failed to create Iris file: " + fileName);
        OutputStream os = context.getContentResolver().openOutputStream(file.getUri(), "w");
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
        return resolveIrisDocument(context, relativeInsideIris, false, null, false) != null;
    }

    public static InputStream openIrisInputStream(String relativeInsideIris) throws Exception {
        if (sContext == null) return null;
        return openIrisInputStream(sContext, relativeInsideIris);
    }

    public static InputStream openIrisInputStream(Context context, String relativeInsideIris) throws Exception {
        DocumentFile file = resolveIrisDocument(context, relativeInsideIris, false, null, false);
        if (file == null || !file.exists() || file.isDirectory()) return null;
        return context.getContentResolver().openInputStream(file.getUri());
    }

    public static OutputStream openIrisOutputStream(String relativeInsideIris, String mime) throws Exception {
        if (sContext == null) return null;
        DocumentFile file = createOrReplaceIrisFile(sContext, relativeInsideIris, mime);
        return file == null ? null : sContext.getContentResolver().openOutputStream(file.getUri(), "w");
    }

    public static DocumentFile createOrReplaceIrisFile(Context context, String relativeInsideIris, String mime) {
        return resolveIrisDocument(context, relativeInsideIris, true, mime, true);
    }

    private static DocumentFile resolveIrisDocument(
            Context context,
            String relativeInsideIris,
            boolean createParents,
            String mime,
            boolean replaceFile) {
        if (context == null) return null;
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

    /** Generic compatibility helper for callers that already hold a primary-storage relative path. */
    public static InputStream openInputStreamByPath(Context context, String relativePath) throws Exception {
        DocumentFile file = DocumentFileCompat.INSTANCE.fromSimplePath(context, StorageId.PRIMARY, relativePath);
        if (file == null || !file.exists()) throw new FileNotFoundException("File not found: " + relativePath);
        InputStream is = context.getContentResolver().openInputStream(file.getUri());
        if (is == null) throw new IOException("Failed to open stream for: " + relativePath);
        return is;
    }

    /**
     * Create/write a file addressed by an existing compatibility absolute path. On Android 11+
     * the selected SAF tree remains the sole authority; direct filesystem access is never used.
     */
    public static int openFdForWrite(String absolutePath) {
        if (sContext == null || absolutePath == null) return -1;
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.R) {
            try {
                File target = new File(absolutePath);
                File parent = target.getParentFile();
                if (parent != null && !parent.isDirectory() && !parent.mkdirs()) return -1;
                ParcelFileDescriptor pfd = ParcelFileDescriptor.open(
                        target,
                        ParcelFileDescriptor.MODE_CREATE
                                | ParcelFileDescriptor.MODE_TRUNCATE
                                | ParcelFileDescriptor.MODE_READ_WRITE);
                return pfd.detachFd();
            } catch (Exception e) {
                Log.e(TAG, "openFdForWrite legacy: " + e.getMessage());
                return -1;
            }
        }
        try {
            DocumentFile newFile = createDocumentFile(absolutePath);
            if (newFile == null) return -1;
            ParcelFileDescriptor pfd = sContext.getContentResolver().openFileDescriptor(newFile.getUri(), "rw");
            if (pfd == null) return -1;
            return pfd.detachFd();
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
            DocumentFile newFile = createDocumentFile(absolutePath);
            if (newFile == null) return null;
            return sContext.getContentResolver().openOutputStream(newFile.getUri(), "w");
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
        String relative = irisRelativeFromAbsolutePath(sContext, absolutePath);
        if (relative == null) return false;
        DocumentFile file = resolveIrisDocument(sContext, relative, false, null, false);
        return file == null || !file.exists() || file.delete();
    }

    public static long lengthByAbsPath(String absolutePath) {
        if (sContext == null || absolutePath == null) return -1L;
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.R) return new File(absolutePath).length();
        String relative = irisRelativeFromAbsolutePath(sContext, absolutePath);
        if (relative == null) return -1L;
        DocumentFile file = resolveIrisDocument(sContext, relative, false, null, false);
        if (file == null) return -1L;
        try (ParcelFileDescriptor pfd = sContext.getContentResolver().openFileDescriptor(file.getUri(), "r")) {
            if (pfd != null) {
                long stat = pfd.getStatSize();
                if (stat >= 0L) return stat;
            }
        } catch (Exception e) {
            Log.e(TAG, "lengthByAbsPath stat: " + e.getMessage());
        }
        return file.length();
    }

    private static DocumentFile createDocumentFile(String absolutePath) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.R) return null;
        String relative = irisRelativeFromAbsolutePath(sContext, absolutePath);
        if (relative == null || relative.isEmpty()) {
            Log.e(TAG, "createDocumentFile: target outside Iris root: " + absolutePath);
            return null;
        }
        return resolveIrisDocument(sContext, relative, true, guessMime(new File(absolutePath).getName()), true);
    }

    private static String guessMime(String fileName) {
        String lower = fileName.toLowerCase(java.util.Locale.US);
        if (lower.endsWith(".flac")) return "audio/flac";
        if (lower.endsWith(".csv") || lower.endsWith(".gcsv")) return "text/csv";
        if (lower.endsWith(".txt") || lower.endsWith(".ini")) return "text/plain";
        if (lower.endsWith(".json")) return "application/json";
        if (lower.endsWith(".jpg") || lower.endsWith(".jpeg")) return "image/jpeg";
        if (lower.endsWith(".png")) return "image/png";
        if (lower.endsWith(".dng")) return "image/x-adobe-dng";
        return "application/octet-stream";
    }
}
