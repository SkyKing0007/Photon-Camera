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
    public enum Mode {
        ORIGINAL_26850("A"), AMAZE_26855("B"), BOTH("AB");
        public final String id;
        Mode(String id) { this.id = id; }
        public static Mode parse(String id) {
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
        if (preferences.contains(PREFIX + physical)) return Mode.parse(preferences.getString(PREFIX + physical, "A"));
        if (logicalId != null && preferences.contains(PREFIX + logicalId))
            return Mode.parse(preferences.getString(PREFIX + logicalId, "A"));
        return Mode.ORIGINAL_26850;
    }
    public static void write(Context context, String lensId, Mode mode) {
        if (mode == null) throw new IllegalArgumentException("missing experiment");
        store(context).edit().putString(PREFIX + identity(lensId, null), mode.id).apply();
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
