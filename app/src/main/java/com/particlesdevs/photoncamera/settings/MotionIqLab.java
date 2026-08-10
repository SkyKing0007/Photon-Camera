package com.particlesdevs.photoncamera.settings;

import com.particlesdevs.photoncamera.api.CameraMode;
import com.particlesdevs.photoncamera.app.PhotonCamera;

/**
 * IRIS_26405_MAIN_MOTION_IQ_LAB
 * Main-settings live controls for Motion IQ experiments.
 *
 * Master OFF means zero behavior changes: the normal build/Tunable path wins.
 * Master ON means values on the Motion IQ Lab settings page are read on each
 * processing run, so A/B tuning takes effect on the next capture.
 */
public final class MotionIqLab {
    private MotionIqLab() {}

    public static final String PREFIX = "pref_motion_iq_";

    public static boolean active() {
        return getBoolRaw("master_enable", false)
                && com.particlesdevs.photoncamera.processing.MotionMetrics.isActive();
    }

    /*
     * IRIS_26408_IQ_STRING_PERSISTENCE_FIX
     * Photon SettingsManager / custom settings widgets persist values as
     * Strings. Read that exact representation so IQ Lab controls actually
     * reach the processing pipeline instead of silently falling back after a
     * SharedPreferences type mismatch.
     */
    private static String getRawString(String suffix, String def) {
        try {
            SettingsManager sm = PhotonCamera.getSettingsManagerStatic();
            if (sm == null) return def;
            String v = sm.getString(
                    PreferenceKeys.SCOPE_GLOBAL, PREFIX + suffix, def);
            return v != null ? v : def;
        } catch (Throwable t) {
            return def;
        }
    }

    private static boolean parseBool(String value, boolean def) {
        if (value == null) return def;
        String v = value.trim();
        if ("1".equals(v) || "true".equalsIgnoreCase(v)) return true;
        if ("0".equals(v) || "false".equalsIgnoreCase(v)) return false;
        return def;
    }

    private static boolean getBoolRaw(String suffix, boolean def) {
        return parseBool(getRawString(suffix, def ? "1" : "0"), def);
    }

    public static float getFloat(String suffix, float def) {
        try {
            return Float.parseFloat(getRawString(suffix, Float.toString(def)));
        } catch (Throwable t) {
            return def;
        }
    }

    public static int getInt(String suffix, int def) {
        try {
            String raw = getRawString(suffix, Integer.toString(def));
            return Math.round(Float.parseFloat(raw));
        } catch (Throwable t) {
            return def;
        }
    }

    public static boolean getBool(String suffix, boolean def) {
        return parseBool(getRawString(suffix, def ? "1" : "0"), def);
    }
}