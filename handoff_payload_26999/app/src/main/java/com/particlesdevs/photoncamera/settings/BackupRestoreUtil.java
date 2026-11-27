package com.particlesdevs.photoncamera.settings;

import android.content.Context;
import android.content.SharedPreferences;
import androidx.preference.PreferenceManager;
import com.particlesdevs.photoncamera.R;
import com.particlesdevs.photoncamera.app.PhotonCamera;
import com.particlesdevs.photoncamera.util.FileManager;
import com.particlesdevs.photoncamera.util.Log;
import com.particlesdevs.photoncamera.util.SimpleStorageHelper;
import org.apache.commons.io.FileUtils;
import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Paths;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Set;

public class BackupRestoreUtil {
    private static volatile boolean restoring;
    public static boolean isRestoring() { return restoring; }
    /** Explicit settings owners: storage grants and hardware-discovery caches are not configs. */
    private static Map<String, SharedPreferences> stores(Context context) {
        Map<String, SharedPreferences> result = new LinkedHashMap<>();
        String pkg = context.getPackageName();
        result.put("per_lens", context.getSharedPreferences(pkg + context.getString(R.string._per_lens), Context.MODE_PRIVATE));
        result.put("cameras", context.getSharedPreferences(pkg + context.getString(R.string._cameras), Context.MODE_PRIVATE));
        result.put("devices", context.getSharedPreferences(pkg + context.getString(R.string._devices), Context.MODE_PRIVATE));
        result.put("experiment_selection", context.getSharedPreferences("iris_26856_physical_lens_ab", Context.MODE_PRIVATE));
        result.put("super_res_fallback", context.getSharedPreferences("iris_26926_b_sr_on_fallback_per_physical_lens", Context.MODE_PRIVATE));
        result.put("super_res_denoise", context.getSharedPreferences("iris26995_c_lkr_denoise", Context.MODE_PRIVATE));
        result.put("b_off_noise_selection", context.getSharedPreferences("iris_26912_b_off_noise_per_physical", Context.MODE_PRIVATE));
        result.put("spektra_preferences", context.getSharedPreferences("camera_preferences", Context.MODE_PRIVATE));
        result.put("main", PreferenceManager.getDefaultSharedPreferences(context));
        return result;
    }

    private static Map<String, Map<String, Object>> snapshot(Map<String, SharedPreferences> stores) {
        Map<String, Map<String, Object>> result = new LinkedHashMap<>();
        for (Map.Entry<String, SharedPreferences> store : stores.entrySet()) {
            Map<String, Object> values = new LinkedHashMap<>();
            for (Map.Entry<String, ?> entry : store.getValue().getAll().entrySet()) {
                Object value = entry.getValue();
                values.put(entry.getKey(), value instanceof Set<?> ? new LinkedHashSet<>((Set<?>)value) : value);
            }
            result.put(store.getKey(), values);
        }
        return result;
    }

    public static synchronized String backupSettings(Context context, String fileName) {
        try {
            String name = Iris26999XmlConfig.fileName(fileName);
            Map<String, SharedPreferences> owners = stores(context);
            Map<String, Map<String, Object>> values = snapshot(owners);
            byte[] xml = Iris26999XmlConfig.encode(values);
            if (!values.equals(Iris26999XmlConfig.decode(new ByteArrayInputStream(xml), owners.keySet())))
                throw new IOException("Configuration round-trip failed");
            SimpleStorageHelper.saveConfig(context, name, xml);
            return "Saved: " + new File(new File(FileManager.sPHOTON_DIR, SimpleStorageHelper.IRIS_CONFIGS_DIR_NAME), name).getAbsolutePath();
        } catch (Exception e) {
            Log.e("BackupRestoreUtil", "Backup: " + e.getMessage());
            return "Error: " + e.getMessage();
        }
    }

    public static synchronized String restorePreferences(Context context, String fileName) {
        try {
            Map<String, SharedPreferences> owners = stores(context);
            Map<String, Map<String, Object>> restored;
            // Complete syntax, type and scope validation before touching any preferences.
            try (InputStream in = SimpleStorageHelper.openConfig(context, fileName)) {
                restored = Iris26999XmlConfig.decode(in, owners.keySet());
            }
            Map<String, Map<String, Object>> before = snapshot(owners);
            restoring = true;
            try {
                // Main last; storage permissions and non-config state are not restored.
                for (String name : owners.keySet())
                    if (restored.containsKey(name)) replace(owners.get(name), restored.get(name));
            } catch (Exception failure) {
                for (String name : owners.keySet()) if (restored.containsKey(name)) {
                    try { replace(owners.get(name), before.get(name)); }
                    catch (Exception rollback) { failure.addSuppressed(rollback); }
                }
                throw failure;
            } finally { restoring = false; }
            PhotonCamera.restartWithDelay(context, 1000);
            return "Restored from XML: " + fileName;
        } catch (Exception e) {
            Log.e("BackupRestoreUtil", "Restore: " + e.getMessage());
            return "Error: " + e.getMessage();
        }
    }

    @SuppressWarnings("unchecked")
    private static void replace(SharedPreferences prefs, Map<String, Object> values) throws IOException {
        SharedPreferences.Editor edit = prefs.edit().clear();
        for (Map.Entry<String, Object> entry : values.entrySet()) {
            String key = entry.getKey(); Object value = entry.getValue();
            if (value instanceof String) edit.putString(key, (String)value);
            else if (value instanceof Boolean) edit.putBoolean(key, (Boolean)value);
            else if (value instanceof Integer) edit.putInt(key, (Integer)value);
            else if (value instanceof Long) edit.putLong(key, (Long)value);
            else if (value instanceof Float) edit.putFloat(key, (Float)value);
            else if (value instanceof Set<?>) edit.putStringSet(key, (Set<String>)value);
            else throw new IOException("Unsupported preference type");
        }
        if (!edit.commit()) throw new IOException("Could not persist restored preferences");
    }

    public static boolean resetPreferences(Context context) {
        File data_dir = context.getDataDir();
        File shared_prefs_dir = Paths.get(data_dir.toPath() + File.separator + "shared_prefs").toFile();
        try {
            FileUtils.deleteDirectory(shared_prefs_dir);
            return true;
        } catch (IOException e) {
            e.printStackTrace();
            return false;
        }
    }
}
