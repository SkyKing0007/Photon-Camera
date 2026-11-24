package com.particlesdevs.photoncamera.settings;

import android.content.Context;
import android.content.SharedPreferences;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CameraManager;
import android.os.Build;
import java.util.Collections;
import java.util.SortedSet;
import java.util.TreeSet;

/**
 * IRIS_26856_PHYSICAL_LENS_AB_SHUTTER_OWNER.
 * Persist only user intent. Selection is snapped into the existing immutable
 * capture plan at shutter; never reread mutable preferences inside GPU work.
 * No capture, AE, ZSL, lens routing or image processing is performed here.
 */
public final class Iris26856ABSettings {
    private static final String FILE = "iris_26856_physical_lens_ab";
    private static final String PREFIX = "physical_";
    private static final String C_SESSION = "iris_26976_c_session";
    public enum Mode {
        ORIGINAL_26850("A"), AMAZE_26855("B"), BJZHOU_26972C("C");
        public final String id;
        Mode(String id) { this.id = id; }
        public static Mode parse(String id) {
            // The discontinued A+B setting must never activate the dormant dual
            // capture path. Preserve a legacy selection as B-only on upgrade.
            if ("AB".equals(id)) return AMAZE_26855;
            for (Mode mode : values()) if (mode.id.equals(id)) return mode;
            // Fail closed on restored/corrupt values; never silently enable B.
            return ORIGINAL_26850;
        }
    }
    private Iris26856ABSettings() {}
    public static String identity(String physicalId, String logicalId) {
        String id = (physicalId == null || physicalId.trim().isEmpty()) ? logicalId : physicalId;
        if (id == null || id.trim().isEmpty()) throw new IllegalArgumentException("missing camera identity");
        return id.trim();
    }
    private static SharedPreferences store(Context context) {
        return context.getApplicationContext().getSharedPreferences(FILE, Context.MODE_PRIVATE);
    }
    public static Mode read(Context context, String physicalId, String logicalId) {
        String physical = identity(physicalId, logicalId);
        SharedPreferences preferences = store(context);
        // Explicit independent C selection follows the physical lens handoffs.
        // Never overwrite a lens's saved A/B choice merely to use C.
        if (preferences.getBoolean(C_SESSION,false)) return Mode.BJZHOU_26972C;
        if (preferences.contains(PREFIX + physical)) return resolvedStoredMode(preferences,PREFIX + physical);
        if (logicalId != null && preferences.contains(PREFIX + logicalId))
            return resolvedStoredMode(preferences,PREFIX + logicalId);
        // 26890: only UNSET per-lens intent defaults to B. Explicit A, B, AB,
        // and invalid restored preference strings retain their existing behavior.
        return Mode.AMAZE_26855;
    }
    private static Mode resolvedStoredMode(SharedPreferences preferences,String key) {
        Mode saved=Mode.parse(preferences.getString(key,"A"));
        // Retain legacy per-lens C until the user explicitly chooses a session mode.
        // On explicit C exit, dormant old C values must not unexpectedly reenter C.
        return saved==Mode.BJZHOU_26972C && preferences.contains(C_SESSION) &&
                !preferences.getBoolean(C_SESSION,false) ? Mode.AMAZE_26855 : saved;
    }
    /* IRIS_26914_PERMANENT_B_HIGHLIGHT: independent of any saved old OFF preference.
     * Callers still gate by frozen Experiment B ownership. Do not restore a UI toggle.
     */
    public static boolean alternativeHighlight(Context context, String physicalId, String logicalId) {
        identity(physicalId, logicalId); // fail on missing physical identity
        return true;
    }
    public static void write(Context context, String lensId, Mode mode) {
        if (mode == null)
            throw new IllegalArgumentException("26972 reconstruction mode is required");
        String key=PREFIX + identity(lensId,null);
        SharedPreferences prefs=store(context);
        if(mode==Mode.BJZHOU_26972C) {
            // Synchronous persistence before the existing main-lens app restart.
            if(!prefs.edit().putBoolean(C_SESSION,true).commit())
                throw new IllegalStateException("C selection not persisted");
        } else if(prefs.getBoolean(C_SESSION,false) || Mode.parse(prefs.getString(key,"A"))==Mode.BJZHOU_26972C) {
            if(!prefs.edit().putBoolean(C_SESSION,false).putString(key,mode.id).commit())
                throw new IllegalStateException("C exit selection not persisted");
        } else prefs.edit().putString(key,mode.id).apply();
    }
    /** Includes logical and Camera2-advertised physical IDs. No zoom-value identity guesses. */
    public static SortedSet<String> cameraIds(Context context) {
        TreeSet<String> result = new TreeSet<>();
        try {
            CameraManager manager = (CameraManager) context.getSystemService(Context.CAMERA_SERVICE);
            if (manager != null) for (String id : manager.getCameraIdList()) {
                result.add(id);
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                    CameraCharacteristics characteristics = manager.getCameraCharacteristics(id);
                    result.addAll(characteristics.getPhysicalCameraIds());
                }
            }
        } catch (Exception ignored) { /* Settings only; never affect camera capture. */ }
        String active = PreferenceKeys.getCameraID();
        if (active != null && !active.isEmpty()) result.add(active);
        return Collections.unmodifiableSortedSet(result);
    }
    public static String lensLabel(Context context, String id) {
        String title = "Camera " + id;
        try {
            CameraManager manager = (CameraManager) context.getSystemService(Context.CAMERA_SERVICE);
            CameraCharacteristics info = manager.getCameraCharacteristics(id);
            float[] focal = info.get(CameraCharacteristics.LENS_INFO_AVAILABLE_FOCAL_LENGTHS);
            if (focal != null && focal.length > 0 && Float.isFinite(focal[0]))
                title += " (" + String.format(java.util.Locale.US, "%.1f mm", focal[0]) + ")";
        } catch (Exception ignored) { /* Physical ID may not be individually openable. */ }
        return title;
    }
}
