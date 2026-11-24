package com.particlesdevs.photoncamera.settings;

import android.content.Context;
import android.content.SharedPreferences;
import androidx.preference.PreferenceManager;

/** C-only, strictly physical-camera-ID-scoped MGC band controls. Never read during GPU work. */
public final class Iris26982CSharpenSettings {
    public static final String PREFIX = "iris_26982_c_mgc_band_";
    private Iris26982CSharpenSettings() { }

    public static String key(String physicalId, int band) {
        if (physicalId == null || physicalId.trim().isEmpty() || band < 0 || band > 2)
            throw new IllegalArgumentException("C sharpening requires physical lens and band 0..2");
        // Camera2 physical IDs are exact identity; encode to avoid clashes across IDs.
        String id = physicalId.trim();
        StringBuilder out = new StringBuilder(PREFIX).append(band).append('_');
        for (int i = 0; i < id.length(); i++) {
            char c = id.charAt(i);
            out.append(Integer.toHexString(c | 0x10000).substring(1));
        }
        return out.toString();
    }

    public static boolean valid(String value) {
        if (value == null) return false;
        try {
            float v = Float.parseFloat(value);
            if (!Float.isFinite(v) || v < 0f || v > 2f) return false;
            return Math.abs(v * 10f - Math.round(v * 10f)) < 0.0001f;
        } catch (NumberFormatException e) { return false; }
    }

    public static String safeValue(Context context, String physicalId, int band) {
        String key = key(physicalId, band);
        SharedPreferences prefs = PreferenceManager.getDefaultSharedPreferences(context.getApplicationContext());
        String value;
        try { value = prefs.getString(key, "1.0"); }
        catch (ClassCastException error) { value = "1.0"; }
        return valid(value) ? value : "1.0";
    }

    /** Capture-local immutable primitive copy, not a mutable preference or GPU singleton. */
    public static float[] freeze(Context context, String physicalId) {
        return new float[] {
            Float.parseFloat(safeValue(context, physicalId, 0)),
            Float.parseFloat(safeValue(context, physicalId, 1)),
            Float.parseFloat(safeValue(context, physicalId, 2)),
        };
    }
}
